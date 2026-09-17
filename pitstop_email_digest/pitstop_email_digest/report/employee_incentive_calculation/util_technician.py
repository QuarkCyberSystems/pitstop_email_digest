"""Technician incentive calculation.

Driven by the Workshop Productivity report grouped by technician/bay/equipment.
The technician earns purely on the shared sold hrs / efficiency / productivity
figures, so this module adds no fetches of its own.
"""

from .util_employee_incentive_calculation import (
    compute_incentive,
    iter_productivity_groups,
)

TEMPLATE_DATA = {
    "weightages": {"sold_hrs": 50, "efficiency": 25, "productivity": 25},
    "sold_hrs_ladder": {
        80: 0,
        85: 80,
        90: 85,
        95: 90,
        100: 95,
        105: 100,
        115: 105,
        125: 115,
    },
    "efficiency_ladder": {
        90: 0,
        95: 90,
        100: 95,
        105: 100,
        110: 105,
        115: 110,
        120: 115,
        125: 120,
    },
    "productivity_ladder": {
        85: 0,
        90: 85,
        95: 90,
        100: 95,
        105: 100,
        110: 105,
        115: 110,
        125: 115,
    },
}

REPORT_FILTERS = {"group_by_1": "Group by Technician/Bay/Equipment"}

SOURCE_REPORT = "productivity"


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
            "label": "Team Lead",
            "fieldname": "reports_to",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150,
            "hidden": 1,
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
    ]


def prepare_lookups(filters):
    return {}


def process_rows(filters, source_data, qc_task_types, lookups):
    for totals_dict in iter_productivity_groups(filters, source_data, qc_task_types):
        totals_dict["calculated_incentive"] = compute_incentive(
            totals_dict, filters.get("based_on")
        )
        yield totals_dict
