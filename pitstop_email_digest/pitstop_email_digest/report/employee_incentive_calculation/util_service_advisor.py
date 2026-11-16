"""Service Advisor incentive calculation.

Driven by the Workshop Turnover report grouped by service advisor, and scored
on revenue against target, customer feedback and WIP ageing.
"""

import frappe
from frappe.utils import flt, getdate

from .util_employee_incentive_calculation import (
    apply_customer_feedback,
    apply_wip_ageing,
    compute_incentive,
    get_ladder_result,
    weightage_amount,
)

TEMPLATE_DATA = {
    "weightages": {"revenue": 45, "customer_feedback": 35, "wip_ageing": 20},
    "revenue_ladder": {
        85: 0,
        90: 85,
        95: 90,
        100: 95,
        105: 100,
        110: 105,
        115: 110,
        125: 115,
    },
    "wip_ageing_ladder": {45: 100.0, 46: 0.0},
    "cfb_rate_ladder": {4.5: 0, 4.6: 100.0, 5.0: 125.0},
}

REPORT_FILTERS = {
    "group_by_1": "Group by Service Advisor",
    "include_tasks": 1,
}

SOURCE_REPORT = "turnover"


def get_leading_columns():
    """Columns shown before the source report's own columns."""
    return [
        {
            "label": "Employee ID",
            "fieldname": "employee",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150,
        },
        {
            "label": "Employee Name",
            "fieldname": "employee_name",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Avg. CFB",
            "fieldname": "customer_overall_rating",
            "fieldtype": "Rating",
            "width": 200,
        },
        {
            "label": "Sales Amount",
            "fieldname": "total_sales_amount",
            "fieldtype": "Currency",
            "width": 100,
        },
        {
            "label": "Target Revenue",
            "fieldname": "sa_target_revenue",
            "fieldtype": "Currency",
            "width": 100,
        },
        {
            "label": "Revenue %",
            "fieldname": "revenue_percentage",
            "fieldtype": "Percent",
            "width": 100,
        },
        {
            "label": "WIP RO Count",
            "fieldname": "wip_ro_count",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "WIP Average Age",
            "fieldname": "wip_average_age",
            "fieldtype": "Float",
            "width": 100,
        },
    ]


def get_trailing_columns():
    """Columns shown after the source report's own columns."""
    return []


def fetch_feedback(filters):
    condition_dict = {
        "from_dt": filters.get("from_date"),
        "to_dt": filters.get("to_date"),
    }

    return frappe.db.sql(
        """
		select
			cbf_task_sa.service_advisor,
			count(distinct cbf_task_sa.project) as ro_count,
			round(avg(cbf_task_sa.overall_satisfaction_rating), 2) as avg_rating
		from (
			select distinct
				p.service_advisor,
				p.name as project,
				tcf.overall_satisfaction_rating
			from
				`tabSales Invoice` si
			join
				`tabSales Invoice Item` sii
			on
				sii.parent = si.name
			join
				`tabProject` p
			on
				p.name = sii.project
			join
				`tabCustomer Feedback` tcf
			on
				p.name = tcf.project
			where
				tcf.status = 'Completed'
				and p.service_advisor != ""
				and p.service_advisor is not null
				and si.docstatus = 1
				and si.posting_date between %(from_dt)s and %(to_dt)s
				and sii.project is not null
				and sii.project != ""
		) cbf_task_sa
		group by
			cbf_task_sa.service_advisor;
	""",
        condition_dict,
        as_dict=True,
    )


def get_service_advisor_designations():
    settings = frappe.get_cached_doc("Incentive Calculation Setttings")
    return [
        d.designation
        for d in (settings.service_advisor_designation or [])
        if d.designation
    ]


def fetch_service_advisors_by_designation(filters):
    """Map of eligible Service Advisor (Sales Person) -> their Employee details."""
    designations = get_service_advisor_designations()
    if not designations:
        return {}

    sp = frappe.qb.DocType("Sales Person")
    emp = frappe.qb.DocType("Employee")

    query = (
        frappe.qb.from_(sp)
        .inner_join(emp)
        .on(emp.name == sp.employee)
        .select(sp.name, emp.name.as_("employee"), emp.employee_name)
        .where(sp.is_service_advisor == 1)
        .where(sp.enabled == 1)
        .where(emp.status == "Active")
        .where(emp.designation.isin(designations))
    )
    if filters.get("company"):
        query = query.where(emp.company == filters.get("company"))

    rows = query.run(as_dict=True)
    return {
        row.name: {"employee": row.employee, "employee_name": row.employee_name}
        for row in rows
    }


def fetch_targets(filters):
    to_date = getdate(filters.get("to_date") or getdate())
    year = to_date.year
    month_field = to_date.strftime("%B").lower()

    trd = frappe.qb.DocType("Target Role Details")
    tr = frappe.qb.DocType("Target Role")

    rows = (
        frappe.qb.from_(trd)
        .inner_join(tr)
        .on(tr.name == trd.parent)
        .select(tr.sales_person, trd[month_field].as_("target_amount"))
        .where(trd.parenttype == "Target Role")
        .where(trd.parentfield == "targets")
        .where(trd.year == year)
        .where(tr.sales_person.isnotnull())
        .where(tr.sales_person != "")
        .run(as_dict=True)
    )

    return {row.get("sales_person"): flt(row.get("target_amount")) for row in rows}


def fetch_wip_age(filters):
    as_of = getdate(filters.get("to_date") or getdate())

    return frappe.db.sql(
        """
		select
			p.service_advisor,
			count(p.name) as ro_count,
			round(avg(datediff(%(as_of)s, date(p.project_date))), 2) as average_wip_age
		from
			`tabProject` p
		where
			p.status != 'Cancelled'
			and p.project_status != 'Completed'
			and p.service_advisor is not null
			and p.service_advisor != ''
			and p.project_date <= %(as_of)s
		group by
			p.service_advisor;
		""",
        {"as_of": as_of},
        as_dict=True,
    )


def prepare_lookups(filters):
    feedback = fetch_feedback(filters) or []
    return {
        "feedback_map": {d.get("service_advisor"): d for d in feedback},
        "wip_average_age": fetch_wip_age(filters) or [],
        "targets": fetch_targets(filters),
        "allowed_service_advisors": fetch_service_advisors_by_designation(filters),
    }


def compute_revenue_amount(filters, totals):
    totals["revenue_amt"] = 0.0

    revenue_percentage = (
        flt(
            (
                flt(totals.get("total_sales_amount"))
                / flt(totals.get("sa_target_revenue"))
            )
            * 100.0,
            3,
        )
        if flt(totals.get("sa_target_revenue"))
        else 0.0
    )
    totals["revenue_percentage"] = revenue_percentage

    result = get_ladder_result(
        based_on=filters.get("based_on"),
        sold_hrs_percentage=revenue_percentage,
        ladder_field="revenue_ladder",
        top_cap=125.0,
    )

    if result:
        totals["revenue_amt"] = flt(
            weightage_amount(filters, "revenue") * (result / 100.0), 3
        )


def process_rows(filters, source_data, qc_task_types, lookups):
    feedback_map = lookups.get("feedback_map") or {}
    wip_average_age = lookups.get("wip_average_age") or []
    targets = lookups.get("targets") or {}
    allowed_service_advisors = lookups.get("allowed_service_advisors") or {}
    seen = set()

    for each_turnover_data in source_data:
        for each_group_data in each_turnover_data.rows:
            totals_dict = each_group_data.totals
            service_advisor = totals_dict.get("service_advisor")

            if not service_advisor or service_advisor not in allowed_service_advisors:
                continue

            totals_dict.update(allowed_service_advisors[service_advisor])
            totals_dict["disable_party_name_formatter"] = 1

            apply_customer_feedback(
                filters, totals_dict, feedback_map.get(service_advisor)
            )
            apply_wip_ageing(filters, totals_dict, wip_average_age, "service_advisor")

            totals_dict["sa_target_revenue"] = targets.get(service_advisor, 0.0)

            compute_revenue_amount(filters, totals_dict)

            totals_dict["calculated_incentive"] = compute_incentive(
                totals_dict, filters.get("based_on")
            )

            if totals_dict.get("_bold"):
                totals_dict["_bold"] = 0

            seen.add(service_advisor)
            yield totals_dict

    # Service advisors with no sales in the period still get a row, left blank
    # with no incentive calculated.
    for service_advisor in sorted(set(allowed_service_advisors) - seen):
        yield frappe._dict(
            allowed_service_advisors[service_advisor],
            service_advisor=service_advisor,
            disable_party_name_formatter=1,
        )
