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
    return frappe.db.sql(
        """
		select
			tse2.project as ro,
			tp.project_status as ro_status,
			tp.service_advisor,
			tp.branch,
			tse2.posting_date,
			sum(
				case
					when tse2.stock_entry_type = %(material_issue)s
						then abs(tsle.stock_value_difference)   -- make positive
					when tse2.stock_entry_type = %(material_receipt)s
						then -abs(tsle.stock_value_difference)  -- make negative
					else 0
				end
			) as total
		from `tabStock Ledger Entry` tsle
		join `tabStock Entry` tse2 on tsle.voucher_no = tse2.name
		join tabProject tp on tp.name = tse2.project
		where
			tse2.docstatus = 1
			and tse2.stock_entry_type in (%(material_issue)s, %(material_receipt)s)
			and tsle.posting_date >= coalesce(%(from_date)s, '1900-01-01')
			and tsle.posting_date <= coalesce(%(to_date)s, '2999-12-31')
			and (%(company)s is null or tsle.company = %(company)s)
			and (%(ro)s is null or tp.name = %(ro)s)
			and (%(branch)s is null or tp.branch = %(branch)s)
			and (%(exclude_ro_status)s is null or tp.project_status != %(exclude_ro_status)s)
			and (%(ro_status)s is null or tp.project_status = %(ro_status)s)
		group by
			tse2.project, tse2.posting_date
		""",
        get_filter_values(filters),
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


def get_filter_values(filters):
    """Bind every supported filter, passing NULL for the ones left blank."""
    filters = filters or {}

    values = {
        fieldname: filters.get(fieldname) or None
        for fieldname in ("company", "from_date", "to_date", "ro", "branch")
    }

    values["material_issue"] = "Material Issue"
    values["material_receipt"] = "Material Receipt"

    # "Not Completed RO" excludes completed orders; otherwise the hidden RO Status
    # filter selects one status. The two are never applied together.
    if filters.get("not_completed_ro_status"):
        values["exclude_ro_status"] = "Completed"
        values["ro_status"] = None
    else:
        values["exclude_ro_status"] = None
        values["ro_status"] = filters.get("ro_status") or None

    return values
