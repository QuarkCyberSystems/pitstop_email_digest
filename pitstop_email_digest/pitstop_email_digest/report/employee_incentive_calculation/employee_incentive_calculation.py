# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

from automotive.automotive.report.workshop_productivity.workshop_productivity import (
    WorkshopProductivityReport,
)
from frappe.utils.data import flt

INCENTIVE_FIELDS = [
    "base_incentive",
    "below_85",
    "between_85_and_100",
    "between_100_and_115",
    "between_115_and_125",
]


def execute(filters=None):
    produtivity_report = WorkshopProductivityReport(filters).run()
    columns = produtivity_report[0]
    columns = update_columns(columns)
    data = produtivity_report[1]
    data = post_process(filters, data)
    return columns, data


def update_columns(columns):
    for each_column in columns:
        if each_column.get("fieldname") in [
            "mttr",
            "no_of_repair_orders",
            "per_utilization",
        ]:
            each_column["hidden"] = 1

    incentive_columns = [
        {
            "label": format_label(field),
            "fieldname": field,
            "fieldtype": "Float",
            "width": 150,
        }
        for field in INCENTIVE_FIELDS
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


def post_process(filters, data):
    for each_data in data:
        for field in INCENTIVE_FIELDS:
            if filters.get(field):
                each_data[field] = filters.get(field)
        if each_data.get("per_efficiency") < 85.0:
            calculated_incentive = compute_incentive(each_data, "below_85")
            each_data["calculated_incentive"] = calculated_incentive
        elif (
            each_data.get("per_efficiency") >= 85.0
            and each_data.get("per_efficiency") < 100.0
        ):
            calculated_incentive = compute_incentive(each_data, "between_85_and_100")
            each_data["calculated_incentive"] = calculated_incentive
        elif (
            each_data.get("per_efficiency") >= 100.0
            and each_data.get("per_efficiency") < 115.0
        ):
            calculated_incentive = compute_incentive(each_data, "between_100_and_115")
            each_data["calculated_incentive"] = calculated_incentive
        elif (
            each_data.get("per_efficiency") >= 115.0
            and each_data.get("per_efficiency") <= 125.0
        ):
            calculated_incentive = compute_incentive(each_data, "between_115_and_125")
            each_data["calculated_incentive"] = calculated_incentive

    return data


def compute_incentive(data_row, incentive_field):
    base_incentive = data_row.get("base_incentive")
    calculated_incentive = (
        (data_row.get("per_efficiency") if data_row.get("per_efficiency") else 0.0)
        * (data_row.get(incentive_field) if data_row.get(incentive_field) else 0.0)
        * (base_incentive if base_incentive else 0.0)
    ) / 100.0
    return flt(calculated_incentive, 2)


def format_label(fieldname):
    if fieldname == "base_incentive":
        return "Base Incentive"

    parts = fieldname.split("_")

    if parts[0] == "below":
        return f"Below {parts[1]}%"

    if parts[0] == "between":
        return f"Between {parts[1]} and {parts[3]}"

    return fieldname.replace("_", " ").title()
