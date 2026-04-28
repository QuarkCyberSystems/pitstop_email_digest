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
    # filters["reporting_manager"] = 28864
    if filters.get("based_on") == "Technician":
        filters["group_by_1"] = "Group by Technician/Service Bay"
    elif filters.get("based_on") == "Reporting Authority":
        filters["group_by_1"] = "Group by Reporting Authority"
        filters["include_tasks"] = 1

    produtivity_report = WorkshopProductivityReport(filters).run()
    columns = produtivity_report[0]
    columns = update_columns(filters, columns)
    data = produtivity_report[1]
    generator = process_rows(filters, data)

    efficiency_cap_counts = {}
    filtered_data = []
    total_data_length = 0
    total_filtered_data_length = 0
    for row in generator:
        total_data_length += 1
        if "_summary" in row:
            efficiency_cap_counts = row["_summary"]
            continue
        total_filtered_data_length += 1
        filtered_data.append(row)

    return (
        columns,
        filtered_data,
        None,
        None,
        calculate_total_summary(
            total_filtered_data_length,
            efficiency_cap_counts,
            total_filtered_data_length,
            filters,
        ),
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
            "reports_to",
            "reports_to_name",
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
                "label": "Reporting Manger",
                "fieldname": "reports_to",
                "fieldtype": "Link",
                "options": "Employee",
                "width": 150,
            },
        ],
        "Reporting Authority": [
            {
                "label": "Reporting Manger",
                "fieldname": "reports_to",
                "fieldtype": "Link",
                "options": "Employee",
                "width": 150,
            },
            {
                "label": "Reporting Manger Name",
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


def fetch_avg_customer_feed_back_overall(filters):
    condition_dict = {
        "from_dt": filters.get("from_date"),
        "to_dt": filters.get("to_date"),
    }

    condition = "and %(from_dt)s <= ttd.to_time and %(to_dt)s >= ttd.from_time"

    return frappe.db.sql(
        f"""
        select
            cbf_task_employee.reports_to,
            cbf_task_employee.reports_to_name,
            count(distinct cbf_task_employee.project) as ro_count,
            round(avg(cbf_task_employee.overall_satisfaction_rating), 2) as avg_rating
        from (
            select distinct
                te.reports_to,
                te.reports_to_name,
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
            join
                tabEmployee te
            on
            	te.name = tt3.assigned_to
            where
                tcf.status = 'Completed'
                and te.reports_to != ""
                and tt.docstatus < 2
                and te.reports_to is not null {condition}
        ) cbf_task_employee
        group by
            cbf_task_employee.reports_to;
    """,
        condition_dict,
        as_dict=True,
    )


def process_rows(filters, data):
    qc_task_types = set(
        frappe.get_all("Task Type", filters={"name": ["like", "%QC%"]}, pluck="name")
    )

    if filters.get("based_on") == "Reporting Authority":
        customer_feed_back = fetch_avg_customer_feed_back_overall(filters) or []
        feedback_map = {d.get("reports_to"): d for d in customer_feed_back}

    efficiency_cap_counts = {}

    for each_data in data:
        for each_group_rows in each_data.rows:
            totals_dict = each_group_rows.totals or {}

            ro_set, qc_ro_set = set(), set()

            for row in each_group_rows.rows or []:
                if row.get("task_type") in qc_task_types:
                    qc_ro_set.add(row.get("project"))
                else:
                    ro_set.add(row.get("project"))

            totals_dict["total_ro_count_non_qc"] = len(ro_set)
            totals_dict["total_qc_ro_count"] = len(qc_ro_set)

            if totals_dict.get("_bold"):
                totals_dict["_bold"] = 0

            if filters.get("based_on") == "Reporting Authority":
                reports_to = totals_dict.get("reports_to")
                if reports_to and reports_to in feedback_map:
                    cfb = feedback_map[reports_to]

                    if cfb.get("avg_rating"):
                        rating = flt(cfb.get("avg_rating"), 2)
                        totals_dict["customer_overall_rating"] = rating
                        totals_dict["customer_overall_rating_value"] = rating
                        totals_dict["ro_count_cfb"] = cfb.get("ro_count")

            # filtering
            if filters.get("based_on") == "Reporting Authority":
                if not totals_dict.get("reports_to"):
                    continue

            if not validate_efficiency_filter(filters, totals_dict):
                continue

            for field in INCENTIVE_FIELD_MAP:
                if filters.get(field):
                    totals_dict[field] = filters.get(field)

            efficiency_cap = get_efficiency_cap(totals_dict)
            efficiency_cap_counts[efficiency_cap] = (
                efficiency_cap_counts.get(efficiency_cap, 0) + 1
            )

            if efficiency_cap:
                totals_dict["calculated_incentive"] = compute_incentive(
                    totals_dict, efficiency_cap
                )

            yield totals_dict

    # return counts separately if needed
    yield {"_summary": efficiency_cap_counts}


def calculate_total_summary(
    total_data_length, efficiency_cap_counts, total_filtered_data_length, filters
):
    if filters.get("based_on") == "Team Lead":
        total_data_length = total_data_length or 0.0
    else:
        total_data_length = total_filtered_data_length or 0.0

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
