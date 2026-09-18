"""Create a draft Stock Reconciliation from a merged item/warehouse list.

Reads the list produced by :mod:`.stock_reconciliation` - each row holding
``item_code``, ``part_no``, ``uom``, ``rate`` and ``warehouses``
(warehouse -> qty) - and turns it into one Stock Reconciliation Item per
item/warehouse pair. The document is only inserted, never submitted, so it is
left in draft for review.

Rows with a zero quantity are kept on purpose: they are the duplicate item codes
whose stock was merged into another item code, and the reconciliation is what
brings them down to zero. ERPNext drops the ones that turn out to be no-ops when
the document is submitted.

``reset_rate`` is on by default so the ``rate`` from the list is used; without it
ERPNext overwrites ``valuation_rate`` with each item's current valuation rate.

Usage::

    bench --site <site> execute \
        pitstop_email_digest.utils.stock_reconciliation.create_stock_reconciliation.create_from_file \
        --kwargs "{'file_path': 'merged_stock_list.json'}"

    # a file uploaded into ERPNext, by its attachment URL
    bench --site <site> execute \
        pitstop_email_digest.utils.stock_reconciliation.create_stock_reconciliation.create_from_file \
        --kwargs "{'file_path': '/private/files/merged_stock_list.json'}"

    # or, to split a long list over several drafts
    bench --site <site> execute \
        pitstop_email_digest.utils.stock_reconciliation.create_stock_reconciliation.create_from_file \
        --kwargs "{'file_path': 'merged_stock_list.json', 'max_rows_per_document': 200}"

    # check the rows without writing anything
    bench --site <site> execute \
        pitstop_email_digest.utils.stock_reconciliation.create_stock_reconciliation.create_from_file \
        --kwargs "{'file_path': 'merged_stock_list.json', 'dry_run': 1}"
"""

import json
import os

import frappe
from frappe import _
from frappe.utils import cint, flt, get_bench_path, get_url, nowtime, today

from .stock_reconciliation import _load, _normalize_warehouses


def build_reconciliation_items(items):
    """Flatten the list into one ``{item_code, warehouse, qty, valuation_rate}``
    row per item/warehouse pair.

    A repeated item/warehouse pair is kept only once - ERPNext rejects duplicate
    entries - and the first occurrence wins.
    """
    sr_items = []
    seen = set()

    for row in _load(items):
        item_code = row.get("item_code")
        if not item_code:
            frappe.throw(_("item_code is required for every row"))

        for warehouse, qty in _normalize_warehouses(row.get("warehouses")).items():
            if (item_code, warehouse) in seen:
                continue

            seen.add((item_code, warehouse))
            sr_items.append(
                {
                    "item_code": item_code,
                    "warehouse": warehouse,
                    "qty": flt(qty),
                    "valuation_rate": flt(row.get("rate")),
                    "uom": row.get("uom"),
                }
            )

    return sr_items


def validate_rows(sr_items):
    """Report every bad item/warehouse up front instead of one row at a time."""
    errors = []

    item_codes = {d["item_code"] for d in sr_items}
    stock_items = dict(
        frappe.get_all(
            "Item",
            filters={"name": ("in", list(item_codes))},
            fields=["name", "is_stock_item"],
            as_list=True,
        )
    )

    missing_items = sorted(item_codes - set(stock_items))
    if missing_items:
        errors.append(_("Item(s) not found: {0}").format(", ".join(missing_items)))

    non_stock = sorted(
        code for code, is_stock in stock_items.items() if not cint(is_stock)
    )
    if non_stock:
        errors.append(
            _("Item(s) are not stock items: {0}").format(", ".join(non_stock))
        )

    warehouses = {d["warehouse"] for d in sr_items}
    existing_warehouses = set(
        frappe.get_all(
            "Warehouse", filters={"name": ("in", list(warehouses))}, pluck="name"
        )
    )
    missing_warehouses = sorted(warehouses - existing_warehouses)
    if missing_warehouses:
        errors.append(
            _("Warehouse(s) not found: {0}").format(", ".join(missing_warehouses))
        )

    negative = sorted(
        "{0} @ {1}".format(d["item_code"], d["warehouse"])
        for d in sr_items
        if flt(d["qty"]) < 0
    )
    if negative:
        errors.append(
            _("Negative quantity is not allowed: {0}").format(", ".join(negative))
        )

    if errors:
        frappe.throw(
            "<br>".join(errors), title=_("Stock Reconciliation cannot be created")
        )


def check_uom(sr_items):
    """Return the rows whose ``uom`` differs from the item's stock UOM.

    Quantities on a Stock Reconciliation are in the item's stock UOM, so a
    mismatch means the qty would be read as a different unit. Reported, not
    blocked - the caller decides.
    """
    given_uoms = {}
    for row in sr_items:
        if row.get("uom"):
            given_uoms.setdefault(row["item_code"], row["uom"])

    if not given_uoms:
        return []

    stock_uoms = dict(
        frappe.get_all(
            "Item",
            filters={"name": ("in", list(given_uoms))},
            fields=["name", "stock_uom"],
            as_list=True,
        )
    )

    return [
        {"item_code": code, "given_uom": uom, "stock_uom": stock_uoms.get(code)}
        for code, uom in given_uoms.items()
        if stock_uoms.get(code) and stock_uoms[code] != uom
    ]


@frappe.whitelist()
def create_stock_reconciliation(
    items,
    company=None,
    posting_date=None,
    posting_time=None,
    purpose="Stock Reconciliation",
    expense_account=None,
    cost_center=None,
    remarks=None,
    reset_rate=1,
    max_rows_per_document=None,
    dry_run=0,
):
    """Create one or more draft Stock Reconciliations and return their names.

    With ``dry_run`` nothing is written: the validated rows are returned so the
    document can be checked before it is created.
    """
    sr_items = build_reconciliation_items(items)

    if not sr_items:
        frappe.throw(_("No item/warehouse rows to reconcile"))

    validate_rows(sr_items)

    uom_mismatches = check_uom(sr_items)
    for mismatch in uom_mismatches:
        frappe.msgprint(
            _(
                "Item {0}: list says {1} but stock UOM is {2} - quantity is taken as {2}"
            ).format(
                mismatch["item_code"], mismatch["given_uom"], mismatch["stock_uom"]
            ),
            title=_("UOM mismatch"),
            indicator="orange",
        )

    if not company:
        company = frappe.db.get_value(
            "Warehouse", sr_items[0]["warehouse"], "company"
        ) or (frappe.defaults.get_user_default("Company"))

    if not company:
        frappe.throw(_("Company is required"))

    if cint(dry_run):
        frappe.msgprint(
            _("Dry run: {0} row(s) for {1}, nothing created").format(
                len(sr_items), company
            )
        )
        return sr_items

    chunk_size = cint(max_rows_per_document) or len(sr_items)
    chunks = [sr_items[i : i + chunk_size] for i in range(0, len(sr_items), chunk_size)]

    docnames = []
    for chunk in chunks:
        doc = frappe.new_doc("Stock Reconciliation")
        doc.company = company
        doc.purpose = purpose
        doc.posting_date = posting_date or today()
        doc.posting_time = posting_time or nowtime()
        doc.set_posting_time = 1
        doc.reset_rate = 1 if cint(reset_rate) else 0
        doc.vehicle_workshop_division = "Mechanical"
        doc.cost_center = "AutoWorks - PASLLC"
        doc.branch = "Sajja"

        if expense_account:
            doc.expense_account = expense_account
        if cost_center:
            doc.cost_center = cost_center
        if remarks:
            doc.remarks = remarks

        for sr_item in chunk:
            doc.append(
                "items",
                {
                    "item_code": sr_item["item_code"],
                    "warehouse": sr_item["warehouse"],
                    "qty": sr_item["qty"],
                    "valuation_rate": sr_item["valuation_rate"],
                },
            )

        # draft only - never submitted here; permissions apply as usual, since
        # this is whitelisted and reachable from the client
        doc.insert()
        docnames.append(doc.name)

    frappe.db.commit()

    frappe.msgprint(
        _("Created {0} draft Stock Reconciliation(s) with {1} row(s): {2}").format(
            len(docnames), len(sr_items), ", ".join(docnames)
        )
    )

    return docnames


@frappe.whitelist()
def create_from_file(file_path, **kwargs):
    """Read the merged list from a JSON file and create the draft(s).

    ``file_path`` accepts any of:

    * an attachment URL - ``/private/files/merged_stock_list.json`` or
      ``/files/merged_stock_list.json`` (what the Attach field / file uploader
      gives you)
    * the name of a **File** record
    * a path on disk, absolute or relative to the bench directory
    """
    return create_stock_reconciliation(read_items(file_path), **kwargs)


def read_items(file_path):
    """Return the parsed JSON list from a File attachment or a path on disk."""
    content = _read_attachment(file_path)

    if content is None:
        path = (
            file_path
            if os.path.isabs(file_path)
            else os.path.join(get_bench_path(), file_path)
        )
        path = os.path.abspath(path)

        if not os.path.exists(path):
            frappe.throw(_("File not found: {0}").format(path))

        with open(path) as f:
            content = f.read()

    try:
        return json.loads(content)
    except ValueError as e:
        frappe.throw(_("{0} is not valid JSON: {1}").format(file_path, e))


def _read_attachment(file_path):
    """Return the contents of the matching File record, or None if there is none."""
    file_url = file_path

    # an uploader may hand over the full site URL
    site_url = get_url()
    if file_url.startswith(site_url):
        file_url = file_url[len(site_url) :]

    filters = None
    if file_url.startswith(("/files/", "/private/files/")):
        filters = {"file_url": file_url}
    elif frappe.db.exists("File", file_path):
        filters = {"name": file_path}

    if not filters:
        return None

    name = frappe.db.get_value("File", filters, "name")
    if not name:
        frappe.throw(_("No File found for {0}").format(file_path))

    content = frappe.get_doc("File", name).get_content()

    if isinstance(content, bytes):
        content = content.decode()

    return content
