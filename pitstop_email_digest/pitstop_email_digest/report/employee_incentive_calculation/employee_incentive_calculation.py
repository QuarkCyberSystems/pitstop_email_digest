# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from automotive.automotive.report.workshop_productivity.workshop_productivity import (
    WorkshopProductivityReport,
)
from frappe.utils.data import flt

INCENTIVE_FIELD_MAP = {
    "base_incentive": (0, 0),
    "below_85": (None, 85.0),
    "between_85_and_100": (85.0, 100.0),
    "between_100_and_115": (100.0, 115.0),
    "between_115_and_125": (115.0, 125.0),
    "above_125": (125.0, None),
}


def execute(filters=None):
    if filters.get("based_on") == "Technician":
        filters["group_by_1"] = "Group by Technician/Service Bay"
    elif filters.get("based_on") == "Team Lead":
        filters["group_by_1"] = "Group by Team Lead/Service Bay"

    produtivity_report = WorkshopProductivityReport(filters).run()
    columns = produtivity_report[0]
    columns = update_columns(filters, columns)
    data = produtivity_report[1]
    data = organize_the_group_data(data)
    filtered_data, efficiency_cap_counts = post_process(filters, data)
    return (
        columns,
        filtered_data,
        None,
        None,
        calculate_total_summary(data, efficiency_cap_counts),
    )


def update_columns(filters, columns):
    for each_column in columns:
        if each_column.get("fieldname") in [
            "mttr",
            "no_of_repair_orders",
            "per_utilization",
            "reference",
            "vehicle_workshop",
            "vehicle_workshop_division",
            "employee",
            "employee_name",
            "technician_workshop_division",
            "vehicle_service_bay",
            "vehicle_service_bay_title",
            "project",
            "task",
            "task_type",
            "subject",
            "team_lead",
            "team_lead_name",
        ]:
            each_column["hidden"] = 1

    employee_columns = []

    based_on = filters.get("based_on")

    columns_map = {
        "Technician": [
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
                "fieldname": "team_lead",
                "fieldtype": "Link",
                "options": "Employee",
                "width": 150,
            },
        ],
        "Team Lead": [
            {
                "label": "Team Lead",
                "fieldname": "team_lead",
                "fieldtype": "Link",
                "options": "Employee",
                "width": 150,
            },
            {
                "label": "Team Lead Name",
                "fieldname": "team_lead_name",
                "fieldtype": "Data",
                "width": 150,
            },
        ],
    }

    employee_columns = columns_map.get(based_on, [])

    columns[:0] = employee_columns

    incentive_columns = [
        {
            "label": format_label(field),
            "fieldname": field,
            "fieldtype": "Float",
            "width": 150,
        }
        for field in INCENTIVE_FIELD_MAP
    ]

    columns.extend(incentive_columns)

    columns.append(
        {
            "label": "Calculated Incentive",
            "fieldname": "calculated_incentive",
            "fieldtype": "Currency",
            "width": 150,
        }
    )
    return columns


def validate_efficiency_filter(filters, each_data):
    filter_type = filters.get("efficiency_filter")
    if not filter_type:
        return True

    if not filters.get(filter_type):
        return False

    efficiency = each_data.get("per_efficiency") or 0

    min_val, max_val = INCENTIVE_FIELD_MAP.get(filter_type, (None, None))

    if min_val is not None and efficiency < min_val:
        return False

    if max_val is not None and efficiency >= max_val:
        return False

    return True


def get_efficiency_cap(row_data):
    efficiency = row_data.get("per_efficiency") or 0
    for key, (min_val, max_val) in INCENTIVE_FIELD_MAP.items():
        if min_val is not None and efficiency < min_val:
            continue
        if max_val is not None and efficiency >= max_val:
            continue
        return key
    return None


def calculate_total_summary(data, efficiency_cap_counts):
    total_data_length = len(data) or 0.0

    total_data_list = [
        {
            "label": frappe._("Total Count"),
            "value": str(total_data_length),
            "indicator": "red",
            "datatype": "html",
        }
    ]

    if efficiency_cap_counts:
        # to make it in order added the INCENTIVE_FIELD_MAP keys
        for each_ince in INCENTIVE_FIELD_MAP:
            for each_key in efficiency_cap_counts:
                if each_ince == each_key:
                    percentage_calc = flt(
                        ((efficiency_cap_counts.get(each_key) or 0) / total_data_length)
                        * 100.0,
                        2,
                    )
                    total_data_list.append(
                        {
                            "label": format_label("efficiency_" + each_key),
                            "value": str(efficiency_cap_counts.get(each_key) or 0)
                            + "("
                            + str(percentage_calc)
                            + "%"
                            + ")",
                            "indicator": "red",
                            "datatype": "html",
                        }
                    )
    return total_data_list


def post_process(filters, data):
    filtered_data = []
    efficiency_cap_counts = {}
    for each_data in data:
        if not validate_efficiency_filter(filters, each_data):
            continue

        for ince_field in INCENTIVE_FIELD_MAP:
            if filters.get(ince_field):
                each_data[ince_field] = filters.get(ince_field)

        efficiency_cap = get_efficiency_cap(each_data)

        if efficiency_cap_counts.get(efficiency_cap):
            efficiency_cap_counts[efficiency_cap] += 1
        else:
            efficiency_cap_counts[efficiency_cap] = 1

        if efficiency_cap:
            calculated_incentive = compute_incentive(each_data, efficiency_cap)
            each_data["calculated_incentive"] = calculated_incentive

        filtered_data.append(each_data)

    return filtered_data, efficiency_cap_counts


def compute_incentive(data_row, incentive_field):
    get = data_row.get
    per_efficiency = min(get("per_efficiency") or 0.0, 125.0)
    base_incentive = get("base_incentive") or 0.0
    incentive_value = get(incentive_field) or 0.0
    return flt((per_efficiency * incentive_value * base_incentive) / 100.0, 2)


def format_label(fieldname):
    if fieldname == "base_incentive":
        return "Base Incentive"

    parts = fieldname.split("_")

    if parts[0] == "below":
        return f"Below {parts[1]}%"

    if parts[0] == "between":
        return f"Between {parts[1]} and {parts[3]}"

    return fieldname.replace("_", " ").title()


def organize_the_group_data(data):
    filter_data_list = []
    for each_data in data:
        for each_group_rows in each_data.rows:
            totals_dict = each_group_rows.totals or {}
            filter_data_list.append(totals_dict.copy())
    return filter_data_list
