# Copyright (c) 2025, QCS and contributors
# For license information, please see license.txt

from frappe import _, qb
from frappe.query_builder.functions import Sum


def execute(filters=None):
    columns = get_column(filters)
    data = get_data(filters)
    return columns, data


def get_column(filters):
    columns = [
        {
            "label": _("Sales Invoice"),
            "fieldname": "sales_invoice",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 200,
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 80,
        },
        {
            "label": _("Customer Name"),
            "fieldname": "customer_name",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200,
        },
        {
            "label": _("Customer Group"),
            "fieldname": "customer_group",
            "fieldtype": "Link",
            "options": "Customer Group",
            "width": 200,
        },
        {
            "label": _("Repair Order"),
            "fieldname": "project",
            "fieldtype": "Link",
            "options": "Project",
            "width": 200,
        },
        {
            "label": _("Chassis Number"),
            "fieldname": "vehicle_chassis_no",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Campaign"),
            "fieldname": "campaign",
            "fieldtype": "Link",
            "options": "Campaign",
            "width": 200,
        },
        {
            "label": _("Net Total Before Discount"),
            "fieldname": "total_before_discount",
            "fieldtype": "Currency",
            "width": 200,
        },
        {
            "label": _("Discount"),
            "fieldname": "discount_amount",
            "fieldtype": "Currency",
            "width": 200,
        },
        {
            "label": _("Net Total After Discount"),
            "fieldname": "total_after_discount",
            "fieldtype": "Currency",
            "width": 200,
        },
        {
            "label": _("Total Taxes And Charges"),
            "fieldname": "total_taxes_and_charges",
            "fieldtype": "Currency",
            "width": 200,
        },
        {
            "label": _("Additional Discount Amount"),
            "fieldname": "additional_discount",
            "fieldtype": "Currency",
            "width": 200,
        },
        {
            "label": _("Grand Total"),
            "fieldname": "grand_total",
            "fieldtype": "Currency",
            "width": 200,
        },
    ]
    return columns


def get_data(filters):
    filters = filters or {}

    Invoice = qb.DocType("Sales Invoice")
    Item = qb.DocType("Sales Invoice Item")
    Tax = qb.DocType("Sales Taxes and Charges")

    tax_table = (
        qb.from_(Tax)
        .select(Tax.parent, Sum(Tax.tax_amount).as_("total_taxes_and_charges"))
        .where(Tax.charge_type != "Actual")
        .groupby(Tax.parent)
    ).as_("tax_table")

    query = (
        qb.from_(Invoice)
        .inner_join(Item)
        .on(Item.parent == Invoice.name)
        .left_join(tax_table)
        .on(tax_table.parent == Invoice.name)
        .select(
            Invoice.name.as_("sales_invoice"),
            Invoice.customer,
            Invoice.customer_name,
            Invoice.customer_group,
            Invoice.campaign,
            Invoice.vehicle_chassis_no,
            Invoice.project,
            Sum(Item.base_amount_before_discount).as_("total_before_discount"),
            Sum(Item.base_total_discount).as_("discount_amount"),
            Sum(Item.base_amount).as_("total_after_discount"),
            tax_table.total_taxes_and_charges,
            Invoice.discount_amount.as_("additional_discount"),
            Invoice.grand_total,
        )
        .where(Invoice.docstatus == 1)
        .where(Invoice.campaign.notnull())
        .where(Invoice.campaign != "")
        .groupby(Invoice.name)
    )

    if filters.get("from_date"):
        query = query.where(Invoice.posting_date >= filters.get("from_date"))
    if filters.get("to_date"):
        query = query.where(Invoice.posting_date <= filters.get("to_date"))
    if filters.get("campaign"):
        query = query.where(Invoice.campaign == filters.get("campaign"))
    if filters.get("customer"):
        query = query.where(Invoice.customer == filters.get("customer"))

    return query.run(as_dict=True)
