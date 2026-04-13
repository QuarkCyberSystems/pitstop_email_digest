# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data


def get_columns(filters=None):
    return [
        {
            "label": "Quotation",
            "fieldname": "quotation",
            "fieldtype": "Link",
            "options": "Quotation",
            "width": 150,
        },
        {
            "label": "Quotation Date",
            "fieldname": "quatation_date",
            "fieldtype": "Date",
            "width": 150,
        },
        {
            "label": "Quotation Net Amt.",
            "fieldname": "quotation_net",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": "Quotation Grand Amt.",
            "fieldname": "quotation_grand",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": "Quotation Status",
            "fieldname": "quotation_status",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Quotation Service Advisor",
            "fieldname": "service_advisor",
            "fieldtype": "Link",
            "options": "Sales Person",
            "width": 150,
        },
        {
            "label": "Quotation Created By",
            "fieldname": "owner",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Repaird Order",
            "fieldname": "ro",
            "fieldtype": "Link",
            "options": "Project",
            "width": 150,
        },
        {
            "label": "Repaird Order Status",
            "fieldname": "project_status",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "RO Total Sales Amt.",
            "fieldname": "total_sales_amount",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": "RO Total Cost",
            "fieldname": "total_cost",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": "RO Total Billed Amount",
            "fieldname": "total_billed_amount",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": "RO Gross Margin",
            "fieldname": "gross_margin",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": "RO Gross Margin %",
            "fieldname": "per_gross_margin",
            "fieldtype": "Currency",
            "width": 150,
        },
    ]


def get_data(filters):
    condition_values_dict, condition = get_conditions_and_values(filters)
    return frappe.db.sql(
        f"""
		select
			tq.name as quotation,
			tq.transaction_date as quatation_date,
			tq.net_total as quotation_net,
			tq.grand_total as quotation_grand,
			tq.status as quotation_status,
			tq.owner,
			tp.name as ro,
			tp.project_status,
			tp.total_sales_amount,
			tp.material_cost_of_sales+tp.total_purchase_cost+
			(tp.timesheet_billable_amount+tp.estimated_costing+tp.total_consumed_material_cost+
			tp.total_expense_claim+tp.timesheet_costing_amount)  as total_cost,
			tp.total_billed_amount,
			tp.gross_margin,
			tp.per_gross_margin,
			tq.service_advisor
		from
			tabQuotation tq
		join
			tabProject tp
		on
			tq.project = tp.name
		where
			1=1 {condition};
	""",
        condition_values_dict,
        as_dict=True,
    )


def get_conditions_and_values(filters):
    condition_values_dict = {}
    condition = ""
    if filters.get("quotation"):
        condition += "and tq.name = %(quotation)s"
        condition_values_dict["quotation"] = filters.get("quotation")

    if filters.get("repair_order"):
        condition += "and tp.name = %(repair_order)s"
        condition_values_dict["repair_order"] = filters.get("repair_order")

    if filters.get("from_date"):
        condition += "and tq.transaction_date >= %(from_date)s"
        condition_values_dict["from_date"] = filters.get("from_date")

    if filters.get("to_date"):
        condition += "and tq.transaction_date <= %(to_date)s"
        condition_values_dict["to_date"] = filters.get("to_date")

    if filters.get("quotation_status"):
        condition += "and tq.status = %(quotation_status)s"
        condition_values_dict["quotation_status"] = filters.get("quotation_status")

    if filters.get("ro_status"):
        condition += "and tp.project_status = %(ro_status)s"
        condition_values_dict["ro_status"] = filters.get("ro_status")

    if filters.get("quotation_service_advisor"):
        condition += "and tq.service_advisor = %(quotation_service_advisor)s"
        condition_values_dict["quotation_service_advisor"] = filters.get(
            "quotation_service_advisor"
        )

    return (condition_values_dict, condition)
