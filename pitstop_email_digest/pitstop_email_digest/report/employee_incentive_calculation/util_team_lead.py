"""Team Lead incentive calculation.

Driven by the Workshop Productivity report grouped by reporting authority, with
customer feedback averaged across the repair orders of the reportees.
"""

import frappe

from .util_employee_incentive_calculation import (
    apply_customer_feedback,
    compute_incentive,
    iter_productivity_groups,
)

TEMPLATE_DATA = {
    "weightages": {
        "efficiency": 30,
        "proficiency": 30,
        "qc_ro": 20,
        "customer_feedback": 20,
    },
    "efficiency_ladder": {
        85: 0,
        90: 85,
        95: 90,
        100: 95,
        105: 100,
        110: 105,
        115: 110,
        125: 115,
    },
    "proficiency_ladder": {
        85: 0,
        90: 85,
        95: 90,
        100: 95,
        105: 100,
        110: 105,
        115: 110,
        125: 115,
    },
    "qc_ro_ladder": {9.9: 0, 10: 100.0},
    "cfb_rate_ladder": {4.5: 0, 4.6: 100.0},
}

REPORT_FILTERS = {
    "group_by_1": "Group by Reporting Authority",
    "include_tasks": 1,
}

SOURCE_REPORT = "productivity"


def get_team_leader_designations():
    settings = frappe.get_cached_doc("Incentive Calculation Setttings")
    return [
        d.designation for d in (settings.team_lead_designation or []) if d.designation
    ]


def get_leading_columns():
    """Columns shown before the source report's own columns."""
    return [
        {
            "label": "Employee ID",
            "fieldname": "reports_to",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150,
        },
        {
            "label": "Employee Name",
            "fieldname": "reports_to_name",
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
            "label": "Rating Value",
            "fieldname": "customer_overall_rating_value",
            "fieldtype": "Float",
            "width": 150,
            "hidden": 1,
        },
        {
            "label": "RO Count (CFB)",
            "fieldname": "ro_count_cfb",
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "label": "QC RO Count",
            "fieldname": "total_qc_ro_count",
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "label": "Non QC RO Count",
            "fieldname": "total_ro_count_non_qc",
            "fieldtype": "Int",
            "width": 150,
        },
    ]


def get_trailing_columns():
    """Columns shown after the source report's own columns."""
    return [
        {
            "label": "Sold Hrs. %",
            "fieldname": "sold_hrs_percentage",
            "fieldtype": "Float",
            "width": 100,
        },
        {
            "label": "QC RO %",
            "fieldname": "total_qc_ro_percentage",
            "fieldtype": "Float",
            "width": 100,
        },
    ]


def fetch_feedback(filters):
    condition_dict = {
        "from_dt": filters.get("from_date"),
        "to_dt": filters.get("to_date"),
    }

    return frappe.db.sql(
        """
		select
			cbf_task_employee.reports_to,
			cbf_task_employee.reports_to_name,
			count(distinct cbf_task_employee.project) as ro_count,
			round(avg(cbf_task_employee.overall_satisfaction_rating), 2) as avg_rating
		from (
			select distinct
				tt3.reports_to,
				tt3.reports_to_name,
				tt3.project,
				tcf.overall_satisfaction_rating
			from
				`tabTimesheet Detail` ttd
			join
				tabTimesheet tt
			on
				tt.name = ttd.parent
			join
				tabTask tt3
			on
				tt3.name = ttd.task
			join
				`tabCustomer Feedback` tcf
			on
				tt3.project = tcf.project
			where
				tcf.status = 'Completed'
				and tt3.reports_to != ""
				and tt.docstatus < 2
				and tt3.reports_to is not null
				and %(from_dt)s <= ttd.to_time
				and %(to_dt)s >= ttd.from_time
		) cbf_task_employee
		group by
			cbf_task_employee.reports_to;
	""",
        condition_dict,
        as_dict=True,
    )


def prepare_lookups(filters):
    feedback = fetch_feedback(filters) or []
    designations = get_team_leader_designations()
    team_leaders = {}
    if designations:
        employee_filters = {"designation": ["in", designations], "status": "Active"}
        if filters.get("company"):
            employee_filters["company"] = filters.get("company")
        team_leaders = {
            d.name: d.employee_name
            for d in frappe.get_all(
                "Employee",
                filters=employee_filters,
                fields=["name", "employee_name"],
                order_by="employee_name",
            )
        }
    return {
        "feedback_map": {d.get("reports_to"): d for d in feedback},
        "team_leaders": team_leaders,
    }


def process_rows(filters, source_data, qc_task_types, lookups):
    feedback_map = lookups.get("feedback_map") or {}
    team_leaders = lookups.get("team_leaders") or {}
    seen = set()
    numeric_fields = set()

    for totals_dict in iter_productivity_groups(filters, source_data, qc_task_types):
        reports_to = totals_dict.get("reports_to")
        if not reports_to or reports_to not in team_leaders:
            continue

        apply_customer_feedback(filters, totals_dict, feedback_map.get(reports_to))

        totals_dict["calculated_incentive"] = compute_incentive(
            totals_dict, filters.get("based_on")
        )
        seen.add(reports_to)
        numeric_fields.update(
            key
            for key, value in totals_dict.items()
            if isinstance(value, (int, float)) and not key.startswith("_")
        )
        yield totals_dict

    # Team leaders with no tasks in the period still get a row, with zeros.
    for reports_to, reports_to_name in team_leaders.items():
        if reports_to in seen:
            continue
        yield get_empty_row(reports_to, reports_to_name, numeric_fields)


def get_empty_row(reports_to, reports_to_name, numeric_fields):
    row = frappe._dict.fromkeys(numeric_fields, 0)
    row.update(
        {
            "reports_to": reports_to,
            "reports_to_name": reports_to_name,
            "customer_overall_rating": 0,
            "customer_overall_rating_value": 0,
            "ro_count_cfb": 0,
            "total_qc_ro_count": 0,
            "total_ro_count_non_qc": 0,
            "sold_hrs_percentage": 0,
            "total_qc_ro_percentage": 0,
        }
    )
    row.update({field + "_amt": 0 for field in TEMPLATE_DATA["weightages"]})
    row["calculated_incentive"] = 0
    return row
