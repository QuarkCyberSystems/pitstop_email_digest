import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def create_asset_custom_fields():
    """Add Master Asset section + purchase_order helper field to Asset.

    Idempotent — safe to call from after_install and from patches.
    """
    custom_fields = {
        "Asset": [
            {
                "fieldname": "master_asset_section",
                "label": "Master Asset",
                "fieldtype": "Section Break",
                "insert_after": "purchase_receipt",
                "collapsible": 0,
            },
            {
                "fieldname": "master_asset",
                "label": "Master Asset",
                "fieldtype": "Link",
                "options": "Master Asset",
                "insert_after": "master_asset_section",
                "in_standard_filter": 1,
                "no_copy": 1,
                "allow_on_submit": 1,
                "description": "Groups this Asset under a parent Master Asset (e.g. all Assets from the same Purchase Order).",
            },
            {
                "fieldname": "column_break_master_asset",
                "fieldtype": "Column Break",
                "insert_after": "master_asset",
            },
            {
                "fieldname": "purchase_order",
                "label": "Purchase Order",
                "fieldtype": "Link",
                "options": "Purchase Order",
                "insert_after": "column_break_master_asset",
                "read_only": 1,
                "in_standard_filter": 1,
                "no_copy": 1,
                "allow_on_submit": 1,
                "description": "Resolved from the source Purchase Receipt / Invoice item row.",
            },
        ]
    }
    create_custom_fields(custom_fields, update=True)
    frappe.clear_cache(doctype="Asset")
