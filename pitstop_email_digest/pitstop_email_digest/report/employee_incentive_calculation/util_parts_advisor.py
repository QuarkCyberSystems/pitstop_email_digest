"""Parts Advisor incentive calculation.

Driven by the Workshop Turnover report grouped by branch: a Parts Advisor is
scored on the parts side of the branch they sit in, so every advisor of a branch
carries that branch's parts figures.

Unlike the other designations this one has no single `weightages` map — each
advisor carries their own, in `TEMPLATE_DATA["employee_weightages"]` — and no
ladders yet, so the rows are built but nothing is scored: `calculated_incentive`
stays 0 until the ladders land.
"""

import frappe
from frappe.utils import flt

from .helper_parts_advisor import TEMPLATE_DATA
from .util_employee_incentive_calculation import fetch_month_targets

TEMPLATE_DATA = TEMPLATE_DATA

REPORT_FILTERS = {
    "group_by_1": "Group by Branch",
    "include_tasks": 1,
}

SOURCE_REPORT = "turnover"

# The branch figures copied onto each of the branch's advisors. Taken by name so
# the group's internal keys (`_bold`, `_group_idx`, `reference`, ...) stay out of
# the row, and so the row is a copy: several advisors share one branch and must
# not share one totals dict.
BRANCH_TOTAL_FIELDS = (
    "part_sales_amount",
    "material_sales_amount",
    "parts_cogs",
    "parts_gross_profit",
    "parts_profit_margin",
)


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
        {
            "label": frappe._("Branch"),
            "fieldname": "branch",
            "fieldtype": "Link",
            "options": "Branch",
            "width": 150,
        },
        {
            "label": frappe._("Parts Sales"),
            "fieldname": "part_sales_amount",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": frappe._("Parts Sales Target"),
            "fieldname": "pa_target_revenue",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "label": frappe._("Parts Sales %"),
            "fieldname": "parts_sales_percentage",
            "fieldtype": "Percent",
            "width": 120,
        },
        {
            "label": frappe._("Parts Gross Profit"),
            "fieldname": "parts_gross_profit",
            "fieldtype": "Currency",
            "width": 130,
        },
        {
            "label": frappe._("Parts GP %"),
            "fieldname": "parts_profit_margin",
            "fieldtype": "Percent",
            "width": 120,
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
            fields=["name", "employee_name", "branch"],
            order_by="branch asc, employee_name asc",
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
        "targets": fetch_targets(filters),
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


def index_branch_totals(source_data):
    """Each branch's turnover totals, keyed by branch.

    The source report is grouped by branch, so every group under the top level
    is one branch and its `totals` carry that branch's figures.
    """
    branch_totals = {}

    for each_turnover_data in source_data:
        if not each_turnover_data.get("rows"):
            continue

        for each_group_data in each_turnover_data.rows:
            totals = each_group_data.get("totals") or {}
            branch = totals.get("branch") or each_group_data.get("group_value")

            if branch:
                branch_totals[branch] = totals

    return branch_totals


def process_rows(filters, source_data, qc_task_types, lookups):
    allowed_parts_advisors = lookups.get("allowed_parts_advisors") or []
    targets = lookups.get("targets") or {}
    branch_totals = index_branch_totals(source_data)

    for each_parts_advisor in allowed_parts_advisors:
        parts_advisor = each_parts_advisor.get("name")
        branch = each_parts_advisor.get("branch")

        totals_dict = frappe._dict(
            {
                "parts_advisor": parts_advisor,
                "parts_advisor_name": each_parts_advisor.get("employee_name"),
                "branch": branch,
            }
        )

        branch_row = branch_totals.get(branch) or {}
        for field in BRANCH_TOTAL_FIELDS:
            totals_dict[field] = flt(branch_row.get(field))

        target = flt(targets.get(parts_advisor))
        totals_dict["pa_target_revenue"] = target
        totals_dict["parts_sales_percentage"] = (
            flt((totals_dict["part_sales_amount"] / target) * 100.0, 3)
            if target
            else 0.0
        )

        # Nothing is scored yet: TEMPLATE_DATA carries the per employee
        # weightages but none of the ladders the parts sales, parts GP, TAT,
        # stock turn and physical inventory results would be read off, and TAT,
        # stock turn and physical inventory have no source at all.
        totals_dict["calculated_incentive"] = 0.0

        yield totals_dict
