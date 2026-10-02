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
    return frappe.db.sql(
        """
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
			tsi.docstatus = 1
			and tsi.posting_date >= coalesce(%(from_date)s, '1900-01-01')
			and tsi.posting_date <= coalesce(%(to_date)s, '2999-12-31')
			and (%(bill_to_customer_group)s is null or tsi.customer_group = %(bill_to_customer_group)s)
			and (%(pdi_non_pdi)s is null or tp.custom_pdi__non_pdi = %(pdi_non_pdi)s)
			and (%(sales_person)s is null or to2.sales_person = %(sales_person)s)
			and (%(opportunity_type)s is null or to2.opportunity_type = %(opportunity_type)s)
			and (%(cost_center)s is null or tsi.cost_center = %(cost_center)s)
		group by
			tsi.name, tsii.project;
	    """,
        get_filter_values(filters),
        as_dict=True,
    )


def get_filter_values(filters):
    """Bind every supported filter, passing NULL for the ones left blank."""
    filters = filters or {}

    return {
        fieldname: filters.get(fieldname) or None
        for fieldname in (
            "from_date",
            "to_date",
            "bill_to_customer_group",
            "pdi_non_pdi",
            "sales_person",
            "opportunity_type",
            "cost_center",
        )
    }
