# Copyright (c) 2025, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, ceil
from frappe.query_builder.functions import IfNull, Max
from frappe import _, qb, query_builder
from ....utils.vehicle_movement.vehicle_movement import get_customers_list


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	total_ro, total_timespend, total_average  = calculate_overall_totals(data)
	total_summary = get_totals_summary(total_ro, total_timespend, total_average)
	return columns, data, None, None, total_summary

def get_columns(filters=None):

	columns = [
		{
			"label": _("Job Status"),
			"fieldname": "project_status",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Current Task Type"),
			"fieldname": "current_task_type",
			"fieldtype": "Link",
			"options": "Task Type",
			"width": 200,
		},
		{
			"label": _("Workshop Division"),
			"fieldname": "vehicle_workshop_division",
			"fieldtype": "Data",
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
			"label": _("Insurance Company"),
			"fieldname": "insurance_company_name",
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
			"label": _("Vehicle Chassis Number"),
			"fieldname": "vehicle_chassis_no",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Vehicle Licesnce Plate Number"),
			"fieldname": "vehicle_license_plate",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Vehicle Model"),
			"fieldname": "vehicle_model",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Gate Pass Posting Date"),
			"fieldname": "gate_pass_posting_date",
			"fieldtype": "Date",
			"width": 200,
		},
		{
			"label": _("Timespend (Days)"),
			"fieldname": "timespend",
			"fieldtype": "Int",
			"width": 200,
		}
	]

	ro_dict = check_link_roles(filters)
	columns.insert(0, ro_dict)
	return columns	

def check_link_roles(filters):

	link_roles = frappe.db.get_all("Role Details", 
				filters={"parent":"Workspace Settings", "parentfield":filters.get("report_link_access_roles_vehicle_mobility_field")}, 
		fields=["roles"], pluck="roles")
	current_user = frappe.session.user
	for each_role in link_roles:
		if each_role in frappe.get_roles(current_user):
			ro_column_dict = {
				"label": _("Reapair Order"),
				"fieldname": "repair_order",
				"fieldtype": "Link",
				"options": "Project",
				"width": 200,
			}
			break
	else:
		ro_column_dict = {
			"label": _("Reapair Order"),
			"fieldname": "repair_order",
			"fieldtype": "Data",
			"width": 200,
		}
	return ro_column_dict


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
		.on((VGP.project == Project.name) & (VGP.docstatus == 1) & (VGP.purpose == 'Service - Vehicle Delivery'))
		.where(LatestVSR.docstatus == 1)
		.select(
			Project.name.as_("repair_order"),
			datediff(IfNull(VGP.posting_date, today()), LatestVSR.posting_date).as_("timespend"),
			Project.project_status,
			Project.current_task_type,
			Project.vehicle_workshop_division,
			Project.project_date,
			Project.customer_name,
			Project.insurance_company_name,
			VGP.posting_date.as_("gate_pass_posting_date"),
			LatestVSR.posting_date.as_("vehicle_receive_date"),
			Project.vehicle_chassis_no.as_("vehicle_chassis_no"),
			Project.vehicle_license_plate.as_("vehicle_license_plate"),
			Project.applies_to_item.as_("vehicle_model")
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
	
	if filters and filters.get("current_task_type"):
		query = query.where(Project.current_task_type == filters.get("current_task_type"))
	
	if filters and filters.get("billing_type"):
		if filters.get("billing_type") == "Customer":
			query = query.where((Project.insurance_company == "") | (Project.insurance_company.isnull()))
		elif filters.get("billing_type") == "Insurance":
			query = query.where((Project.insurance_company != "") & (Project.insurance_company.isnotnull()))
	
	if filters and filters.get("branch"):
		query = query.where((Project.branch == filters.get("branch")))

	customer_list = []
	if filters.get("workspace"):
		customer_list = get_customers_list(filters.get("workspace"))

	if customer_list:
		query = query.where(Project.customer.isin(customer_list))

	workshop_division_project_status_data_mechanical = query.run(as_dict=True)

	return 	workshop_division_project_status_data_mechanical

def calculate_overall_totals(data):
	if not data:
		return 0.0, 0.0, 0.0
	
	total_timespend = sum(each_dict.get("timespend") or 0 for each_dict in data)
	total_ro = sum(1 for item in data if item.get("repair_order") is not None)

	average = total_timespend/total_ro
	return total_ro, total_timespend, ceil(average)

def get_totals_summary(total_ro, total_timespend, total_average):
	the_symbol = "="
	if (total_ro and ((total_timespend/total_ro) != total_average)):
		the_symbol = "&#8776;"

	return [
		{
			"label": _("Average Time in Days"),
			"value": str(total_timespend)+"/"+str(total_ro)+the_symbol+str(total_average),
			"indicator": "red",
			"datatype": "html",
		}
	]
