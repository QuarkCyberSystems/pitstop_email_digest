"""Technician incentive calculation.

Driven by the Workshop Productivity report grouped by technician/bay/equipment.
The technician earns purely on the shared sold hrs / efficiency / productivity
figures, so this module adds no fetches of its own.
"""

import frappe

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

REPORT_FILTERS = {
    "group_by_1": "Group by Technician/Bay/Equipment",
    "not_include_quality_controller": True,
}

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
    return {"technicians": fetch_technicians(filters)}


def fetch_technicians(filters):
    """Active technicians, excluding Quality Controllers."""
    employee_filters = {
        "is_technician": 1,
        "status": "Active",
        "designation": ["!=", "Quality Controller"],
    }
    for field in ("company", "branch"):
        if filters.get(field):
            employee_filters[field] = filters.get(field)
    if filters.get("employee"):
        employee_filters["name"] = filters.get("employee")

    technicians = frappe.get_all(
        "Employee",
        filters=employee_filters,
        fields=[
            "name as employee",
            "employee_name",
            "reports_to",
            "vehicle_workshop_division as technician_workshop_division",
        ],
        order_by="employee_name",
    )
    return {d.employee: d for d in technicians}


def process_rows(filters, source_data, qc_task_types, lookups):
    technicians = lookups.get("technicians") or {}
    seen = set()

    for totals_dict in iter_productivity_groups(filters, source_data, qc_task_types):
        # Productivity report also lists non-technicians who logged time on tasks
        employee = totals_dict.get("employee")
        if employee not in technicians:
            continue

        seen.add(employee)
        totals_dict["calculated_incentive"] = compute_incentive(
            totals_dict, filters.get("based_on")
        )
        yield totals_dict

    # Technicians with no timesheets/attendance in the period still get a row
    for employee, details in technicians.items():
        if employee not in seen:
            yield frappe._dict(details, disable_party_name_formatter=1)
