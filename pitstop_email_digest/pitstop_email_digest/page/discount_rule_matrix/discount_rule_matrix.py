"""Discount Rule Cards: Discount Rules grouped by Role, then Customer / Customer Group."""

import frappe


@frappe.whitelist()
def get_discount_rules(company=None, role=None):
    frappe.has_permission("Discount Rule", "read", throw=True)

    filters = {}
    if company:
        filters["company"] = company
    if role:
        filters["role"] = role

    return frappe.get_list(
        "Discount Rule",
        filters=filters,
        fields=[
            "name",
            "role",
            "user",
            "company",
            "customer_group",
            "customer",
            "customer_name",
            "territory",
            "item_group",
            "item_code",
            "item_name",
            "brand",
            "item_source",
            "applies_to_item",
            "applies_to_item_name",
            "applies_to_item_group",
            "applies_to_item_brand",
            "max_discount",
        ],
        order_by="role asc, customer_group asc, max_discount asc",
        limit_page_length=0,
    )
