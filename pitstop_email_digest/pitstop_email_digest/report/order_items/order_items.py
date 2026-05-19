# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
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
    },
    "Purchase Order": {
        "order_doctype": "Purchase Order",
        "item_doctype": "Purchase Order Item",
        "party_field": "supplier",
        "party_label": "Supplier",
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
        conditions = self.get_conditions()
        conditions_str = (
            "and {0}".format(" and ".join(conditions)) if conditions else ""
        )
        order_doctype = self.config["order_doctype"]
        item_doctype = self.config["item_doctype"]
        party_field = self.config["party_field"]

        return frappe.db.sql(
            f"""
			select
				o.transaction_date,
				o.name as order_no,
				o.{party_field} as party,
				o.project as repair_order,
				o.branch as branch,
				oi.item_code,
				oi.item_name,
				oi.uom,
				oi.base_rate,
				oi.qty,
				oi.base_amount,
				oi.stock_uom,
				oi.conversion_factor
			from
				`tab{item_doctype}` oi
			join
				`tab{order_doctype}` o
			on
				o.name = oi.parent
			where
				o.docstatus = 1 {conditions_str}
			order by
				o.transaction_date;
		""",
            self.filters,
            as_dict=True,
        )

    def get_conditions(self):
        conditions = []

        if self.filters.company:
            conditions.append("o.company = %(company)s")
        if self.filters.from_date:
            conditions.append("o.transaction_date >= %(from_date)s")
        if self.filters.to_date:
            conditions.append("o.transaction_date <= %(to_date)s")
        if self.filters.branch:
            conditions.append("o.branch = %(branch)s")
        if self.filters.item_code:
            conditions.append("oi.item_code = %(item_code)s")

        return conditions
