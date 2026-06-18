import frappe


def item_validation(doc, method=None):
    item_extended_warranty_validation(doc)


def item_extended_warranty_validation(doc):
    if not doc.is_extended_warranty:
        ext_warranty_item_codes = frappe.get_all(
            "Extended Warranty Configure Details",
            fields=["warranty_item"],
            pluck="warranty_item",
        )
        if doc.name in ext_warranty_item_codes:
            frappe.throw("the Item configured in Extended Warranty Configure Details")
