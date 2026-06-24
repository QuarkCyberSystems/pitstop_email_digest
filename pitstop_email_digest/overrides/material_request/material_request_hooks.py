import frappe


def on_cancel(doc, method=None):
    unlink_purchase_orders(doc)


def unlink_purchase_orders(self):
    """
    When a Material Request is cancelled, remove its reference
    from all linked Draft Purchase Order items.
    """

    # Find all Purchase Order Items linked to this Material Request
    po_items = frappe.get_all(
        "Purchase Order Item",
        filters={
            "material_request": self.name,
            "docstatus": 0,  # Only Draft POs (docstatus 0 = Draft)
        },
        fields=["name", "parent"],
    )

    if not po_items:
        frappe.msgprint(
            f"No Draft Purchase Orders found linked to {self.name}.", alert=True
        )
        return

    updated_pos = set()

    for item in po_items:
        # Clear the material_request and material_request_item fields
        frappe.db.set_value(
            "Purchase Order Item",
            item["name"],
            {"material_request": None, "material_request_item": None},
        )
        updated_pos.add(item["parent"])

    frappe.msgprint(
        f"Unlinked Material Request <b>{self.name}</b> from Purchase Order(s): "
        + ", ".join(f"<b>{po}</b>" for po in updated_pos),
        title="PO Unlinked",
        indicator="green",
    )
