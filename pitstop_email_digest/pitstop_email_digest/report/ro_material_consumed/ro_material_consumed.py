# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns, data = [], []
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data


def get_columns(filters):
    columns = [
        {
            "label": frappe._("Repair Order"),
            "fieldname": "ro",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": frappe._("Repair Order Status"),
            "fieldname": "ro_status",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": frappe._("Service Advisor"),
            "fieldtype": "Link",
            "options": "Sales Person",
            "fieldname": "service_advisor",
            "width": 150,
        },
        {
            "label": frappe._("Branch"),
            "fieldname": "branch",
            "fieldtype": "Link",
            "options": "Branch",
            "width": 100,
        },
        {
            "label": frappe._("Material Issue"),
            "fieldname": "material_issue_amount",
            "fieldtype": "Currency",
            "width": 200,
            "hidden": 0,
        },
        {
            "label": frappe._("Material Receipt"),
            "fieldname": "material_receipt_amount",
            "fieldtype": "Currency",
            "width": 200,
            "hidden": 0,
        },
        {
            "label": frappe._("Total"),
            "fieldname": "total",
            "fieldtype": "Currency",
            "width": 200,
            "hidden": 0,
        },
    ]
    return columns


def get_data(filters):
    condition_dict, condition_values = get_condition(filters)
    return frappe.db.sql(
        f"""
		select
			tse2.project as ro,
			tp.status as ro_status,
			tp.service_advisor,
			tp.branch,
			sum(case when tse2.stock_entry_type = "Material Issue"
				then abs(tsle.stock_value_difference) else 0 end) as material_issue_amount,
			sum(case when tse2.stock_entry_type = "Material Receipt"
				then abs(tsle.stock_value_difference) else 0 end) as material_receipt_amount,
			sum(
				case
					when tse2.stock_entry_type = "Material Issue"
					then abs(tsle.stock_value_difference)
					else 0
				end
			)
			-
			sum(
				case
					when tse2.stock_entry_type = "Material Receipt"
					then abs(tsle.stock_value_difference)
					else 0
				end
			) as total
		from
			`tabStock Ledger Entry` tsle
		join
			`tabStock Entry` tse2
			on tsle.voucher_no = tse2.name
		join
			tabProject tp
			on tp.name = tse2.project
		where
			tse2.docstatus = 1
			and tse2.stock_entry_type in ("Material Issue", "Material Receipt") {condition_values}
		group by
			tse2.project;
	""",
        condition_dict,
        as_dict=True,
    )


def get_condition(filters):
    condition_values_dict = {}
    condition = ""
    if filters.get("company"):
        condition += "and tsle.company = %(company)s"
        condition_values_dict["company"] = filters.get("company")
    if filters.get("from_date"):
        condition += "and tsle.posting_date >= %(from_date)s"
        condition_values_dict["from_date"] = filters.get("from_date")
    if filters.get("to_date"):
        condition += "and tsle.posting_date <= %(to_date)s"
        condition_values_dict["to_date"] = filters.get("to_date")
    if filters.get("to_date"):
        condition += "and tsle.posting_date <= %(to_date)s"
        condition_values_dict["to_date"] = filters.get("to_date")
    if filters.get("ro_status"):
        condition += "and tp.status = %(ro_status)s"
        condition_values_dict["ro_status"] = filters.get("ro_status")
    return condition_values_dict, condition
