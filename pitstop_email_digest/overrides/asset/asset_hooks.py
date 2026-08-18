"""Asset <-> Master Asset integration hooks.

Master Asset linking is only allowed on **submitted** Assets (docstatus == 1).
Draft Assets cannot be linked; the invariant blocks it in `validate`.

Wired in hooks.py under `doc_events["Asset"]`:
    validate                    -> resolve purchase_order, enforce MA/PO invariant,
                                   forbid MA link on Draft
    before_update_after_submit  -> same as validate (submitted-doc save path)
    on_submit                   -> auto-create/link Master Asset when PO is known,
                                   then refresh linked MA summary
    on_update / on_update_after_submit -> refresh linked MA summary
    on_cancel                   -> unlink Master Asset, refresh its summary
    on_trash                    -> refresh linked MA summary (asset being deleted)

Also exposes a whitelisted method for the Asset form's "Create Master Asset" button.
"""

import frappe
from frappe import _

# ---------- resolvers ----------


def resolve_purchase_order(asset) -> str | None:
    """Resolve the source Purchase Order for an Asset by walking PR/PI item rows.

    Returns the PO name if unambiguous, otherwise None (ambiguous or unknown).
    """
    item_code = asset.get("item_code")
    if not item_code:
        return None

    for parent_field, child_dt in (
        ("purchase_receipt", "Purchase Receipt Item"),
        ("purchase_invoice", "Purchase Invoice Item"),
    ):
        parent = asset.get(parent_field)
        if not parent:
            continue
        pos = frappe.db.sql_list(
            f"""
			select distinct child.purchase_order
			from `tab{child_dt}` child
			join `tabPurchase Order` po on po.name = child.purchase_order
			where child.parent = %s
			  and child.item_code = %s
			  and ifnull(child.purchase_order, '') != ''
			  and po.docstatus = 1
			""",
            (parent, item_code),
        )
        if len(pos) == 1:
            return pos[0]
        # ambiguous (multiple POs) or none — try the next source
    return None


# ---------- doc_events ----------


def validate(doc, method=None):
    _sync_purchase_order_field(doc)
    _forbid_master_asset_on_draft(doc)
    _validate_master_asset_po_invariant(doc)


def on_update(doc, method=None):
    _refresh_linked_master_asset(doc)


def on_submit(doc, method=None):
    # Auto-link on submit (not at insert time — Draft Assets cannot carry a MA link).
    _auto_link_master_asset(doc)
    _refresh_linked_master_asset(doc)


def on_cancel(doc, method=None):
    # Cancellation unlinks the Master Asset and refreshes its totals/status.
    prior_ma = doc.get("master_asset")
    if prior_ma:
        doc.db_set("master_asset", None, update_modified=False)
        if frappe.db.exists("Master Asset", prior_ma):
            _refresh_master_asset(prior_ma)


def on_trash(doc, method=None):
    # Refresh both current and prior MA references (asset row is about to disappear).
    _refresh_linked_master_asset(doc)


# ---------- whitelisted API for Asset form UI ----------


@frappe.whitelist()
def create_master_asset_from_asset(
    asset: str, purchase_order: str | None = None, remarks: str | None = None
) -> str:
    """Create a new Master Asset and link it to the given Asset.

    If purchase_order is given, enforces the PO uniqueness (get_or_create).
    Called from the "Create Master Asset" button on the Asset form.
    """
    asset_doc = frappe.get_doc("Asset", asset)
    asset_doc.check_permission("write")

    if asset_doc.docstatus != 1:
        frappe.throw(
            _(
                "Master Asset can only be linked to a submitted Asset. Submit Asset {0} first."
            ).format(frappe.bold(asset))
        )

    if asset_doc.get("master_asset"):
        frappe.throw(
            _("Asset {0} is already linked to Master Asset {1}.").format(
                frappe.bold(asset), frappe.bold(asset_doc.master_asset)
            )
        )

    resolved_po = (
        purchase_order
        or asset_doc.get("purchase_order")
        or resolve_purchase_order(asset_doc)
    )

    if (
        resolved_po
        and asset_doc.get("purchase_order")
        and resolved_po != asset_doc.get("purchase_order")
    ):
        frappe.throw(
            _(
                "Purchase Order {0} does not match the Asset's Purchase Order {1}."
            ).format(
                frappe.bold(resolved_po), frappe.bold(asset_doc.get("purchase_order"))
            )
        )

    if (
        resolved_po
        and frappe.db.get_value("Purchase Order", resolved_po, "docstatus") != 1
    ):
        frappe.throw(
            _(
                "Purchase Order {0} must be submitted before it can be linked to a Master Asset."
            ).format(frappe.bold(resolved_po))
        )

    if resolved_po:
        ma_name = _get_or_create_master_asset_for_po(resolved_po, asset_doc)
    else:
        ma = frappe.new_doc("Master Asset")
        ma.company = asset_doc.get("company")
        ma.supplier = asset_doc.get("supplier")
        ma.source_type = "Manual"
        ma.status = "Draft"
        if remarks:
            ma.remarks = remarks
        ma.insert()
        ma_name = ma.name

    # Persist remarks even in the get_or_create path if a new MA was created and remarks provided.
    if remarks and resolved_po:
        existing_remarks = frappe.db.get_value("Master Asset", ma_name, "remarks") or ""
        if not existing_remarks:
            frappe.db.set_value(
                "Master Asset", ma_name, "remarks", remarks, update_modified=False
            )

    asset_doc.db_set("master_asset", ma_name, update_modified=False)
    if resolved_po and asset_doc.get("purchase_order") != resolved_po:
        asset_doc.db_set("purchase_order", resolved_po, update_modified=False)

    _refresh_master_asset(ma_name)
    return ma_name


# ---------- internals ----------


def _sync_purchase_order_field(doc):
    """Keep Asset.purchase_order in sync with the PR/PI item it originated from."""
    resolved = resolve_purchase_order(doc)
    if resolved and doc.get("purchase_order") != resolved:
        doc.purchase_order = resolved
    elif (
        not resolved
        and doc.get("purchase_order")
        and (doc.get("purchase_receipt") or doc.get("purchase_invoice"))
    ):
        # The linked PR/PI no longer supports this PO — clear stale value.
        doc.purchase_order = None


def _forbid_master_asset_on_draft(doc):
    """Only submitted Assets (docstatus == 1) may be linked to a Master Asset."""
    if not doc.get("master_asset"):
        return
    if doc.docstatus == 0:
        frappe.throw(
            _(
                "Master Asset can only be linked after the Asset is submitted. Submit this Asset first, then attach it to a Master Asset."
            ),
            title=_("Asset not submitted"),
        )


def _validate_master_asset_po_invariant(doc):
    """If asset is linked to an MA that is bound to a PO, POs must match."""
    if not doc.get("master_asset"):
        return
    ma_po = frappe.db.get_value("Master Asset", doc.master_asset, "purchase_order")
    if not ma_po:
        # Manual MA — any asset can be attached.
        return
    if doc.get("purchase_order") and doc.purchase_order != ma_po:
        frappe.throw(
            _(
                "Asset belongs to Purchase Order {0}, but Master Asset {1} is bound to Purchase Order {2}."
            ).format(
                frappe.bold(doc.purchase_order),
                frappe.bold(doc.master_asset),
                frappe.bold(ma_po),
            ),
            title=_("Master Asset mismatch"),
        )
    if not doc.get("purchase_order"):
        frappe.throw(
            _(
                "Master Asset {0} is bound to Purchase Order {1}. This Asset has no Purchase Order and cannot be attached."
            ).format(frappe.bold(doc.master_asset), frappe.bold(ma_po)),
            title=_("Master Asset mismatch"),
        )


def _auto_link_master_asset(doc):
    """On submit, if we can resolve a PO, get_or_create the Master Asset and link it."""
    if doc.get("master_asset"):
        return
    po = doc.get("purchase_order") or resolve_purchase_order(doc)
    if not po:
        return

    ma_name = _get_or_create_master_asset_for_po(po, doc)
    if not ma_name:
        return

    # db_set to avoid re-triggering validate/on_update on this doc.
    doc.db_set("master_asset", ma_name, update_modified=False)
    # Also persist the resolved PO if it wasn't already stored.
    if doc.get("purchase_order") != po:
        doc.db_set("purchase_order", po, update_modified=False)

    # Refresh the MA summary to include this new asset.
    _refresh_master_asset(ma_name)


def _get_or_create_master_asset_for_po(po: str, asset_doc) -> str | None:
    """Return the Master Asset for a given PO, creating it if missing.

    Uses SELECT ... FOR UPDATE on the PO row to serialize concurrent creators.
    """
    # Lock the PO row to serialize concurrent Asset inserts sharing this PO.
    # (Any lock target tied to the PO works; the PO row itself is a natural key.)
    frappe.db.sql("select name from `tabPurchase Order` where name = %s for update", po)

    existing = frappe.db.get_value("Master Asset", {"purchase_order": po}, "name")
    if existing:
        return existing

    po_row = frappe.db.get_value(
        "Purchase Order",
        po,
        ["company", "supplier", "transaction_date"],
        as_dict=True,
    )
    if not po_row:
        return None

    ma = frappe.new_doc("Master Asset")
    ma.company = asset_doc.get("company") or po_row.company
    ma.supplier = asset_doc.get("supplier") or po_row.supplier
    ma.purchase_order = po
    ma.purchase_date = po_row.transaction_date
    ma.source_type = "From Purchase Order"
    ma.status = "Draft"
    ma.flags.ignore_permissions = True
    ma.insert()
    return ma.name


def _refresh_linked_master_asset(doc):
    """Recompute totals/status on the Asset's currently linked MA."""
    ma_name = doc.get("master_asset")
    if not ma_name:
        return
    if not frappe.db.exists("Master Asset", ma_name):
        return
    _refresh_master_asset(ma_name)


def _refresh_master_asset(ma_name: str):
    ma = frappe.get_doc("Master Asset", ma_name)
    ma.recompute_summary()
    new_status = _derive_status(ma_name)
    ma.db_set(
        {
            "total_assets": ma.total_assets,
            "total_asset_value": ma.total_asset_value,
            "status": new_status,
        },
        update_modified=False,
    )


def _derive_status(ma_name: str) -> str:
    """Derive Master Asset status from the aggregate state of its child Assets."""
    rows = frappe.db.sql(
        """
		select status, count(name) as cnt
		from `tabAsset`
		where master_asset = %s and docstatus < 2
		group by status
		""",
        ma_name,
        as_dict=True,
    )
    if not rows:
        return "Draft"

    counts = {r.status: r.cnt for r in rows}
    total = sum(counts.values())

    def only(*statuses):
        return set(counts.keys()) <= set(statuses)

    if only("Sold"):
        return "Sold"
    if only("Scrapped"):
        return "Scrapped"
    if only("Fully Depreciated"):
        return "Fully Depreciated"

    sold_or_scrapped = counts.get("Sold", 0) + counts.get("Scrapped", 0)
    if sold_or_scrapped and sold_or_scrapped < total:
        return "Partially Disposed"

    if (
        counts.get("Fully Depreciated", 0)
        and counts.get("Fully Depreciated", 0) < total
    ):
        return "Partially Depreciated"

    # If any child is submitted (In Locations / Partially Depreciated / etc.), treat MA as Active.
    if any(s not in ("Draft",) for s in counts.keys()):
        return "Active"

    return "Draft"
