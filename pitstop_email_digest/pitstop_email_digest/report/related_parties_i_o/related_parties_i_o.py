# Copyright (c) 2025, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, floor
from frappe.query_builder.functions import IfNull, Max
from frappe import _, qb, query_builder


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	totals = calculate_overall_totals(data)
	total_summary = get_totals_summary(totals)
	return columns, data, None, None, total_summary

def get_columns(filters=None):
	return [
		{
			"label": _("Reapair Order"),
			"fieldname": "repair_order",
			"fieldtype": "Link",
			"options": "Project",
			"width": 200,
		},
		{
			"label": _("Job Status"),
			"fieldname": "project_status",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Workshop Division"),
			"fieldname": "vehicle_workshop_division",
			"fieldtype": "Link",
			"options":"Vehicle Workshop Division",
			"width": 200,
		},
		{
			"label": _("Customer"),
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"options":"Customer",
			"width": 200,
		},
		{
			"label": _("Bill To"),
			"fieldname": "bill_to_name",
			"fieldtype": "Data",
			"options":"Customer",
			"width": 200,
		},
		{
			"label": _("Job Date"),
			"fieldname": "project_date",
			"fieldtype": "date",
			"width": 200,
		},
		{
			"label": _("Vehicle Receive Date"),
			"fieldname": "vehicle_receive_date",
			"fieldtype": "date",
			"width": 200,
		},
		{
			"label": _("Gate Pass Posting Date"),
			"fieldname": "gate_pass_posting_date",
			"fieldtype": "Date",
			"width": 200,
		},
		{
			"label": _("Timespend"),
			"fieldname": "timespend",
			"fieldtype": "Float",
			"width": 200,
		}
	]

def get_data(filters=None):
	"""
	Fetch data based on filters.
	"""
	Project = qb.DocType("Project")
	VSR = qb.DocType("Vehicle Service Receipt")
	VGP = qb.DocType("Vehicle Gate Pass")

	datediff = query_builder.CustomFunction("DATEDIFF", ["cur_date", "due_date"])

	# Step 1: Subquery to get max(posting_date) for each project in VSR
	LatestVSRSub = (
		frappe.qb.from_(VSR)
		.select(VSR.project, Max(VSR.posting_date).as_("max_posting_date"))
		.where(VSR.docstatus == 1)
		.groupby(VSR.project)
	).as_("latest_vsr_sub")

	# Step 2: Join this with VSR to get the full latest VSR record
	LatestVSR = (
		frappe.qb.from_(VSR)
		.join(LatestVSRSub)
		.on((VSR.project == LatestVSRSub.project) & (VSR.posting_date == LatestVSRSub.max_posting_date))
		.select(
			VSR.name,
			VSR.project,
			VSR.posting_date,
			VSR.docstatus
		)
	).as_("latest_vsr")

	query = (
		frappe.qb
		.from_(Project)
		.left_join(LatestVSR)
		.on(LatestVSR.project == Project.name)
		.left_join(VGP)
		.on((VGP.project == Project.name) & (VGP.docstatus == 1))
		.where(LatestVSR.docstatus == 1)
		.select(
			Project.name.as_("repair_order"),
			datediff(IfNull(VGP.posting_date, today()), LatestVSR.posting_date).as_("timespend"),
			Project.project_status,
			Project.vehicle_workshop_division,
			Project.project_date,
			Project.customer_name,
			Project.bill_to_name,
			VGP.posting_date.as_("gate_pass_posting_date"),
			LatestVSR.posting_date.as_("vehicle_receive_date"),
		)
	)

	if filters and filters.get("from_date"):
		query = query.where(Project.project_date>=filters.get("from_date"))
	
	if filters and filters.get("to_date"):
		query = query.where(Project.project_date<=filters.get("to_date"))
	
	if filters and filters.get("workshop_division"):
		query = query.where(Project.vehicle_workshop_division == filters.get("workshop_division"))
	
	if filters and filters.get("project_status"):
		query = query.where(Project.project_status == filters.get("project_status"))
	
	if filters and filters.get("billing_type"):
		if filters.get("billing_type") == "Customer":
			query = query.where(Project.customer == Project.bill_to)
		elif filters.get("billing_type") == "Insurance":
			query = query.where(((Project.bill_to!="") & (Project.bill_to.isnotnull())) & (Project.customer != Project.bill_to))
		elif filters.get("billing_type") == "No Bill To":
			query = query.where((Project.bill_to == "") | (Project.bill_to.isnull()))
	
	customer_list = ["C00883", "C00276", "C01053"]
	if customer_list:
		query = query.where(Project.customer.isin(customer_list))
	
	print(query.get_sql())

	workshop_division_project_status_data_mechanical = query.run(as_dict=True)

	return 	workshop_division_project_status_data_mechanical

def calculate_overall_totals(data):
	if not data:
		return 0.0
	
	total_timespend = sum(each_dict.get("timespend") or 0 for each_dict in data)
	total_ro = sum(1 for item in data if item.get("repair_order") is not None)

	average = total_timespend/total_ro
	return floor(average)

def get_totals_summary(totals):
	if not totals:
		return None

	return [
		{
			"label": _("Average Time in Days"),
			"value": totals,
			"indicator": "red",
			"datatype": "Float",
		}
	]
