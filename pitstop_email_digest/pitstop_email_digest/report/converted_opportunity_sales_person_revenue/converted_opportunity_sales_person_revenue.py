# Copyright (c) 2025, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = get_column(filters)
    data = get_data(filters)
    return columns, data


def get_column(filters):
    columns = [
        {
            "label": _("Opportunity"),
            "fieldname": "opportunity",
            "fieldtype": "Link",
            "options": "Opportunity",
            "width": 200,
        },
        {
            "label": _("Opportunity Type"),
            "fieldname": "opportunity_type",
            "fieldtype": "Link",
            "options": "Opportunity Type",
            "width": 200,
        },
        {
            "label": _("Sales Person"),
            "fieldname": "sales_person",
            "fieldtype": "Link",
            "options": "Sales Person",
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
            "label": _("PDI/NON-PDI"),
            "fieldname": "pdi_non_pdi",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Job Type"),
            "fieldname": "job_type",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Sales Invoice"),
            "fieldname": "sales_invoice",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 150,
        },
        {
            "label": _("Sales Invoice Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 150,
        },
        {
            "label": _("Cost Center"),
            "fieldname": "cost_center",
            "fieldtype": "Link",
            "options": "Cost Center",
            "width": 150,
        },
        {
            "label": _("Customer"),
            "fieldname": "customer",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200,
        },
        {
            "label": _("Customer Name"),
            "fieldname": "customer_name",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Bill To"),
            "fieldname": "bill_to",
            "fieldtype": "Link",
            "options": "Customer",
            "width": 200,
        },
        {
            "label": _("Bill To Name"),
            "fieldname": "bill_to_name",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Bill To Group"),
            "fieldname": "bill_to_group",
            "fieldtype": "Link",
            "options": "Customer Group",
            "width": 200,
        },
        {
            "label": _("Chassis Number"),
            "fieldname": "vehicle_chassis_no",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": _("Total Net Amount"),
            "fieldname": "net_total_after_discount",
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
            "label": _("Total Amount"),
            "fieldname": "total_amount",
            "fieldtype": "Currency",
            "width": 200,
        },
    ]
    return columns


def get_data(filters):
    conditions, condition_values_dict = get_conditions_and_values(filters)

    return frappe.db.sql(
        f"""
		select
			to2.name as opportunity,
            to2.opportunity_type,
            to2.sales_person,
            tp.custom_pdi__non_pdi as pdi_non_pdi,
            tp.job_type,
			tsi.name as sales_invoice,
            tsi.posting_date as posting_date,
			tsi.customer,
			tsi.customer_name,
			tsi.bill_to,
			tsi.bill_to_name,
            tsi.cost_center,
			tsi.customer_group as bill_to_group,
			tsi.vehicle_chassis_no,
			tsii.project,
            sum(tsii.base_net_amount) as net_total_after_discount,
            sum(tsii.base_item_taxes) as total_taxes_and_charges,
            sum(tsii.base_net_amount) + sum(tsii.base_item_taxes) AS total_amount
		from
			tabOpportunity to2
		join
			tabProject tp
		on
			tp.opportunity = to2.name
		join
			`tabSales Invoice Item` tsii
		on
			tsii.project = tp.name
		join
			`tabSales Invoice` tsi
		on
			tsi.name = tsii.parent
		where
			tsi.docstatus=1  {conditions}
		group by
			tsi.name, tsii.project;
	    """,
        condition_values_dict,
        as_dict=True,
    )


def get_conditions_and_values(filters):
    condition_values_dict = {}
    conditions = ""

    if filters.get("from_date"):
        conditions += "and tsi.posting_date>= %(from_posting_date)s"
        condition_values_dict["from_posting_date"] = filters.get("from_date")

    if filters.get("to_date"):
        conditions += "and tsi.posting_date<= %(to_posting_date)s"
        condition_values_dict["to_posting_date"] = filters.get("to_date")

    if filters.get("bill_to_customer_group"):
        conditions += "and tsi.customer_group = %(bill_to_customer_group)s"
        condition_values_dict["bill_to_customer_group"] = filters.get(
            "bill_to_customer_group"
        )

    if filters.get("pdi_non_pdi"):
        conditions += "and tp.custom_pdi__non_pdi = %(pdi_non_pdi)s"
        condition_values_dict["pdi_non_pdi"] = filters.get("pdi_non_pdi")

    if filters.get("sales_person"):
        conditions += "and to2.sales_person = %(sales_person)s"
        condition_values_dict["sales_person"] = filters.get("sales_person")

    if filters.get("opportunity_type"):
        conditions += "and to2.opportunity_type = %(opportunity_type)s"
        condition_values_dict["opportunity_type"] = filters.get("opportunity_type")

    if filters.get("cost_center"):
        conditions += "and tsi.cost_center = %(cost_center)s"
        condition_values_dict["cost_center"] = filters.get("cost_center")

    return conditions, condition_values_dict
