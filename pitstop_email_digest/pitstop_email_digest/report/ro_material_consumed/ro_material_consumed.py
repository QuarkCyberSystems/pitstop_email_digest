# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, today


def execute(filters=None):
    if filters.get("ageing_ranges"):
        filters["ageing_ranges"] = validate_age_ranges(filters)

    columns = get_columns(filters)
    data = get_base_data(filters)
    data = apply_dynamic_ageing(data, filters)
    return columns, data


def get_columns(filters):
    columns = [
        {
            "label": frappe._("Repair Order"),
            "fieldname": "ro",
            "options": "Project",
            "fieldtype": "Link",
            "width": 200,
        },
        {
            "label": frappe._("Repair Order Status"),
            "fieldname": "ro_status",
            "fieldtype": "Data",
            "width": 200,
        },
        {
            "label": frappe._("Service Advisor"),
            "fieldtype": "Link",
            "options": "Sales Person",
            "fieldname": "service_advisor",
            "width": 150,
        },
        {
            "label": frappe._("Branch"),
            "fieldname": "branch",
            "fieldtype": "Link",
            "options": "Branch",
            "width": 100,
        },
    ]

    buckets = get_ageing_ranges(filters)
    for b in buckets:
        start, end = b

        if end is None:
            label = f"{start} Above"
            fieldname = f"{start}_above"
        else:
            label = f"{start} - {end} Days"
            fieldname = f"{start}_{end}"

        columns.append(
            {
                "label": label,
                "fieldname": fieldname,
                "fieldtype": "Currency",
                "width": 100,
            }
        )

    columns.append(
        {
            "label": "Total",
            "fieldname": "total",
            "fieldtype": "Currency",
            "width": 100,
        }
    )

    return columns


def apply_dynamic_ageing(data, filters):
    buckets = get_ageing_ranges(filters)
    today_date = getdate(today())

    result = {}

    for row in data:
        key = row.ro

        if key not in result:
            result[key] = {
                "ro": row.ro,
                "ro_status": row.ro_status,
                "service_advisor": row.service_advisor,
                "branch": row.branch,
                "total": 0,
            }

            # initialize dynamic columns
            for b in buckets:
                start, end = b
                if end is None:
                    label = f"{start}_above"
                else:
                    label = f"{start}_{end}"
                result[key][label] = 0

        age_days = (today_date - getdate(row.posting_date)).days
        total = row.total or 0

        result[key]["total"] += total

        # assign to bucket
        for b in buckets:
            start, end = b
            if end is None:
                if age_days >= start:
                    label = f"{start}_above"
                    result[key][label] += total
                    break
            else:
                if start <= age_days <= end:
                    label = f"{start}_{end}"
                    result[key][label] += total
                    break

    return list(result.values())


def get_base_data(filters):
    condition_dict, condition_values = get_condition(filters)
    return frappe.db.sql(
        f"""
        select
            tse2.project as ro,
            tp.project_status as ro_status,
            tp.service_advisor,
            tp.branch,
            tse2.posting_date,
            sum(
                case
                    when tse2.stock_entry_type = "Material Issue"
                        then abs(tsle.stock_value_difference)   -- make positive
                    when tse2.stock_entry_type = "Material Receipt"
                        then -abs(tsle.stock_value_difference)  -- make negative
                    else 0
                end
            ) as total
        from `tabStock Ledger Entry` tsle
        join `tabStock Entry` tse2 on tsle.voucher_no = tse2.name
        join tabProject tp on tp.name = tse2.project
        where
            tse2.docstatus = 1
            and tse2.stock_entry_type in ("Material Issue", "Material Receipt")
            {condition_values}
        group by
            tse2.project, tse2.posting_date
        """,
        condition_dict,
        as_dict=True,
    )


def get_ageing_ranges(filters):
    ranges = (
        [int(x) for x in filters.get("ageing_ranges")]
        if filters.get("ageing_ranges")
        else []
    )
    ranges.sort()
    buckets = []
    prev = 0
    for r in ranges:
        buckets.append((prev, r))
        prev = r + 1
    buckets.append((prev, None))
    return buckets


def validate_age_ranges(filters):
    age_ranges = filters.get("ageing_ranges")

    if isinstance(age_ranges, str):
        parts = age_ranges.split(",")
    elif isinstance(age_ranges, list):
        parts = age_ranges
    else:
        frappe.throw("Invalid format for Ageing ranges")

    cleaned = []
    for p in parts:
        try:
            val = int(p)
        except Exception:
            frappe.throw(f"Invalid ageing range value: {p}")

        if val <= 0:
            frappe.throw(f"Ageing range must be greater than 0: {val}")

        cleaned.append(val)

    # remove duplicates + sort
    cleaned = sorted(set(cleaned))
    if len(cleaned) < 1:
        frappe.throw("At least one ageing range is required")

    return cleaned


def get_condition(filters):
    condition_values_dict = {}
    condition = ""
    if filters.get("company"):
        condition += "and tsle.company = %(company)s"
        condition_values_dict["company"] = filters.get("company")
    if filters.get("from_date"):
        condition += "and tsle.posting_date >= %(from_date)s"
        condition_values_dict["from_date"] = filters.get("from_date")
    if filters.get("to_date"):
        condition += "and tsle.posting_date <= %(to_date)s"
        condition_values_dict["to_date"] = filters.get("to_date")
    if filters.get("to_date"):
        condition += "and tsle.posting_date <= %(to_date)s"
        condition_values_dict["to_date"] = filters.get("to_date")
    if filters.get("ro_status"):
        if filters.get("ro_status") == "Completed":
            condition += "and tp.project_status = %(ro_status)s"
        else:
            condition += "and tp.project_status != %(ro_status)s"
        condition_values_dict["ro_status"] = "Completed"
    if filters.get("ro"):
        condition += "and tp.name = %(ro)s"
        condition_values_dict["ro"] = filters.get("ro")
    if filters.get("branch"):
        condition += "and tp.branch = %(branch)s"
        condition_values_dict["branch"] = filters.get("branch")
    return condition_values_dict, condition
