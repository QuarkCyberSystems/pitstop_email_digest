"""Quality Controller incentive calculation.

Built directly from the QC technicians' tasks rather than from a source report,
and scored on invoiced QC ROs, comeback ROs and customer feedback.
"""

import frappe
from frappe.utils import flt

from .util_employee_incentive_calculation import (
    apply_customer_feedback,
    compute_incentive,
    get_rate_ladder_result,
    weightage_amount,
)

TEMPLATE_DATA = {
    "weightages": {"qc_ro": 40, "come_back_ro": 40, "customer_feedback": 20},
    "qc_ro_ladder": {9.9: 0, 10: 100.0},
    "come_back_ro_ladder": {0.9: 100.0, 1.0: 0.0},
    "cfb_rate_ladder": {4.5: 0, 4.6: 100.0},
}

REPORT_FILTERS = {
    "group_by_1": "Group by Technician/Bay/Equipment",
    "include_tasks": 1,
}

SOURCE_REPORT = None


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
            "label": "Total RO Count",
            "fieldname": "total_ro_count",
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "label": "Avg. CFB",
            "fieldname": "customer_overall_rating",
            "fieldtype": "Rating",
            "width": 200,
        },
        {
            "label": "QC RO Count",
            "fieldname": "total_qc_ro_count",
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "label": "Invoiced QC RO Count",
            "fieldname": "total_qc_invoice_ro_count",
            "fieldtype": "Int",
            "width": 120,
        },
        {
            "label": "Non QC RO Count",
            "fieldname": "total_ro_count_non_qc",
            "fieldtype": "Int",
            "width": 150,
        },
        {
            "label": "Comeback RO Count",
            "fieldname": "total_comeback_ro_count",
            "fieldtype": "Int",
            "width": 150,
        },
    ]


def get_trailing_columns():
    """Columns shown after the source report's own columns."""
    return []


def fetch_feedback(filters):
    return frappe.db.sql(
        """
		SELECT
			cbf_task_employee.assigned_to,
			cbf_task_employee.assigned_to_name,
			COUNT(DISTINCT cbf_task_employee.project) AS ro_count,
			ROUND(
				AVG(cbf_task_employee.overall_satisfaction_rating),
				2
			) AS avg_rating
		FROM (
			select distinct
				tt3.assigned_to,
				tt3.assigned_to_name,
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
				tabEmployee te
			on
				te.name = tt3.assigned_to
			join
				tabProject tp
			on
				tp.name = tt3.project
			join
				`tabCustomer Feedback` tcf
			on
				tt3.project = tcf.project
			WHERE te.status = 'Active'
				AND te.designation = 'Quality Controller'
				AND tp.project_date BETWEEN %(from_date)s AND %(to_date)s
		) AS cbf_task_employee
		GROUP BY
			cbf_task_employee.assigned_to,
			cbf_task_employee.assigned_to_name
		""",
        {
            "from_date": filters.get("from_date"),
            "to_date": filters.get("to_date"),
        },
        as_dict=True,
    )


def fetch_qc_technician():
    settings = frappe.get_cached_doc("Incentive Calculation Setttings")
    designations = [
        d.designation
        for d in (settings.quality_controller_designation or [])
        if d.designation
    ]
    if not designations:
        return None

    return frappe.get_all(
        "Employee",
        filters={
            "status": "Active",
            "is_technician": 1,
            "designation": ["in", designations],
        },
        pluck="name",
    )


def fetch_ro_task_qc(filters, qc_technicians):
    if not qc_technicians:
        return []

    rows = frappe.db.sql(
        """
		select
			p.name as project,
			p.billing_status,
			p.project_date,
			p.project_type as service_type,
			t.name as task,
			t.task_type,
			t.assigned_to as employee,
			t.assigned_to_name as employee_name
		from
			`tabProject` p
		join
			`tabTask` t
		on
			t.project = p.name
		where
			p.project_date between %(from_dt)s and %(to_dt)s
			and t.assigned_to in %(qc_technicians)s
		""",
        {
            "from_dt": filters.get("from_date"),
            "to_dt": filters.get("to_date"),
            "qc_technicians": tuple(qc_technicians),
        },
        as_dict=True,
    )

    groups = {}
    for row in rows:
        employee = row.get("employee")
        employee_name = row.get("employee_name")
        group = groups.setdefault(
            employee,
            frappe._dict(
                {
                    "employee": employee,
                    "totals": frappe._dict(
                        {"employee": employee, "employee_name": employee_name}
                    ),
                    "rows": [],
                }
            ),
        )
        group["rows"].append(row)

    return [frappe._dict({"rows": list(groups.values())})]


def prepare_lookups(filters):
    qc_technicians = fetch_qc_technician()
    feedback = fetch_feedback(filters) or []

    return {
        "qc_technicians": qc_technicians,
        "feedback_map": {d.get("assigned_to"): d for d in feedback},
        "ro_task_qc": fetch_ro_task_qc(filters, qc_technicians),
    }


def compute_qc_invoiced_ro_amount(filters, totals, invoiced_qc_ro_count, total_qc_ro):
    totals["qc_ro_amt"] = 0.0

    percentage_of_invoiced_qc_ro = (
        flt((invoiced_qc_ro_count / total_qc_ro) * 100, 3) if total_qc_ro else 0.0
    )

    result = get_rate_ladder_result(
        based_on=filters.get("based_on"),
        percentage=percentage_of_invoiced_qc_ro,
        ladder_field="qc_ro_ladder",
        top_cap=5.0,
    )

    if result:
        totals["qc_ro_amt"] = flt(
            weightage_amount(filters, "qc_ro") * (result / 100.0), 3
        )


def compute_comeback_ro_amount(filters, totals, total_comeback_ro, total_ro):
    totals["come_back_ro_amt"] = 0.0

    percentage_of_comeback_ro = (
        flt((total_comeback_ro / total_ro) * 100, 3) if total_ro else 0.0
    )

    result = get_rate_ladder_result(
        based_on=filters.get("based_on"),
        percentage=percentage_of_comeback_ro,
        ladder_field="come_back_ro_ladder",
        top_cap=5.0,
    )

    if result:
        totals["come_back_ro_amt"] = flt(
            weightage_amount(filters, "come_back_ro") * (result / 100.0), 3
        )


def process_rows(filters, source_data, qc_task_types, lookups):
    qc_technicians = lookups.get("qc_technicians")
    feedback_map = lookups.get("feedback_map") or {}
    data = lookups.get("ro_task_qc") or []

    for each_data in data:
        if not each_data.get("rows"):
            continue

        for each_group_rows in each_data.rows:
            totals_dict = each_group_rows.totals or {}

            if qc_technicians:
                assignee = each_group_rows.get("employee") or totals_dict.get(
                    "employee"
                )
                if assignee not in qc_technicians:
                    continue
                apply_customer_feedback(
                    filters, totals_dict, feedback_map.get(assignee)
                )

            all_ro = set()
            ro_with_qc = set()
            qc_invoice_ro = set()
            comeback_ro = set()

            for row in each_group_rows.rows or []:
                repair_order = row.get("project")
                if not repair_order:
                    continue

                all_ro.add(repair_order)

                if row.get("task_type") in qc_task_types:
                    ro_with_qc.add(repair_order)

                if row.get("task_type") in qc_task_types and row.get(
                    "billing_status"
                ) not in ("Not Applicable", "Not Billed"):
                    qc_invoice_ro.add(repair_order)

                if row.get("service_type") == "Comeback":
                    comeback_ro.add(repair_order)

            qc_projects = ro_with_qc
            non_qc_projects = all_ro - ro_with_qc

            total_ro = len(all_ro)
            total_qc_ro = len(qc_projects)

            totals_dict["total_qc_ro_count"] = total_qc_ro
            totals_dict["total_ro_count_non_qc"] = len(non_qc_projects)
            totals_dict["total_qc_invoice_ro_count"] = len(qc_invoice_ro)
            totals_dict["total_comeback_ro_count"] = len(comeback_ro)
            totals_dict["total_ro_count"] = total_ro

            compute_qc_invoiced_ro_amount(
                filters, totals_dict, len(qc_invoice_ro), total_qc_ro
            )
            compute_comeback_ro_amount(filters, totals_dict, len(comeback_ro), total_ro)

            totals_dict["total_qc_ro_percentage"] = (
                flt((total_qc_ro / total_ro) * 100.0, 3) if total_ro else 0.0
            )

            if totals_dict.get("_bold"):
                totals_dict["_bold"] = 0

            totals_dict["calculated_incentive"] = compute_incentive(
                totals_dict, filters.get("based_on")
            )

            yield totals_dict
