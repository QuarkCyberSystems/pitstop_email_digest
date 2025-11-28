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
			"label": _("Sales Invoice"),
			"fieldname": "sales_invoice",
			"fieldtype": "Link",
			"options":"Sales Invoice",
			"width": 200,
		},
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options":"Customer",
			"width": 80,
		},
		{
			"label": _("Customer Name"),
			"fieldname": "customer_name",
			"fieldtype": "Link",
			"options":"Customer",
			"width": 200,
		},
		{
			"label": _("Customer Group"),
			"fieldname": "customer_group",
			"fieldtype": "Link",
			"options":"Customer Group",
			"width": 200,
		},
		{
			"label": _("Repair Order"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options":"Project",
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
		}
	]
	return columns


def get_data(filters):
	conditions = ""
	if filters.get("from_date"):
		conditions += "and tsi.posting_date>='{from_posting_date}'".format(from_posting_date=filters.get("from_date"))
	if filters.get("to_date"):
		conditions += "and tsi.posting_date<='{to_posting_date}'".format(to_posting_date=filters.get("to_date"))
	if filters.get("campaign"):
		conditions += "and tsi.campaign = '{campaign}'".format(campaign=filters.get("campaign"))
	if filters.get("customer"):
		conditions += "and tsi.customer = '{customer}'".format(customer=filters.get("customer"))
	return frappe.db.sql("""
		SELECT
			tsi.name as sales_invoice,
			tsi.customer,
			tsi.customer_name,
			tsi.customer_group,
			tsi.campaign,
			tsi.vehicle_chassis_no,
			tsi.project,
			sum(tsii.base_amount_before_discount) as total_before_discount,
			sum(tsii.discount_amount) as discount_amount,
			sum(tsii.base_amount) as total_after_discount,
			tax_table.total_taxes_and_charges,
			tsi.discount_amount as additional_discount,
			tsi.grand_total
		FROM 
			`tabSales Invoice` tsi
		Join 
			`tabSales Invoice Item` tsii
		on
			tsii.parent = tsi.name
		LEFT JOIN (
			SELECT
				parent,
				SUM(tax_amount) AS total_taxes_and_charges
			FROM `tabSales Taxes and Charges`
			WHERE charge_type != 'Actual'
			GROUP BY parent
		) AS tax_table
			ON tax_table.parent = tsi.name
		WHERE 
			tsi.docstatus=1 and 
			tsi.campaign is not null and 
			tsi.campaign != '' {conditions}
		group by 
			tsi.name;
	""".format(conditions=conditions), as_dict=True)