
import frappe
from frappe.utils import today, nowtime
from frappe.query_builder.functions import Count, Sum, IfNull, Max, Concat
from frappe import _, qb, query_builder
import json
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils.nestedset import get_descendants_of
from pypika.terms import Term
from pypika.enums import SqlTypes
from pypika.terms import Function
from ..download_excel_sheet_from_html.download_excel_sheet import html_table_to_excel

class Literal(Term):
	def __init__(self, value):
		super().__init__()
		self.value = value
		self.type = SqlTypes.VARCHAR

	def get_sql(self, **kwargs):
		if isinstance(self.value, str):
			return f"'{self.value}'"
		return str(self.value)
	
# Define CEIL function
class Ceil(Function):
    def __init__(self, term, *args):
        super().__init__("CEIL", term, *args)

@frappe.whitelist()
def get_vehicle_movement(workspace=None):
	"""
	Fetch vehicle movement data based on the specified frequency.
	"""
	frequency = ["Daily", "Monthly", "Yearly"]
	final_dict = {"Daily":[], "Monthly":[], "Yearly":[]}
	customer_list = []
	if workspace:
		customer_list = get_customers_list(workspace)
	
	today_date = frappe.utils.getdate(frappe.utils.nowdate())

	fy = frappe.db.get_value(
		"Fiscal Year",
		{
			"year_start_date": ["<=", today_date],
			"year_end_date":   [">=", today_date]
		},
		["year_start_date"],
		as_dict=True
	) or {}

	fiscal_start = fy.get("year_start_date") or frappe.utils.getdate(f"{today_date.year}-01-01")

	for each_frequency in frequency:
		posting_date_filter_list = []

		if each_frequency == "Daily":
			from_date = today()
			posting_date_filter_list = [from_date, from_date]
		elif each_frequency == "Monthly":
			from_date = frappe.utils.get_first_day(today())
			posting_date_filter_list = [from_date, today()] 
		elif each_frequency == "Yearly":
			from_date = fiscal_start
			posting_date_filter_list = [from_date, today()]
		to_date = today()

		number_of_vehicle_in = frappe.db.get_all('Vehicle Service Receipt', 
			fields=['count(name) as total_number_cars_in'],
			filters= {
				'posting_date': ["between", posting_date_filter_list],
				'customer': ["in", customer_list],
				'docstatus': 1
			}
		)

		number_of_vehicle_out = frappe.db.get_all('Vehicle Gate Pass', 
			fields=['count(name) as total_number_cars_out'],
			filters= {
				'posting_date': ["between", posting_date_filter_list],
				'customer': ["in", customer_list],
				'docstatus': 1
			}
		)

		TVGP = qb.DocType("Vehicle Gate Pass")
		TP = qb.DocType("Project")
		TVSR = qb.DocType("Vehicle Service Receipt")
		
		# Step 1: Subquery to get max(posting_date) for each project in VSR
		LatestVSRSub = (
			frappe.qb.from_(TVSR)
			.select(TVSR.project, Max(TVSR.posting_date).as_("max_posting_date"))
			.where(TVSR.docstatus == 1)
			.groupby(TVSR.project)
		).as_("latest_vsr_sub")

		# Step 2: Join this with VSR to get the full latest VSR record
		LatestVSR = (
			frappe.qb.from_(TVSR)
			.join(LatestVSRSub)
			.on((TVSR.project == LatestVSRSub.project) & (TVSR.posting_date == LatestVSRSub.max_posting_date))
			.select(
				TVSR.name,
				TVSR.project,
				TVSR.posting_date,
				TVSR.docstatus
			)
		).as_("latest_vsr")

		datediff = query_builder.CustomFunction("DATEDIFF", ["cur_date", "due_date"])

		average_time_delivery = (
			frappe.qb
			.from_(TVGP)
			.join(TP)
			.on(TP.name == TVGP.project)
			.left_join(LatestVSR)
			.on(LatestVSR.project == TP.name)
			.select(
				Count(TVGP.name).as_("tvsr_name_count"),
				Sum(datediff(TVGP.posting_date, LatestVSR.posting_date)).as_("timespend"),
				Ceil(
					IfNull(
						Sum(datediff(TVGP.posting_date, LatestVSR.posting_date)) / Count(TVGP.name),
						0
					)
				).as_("average")
			)
			.where(
				(TVGP.docstatus == 1) &
				(LatestVSR.docstatus == 1) &
				(TVGP.posting_date>=from_date) & 
				(TVGP.posting_date<=to_date)
			)
		)

		if customer_list:
			average_time_delivery = average_time_delivery.where((TP.customer.isin(customer_list)))
		else:
			average_time_delivery = average_time_delivery.where(TP.customer == None)
		average_time_delivery = average_time_delivery.run(as_dict=True)

		final_dict[each_frequency] = {"number_of_vehicle_in":number_of_vehicle_in, "number_of_vehicle_out":number_of_vehicle_out, "average_time_delivery":average_time_delivery}

	return final_dict

@frappe.whitelist()
def fetch_ro_project_status_based_workshop_division(
	workshop_division=None, bill_to_customer_check=None, 
	customer_list=None, timespan_list=None, 
	selected_date=None, branch=None, task_type_job_status_field=None):

	Project = qb.DocType("Project")
	VSR = qb.DocType("Vehicle Service Receipt")
	VGP = qb.DocType("Vehicle Gate Pass")

	datediff = query_builder.CustomFunction("DATEDIFF", ["cur_date", "due_date"])

	task_type_job_status = frappe.db.get_all(
		"Job Status Details", 
		filters={"parent":"Workspace Settings", "parentfield":task_type_job_status_field}, 
		fields=["job_status"],pluck="job_status"
	)

	final_list = []

	for each_timespan in timespan_list:

		today_date = today()

		if each_timespan == "YTD":
			from_date = get_fiscal_year(today_date)[1]
			to_date = today()
		elif each_timespan == "MTD":
			from_date = frappe.utils.data.get_first_day(today_date)
			to_date = today()
		elif each_timespan == "Custom Date":
			from_date = selected_date
			to_date = selected_date

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

		query_wo_ass_inp = (
			frappe.qb
			.from_(Project)
			.left_join(LatestVSR)
			.on((LatestVSR.project == Project.name) & (LatestVSR.docstatus == 1))
			.left_join(VGP)
			.on((VGP.project == Project.name) & (VGP.docstatus == 1))
			.where((LatestVSR.docstatus == 1))  # Additional filters below
			.groupby(Project.project_status)
			.select(
				Count(Project.name).distinct().as_("total_ro"),
				Sum(datediff(IfNull(VGP.posting_date, today()), LatestVSR.posting_date)).as_("timespend"),
				Ceil(
					IfNull(
						Sum(datediff(IfNull(VGP.posting_date, today()), LatestVSR.posting_date)) / Count(Project.name).distinct(),
						0
					)
				).as_("average"),
				Ceil(
					IfNull(
						Sum(datediff(IfNull(VGP.posting_date, today()), LatestVSR.posting_date)),
						0
					)
				).as_("total_time_take"),
				Project.project_status,
				Project.project_status.as_("original_project_status"),
				Project.vehicle_workshop_division,
				Literal(each_timespan).as_("timespan")
			)
		)

		if task_type_job_status:
			query_wo_ass_inp = query_wo_ass_inp.where((Project.project_status.notin(task_type_job_status)))
			query_with_ass_inp = query_with_ass_inp_method(Project, LatestVSR, VGP, datediff, each_timespan, task_type_job_status)

		# Add dynamic filters if applicable
		if workshop_division:
			query_wo_ass_inp = query_wo_ass_inp.where(Project.vehicle_workshop_division == workshop_division)
			if task_type_job_status:
				query_with_ass_inp = query_with_ass_inp.where(Project.vehicle_workshop_division == workshop_division)
		
		if branch:
			query_wo_ass_inp = query_wo_ass_inp.where(Project.branch == branch)
			if task_type_job_status:
				query_with_ass_inp = query_with_ass_inp.where(Project.branch == branch)

		if bill_to_customer_check:
			if bill_to_customer_check == "Same":
				query_wo_ass_inp = query_wo_ass_inp.where((Project.insurance_company == "") | (Project.insurance_company.isnull()))
				if task_type_job_status:
					query_with_ass_inp = query_with_ass_inp.where((Project.insurance_company == "") | (Project.insurance_company.isnull()))
			else:
				query_wo_ass_inp = query_wo_ass_inp.where(((Project.insurance_company!="") & (Project.insurance_company.isnotnull())))
				if task_type_job_status:
					query_with_ass_inp = query_with_ass_inp.where(((Project.insurance_company!="") & (Project.insurance_company.isnotnull())))
		
		if customer_list:
			query_wo_ass_inp = query_wo_ass_inp.where(Project.customer.isin(customer_list))
			if task_type_job_status:
				query_with_ass_inp = query_with_ass_inp.where(Project.customer.isin(customer_list))
		else:
			query_wo_ass_inp = query_wo_ass_inp.where(Project.customer == None)
			if task_type_job_status:
				query_with_ass_inp = query_with_ass_inp.where(Project.customer == None)
		
		query_wo_ass_inp = query_wo_ass_inp.where((Project.project_date>=from_date) & (Project.project_date<=to_date))
		if task_type_job_status:
			query_with_ass_inp = query_with_ass_inp.where((Project.project_date>=from_date) & (Project.project_date<=to_date))

		if task_type_job_status:
			query_with_ass_inp_result = query_with_ass_inp.run(as_dict=True)
		
		workshop_division_project_status_data_mechanical = query_wo_ass_inp.run(as_dict=True)

		final_list.extend(workshop_division_project_status_data_mechanical)
		if task_type_job_status:
			final_list.extend(query_with_ass_inp_result)
	return final_list

def query_with_ass_inp_method(Project, LatestVSR, VGP, datediff, each_timespan, task_type_job_status):

	query_wo_ass_inp = (
			frappe.qb
			.from_(Project)
			.left_join(LatestVSR)
			.on((LatestVSR.project == Project.name) & (LatestVSR.docstatus == 1))
			.left_join(VGP)
			.on((VGP.project == Project.name) & (VGP.docstatus == 1))
			.where((LatestVSR.docstatus == 1) & Project.project_status.isin(task_type_job_status))  # Additional filters below
			.groupby(Project.current_task_type, Project.project_status)
			.select(
				Count(Project.name).distinct().as_("total_ro"),
				Sum(datediff(IfNull(VGP.posting_date, today()), LatestVSR.posting_date)).as_("timespend"),
				Ceil(
					IfNull(
						Sum(datediff(IfNull(VGP.posting_date, today()), LatestVSR.posting_date)) / Count(Project.name).distinct(),
						0
					)
				).as_("average"),
				Ceil(
					IfNull(
						Sum(datediff(IfNull(VGP.posting_date, today()), LatestVSR.posting_date)),
						0
					)
				).as_("total_time_take"),
				Project.current_task_type,
				Project.vehicle_workshop_division,
				Literal(each_timespan).as_("timespan"),
				Concat(
					Project.project_status, 
					" (", 
					Project.current_task_type, 
					")"
				).as_("project_status"),
				Project.project_status.as_("original_project_status")
			)
		)
	return query_wo_ass_inp


@frappe.whitelist()
def fetch_ro_project_status_based_workshop_division_for_vehicle(
	workshop_division=None, bill_to_customer_check=None, 
	customer_list=None, division_dict=None, 
	timespan=None, selected_date=None, 
	branch=None, workspace=None, 
	custom_order_field=None, task_type_job_status_field=None):
	"""
	Fetch RO project status based on workshop division and customer.
	"""
	if division_dict:
		division_dict = json.loads(division_dict)
	
	if timespan == "YTD":
		timespan = ["YTD"]
	elif timespan == "MTD":
		timespan = ["MTD"]
	elif timespan == "MTD and YTD":
		timespan = ["MTD", "YTD"]
	elif timespan == "Custom Date":
		timespan = ["Custom Date"]

	final_category_result = {
		"brac_mechanical": None, 
		"brac_bodyshop": None, 
		"mechanical_category": None, 
		"brac_category": None, 
		"body_shop_cash_category": None, 
		"body_shop_insurance_category": None,
		"selected_filters" : {
			"branch": branch
		},
		"custom_order_field":[]
	}

	customer_list = get_customers_list(workspace)

	if fetch_custom_order_data(custom_order_field):
		final_category_result["custom_order_field"] = fetch_custom_order_data(custom_order_field)

	for each_division in division_dict:
		if each_division.get("category") == "Mechanical":
			workshop_division = each_division.get("workshop_division")
			bill_to_customer_check = each_division.get("bill_to_customer_check")
			final_category_result["mechanical_category"] = fetch_ro_project_status_based_workshop_division(
				workshop_division = workshop_division, bill_to_customer_check = bill_to_customer_check, 
				customer_list = customer_list, timespan_list = timespan, 
				selected_date=selected_date, branch=branch, task_type_job_status_field=task_type_job_status_field)
		elif each_division.get("category") == "BRAC":
			workshop_division = each_division.get("workshop_division")
			bill_to_customer_check = each_division.get("bill_to_customer_check")
			final_category_result["brac_category"] = fetch_ro_project_status_based_workshop_division(
				workshop_division = workshop_division, bill_to_customer_check = bill_to_customer_check, 
				customer_list = customer_list, timespan_list = timespan, selected_date=selected_date, 
				branch=branch, task_type_job_status_field=task_type_job_status_field)
		elif each_division.get("category") == "BRAC MECHANICAL":
			workshop_division = each_division.get("workshop_division")
			bill_to_customer_check = each_division.get("bill_to_customer_check")
			final_category_result["brac_mechanical"] = fetch_ro_project_status_based_workshop_division(
				workshop_division = workshop_division, bill_to_customer_check = bill_to_customer_check, 
				customer_list = customer_list, timespan_list = timespan, selected_date=selected_date, 
				branch=branch, task_type_job_status_field=task_type_job_status_field)
		elif each_division.get("category") == "BRAC BODYSHOP":
			workshop_division = each_division.get("workshop_division")
			bill_to_customer_check = each_division.get("bill_to_customer_check")
			final_category_result["brac_bodyshop"] = fetch_ro_project_status_based_workshop_division(
				workshop_division = workshop_division, bill_to_customer_check = bill_to_customer_check, 
				customer_list = customer_list, timespan_list = timespan, selected_date=selected_date, 
				branch=branch, task_type_job_status_field=task_type_job_status_field)
		elif each_division.get("category") == "Body Shop - Cash":
			workshop_division = each_division.get("workshop_division")
			bill_to_customer_check = each_division.get("bill_to_customer_check")
			final_category_result["body_shop_cash_category"] = fetch_ro_project_status_based_workshop_division(
				workshop_division = workshop_division, bill_to_customer_check = bill_to_customer_check, 
				customer_list = customer_list, timespan_list = timespan, selected_date=selected_date, 
				branch=branch, task_type_job_status_field=task_type_job_status_field)
		elif each_division.get("category") == "Body Shop - Insurance":
			workshop_division = each_division.get("workshop_division")
			bill_to_customer_check = each_division.get("bill_to_customer_check")
			final_category_result["body_shop_insurance_category"] = fetch_ro_project_status_based_workshop_division(
				workshop_division = workshop_division, bill_to_customer_check = bill_to_customer_check, 
				customer_list = customer_list, timespan_list = timespan, selected_date=selected_date, 
				branch=branch, task_type_job_status_field=task_type_job_status_field)

	return final_category_result

@frappe.whitelist()
def get_customers_list(workspace):
	customer_list = []
	customer_groups_list = []
	customer_group = None

	if frappe.db.exists("Workspace Customer Group Details",
			{
				"parent":"Workspace Settings", 
				"workspace":workspace
			}
		):
		customer_group =  frappe.db.get_value(
			"Workspace Customer Group Details", 
			filters={
				"parent":"Workspace Settings", 
				"workspace":workspace
			},
			fieldname=["customer_group"]
		)
	
	if customer_group:
		customer_groups_list = get_descendants_of("Customer Group", customer_group)
		customer_groups_list.append(customer_group)

	if customer_groups_list:
		customer_list = frappe.get_list("Customer", 
		filters={"customer_group":["in",customer_groups_list]}, 
		pluck="name")
	
	return customer_list

@frappe.whitelist()
def fetch_branch():
	return frappe.get_all("Branch", pluck="name")

@frappe.whitelist()
def download_excel_sheet(html_table):
	file_name = "excel_sheet_"+nowtime()+".xlsx"
	html_table_to_excel(html_table, file_name)

def fetch_custom_order_data(field_name):
	job_status_list = frappe.get_all("Job Status Details", filters={
			"parent":"Workspace Settings", 
			"parentfield":field_name
		}, fields=["job_status"], pluck="job_status")
	if job_status_list:
		return job_status_list