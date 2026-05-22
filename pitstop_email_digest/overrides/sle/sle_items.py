import frappe


def get_sle_item_conditions(filters, conditions, alias):
    if filters.get("voucher_type") and filters.get("voucher_no"):
        items = get_items_from_voucher(
            filters.get("voucher_type"), filters.get("voucher_no")
        )
        if items:
            item_list = ", ".join([f"'{item}'" for item in items])
            conditions.append(f"{alias}.name IN ({item_list})")


def get_items_from_voucher(voucher_type, voucher_no, item_name=False):
    if item_name:
        return frappe.db.get_all(
            f"{voucher_type} Item",
            {"parent": voucher_no},
            ["item_code", "item_name", "uom", "qty", "stock_uom", "stock_qty"],
        )
    return frappe.db.get_all(
        f"{voucher_type} Item",
        {"parent": voucher_no},
        pluck="item_code",
    )
