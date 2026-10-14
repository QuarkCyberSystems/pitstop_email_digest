import frappe
from erpnext.accounts.utils import get_fiscal_year
from frappe import _, qb, query_builder
from frappe.query_builder.functions import Count, IfNull, Max, Sum
from frappe.utils import getdate, nowtime, today
from frappe.utils.nestedset import get_descendants_of
from pypika.terms import Function

from pitstop_email_digest.utils.download_excel_sheet_from_html.download_excel_sheet import (
    html_table_to_excel,
)


# Define CEIL function
class Ceil(Function):
    def __init__(self, term, *args):
        super().__init__("CEIL", term, *args)


@frappe.whitelist()
def get_vehicle_movement(
    customer=None, customer_group=None, from_year=None, to_year=None
):
    """
    Optimized vehicle movement metrics (Daily / Monthly / Yearly)
    """
    frequencies = ("Daily", "Monthly", "Yearly")

    validate_year_range(from_year, to_year)
    customer_list = get_customers_list(customer, customer_group)

    # no customers matched the filters, nothing to count
    if customer_list == []:
        return {
            f: {
                "number_of_vehicle_in": 0,
                "number_of_vehicle_out": 0,
                "average_time_delivery": [{"average": 0}],
            }
            for f in frequencies
        }

    result = {f: {} for f in frequencies}

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

        if customer_list is not None:
            vehicle_in_q = vehicle_in_q.where(TVSR.customer.isin(customer_list))
            vehicle_out_q = vehicle_out_q.where(TVGP.customer.isin(customer_list))
            avg_delivery_q = avg_delivery_q.where(TP.customer.isin(customer_list))

        # Fetch data based on the branch
        branch_list = frappe.get_list("Branch", pluck="name")
        if branch_list:
            vehicle_in_q = vehicle_in_q.where(TVSR.branch.isin(branch_list))
            vehicle_out_q = vehicle_out_q.where(TVGP.branch.isin(branch_list))
            avg_delivery_q = avg_delivery_q.where(TP.branch.isin(branch_list))
        else:
            vehicle_in_q = vehicle_in_q.where(
                (TVSR.branch.isnull()) | (TVSR.branch == "")
            )
            vehicle_out_q = vehicle_out_q.where(
                (TVGP.branch.isnull()) | (TVGP.branch == "")
            )
            avg_delivery_q = avg_delivery_q.where(
                (TP.branch.isnull()) | (TP.branch == "")
            )

        result[freq] = {
            "number_of_vehicle_in": vehicle_in_q.run(as_dict=True)[0]["count"],
            "number_of_vehicle_out": vehicle_out_q.run(as_dict=True)[0]["count"],
            "average_time_delivery": avg_delivery_q.run(as_dict=True),
        }

    return result


def get_customers_list(customer=None, customer_group=None):
    """
    Customers to filter on, from the selected Customer and / or Customer Group.
    At least one of them is mandatory.

    Returns None when no customer filter is needed (root Customer Group selected),
    otherwise the list of customers, which can be empty when nothing matched.
    """
    if not customer and not customer_group:
        frappe.throw(_("Please select a Customer or Customer Group"))

    if customer_group and not frappe.db.exists("Customer Group", customer_group):
        frappe.throw(_("Customer Group {0} does not exist").format(customer_group))

    customer_groups_list = []
    if customer_group:
        customer_groups_list = get_descendants_of("Customer Group", customer_group)
        customer_groups_list.append(customer_group)

    if customer:
        if not frappe.db.exists("Customer", customer):
            frappe.throw(_("Customer {0} does not exist").format(customer))

        if customer_groups_list:
            group = frappe.db.get_value("Customer", customer, "customer_group")
            if group not in customer_groups_list:
                frappe.throw(
                    _("Customer {0} does not belong to Customer Group {1}").format(
                        customer, customer_group
                    )
                )

        return [customer]

    # no filter for root customer group, it covers every customer
    if not frappe.db.get_value(
        "Customer Group", customer_group, "parent_customer_group"
    ):
        return None

    return frappe.get_list(
        "Customer",
        filters={"customer_group": ["in", customer_groups_list]},
        pluck="name",
    )


def validate_year_range(from_year, to_year):
    if not from_year or not to_year:
        frappe.throw(_("From Year and To Year are mandatory"))

    if str(to_year) < str(from_year):
        frappe.throw(_("From Year should be before the To Year"))


@frappe.whitelist()
def fetch_branch():
    return frappe.get_list("Branch", pluck="name")


@frappe.whitelist()
def fetch_fiscal_year():
    return frappe.get_all("Fiscal Year", filters={"disabled": 0}, pluck="name")


def fetch_all_category(
    from_date, to_date, branch=None, customer_list=None, timespan=None
):
    customer_condition = ""
    params = {
        "from_date": from_date,
        "to_date": to_date,
        "timespan": timespan,
    }

    if branch and frappe.has_permission(
        "Branch", "read", user=frappe.session.user, doc=branch, throw=False
    ):
        branch_condition = "AND p.branch = %(branch)s"
        params["branch"] = branch
    elif branch:
        branch_list = frappe.get_list("Branch", pluck="name")
        if branch_list and (branch in branch_list):
            branch_condition = "AND p.branch in %(branch)s"
        else:
            branch_condition = "AND (p.branch is null or p.branch = '')"
        params["branch"] = branch_list
    elif not branch:
        branch_list = frappe.get_list("Branch", pluck="name")
        if branch_list:
            branch_condition = "AND p.branch in %(branch)s"
        else:
            branch_condition = "AND (p.branch is null or p.branch = '')"
        params["branch"] = branch_list

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
        p.project_status AS original_project_status,
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
        {customer_condition} {branch_condition}
    GROUP BY
        p.project_status,
        CASE
            WHEN p.project_status IN ('Assigned', 'In Progress')
            THEN p.current_task_type
            ELSE NULL
        END
    """
    return frappe.db.sql(sql_query_fstring, params, as_dict=True)


def fetch_custom_order_data(field_name):
    job_status_list = frappe.get_all(
        "Job Status Details",
        filters={"parent": "Workspace Settings", "parentfield": field_name},
        fields=["job_status"],
        pluck="job_status",
        order_by="idx asc",
    )
    if job_status_list:
        return job_status_list


@frappe.whitelist()
def get_vehicle_movement_a_day(
    selected_date=None, customer=None, customer_group=None, custom_order_field=None
):
    """
    Project status wise RO count for Mechanical / Body Shop on a single day.
    """
    if not selected_date:
        frappe.throw(_("Please select a date."))

    customer_list = get_customers_list(customer, customer_group)

    result = {"all_mechanical": [], "all_bodyshop": [], "custom_order_field": []}
    result["custom_order_field"] = fetch_custom_order_data(custom_order_field) or []

    # no customers matched the filters, nothing to count
    if customer_list == []:
        return result

    for row in fetch_all_category(
        selected_date,
        selected_date,
        customer_list=customer_list,
        timespan="Custom Date",
    ):
        if row["check_mechanical_bodyshop"] in result:
            result[row["check_mechanical_bodyshop"]].append(row)

    return result


def fetch_division_group_category(
    from_date, to_date, branch=None, customer_list=None, timespan=None
):
    customer_condition = ""
    branch_condition = ""
    params = {"from_date": from_date, "to_date": to_date, "timespan": timespan}

    if branch and frappe.has_permission(
        "Branch", "read", user=frappe.session.user, doc=branch, throw=False
    ):
        branch_condition = "AND p.branch = %(branch)s"
        params["branch"] = branch
    elif branch:
        branch_list = frappe.get_list("Branch", pluck="name")
        if branch_list and (branch in branch_list):
            branch_condition = "AND p.branch in %(branch)s"
        else:
            branch_condition = "AND (p.branch is null or p.branch = '')"
        params["branch"] = branch_list
    elif not branch:
        branch_list = frappe.get_list("Branch", pluck="name")
        if branch_list:
            branch_condition = "AND p.branch in %(branch)s"
        else:
            branch_condition = "AND (p.branch is null or p.branch = '')"
        params["branch"] = branch_list

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
		p.project_status AS original_project_status,

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
		{customer_condition} {branch_condition}
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
def get_vehicle_movement_workshop_division(
    branch=None,
    from_year=None,
    to_year=None,
    customer=None,
    customer_group=None,
    custom_order_field=None,
):
    """
    Project status wise RO count / average days for Mechanical, Body Shop (Cash / Insurance)
    and all categories, for MTD and YTD.
    """
    validate_year_range(from_year, to_year)
    customer_list = get_customers_list(customer, customer_group)

    branch = branch or None
    today_date = today()

    date_ranges = {
        "MTD": (frappe.utils.data.get_first_day(today_date), today_date),
        "YTD": (
            get_fiscal_year(fiscal_year=str(from_year))[1]
            if from_year
            else get_fiscal_year(today_date)[1],
            get_fiscal_year(fiscal_year=str(to_year))[2] if to_year else today_date,
        ),
    }

    result = {
        "mechanical_category": [],
        "body_shop_cash_category": [],
        "body_shop_insurance_category": [],
        "all_category": [],
        "custom_order_field": fetch_custom_order_data(custom_order_field) or [],
        # date range of each timespan, used by the page to drill down into the report
        "date_ranges": {
            timespan: [str(from_date), str(to_date)]
            for timespan, (from_date, to_date) in date_ranges.items()
        },
    }

    # no customers matched the filters, nothing to count
    if customer_list == []:
        return result

    for timespan, (from_date, to_date) in date_ranges.items():
        for row in fetch_division_group_category(
            from_date,
            to_date,
            branch=branch,
            customer_list=customer_list,
            timespan=timespan,
        ):
            if row["category_key"]:
                result[row["category_key"]].append(row)

        result["all_category"].extend(
            fetch_all_category(
                from_date,
                to_date,
                branch=branch,
                customer_list=customer_list,
                timespan=timespan,
            )
        )

    return result


@frappe.whitelist()
def download_excel_sheet(html_table, filters=None):
    html_table_to_excel(html_table, "excel_sheet_" + nowtime() + ".xlsx", filters)


@frappe.whitelist()
def get_vehicle_movement_details(
    from_date=None,
    to_date=None,
    customer=None,
    customer_group=None,
    workshop_division=None,
    project_status=None,
    current_task_type=None,
    branch=None,
    billing_type=None,
    task_type_job_status_field=None,
    link_access_roles_field=None,
):
    """
    Repair orders behind a count on the page, shown in the drill down popup.
    """
    if not from_date or not to_date:
        frappe.throw(_("From Date and To Date are mandatory"))

    if getdate(from_date) > getdate(to_date):
        frappe.throw(_("From Date should be before the To Date"))

    customer_list = get_customers_list(customer, customer_group)
    result = {
        "data": [],
        "can_open_repair_order": can_open_repair_order(link_access_roles_field),
    }

    # no customers matched the filters
    if customer_list == []:
        return result

    Project = qb.DocType("Project")
    VSR = qb.DocType("Vehicle Service Receipt")
    VGP = qb.DocType("Vehicle Gate Pass")

    datediff = query_builder.CustomFunction("DATEDIFF", ["cur_date", "due_date"])

    LatestVSRSub = (
        qb.from_(VSR)
        .select(VSR.project, Max(VSR.posting_date).as_("max_posting_date"))
        .where(VSR.docstatus == 1)
        .groupby(VSR.project)
    ).as_("latest_vsr_sub")

    LatestVSR = (
        qb.from_(VSR)
        .join(LatestVSRSub)
        .on(
            (VSR.project == LatestVSRSub.project)
            & (VSR.posting_date == LatestVSRSub.max_posting_date)
        )
        .select(VSR.name, VSR.project, VSR.posting_date, VSR.docstatus)
    ).as_("latest_vsr")

    query = (
        qb.from_(Project)
        .left_join(LatestVSR)
        .on(LatestVSR.project == Project.name)
        .left_join(VGP)
        .on(
            (VGP.project == Project.name)
            & (VGP.docstatus == 1)
            & (VGP.purpose == "Service - Vehicle Delivery")
        )
        .where(LatestVSR.docstatus == 1)
        .where(Project.project_date.between(from_date, to_date))
        .select(
            Project.name.as_("repair_order"),
            datediff(IfNull(VGP.posting_date, today()), LatestVSR.posting_date).as_(
                "timespend"
            ),
            Project.project_status,
            Project.current_task_type,
            Project.vehicle_workshop_division,
            Project.project_date,
            Project.customer_name,
            Project.insurance_company_name,
            VGP.posting_date.as_("gate_pass_posting_date"),
            LatestVSR.posting_date.as_("vehicle_receive_date"),
            Project.vehicle_chassis_no,
            Project.vehicle_license_plate,
            Project.applies_to_item.as_("vehicle_model"),
        )
        .orderby(Project.project_date)
    )

    if customer_list is not None:
        query = query.where(Project.customer.isin(customer_list))

    if workshop_division:
        query = query.where(Project.vehicle_workshop_division == workshop_division)

    if project_status:
        query = query.where(Project.project_status == project_status)

    task_type_job_status = (
        fetch_custom_order_data(task_type_job_status_field) or []
        if task_type_job_status_field
        else []
    )
    if current_task_type:
        query = query.where(Project.current_task_type == current_task_type)
    elif project_status in task_type_job_status:
        query = query.where(
            (Project.current_task_type.isnull()) | (Project.current_task_type == "")
        )

    if billing_type == "Customer":
        query = query.where(
            (Project.insurance_company == "") | (Project.insurance_company.isnull())
        )
    elif billing_type == "Insurance":
        query = query.where(
            (Project.insurance_company != "") & (Project.insurance_company.isnotnull())
        )

    if branch and frappe.has_permission(
        "Branch", "read", user=frappe.session.user, doc=branch, throw=False
    ):
        query = query.where(Project.branch == branch)
    else:
        branch_list = frappe.get_list("Branch", pluck="name")
        if branch_list:
            query = query.where(Project.branch.isin(branch_list))
        else:
            query = query.where((Project.branch.isnull()) | (Project.branch == ""))

    result["data"] = query.run(as_dict=True)
    return result


def can_open_repair_order(link_access_roles_field):
    """
    Repair order is shown as a link only for the roles set in Workspace Settings.
    """
    if not link_access_roles_field:
        return False

    link_roles = frappe.get_all(
        "Role Details",
        filters={
            "parent": "Workspace Settings",
            "parentfield": link_access_roles_field,
        },
        pluck="roles",
    )
    return bool(set(link_roles) & set(frappe.get_roles()))
