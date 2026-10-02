# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _, qb
from frappe.query_builder.functions import Sum
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


def get_tree_condition(field, doctype, value):
    """Match `value`, and everything under it when it is a group node."""
    lft, rgt = frappe.db.get_value(doctype, value, ["lft", "rgt"]) or (None, None)
    if lft is None or rgt is None:
        return field == value

    Tree = qb.DocType(doctype)
    return field.isin(
        qb.from_(Tree).select(Tree.name).where((Tree.lft >= lft) & (Tree.rgt <= rgt))
    )


def get_data(filters):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    if not from_date or not to_date:
        frappe.throw(_("From Date and To Date are required."))

    Invoice = qb.DocType("Sales Invoice")
    Item = qb.DocType("Sales Invoice Item")
    Team = qb.DocType("Sales Team")
    Person = qb.DocType("Sales Person")

    query = (
        qb.from_(Invoice)
        .inner_join(Item)
        .on(Item.parent == Invoice.name)
        .inner_join(Team)
        .on((Team.parent == Invoice.name) & (Team.parenttype == "Sales Invoice"))
        .inner_join(Person)
        .on(Person.name == Team.sales_person)
        .select(
            Team.sales_person.as_("sales_person"),
            Item.item_group.as_("item_group"),
            Sum(Item.base_net_amount * Team.allocated_percentage / 100).as_("revenue"),
        )
        .where(Invoice.docstatus == 1)
        .where(Invoice.posting_date.between(from_date, to_date))
        .groupby(Team.sales_person, Item.item_group)
        .orderby(Team.sales_person, Item.item_group)
    )

    item_group = filters.get("item_group")
    if item_group:
        query = query.where(
            get_tree_condition(Item.item_group, "Item Group", item_group)
        )

    sales_person = filters.get("sales_person")
    if sales_person:
        query = query.where(
            get_tree_condition(Team.sales_person, "Sales Person", sales_person)
        )

    department = filters.get("department")
    if department:
        query = query.where(Person.department == department)

    rows = query.run(as_dict=True)

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
