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
            "label": _("PDI/NON-PDI"),
            "fieldname": "pdi_non_pdi",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": _("Sales Invoice"),
            "fieldname": "sales_invoice",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 80,
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
    conditions = ""
    if filters.get("from_date"):
        conditions += "and tsi.posting_date>='{from_posting_date}'".format(
            from_posting_date=filters.get("from_date")
        )
    if filters.get("to_date"):
        conditions += "and tsi.posting_date<='{to_posting_date}'".format(
            to_posting_date=filters.get("to_date")
        )
    if filters.get("bill_to_customer_group"):
        conditions += "and tsi.customer_group = '{bill_to_customer_group}'".format(
            bill_to_customer_group=filters.get("bill_to_customer_group")
        )
    if filters.get("pdi_non_pdi"):
        conditions += "and tp.custom_pdi__non_pdi = '{pdi_non_pdi}'".format(
            pdi_non_pdi=filters.get("pdi_non_pdi")
        )
    if filters.get("sales_person"):
        conditions += "and to2.sales_person = '{sales_person}'".format(
            sales_person=filters.get("sales_person")
        )
    if filters.get("opportunity_type"):
        conditions += "and to2.opportunity_type = '{opportunity_type}'".format(
            opportunity_type=filters.get("opportunity_type")
        )

    return frappe.db.sql(
        """
		select
			to2.name as opportunity,
            to2.opportunity_type,
            to2.sales_person,
            tp.custom_pdi__non_pdi as pdi_non_pdi,
			tsi.name as sales_invoice,
			tsi.customer,
			tsi.customer_name,
			tsi.bill_to,
			tsi.bill_to_name,
			tsi.customer_group as bill_to_group,
			tsi.vehicle_chassis_no,
			tsi.project,
			sum(tsii.base_amount_before_discount) as total_before_discount,
			sum(tsii.base_total_discount) as discount_amount,
			sum(tsii.base_amount) as total_after_discount,
			tax_table.total_taxes_and_charges,
			tsi.discount_amount as additional_discount,
			tsi.grand_total
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
		left join (
					SELECT
						parent,
						SUM(tax_amount) AS total_taxes_and_charges
					FROM `tabSales Taxes and Charges`
					WHERE charge_type != 'Actual'
					GROUP BY parent
				) AS tax_table
		on
			tax_table.parent = tsi.name
		where
			tsi.docstatus=1 {conditions}
		group by
			tsi.name;
	""".format(conditions=conditions),
        as_dict=True,
    )
