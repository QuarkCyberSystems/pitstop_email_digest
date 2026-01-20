# Vehicle WIP Aging Report  – grand total, grouped by workshop, excludes "Completed"
# Copyright (c) 2025, Quark Cyber Systems
# License: GPL-3.0

import frappe
from frappe import _
from frappe.utils import getdate


# ────────────────────────────────────────────────
def _label_to_field(label: str) -> str:
    """Convert a bucket label like '1-30' to a safe fieldname '1_30'."""
    return label.replace(">", "gt").replace("-", "_")


BUCKETS = [
    (1, 30, "1-30"),
    (31, 60, "30-60"),
    (61, 120, "60-120"),
    (121, 240, "120-240"),
    (241, 360, "240-360"),
    # (361, 99999, ">360"),   # uncomment to add a >360 bucket
]

NUMERIC_KEYS = {"total"} | {_label_to_field(lbl) for _, _, lbl in BUCKETS}


# ────────────────────────────────────────────────
def execute(filters=None):
    filters = frappe._dict(filters or {})
    filters.as_of = getdate(filters.get("as_of") or getdate())

    columns = _get_columns()
    raw = _get_raw_data(filters)
    data = _structure_rows(raw)

    return columns, data


# ────────────────────────────────────────────────
def _get_columns():
    cols = [
        {
            "label": _("Workshop"),
            "fieldname": "branch",
            "fieldtype": "Link",
            "options": "Vehicle Workshop",
            "width": 140,
        },
        {
            "label": _("Status"),
            "fieldname": "status_name",
            "fieldtype": "Data",
            "width": 220,
        },
        {"label": _("Total"), "fieldname": "total", "fieldtype": "Int", "width": 70},
    ]

    for start_day, end_day, label in BUCKETS:  # ← no '_' shadowing
        cols.append(
            {
                "label": label,
                "fieldname": _label_to_field(label),
                "fieldtype": "Int",
                "width": 70,
            }
        )
    return cols


# ────────────────────────────────────────────────
def _get_raw_data(filters):
    """Fetch one row per (workshop, status) with counts in each ageing bucket."""
    age_expr = "DATEDIFF(%(as_of)s, DATE(p.creation))"  # change to vehicle_received_date if required

    bucket_sql = ",\n       ".join(
        f"SUM(CASE WHEN {age_expr} BETWEEN {s} AND {e} THEN 1 ELSE 0 END)"
        f" AS `{_label_to_field(label)}`"
        for s, e, label in BUCKETS
    )

    # dynamic filter conditions
    conds = []
    if filters.get("vehicle_workshop"):
        conds.append("p.vehicle_workshop = %(vehicle_workshop)s")
    if filters.get("service_type"):
        conds.append("p.service_type = %(service_type)s")
    if filters.get("workshop_division"):
        conds.append("p.workshop_division = %(workshop_division)s")
    where_extra = f"AND {' AND '.join(conds)}" if conds else ""

    return frappe.db.sql(
        f"""
        SELECT
            p.vehicle_workshop  AS branch,
            p.project_status    AS status_name,
            COUNT(*)            AS total,
            {bucket_sql}
        FROM `tabProject` p
        WHERE
            p.status != 'Cancelled'
            AND p.project_status != 'Completed'      -- exclude fully completed ROs
            {where_extra}
        GROUP BY p.vehicle_workshop, p.project_status
        ORDER BY p.vehicle_workshop, p.project_status
        """,
        filters,
        as_dict=True,
    )


# ────────────────────────────────────────────────
def _structure_rows(raw_rows):
    """Return Grand Total row, then workshop totals + indented status rows."""
    grand = {"branch": _("Grand Total"), "status_name": "", "indent": 0}
    for key in NUMERIC_KEYS:
        grand[key] = 0

    output, current_ws, block = [], None, []

    def flush():
        nonlocal grand
        if not block:
            return
        # workshop total
        ws_total = _make_total_row(current_ws, block)
        output.append(ws_total)
        # detail lines
        for r in block:
            r["indent"] = 1
            r["branch"] = ""  # hide workshop name in detail rows
            output.append(r)
            # accumulate into grand total
            for k in NUMERIC_KEYS:
                grand[k] += r.get(k, 0) or 0

    for row in raw_rows:
        if row.branch != current_ws:
            flush()
            current_ws, block = row.branch, []
        block.append(row)

    flush()
    return [grand] + output


# ────────────────────────────────────────────────
def _make_total_row(branch, rows):
    row = {"branch": branch, "status_name": _("Total"), "indent": 0}
    for key in NUMERIC_KEYS:
        row[key] = sum(r.get(key, 0) or 0 for r in rows)
    return row
