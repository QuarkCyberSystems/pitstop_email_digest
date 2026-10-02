# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _, qb
from frappe.utils import getdate


def execute(filters=None):
    return OrderItems(filters).run()


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_branches(doctype, txt, searchfield, start, page_len, filters):
    """Custom query for the Branch filter.

    Fetches all branches regardless of the logged-in user's permissions or
    user permission restrictions. Raw SQL is used here intentionally so the
    result is not filtered by `frappe.db.get_list` permission checks.
    """
    return frappe.db.sql(
        """
		select name
		from `tabBranch`
		where name like %(txt)s
		order by name
		limit %(start)s, %(page_len)s
		""",
        {
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len,
        },
    )


# Maps the "Order Voucher Type" filter to the doctypes/fields that differ
# between a Sales Order (customer side) and a Purchase Order (supplier side).
VOUCHER_CONFIG = {
    "Sales Order": {
        "order_doctype": "Sales Order",
        "item_doctype": "Sales Order Item",
        "party_field": "customer",
        "party_label": "Customer",
        "party_name_field": "customer_name",
        "party_name_label": "Customer Name",
    },
    "Purchase Order": {
        "order_doctype": "Purchase Order",
        "item_doctype": "Purchase Order Item",
        "party_field": "supplier",
        "party_label": "Supplier",
        "party_name_field": "supplier_name",
        "party_name_label": "Supplier Name",
    },
}


class OrderItems:
    def __init__(self, filters=None):
        self.filters = frappe._dict(filters)
        voucher_type = self.filters.order_voucher_type or "Sales Order"
        if voucher_type not in VOUCHER_CONFIG:
            frappe.throw(_("Invalid Order Voucher Type: {0}").format(voucher_type))
        self.config = VOUCHER_CONFIG[voucher_type]

    def run(self):
        self.validate_filters()
        return self.get_columns(), self.get_data()

    def validate_filters(self):
        self.filters.from_date = getdate(self.filters.from_date)
        self.filters.to_date = getdate(self.filters.to_date)

        if self.filters.from_date > self.filters.to_date:
            frappe.throw(_("From Date must be before To Date"))

    def get_columns(self):
        return [
            {
                "label": _("Order Date"),
                "fieldname": "transaction_date",
                "fieldtype": "Date",
                "width": 120,
            },
            {
                "label": _(self.config["order_doctype"]),
                "fieldname": "order_no",
                "fieldtype": "Link",
                "options": self.config["order_doctype"],
                "width": 120,
            },
            {
                "label": _(self.config["party_label"]),
                "fieldname": "party",
                "fieldtype": "Data",
                "width": 130,
                "hidden": 0,
            },
            {
                "label": _(self.config["party_name_label"]),
                "fieldname": "party_name",
                "fieldtype": "Data",
                "width": 130,
                "hidden": 0,
            },
            {
                "label": _("Repair Order"),
                "fieldname": "repair_order",
                "fieldtype": "Link",
                "options": "Project",
                "width": 130,
                "hidden": 0,
            },
            {
                "label": _("Branch"),
                "fieldname": "branch",
                "fieldtype": "Data",
                "width": 130,
                "hidden": 0,
            },
            {
                "label": _("Item Code"),
                "fieldname": "item_code",
                "fieldtype": "Link",
                "options": "Item",
                "width": 130,
                "hidden": 0,
            },
            {
                "label": _("Item Name"),
                "fieldname": "item_name",
                "fieldtype": "Data",
                "width": 130,
                "hidden": 0,
            },
            {
                "label": _("UOM"),
                "fieldname": "uom",
                "fieldtype": "Data",
                "width": 130,
                "hidden": 0,
            },
            {
                "label": _("Rate"),
                "fieldname": "base_rate",
                "fieldtype": "Currency",
                "width": 130,
                "hidden": 0,
            },
            {
                "label": _("Qty"),
                "fieldname": "qty",
                "fieldtype": "Int",
                "width": 130,
                "hidden": 0,
            },
            {
                "label": _("Amount"),
                "fieldname": "base_amount",
                "fieldtype": "Currency",
                "width": 130,
                "hidden": 0,
            },
            {
                "label": _("Stock UOM"),
                "fieldname": "stock_uom",
                "fieldtype": "Data",
                "width": 130,
                "hidden": 0,
            },
            {
                "label": _("Conversion Factor"),
                "fieldname": "conversion_factor",
                "fieldtype": "Float",
                "width": 130,
                "hidden": 0,
            },
        ]

    def get_data(self):
        # Doctype and fieldnames come from VOUCHER_CONFIG, which `__init__` has
        # already checked the filter against.
        order = qb.DocType(self.config["order_doctype"])
        order_item = qb.DocType(self.config["item_doctype"])

        query = (
            qb.from_(order_item)
            .inner_join(order)
            .on(order.name == order_item.parent)
            .select(
                order.transaction_date,
                order.name.as_("order_no"),
                order[self.config["party_field"]].as_("party"),
                order[self.config["party_name_field"]].as_("party_name"),
                order.project.as_("repair_order"),
                order.branch,
                order_item.item_code,
                order_item.item_name,
                order_item.uom,
                order_item.base_rate,
                order_item.qty,
                order_item.base_amount,
                order_item.stock_uom,
                order_item.conversion_factor,
            )
            .where(order.docstatus == 1)
            .orderby(order.transaction_date)
        )

        for condition in self.get_conditions(order, order_item):
            query = query.where(condition)

        return query.run(as_dict=True)

    def get_conditions(self, order, order_item):
        conditions = []

        if self.filters.company:
            conditions.append(order.company == self.filters.company)
        if self.filters.from_date:
            conditions.append(order.transaction_date >= self.filters.from_date)
        if self.filters.to_date:
            conditions.append(order.transaction_date <= self.filters.to_date)
        if self.filters.branch:
            conditions.append(order.branch == self.filters.branch)
        if self.filters.item_code:
            conditions.append(order_item.item_code == self.filters.item_code)

        # Apply the party filter that matches the selected voucher type:
        # `customer` for Sales Order, `supplier` for Purchase Order.
        party_field = self.config["party_field"]
        party_value = self.filters.get(party_field)
        if party_value:
            conditions.append(order[party_field] == party_value)

        return conditions
