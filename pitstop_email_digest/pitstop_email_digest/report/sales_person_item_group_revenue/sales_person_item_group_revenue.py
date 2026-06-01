# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": _("Sales Person"),
            "fieldname": "sales_person",
            "fieldtype": "Link",
            "options": "Sales Person",
            "width": 240,
        },
        {
            "label": _("Item Group"),
            "fieldname": "item_group",
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 240,
        },
        {
            "label": _("Revenue"),
            "fieldname": "revenue",
            "fieldtype": "Currency",
            "width": 180,
        },
    ]


def get_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    if not from_date or not to_date:
        frappe.throw(_("From Date and To Date are required."))

    conditions = [
        "inv.docstatus = 1",
        "inv.posting_date between %(from_date)s and %(to_date)s",
    ]
    params = {"from_date": from_date, "to_date": to_date}

    item_group = filters.get("item_group")
    if item_group:
        lft, rgt = frappe.db.get_value("Item Group", item_group, ["lft", "rgt"]) or (
            None,
            None,
        )
        if lft is not None and rgt is not None:
            conditions.append(
                "i.item_group in (select name from `tabItem Group` where lft >= %(ig_lft)s and rgt <= %(ig_rgt)s)"
            )
            params["ig_lft"] = lft
            params["ig_rgt"] = rgt
        else:
            conditions.append("i.item_group = %(item_group)s")
            params["item_group"] = item_group

    sales_person = filters.get("sales_person")
    if sales_person:
        lft, rgt = frappe.db.get_value(
            "Sales Person", sales_person, ["lft", "rgt"]
        ) or (None, None)
        if lft is not None and rgt is not None:
            conditions.append(
                "st.sales_person in (select name from `tabSales Person` where lft >= %(sp_lft)s and rgt <= %(sp_rgt)s)"
            )
            params["sp_lft"] = lft
            params["sp_rgt"] = rgt
        else:
            conditions.append("st.sales_person = %(sales_person)s")
            params["sales_person"] = sales_person

    department = filters.get("department")
    if department:
        conditions.append("sp.department = %(department)s")
        params["department"] = department

    where_clause = " and ".join(conditions)

    rows = frappe.db.sql(
        """
        select
            st.sales_person as sales_person,
            i.item_group as item_group,
            sum(i.base_net_amount * st.allocated_percentage / 100) as revenue
        from `tabSales Invoice` inv
        inner join `tabSales Invoice Item` i on i.parent = inv.name
        inner join `tabSales Team` st on st.parent = inv.name and st.parenttype = 'Sales Invoice'
        inner join `tabSales Person` sp on sp.name = st.sales_person
        where {where_clause}
        group by st.sales_person, i.item_group
        order by st.sales_person, i.item_group
        """.format(where_clause=where_clause),
        params,
        as_dict=1,
    )

    data = []
    last_sales_person = None
    for r in rows:
        sales_person = r.get("sales_person")
        data.append(
            {
                "sales_person": sales_person
                if sales_person != last_sales_person
                else "",
                "item_group": r.get("item_group"),
                "revenue": flt(r.get("revenue")),
            }
        )
        last_sales_person = sales_person

    return data
