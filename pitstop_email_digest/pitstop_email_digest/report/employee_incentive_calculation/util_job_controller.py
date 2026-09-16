"""Job Controller incentive calculation.

Driven by the Workshop Productivity report grouped by job controller, and
scored on idle time, productivity, WIP ageing and key-to-key duration.
"""

import frappe
from frappe.utils import flt, getdate

from pitstop_email_digest.pitstop_email_digest.report.key_to_key_report.key_to_key_report import (
    VehicleKeyToKeyReport,
)

from .util_employee_incentive_calculation import (
    apply_wip_ageing,
    compute_incentive,
    get_rate_ladder_result,
    iter_productivity_groups,
    weightage_amount,
)

TEMPLATE_DATA = {
    "weightages": {
        "idle_time": 40,
        "productivity": 30,
        "wip_ageing": 20,
        "key_to_key": 10,
    },
    # Lower idle time is better. Each key is the inclusive lower bound of
    # the band, the value is the multiplier applied to the idle time
    # weightage. 0.0 covers everything below 12% (the best band).
    "idle_time_ladder": {
        0.0: 125.0,
        12.0: 120.0,
        12.75: 115.0,
        13.5: 110.0,
        14.25: 105.0,
        14.5: 100.0,
        15.0: 95.0,
        15.75: 90.0,
        16.5: 85.0,
        17.25: 80.0,
        18.0: 0.0,
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
    "wip_ageing_ladder": {44.9: 100.0, 45.0: 0.0},
    "key_to_key_mechanical_ladder": {1.9: 100.0, 2.0: 0.0},
    "key_to_key_bodyshop_ladder": {10.9: 100.0, 11.0: 0.0},
}

REPORT_FILTERS = {
    "group_by_1": "Group by Job Controller",
    "include_tasks": 1,
}

SOURCE_REPORT = "productivity"


def get_leading_columns():
    """Columns shown before the source report's own columns."""
    return [
        {
            "label": frappe._("Controller"),
            "fieldname": "job_controller",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150,
        },
        {
            "label": frappe._("Controller Name"),
            "fieldname": "job_controller_name",
            "fieldtype": "Data",
            "width": 150,
        },
    ]


def get_trailing_columns():
    """Columns shown after the source report's own columns."""
    return [
        {
            "label": "Idle %",
            "fieldname": "total_idle_percentage",
            "fieldtype": "Percentage",
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
        {
            "label": "K2K Bodyshop Avg. Age",
            "fieldname": "key_to_key_duration_bodyshop",
            "fieldtype": "Int",
            "width": 100,
        },
        {
            "label": "K2K Mechanical Avg. Age",
            "fieldname": "key_to_key_duration_mechanical",
            "fieldtype": "Int",
            "width": 100,
        },
    ]


def fetch_wip_age(filters):
    as_of = getdate(filters.get("to_date") or getdate())

    return frappe.db.sql(
        """
		select
			p.job_controller,
			count(p.name) as ro_count,
			round(avg(datediff(%(as_of)s, date(p.project_date))), 2) as average_wip_age
		from
			`tabProject` p
		where
			p.status != 'Cancelled'
			and p.project_status != 'Completed'
			and p.job_controller is not null
			and p.job_controller != ''
			and p.project_date <= %(as_of)s
		group by
			p.job_controller;
		""",
        {"as_of": as_of},
        as_dict=True,
    )


def fetch_key_to_key(filters, workshop_division):
    filters["workshop_division"] = workshop_division
    key_to_key_report = VehicleKeyToKeyReport(filters).run()
    return key_to_key_report[1]


def prepare_lookups(filters):
    return {
        "wip_average_age": fetch_wip_age(filters) or [],
        "key_to_key_mechanical": fetch_key_to_key(filters, "Mechanical"),
        "key_to_key_bodyshop": fetch_key_to_key(filters, "Body Shop"),
    }


def compute_idle_amount(filters, totals):
    result = get_rate_ladder_result(
        based_on=filters.get("based_on"),
        percentage=totals.get("total_idle_percentage"),
        ladder_field="idle_time_ladder",
        top_cap=10.0,
    )
    if result:
        totals["idle_time_amt"] = flt(
            weightage_amount(filters, "idle_time") * (result / 100.0), 3
        )
    else:
        totals["idle_time_amt"] = 0


def compute_key_to_key_amount(filters, totals):
    totals["key_to_key_amt"] = 0.0

    bodyshop_result = get_rate_ladder_result(
        based_on=filters.get("based_on"),
        percentage=totals.get("key_to_key_duration_bodyshop"),
        ladder_field="key_to_key_bodyshop_ladder",
        top_cap=10.0,
    )
    if bodyshop_result:
        totals["key_to_key_amt"] = flt(
            weightage_amount(filters, "key_to_key") * (bodyshop_result / 100.0), 3
        )
        return

    mechanical_result = get_rate_ladder_result(
        based_on=filters.get("based_on"),
        percentage=totals.get("key_to_key_duration_mechanical"),
        ladder_field="key_to_key_mechanical_ladder",
        top_cap=10.0,
    )
    if mechanical_result:
        totals["key_to_key_amt"] = flt(
            weightage_amount(filters, "key_to_key") * (mechanical_result / 100.0),
            3,
        )


def compute_idle_percentage(totals):
    totals["total_idle_percentage"] = flt(
        (
            flt(
                flt(totals.get("available_hours"))
                - flt(totals.get("actual_time"))
                - flt(totals.get("out_of_shift_hours"))
            )
            / flt(totals.get("available_hours"))
        )
        * 100.0,
        3,
    )


def average_key_to_key_age(key_to_key_rows, job_controller):
    """Average key-to-key age across the rows belonging to one job controller."""
    total_age = 0
    matched_rows = 0
    for each_key_to_key in key_to_key_rows:
        if each_key_to_key.get("job_controller") == job_controller:
            total_age += (
                int(each_key_to_key.get("age")) if each_key_to_key.get("age") else 0
            )
            matched_rows += 1

    return int(total_age / matched_rows) if matched_rows else 0


def process_rows(filters, source_data, qc_task_types, lookups):
    wip_average_age = lookups.get("wip_average_age") or []
    key_to_key_bodyshop = lookups.get("key_to_key_bodyshop") or []
    key_to_key_mechanical = lookups.get("key_to_key_mechanical") or []

    for totals_dict in iter_productivity_groups(filters, source_data, qc_task_types):
        job_controller = totals_dict.get("job_controller")
        if not job_controller:
            continue

        compute_idle_percentage(totals_dict)
        compute_idle_amount(filters, totals_dict)

        apply_wip_ageing(filters, totals_dict, wip_average_age, "job_controller")

        totals_dict["key_to_key_duration_bodyshop"] = average_key_to_key_age(
            key_to_key_bodyshop, job_controller
        )
        totals_dict["key_to_key_duration_mechanical"] = average_key_to_key_age(
            key_to_key_mechanical, job_controller
        )

        compute_key_to_key_amount(filters, totals_dict)

        totals_dict["calculated_incentive"] = compute_incentive(
            totals_dict, filters.get("based_on")
        )
        yield totals_dict
