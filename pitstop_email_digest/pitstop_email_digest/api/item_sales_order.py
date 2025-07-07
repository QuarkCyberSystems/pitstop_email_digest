import frappe
from frappe import _

# ──────────────────────────────────────────────────────────────
# Constants – adjust only if you use different masters
# ──────────────────────────────────────────────────────────────
DEFAULT_ITEM_GROUP = "Parts"   # must exist in Item Group master

# ──────────────────────────────────────────────────────────────
# Main API
# ──────────────────────────────────────────────────────────────
@frappe.whitelist(methods=["POST"])
def upsert_item_and_add_to_so():
    """
    POST body (JSON):
    {
        "item_code": "ABC-002",
        "item_name": "Widget 99",
        "uom":       "Nos",
        "sales_order_no": "SO-00047"
    }
    """
    data = frappe._dict(frappe.local.form_dict)

    # ------------------------------------------------------------------
    # 0) Validate incoming parameters
    # ------------------------------------------------------------------
    required = ["item_code", "item_name", "uom", "sales_order_no"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        frappe.throw(_("Missing parameters: {0}").format(", ".join(missing)))

    # ------------------------------------------------------------------
    # 1) Ensure the Item exists and is enabled for Sales & Purchase
    # ------------------------------------------------------------------
    if frappe.db.exists("Item", data.item_code):
        item = frappe.get_doc("Item", data.item_code)
        item_status = "exists"
        updated = False

        # flip flags if they’re off
        if not item.is_sales_item:
            item.is_sales_item = 1
            updated = True
        if not item.is_purchase_item:
            item.is_purchase_item = 1
            updated = True

        if updated:
            item.flags.ignore_permissions = True   # integration users may lack rights
            item.save()
            item_status = "exists-and-updated"
    else:
        item_status = "created"
        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": data.item_code,
            "item_name": data.item_name,
            "item_group": DEFAULT_ITEM_GROUP,
            "stock_uom": data.uom,
            "maintain_stock": 1,
            "is_sales_item": 1,
            "is_purchase_item": 1,
        })
        item.append("uoms", {"uom": data.uom, "conversion_factor": 1})
        item.save(ignore_permissions=True)

    # ------------------------------------------------------------------
    # 2) Load & validate the Sales Order
    # ------------------------------------------------------------------
    so = frappe.get_doc("Sales Order", data.sales_order_no)

    if so.docstatus == 2:
        return {"status": "error", "message": _("Sales Order is Cancelled")}
    if so.docstatus == 1:
        return {"status": "error", "message": _("Sales Order is Submitted")}

    if any(row.item_code == data.item_code for row in so.items):
        return {
            "status": "warning",
            "item_status": item_status,
            "message": _("Item already present on Sales Order")
        }

    # ------------------------------------------------------------------
    # 3) Append new Item row and save
    # ------------------------------------------------------------------
    so.append("items", {
        "item_code": data.item_code,
        "item_name": data.item_name,
        "uom": data.uom,
        "qty": 1,
        #"schedule_date": frappe.utils.today()
    })
    so.save()

    # ------------------------------------------------------------------
    # 4) Done
    # ------------------------------------------------------------------
    return {
        "status": "success",
        "item_status": item_status,
        "message": _("Item added to Sales Order")
    }
