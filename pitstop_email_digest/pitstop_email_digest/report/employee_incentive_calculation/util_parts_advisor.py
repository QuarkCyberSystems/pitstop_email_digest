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
from .util_employee_incentive_calculation import (
    employee_weightage_amount,
    fetch_month_targets,
    get_employee_ladder_result,
    get_ladder_result,
)

TEMPLATE_DATA = TEMPLATE_DATA

REPORT_FILTERS = {
    "group_by_1": "Group by Branch",
    "group_by_2": "Group by Workshop Division",
    "group_by_3": "Group by Vehicle Brand",
    "totals_only": 1,
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
            "hidden": 1,
        },
        {
            "label": frappe._("Parts GP %"),
            "fieldname": "parts_profit_margin",
            "fieldtype": "Percent",
            "width": 120,
            "hidden": 0,
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


def compute_revenue_amount(filters, totals):
    totals["parts_sales_amt"] = 0.0

    revenue_percentage = totals.get("parts_sales_percentage")

    result = get_ladder_result(
        based_on=filters.get("based_on"),
        sold_hrs_percentage=revenue_percentage,
        ladder_field="parts_sales_ladder",
        top_cap=125.0,
    )

    if result:
        totals["parts_sales_amt"] = flt(
            employee_weightage_amount(
                filters, totals.get("parts_advisor"), "parts_sales"
            )
            * (result / 100.0),
            3,
        )


def compute_gp_amount(filters, totals):
    totals["parts_gp_amt"] = 0.0

    gp_percentage = totals.get("parts_profit_margin")

    result = get_employee_ladder_result(
        based_on=filters.get("based_on"),
        employee_id=totals.get("parts_advisor"),
        percentage=gp_percentage,
        ladder_field="parts_gp_ladder",
        top_cap=30.0,
    )

    if result:
        totals["parts_gp_amt"] = flt(
            employee_weightage_amount(filters, totals.get("parts_advisor"), "parts_gp")
            * (result / 100.0),
            3,
        )


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


def copy_totals(totals):
    """A copy of just the `BRANCH_TOTAL_FIELDS` of a group's totals."""
    return frappe._dict(
        {field: flt(totals.get(field)) for field in BRANCH_TOTAL_FIELDS}
    )


def add_totals(target, totals):
    """Add `totals` into `target`, recomputing the margin from the summed figures.

    `parts_profit_margin` is a ratio, so it is not summed: it is worked out again
    the way the turnover report does, GP over material sales.
    """
    for field in BRANCH_TOTAL_FIELDS:
        if field != "parts_profit_margin":
            target[field] = flt(target.get(field)) + flt(totals.get(field))

    target["parts_profit_margin"] = (
        target["parts_gross_profit"] / target["material_sales_amount"] * 100.0
        if target["material_sales_amount"]
        else 0.0
    )


def index_branch_totals(source_data):
    """Each branch's turnover totals, keyed by branch.

    The source report is grouped by branch > workshop division > vehicle brand,
    so every group under the top level is one branch, its `rows` are that
    branch's divisions and theirs are the brand totals within each division.

    Besides the branch figures, each branch carries:
      - `workshop_divisions`: the totals of each division, keyed by division,
        each with its own `vehicle_brands` (the brand totals within it)
      - `vehicle_brands`: the totals of each brand, keyed by brand, summed
        across the branch's divisions
    """
    branch_totals = {}

    for each_turnover_data in source_data:
        if not each_turnover_data.get("rows"):
            continue

        for each_group_data in each_turnover_data.rows:
            totals = each_group_data.get("totals") or {}
            branch = totals.get("branch") or each_group_data.get("group_value")

            if not branch:
                continue

            branch_row = copy_totals(totals)
            branch_row["workshop_divisions"] = {}
            branch_row["vehicle_brands"] = {}

            for each_division_data in each_group_data.get("rows") or []:
                division_totals = each_division_data.get("totals") or {}
                division = division_totals.get(
                    "vehicle_workshop_division"
                ) or each_division_data.get("group_value")

                division_row = None
                if division:
                    division_row = copy_totals(division_totals)
                    division_row["vehicle_brands"] = {}
                    branch_row["workshop_divisions"][division] = division_row

                for each_brand_data in each_division_data.get("rows") or []:
                    # With `totals_only` the last level is the totals rows
                    # themselves rather than groups wrapping them.
                    brand_totals = each_brand_data.get("totals") or each_brand_data
                    brand = brand_totals.get(
                        "applies_to_item_brand"
                    ) or each_brand_data.get("group_value")

                    if brand:
                        if division_row is not None:
                            add_totals(
                                division_row["vehicle_brands"].setdefault(
                                    brand, frappe._dict()
                                ),
                                brand_totals,
                            )
                        add_totals(
                            branch_row["vehicle_brands"].setdefault(
                                brand, frappe._dict()
                            ),
                            brand_totals,
                        )

            branch_totals[branch] = branch_row

    return branch_totals


def matches_filter(value, condition):
    """Whether `value` passes one employee filter condition.

    `condition` is either a plain value (equality) or an `[operator, value]`
    pair, with `=`, `!=`, `in` and `not in` understood.
    """
    if not isinstance(condition, (list, tuple)):
        return value == condition

    operator, expected = condition
    if operator == "=":
        return value == expected
    if operator == "!=":
        return value != expected
    if operator == "in":
        return value in expected
    if operator == "not in":
        return value not in expected

    frappe.throw(frappe._("Unsupported filter operator: {0}").format(operator))


def filter_branch_totals(branch_row, employee_filter):
    """The `BRANCH_TOTAL_FIELDS` of `branch_row`, narrowed to `employee_filter`.

    The filter may set `vehicle_workshop_division`, `applies_to_item_brand` or
    both. Divisions are picked first; within each, either the whole division is
    taken or, when a brand condition is set, only its matching brands.
    """
    division_condition = employee_filter.get("vehicle_workshop_division")
    brand_condition = employee_filter.get("applies_to_item_brand")

    filtered = frappe._dict({field: 0.0 for field in BRANCH_TOTAL_FIELDS})

    for division, division_row in (branch_row.get("workshop_divisions") or {}).items():
        if division_condition is not None and not matches_filter(
            division, division_condition
        ):
            continue

        if brand_condition is None:
            add_totals(filtered, division_row)
            continue

        for brand, brand_row in (division_row.get("vehicle_brands") or {}).items():
            if matches_filter(brand, brand_condition):
                add_totals(filtered, brand_row)

    return filtered


def process_rows(filters, source_data, qc_task_types, lookups):
    allowed_parts_advisors = lookups.get("allowed_parts_advisors") or []
    targets = lookups.get("targets") or {}
    branch_totals = index_branch_totals(source_data)
    # print(allowed_parts_advisors)
    # print(targets)
    # print(branch_totals)

    for each_parts_advisor in allowed_parts_advisors:
        parts_advisor = each_parts_advisor.get("name")
        branch = each_parts_advisor.get("branch")
        employee_filter = {}
        for each_weightage in TEMPLATE_DATA.get("employee_weightages"):
            if each_weightage.get("employee_id") == parts_advisor:
                employee_filter = each_weightage.get("filters")
                break
        else:
            continue
        totals_dict = frappe._dict(
            {
                "parts_advisor": parts_advisor,
                "parts_advisor_name": each_parts_advisor.get("employee_name"),
                "branch": branch,
            }
        )
        branch_row = branch_totals.get(branch) or {}
        if employee_filter:
            branch_row = filter_branch_totals(branch_row, employee_filter)

        for field in BRANCH_TOTAL_FIELDS:
            totals_dict[field] = flt(branch_row.get(field))

        target = flt(targets.get(parts_advisor))
        totals_dict["pa_target_revenue"] = target
        totals_dict["parts_sales_percentage"] = (
            flt((totals_dict["part_sales_amount"] / target) * 100.0, 3)
            if target
            else 0.0
        )

        compute_revenue_amount(filters, totals_dict)
        compute_gp_amount(filters, totals_dict)

        #     # Nothing is scored yet: TEMPLATE_DATA carries the per employee
        #     # weightages but none of the ladders the parts sales, parts GP, TAT,
        #     # stock turn and physical inventory results would be read off, and TAT,
        #     # stock turn and physical inventory have no source at all.
        totals_dict["calculated_incentive"] = 0.0

        yield totals_dict
