# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate, nowdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": _("Purchase Order"),
            "fieldname": "purchase_order",
            "fieldtype": "Link",
            "options": "Purchase Order",
            "width": 180,
        },
        {
            "label": _("Supplier"),
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "width": 160,
        },
        {
            "label": _("Supplier Name"),
            "fieldname": "supplier_name",
            "fieldtype": "Data",
            "width": 220,
        },
        {
            "label": _("Grand Total"),
            "fieldname": "grand_total",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 140,
        },
        {
            "label": _("Age (Days)"),
            "fieldname": "age",
            "fieldtype": "Int",
            "width": 110,
        },
    ]


def get_data(filters):
    conditions = []
    values = {
        "as_on_date": getdate(filters.get("as_on_date") or nowdate()),
        "min_age": int(filters.get("min_age") or 90),
    }

    if filters.get("company"):
        conditions.append("po.company = %(company)s")
        values["company"] = filters.get("company")

    if filters.get("supplier"):
        conditions.append("po.supplier = %(supplier)s")
        values["supplier"] = filters.get("supplier")

    conditions_str = " and ".join(conditions)
    if conditions_str:
        conditions_str = "and " + conditions_str

    return frappe.db.sql(
        f"""
            select
                po.name as purchase_order,
                po.supplier,
                po.supplier_name,
                po.grand_total,
                po.currency,
                datediff(%(as_on_date)s, po.transaction_date) as age
            from `tabPurchase Order` po
            where
                po.docstatus = 1
                and po.status not in ('Closed', 'Completed')
                and datediff(%(as_on_date)s, po.transaction_date) > %(min_age)s
                {conditions_str}
            order by age desc, po.transaction_date asc
        """,
        values,
        as_dict=1,
    )
