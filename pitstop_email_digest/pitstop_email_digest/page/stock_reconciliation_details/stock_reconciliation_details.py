import frappe
from agmc_custom.overrides.stock_reconciliation.stock_reconciliation_hooks import (
    set_print_items,
)
from frappe.utils import cint, flt

ITEM_FIELDS = (
    "idx",
    "warehouse",
    "item_code",
    "oe_no",
    "item_name",
    "stock_uom",
    "loose_uom",
    "qty",
    "current_qty",
    "quantity_difference",
    "amount",
    "current_amount",
    "amount_difference",
)


@frappe.whitelist()
def get_details(
    stock_reconciliation,
    discrepancy=0,
    based_on=None,
    ignored_item_group=None,
    item_code=None,
):
    doc = frappe.get_doc("Stock Reconciliation", stock_reconciliation)
    doc.check_permission("read")

    # Rows follow the page filters, not the document's print settings (set in memory only, never saved)
    doc.discrepancy = cint(discrepancy)
    doc.based_on = based_on or "Any Difference"
    doc.ignore_item_group = 1 if ignored_item_group else 0
    doc.ignored_item_group = ignored_item_group

    if ignored_item_group:
        set_missing_item_groups(doc)

    # Same row selection as the Pitstop Stock Reconciliation print (Ignore Item Group / Discrepancy)
    set_print_items(doc)

    if item_code:
        doc.print_items = [d for d in doc.print_items if d.item_code == item_code]

    items = []
    for i, row in enumerate(doc.print_items, 1):
        item = {field: row.get(field) for field in ITEM_FIELDS}
        item["sr_no"] = i
        items.append(item)

    return {
        "header": {
            "name": doc.name,
            "docstatus": doc.docstatus,
            "company": doc.company,
            "currency": frappe.get_cached_value(
                "Company", doc.company, "default_currency"
            ),
            "default_warehouse": doc.get("default_warehouse"),
            "posting_date": doc.posting_date,
            "posting_time": doc.posting_time,
            "purpose": doc.purpose,
            "total_items": len(doc.items),
            # Item Code filter options: every item on the document
            "item_codes": sorted({d.item_code for d in doc.items}),
        },
        "items": items,
        "totals": get_totals(items),
    }


def set_missing_item_groups(doc):
    # Most rows have no Item Group saved, so take it from the Item master (in memory only, never saved)
    item_codes = list({d.item_code for d in doc.items if not d.get("item_group")})
    if not item_codes:
        return

    item_groups = dict(
        frappe.get_all(
            "Item",
            filters={"name": ("in", item_codes)},
            fields=["name", "item_group"],
            as_list=True,
        )
    )
    for d in doc.items:
        if not d.get("item_group"):
            d.item_group = item_groups.get(d.item_code)


def get_totals(items):
    totals = {
        "row_count": len(items),
        "physical_qty": 0,
        "system_qty": 0,
        "added_qty": 0,
        "minus_qty": 0,
        "qty_difference": 0,
        "added_amount": 0,
        "minus_amount": 0,
        "amount_difference": 0,
    }

    # Differences split into added (positive) and minus (negative), as in the print
    for d in items:
        qty_diff = flt(d["quantity_difference"])
        amount_diff = flt(d["amount_difference"])

        totals["physical_qty"] += flt(d["qty"])
        totals["system_qty"] += flt(d["current_qty"])
        totals["qty_difference"] += qty_diff
        totals["amount_difference"] += amount_diff

        if qty_diff > 0:
            totals["added_qty"] += qty_diff
        elif qty_diff < 0:
            totals["minus_qty"] += qty_diff

        if amount_diff > 0:
            totals["added_amount"] += amount_diff
        elif amount_diff < 0:
            totals["minus_amount"] += amount_diff

    return totals
