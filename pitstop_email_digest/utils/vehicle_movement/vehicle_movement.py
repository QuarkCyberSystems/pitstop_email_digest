import json

import frappe
from erpnext.accounts.utils import get_fiscal_year
from frappe import qb, query_builder
from frappe.query_builder.functions import Count, IfNull, Max, Sum
from frappe.utils import nowtime, today
from frappe.utils.nestedset import get_descendants_of
from pypika.enums import SqlTypes
from pypika.terms import Function, Term

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
def get_vehicle_movement(workspace=None, from_year=None, to_year=None):
    """
    Optimized vehicle movement metrics (Daily / Monthly / Yearly)
    """
    frequencies = ("Daily", "Monthly", "Yearly")
    result = {f: {} for f in frequencies}

    customer_list = get_customers_list(workspace) if workspace else []

    today_date = frappe.utils.getdate(frappe.utils.nowdate())

    date_ranges = {
        "Daily": (today(), today()),
        "Monthly": (frappe.utils.get_first_day(today()), today()),
        "Yearly": (
            get_fiscal_year(str(from_year))[1]
            if from_year
            else get_fiscal_year(today_date)[1],
            get_fiscal_year(str(to_year))[2] if to_year else today(),
        ),
    }

    TVSR = qb.DocType("Vehicle Service Receipt")
    TVGP = qb.DocType("Vehicle Gate Pass")
    TP = qb.DocType("Project")

    LatestVSRSub = (
        qb.from_(TVSR)
        .select(TVSR.project, Max(TVSR.posting_date).as_("max_posting_date"))
        .where(TVSR.docstatus == 1)
        .groupby(TVSR.project)
    ).as_("latest_vsr_sub")

    LatestVSR = (
        qb.from_(TVSR)
        .join(LatestVSRSub)
        .on(
            (TVSR.project == LatestVSRSub.project)
            & (TVSR.posting_date == LatestVSRSub.max_posting_date)
        )
        .select(TVSR.project, TVSR.posting_date, TVSR.docstatus)
    ).as_("latest_vsr")

    datediff = query_builder.CustomFunction("DATEDIFF", ["cur_date", "due_date"])

    for freq in frequencies:
        from_date, to_date = date_ranges[freq]

        vehicle_in_q = (
            qb.from_(TVSR)
            .select(Count(TVSR.name).as_("count"))
            .where(
                (TVSR.docstatus == 1) & (TVSR.posting_date.between(from_date, to_date))
            )
        )

        vehicle_out_q = (
            qb.from_(TVGP)
            .select(Count(TVGP.name).as_("count"))
            .where(
                (TVGP.docstatus == 1) & (TVGP.posting_date.between(from_date, to_date))
            )
        )

        avg_delivery_q = (
            qb.from_(TVGP)
            .join(TP)
            .on(TP.name == TVGP.project)
            .left_join(LatestVSR)
            .on(LatestVSR.project == TP.name)
            .select(
                Count(TVGP.name).as_("total_deliveries"),
                Sum(datediff(TVGP.posting_date, LatestVSR.posting_date)).as_(
                    "timespend"
                ),
                Ceil(
                    IfNull(
                        Sum(datediff(TVGP.posting_date, LatestVSR.posting_date))
                        / Count(TVGP.name),
                        0,
                    )
                ).as_("average"),
            )
            .where(
                (TVGP.docstatus == 1)
                & (LatestVSR.docstatus == 1)
                & (TVGP.posting_date.between(from_date, to_date))
                & (TVGP.purpose == "Service - Vehicle Delivery")
            )
        )

        if customer_list:
            vehicle_in_q = vehicle_in_q.where(TVSR.customer.isin(customer_list))
            vehicle_out_q = vehicle_out_q.where(TVGP.customer.isin(customer_list))
            avg_delivery_q = avg_delivery_q.where(TP.customer.isin(customer_list))

        result[freq] = {
            "number_of_vehicle_in": vehicle_in_q.run(as_dict=True)[0]["count"],
            "number_of_vehicle_out": vehicle_out_q.run(as_dict=True)[0]["count"],
            "average_time_delivery": avg_delivery_q.run(as_dict=True),
        }

    return result


def fetch_all_category(
    from_date, to_date, branch=None, customer_list=None, timespan=None
):
    customer_condition = ""
    params = {
        "from_date": from_date,
        "to_date": to_date,
        "branch": branch,
        "timespan": timespan,
    }

    if customer_list:
        customer_condition = "AND p.customer IN %(customer_list)s"
        params["customer_list"] = tuple(customer_list)

    sql_query_fstring = f"""
    SELECT
        COUNT(DISTINCT p.name) AS total_ro,
        CEIL(SUM(DATEDIFF(IFNULL(vgp.posting_date, CURDATE()), lv.posting_date))) AS total_time_take,
        CEIL(
            IFNULL(
                SUM(DATEDIFF(IFNULL(vgp.posting_date, CURDATE()), lv.posting_date)) / COUNT(DISTINCT p.name),
                0
            )
        ) AS average,
        p.project_status,
        p.project_status AS original_status,
        CASE
            WHEN p.project_status IN ('Assigned', 'In Progress')
            THEN p.current_task_type
            ELSE NULL
        END AS current_task_type,
		CASE
			WHEN p.vehicle_workshop_division = 'Mechanical'
				THEN 'all_mechanical'
			WHEN p.vehicle_workshop_division = 'Body Shop'
				THEN 'all_bodyshop'
		END AS check_mechanical_bodyshop,
        %(timespan)s AS timespan
    FROM `tabProject` p
    INNER JOIN (
        SELECT project, MAX(posting_date) AS posting_date
        FROM `tabVehicle Service Receipt`
        WHERE docstatus = 1
        GROUP BY project
    ) lv ON lv.project = p.name
    LEFT JOIN `tabVehicle Gate Pass` vgp
        ON vgp.project = p.name
        AND vgp.docstatus = 1
        AND vgp.purpose = 'Service - Vehicle Delivery'
    WHERE
        p.project_date BETWEEN %(from_date)s AND %(to_date)s
        AND (%(branch)s IS NULL OR p.branch = %(branch)s)
        {customer_condition}
    GROUP BY
        p.project_status,
        CASE
            WHEN p.project_status IN ('Assigned', 'In Progress')
            THEN p.current_task_type
            ELSE NULL
        END
    """
    return frappe.db.sql(sql_query_fstring, params, as_dict=True)


def fetch_division_group_category(
    from_date, to_date, branch=None, customer_list=None, timespan=None
):
    customer_condition = ""
    params = {
        "from_date": from_date,
        "to_date": to_date,
        "branch": branch,
        "timespan": timespan,
    }

    if customer_list:
        customer_condition = "AND p.customer IN %(customer_list)s"
        params["customer_list"] = tuple(customer_list)

    sql_f_string = f"""
	SELECT
		COUNT(DISTINCT p.name) AS total_ro,
		CEIL(
			SUM(
				DATEDIFF(
					IFNULL(vgp.posting_date, CURDATE()),
					lv.posting_date
				)
			)
		) AS total_time_take,
		CEIL(
			IFNULL(
				SUM(
					DATEDIFF(
						IFNULL(vgp.posting_date, CURDATE()),
						lv.posting_date
					)
				) / COUNT(DISTINCT p.name),
				0
			)
		) AS average,
		p.project_status,
		p.project_status AS original_status,

		-- ✅ conditional task grouping for Assigned & In Progress
		CASE
			WHEN p.project_status IN ('Assigned', 'In Progress')
			THEN p.current_task_type
			ELSE NULL
		END AS current_task_type,

		CASE
			WHEN p.vehicle_workshop_division = 'Mechanical'
				THEN 'mechanical_category'
			WHEN p.vehicle_workshop_division = 'Body Shop'
				AND (p.insurance_company IS NULL OR p.insurance_company = '')
				THEN 'body_shop_cash_category'
			WHEN p.vehicle_workshop_division = 'Body Shop'
				AND (p.insurance_company IS NOT NULL AND p.insurance_company != '')
				THEN 'body_shop_insurance_category'
		END AS category_key,
		CASE
			WHEN p.vehicle_workshop_division = 'Mechanical'
				THEN 'all_mechanical'
			WHEN p.vehicle_workshop_division = 'Body Shop'
				THEN 'all_bodyshop'
		END AS check_mechanical_bodyshop,
		%(timespan)s AS timespan
	FROM `tabProject` p
	INNER JOIN (
		SELECT project, MAX(posting_date) AS posting_date
		FROM `tabVehicle Service Receipt`
		WHERE docstatus = 1
		GROUP BY project
	) lv ON lv.project = p.name
	LEFT JOIN `tabVehicle Gate Pass` vgp
		ON vgp.project = p.name
		AND vgp.docstatus = 1
		AND vgp.purpose = 'Service - Vehicle Delivery'
	WHERE
		p.project_date BETWEEN %(from_date)s AND %(to_date)s
		AND (%(branch)s IS NULL OR p.branch = %(branch)s)
		{customer_condition}
	GROUP BY
		category_key,
		p.project_status,
		CASE
			WHEN p.project_status IN ('Assigned', 'In Progress')
			THEN p.current_task_type
			ELSE NULL
		END
	"""

    return frappe.db.sql(sql_f_string, params, as_dict=True)


@frappe.whitelist()
def fetch_ro_project_status_based_workshop_division_for_vehicle(
    workshop_division=None,
    bill_to_customer_check=None,
    customer_list=None,
    division_dict=None,
    timespan=None,
    selected_date=None,
    branch=None,
    workspace=None,
    custom_order_field=None,
    task_type_job_status_field=None,
    from_year=None,
    to_year=None,
):
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
        "all_mechanical": [],
        "all_bodyshop": [],
        "mechanical_category": [],
        "all_category": [],
        "body_shop_cash_category": [],
        "body_shop_insurance_category": [],
        "selected_filters": {"branch": branch},
        "custom_order_field": [],
    }

    customer_list = get_customers_list(workspace)

    for each_timespan in timespan:
        today_date = today()

        if each_timespan == "YTD":
            from_date = (
                get_fiscal_year(fiscal_year=str(from_year))[1]
                if from_year
                else get_fiscal_year(today_date)[1]
            )
            to_date = (
                get_fiscal_year(fiscal_year=str(to_year))[2] if to_year else today()
            )
        elif each_timespan == "MTD":
            from_date = frappe.utils.data.get_first_day(today_date)
            to_date = today()
        elif each_timespan == "Custom Date":
            from_date = selected_date
            to_date = selected_date

        division_group_result = fetch_division_group_category(
            from_date,
            to_date,
            branch=branch if (branch and branch != "") else None,
            customer_list=customer_list,
            timespan=each_timespan,
        )
        for row in division_group_result:
            if row["category_key"]:
                final_category_result[row["category_key"]].append(row)

        # fetch brac_category separately
        all_result = fetch_all_category(
            from_date,
            to_date,
            branch=branch if (branch and branch != "") else None,
            customer_list=customer_list,
            timespan=each_timespan,
        )

        for row in all_result:
            if row["check_mechanical_bodyshop"] == "all_mechanical":
                final_category_result["all_mechanical"].append(row)
            if row["check_mechanical_bodyshop"] == "all_bodyshop":
                final_category_result["all_bodyshop"].append(row)
            final_category_result["all_category"].append(row)

    if fetch_custom_order_data(custom_order_field):
        final_category_result["custom_order_field"] = fetch_custom_order_data(
            custom_order_field
        )

    return final_category_result


@frappe.whitelist()
def get_customers_list(workspace):
    customer_list = []
    customer_groups_list = []
    customer_group = None

    if frappe.db.exists(
        "Workspace Customer Group Details",
        {"parent": "Workspace Settings", "workspace": workspace},
    ):
        customer_group = frappe.db.get_value(
            "Workspace Customer Group Details",
            filters={"parent": "Workspace Settings", "workspace": workspace},
            fieldname=["customer_group"],
        )

        parent_customer_group = frappe.db.get_value(
            "Customer Group", customer_group, "parent_customer_group"
        )

        # no filter for root customer group
        if not parent_customer_group:
            customer_group = None

    if customer_group:
        customer_groups_list = get_descendants_of("Customer Group", customer_group)
        customer_groups_list.append(customer_group)

    if customer_groups_list:
        customer_list = frappe.get_list(
            "Customer",
            filters={"customer_group": ["in", customer_groups_list]},
            pluck="name",
        )

    return customer_list


@frappe.whitelist()
def fetch_branch():
    return frappe.get_all("Branch", pluck="name")


@frappe.whitelist()
def fetch_fiscal_year():
    return frappe.get_all("Fiscal Year", filters={"disabled": 0}, pluck="name")


@frappe.whitelist()
def download_excel_sheet(html_table):
    file_name = "excel_sheet_" + nowtime() + ".xlsx"
    html_table_to_excel(html_table, file_name)


def fetch_custom_order_data(field_name):
    job_status_list = frappe.get_all(
        "Job Status Details",
        filters={"parent": "Workspace Settings", "parentfield": field_name},
        fields=["job_status"],
        pluck="job_status",
    )
    if job_status_list:
        return job_status_list
