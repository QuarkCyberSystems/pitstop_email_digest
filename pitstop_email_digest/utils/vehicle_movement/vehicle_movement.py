
import frappe
from frappe.utils import today
from frappe.query_builder.functions import Count, Sum, IfNull, Floor, Max
from frappe import _, qb, query_builder
import json
from erpnext.accounts.utils import get_fiscal_year
from pypika.terms import Term
from pypika.enums import SqlTypes

class Literal(Term):
	def __init__(self, value):
		super().__init__()
		self.value = value
		self.type = SqlTypes.VARCHAR

	def get_sql(self, **kwargs):
		if isinstance(self.value, str):
			return f"'{self.value}'"
		return str(self.value)

@frappe.whitelist()
def get_vehicle_movement(customer_list=None):
	"""
	Fetch vehicle movement data based on the specified frequency.
	"""
	frequency = ["Daily", "Monthly", "Yearly"]
	final_dict = {"Daily":[], "Monthly":[], "Yearly":[]}
	if customer_list:
		customer_list = json.loads(customer_list)
	
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

		number_of_vehicle_in = frappe.db.get_list('Vehicle Service Receipt', 
			fields=['count(name) as total_number_cars_in'],
			filters= {
				'posting_date': ["between", posting_date_filter_list],
				'customer': ["in", customer_list],
				'docstatus': 1
			}
		)

		number_of_vehicle_out = frappe.db.get_list('Vehicle Gate Pass', 
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
				Floor(
					IfNull(
						Sum(datediff(TVGP.posting_date, LatestVSR.posting_date)) / Count(TVGP.name),
						0
					), 0
				).as_("average")
			)
			.where(
				(TVGP.docstatus == 1) &
				(LatestVSR.docstatus == 1) &
				(TP.customer.isin(customer_list)) &
				(TVGP.posting_date>=from_date) & 
				(TVGP.posting_date<=to_date)
			)
		).run(as_dict=True)

		final_dict[each_frequency] = {"number_of_vehicle_in":number_of_vehicle_in, "number_of_vehicle_out":number_of_vehicle_out, "average_time_delivery":average_time_delivery}

	return final_dict

@frappe.whitelist()
def fetch_ro_project_status_based_workshop_division(workshop_division=None, bill_to_customer_check=None, customer_list=None, timespan_list=None, selected_date=None):

	Project = qb.DocType("Project")
	VSR = qb.DocType("Vehicle Service Receipt")
	VGP = qb.DocType("Vehicle Gate Pass")

	datediff = query_builder.CustomFunction("DATEDIFF", ["cur_date", "due_date"])

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

		query = (
			frappe.qb
			.from_(Project)
			.left_join(LatestVSR)
			.on((LatestVSR.project == Project.name) & (LatestVSR.docstatus == 1))
			.left_join(VGP)
			.on((VGP.project == Project.name) & (VGP.docstatus == 1))
			.where((LatestVSR.docstatus == 1))  # Additional filters below
			.groupby(Project.project_status)
			.select(
				Count(Project.name).as_("total_ro"),
				Sum(datediff(IfNull(VGP.posting_date, today()), LatestVSR.posting_date)).as_("timespend"),
				Floor(
					IfNull(
						Sum(datediff(IfNull(VGP.posting_date, today()), LatestVSR.posting_date)) / Count(Project.name),
						0
					),
					0
				).as_("average"),
				Floor(
					IfNull(
						Sum(datediff(IfNull(VGP.posting_date, today()), LatestVSR.posting_date)),
						0
					),
					0
				).as_("total_time_take"),
				Project.project_status,
				Project.vehicle_workshop_division,
				Literal(each_timespan).as_("timespan")
			)
		)

		# Add dynamic filters if applicable
		if workshop_division:
			query = query.where(Project.vehicle_workshop_division == workshop_division)

		if bill_to_customer_check:
			if bill_to_customer_check == "Same":
				query = query.where((Project.insurance_company == "") | (Project.insurance_company.isnull()))
			else:
				query = query.where(((Project.insurance_company!="") & (Project.insurance_company.isnotnull())))
		
		if customer_list:
			query = query.where(Project.customer.isin(customer_list))
		
		query = query.where((Project.project_date>=from_date) & (Project.project_date<=to_date))

		workshop_division_project_status_data_mechanical = query.run(as_dict=True)

		final_list.extend(workshop_division_project_status_data_mechanical)
	
	return final_list


@frappe.whitelist()
def fetch_ro_project_status_based_workshop_division_for_vehicle(workshop_division=None, bill_to_customer_check=None, customer_list=None, division_dict=None, timespan=None, selected_date=None):
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

	final_category_result = {"brac_mechanical": None, "brac_bodyshop": None, "mechanical_category": None, "brac_category": None, "body_shop_cash_category": None, "body_shop_insurance_category": None}
	for each_division in division_dict:
		if each_division.get("category") == "Mechanical":
			workshop_division = each_division.get("workshop_division")
			bill_to_customer_check = each_division.get("bill_to_customer_check")
			customer_list = each_division.get("customer_list")
			final_category_result["mechanical_category"] = fetch_ro_project_status_based_workshop_division(
				workshop_division = workshop_division, bill_to_customer_check = bill_to_customer_check, 
				customer_list = customer_list, timespan_list = timespan, selected_date=selected_date)
		elif each_division.get("category") == "BRAC":
			workshop_division = each_division.get("workshop_division")
			bill_to_customer_check = each_division.get("bill_to_customer_check")
			customer_list = each_division.get("customer_list")
			final_category_result["brac_category"] = fetch_ro_project_status_based_workshop_division(
				workshop_division = workshop_division, bill_to_customer_check = bill_to_customer_check, 
				customer_list = customer_list, timespan_list = timespan, selected_date=selected_date)
		elif each_division.get("category") == "BRAC MECHANICAL":
			workshop_division = each_division.get("workshop_division")
			bill_to_customer_check = each_division.get("bill_to_customer_check")
			customer_list = each_division.get("customer_list")
			final_category_result["brac_mechanical"] = fetch_ro_project_status_based_workshop_division(
				workshop_division = workshop_division, bill_to_customer_check = bill_to_customer_check, 
				customer_list = customer_list, timespan_list = timespan, selected_date=selected_date)
		elif each_division.get("category") == "BRAC BODYSHOP":
			workshop_division = each_division.get("workshop_division")
			bill_to_customer_check = each_division.get("bill_to_customer_check")
			customer_list = each_division.get("customer_list")
			final_category_result["brac_bodyshop"] = fetch_ro_project_status_based_workshop_division(
				workshop_division = workshop_division, bill_to_customer_check = bill_to_customer_check, 
				customer_list = customer_list, timespan_list = timespan, selected_date=selected_date)
		elif each_division.get("category") == "Body Shop - Cash":
			workshop_division = each_division.get("workshop_division")
			bill_to_customer_check = each_division.get("bill_to_customer_check")
			customer_list = each_division.get("customer_list")
			final_category_result["body_shop_cash_category"] = fetch_ro_project_status_based_workshop_division(
				workshop_division = workshop_division, bill_to_customer_check = bill_to_customer_check, 
				customer_list = customer_list, timespan_list = timespan, selected_date=selected_date)
		elif each_division.get("category") == "Body Shop - Insurance":
			workshop_division = each_division.get("workshop_division")
			bill_to_customer_check = each_division.get("bill_to_customer_check")
			customer_list = each_division.get("customer_list")
			final_category_result["body_shop_insurance_category"] = fetch_ro_project_status_based_workshop_division(
				workshop_division = workshop_division, bill_to_customer_check = bill_to_customer_check, 
				customer_list = customer_list, timespan_list = timespan, selected_date=selected_date)

	return final_category_result