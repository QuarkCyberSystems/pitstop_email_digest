import frappe

from .helper_parts_advisor import TEMPLATE_DATA
from .util_employee_incentive_calculation import fetch_month_targets

TEMPLATE_DATA = TEMPLATE_DATA

REPORT_FILTERS = {
    "group_by_1": "Group by Branch",
    "include_tasks": 1,
}

SOURCE_REPORT = "turnover"


def get_leading_columns():
    """Columns shown before the source report's own columns."""
    return [
        {
            "label": frappe._("Parts Advisor ID"),
            "fieldname": "parts_advisor",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150,
        },
        {
            "label": frappe._("Parts Advisor Name"),
            "fieldname": "parts_advisor_name",
            "fieldtype": "Data",
            "width": 150,
        },
    ]


def get_trailing_columns():
    """Columns shown after the source report's own columns."""
    return []


def fetch_parts_advisors(is_list=True):
    settings = frappe.get_cached_doc("Incentive Calculation Setttings")
    designations = [
        d.designation
        for d in (settings.parts_advisor_designation or [])
        if d.designation
    ]
    if not designations:
        return None

    if not is_list:
        return frappe.get_all(
            "Employee",
            filters={
                "status": "Active",
                "designation": ["in", designations],
            },
            fields=["name", "branch"],
        )

    return frappe.get_all(
        "Employee",
        filters={
            "status": "Active",
            "designation": ["in", designations],
        },
        pluck="name",
    )


def prepare_lookups(filters):
    return {
        "allowed_parts_advisors": fetch_parts_advisors(is_list=False),
    }


def fetch_targets(filters):
    settings = frappe.get_cached_doc("Incentive Calculation Setttings")
    designations = [
        d.designation
        for d in (settings.parts_advisor_designation or [])
        if d.designation
    ]
    if not designations:
        return None

    return fetch_month_targets(designations, filters.get("to_date"), "parts_advisor_id")


def process_rows(filters, source_data, qc_task_types, lookups):
    allowed_parts_advisors = lookups.get("allowed_parts_advisors") or []
    for each_parts_advisor in allowed_parts_advisors:
        for each_turnover_data in source_data:
            for each_group_data in each_turnover_data.rows:
                totals_dict = each_group_data.totals
                branch = totals_dict.get("branch")
                if each_parts_advisor.get("branch") == branch:
                    pass
    return {}
