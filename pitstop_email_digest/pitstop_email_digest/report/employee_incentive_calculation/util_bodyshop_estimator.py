"""Bodyshop Estimator incentive calculation.

Built from the estimator's own quotations and what became of them: the ROs they
were invoiced on, the estimates that turned into sales orders, and the gross
margin of the ROs that completed.
"""

import frappe
from frappe.utils import flt

TEMPLATE_DATA = {
    "weightages": {
        "invoiced_ro": 40,
        "gross_profit": 30,
        "estimate_to_approval": 30,
    },
    "invoiced_ro_ladder": {
        85: 0,
        90: 85,
        95: 90,
        100: 95,
        105: 100,
        110: 105,
        115: 110,
        125: 115,
    },
    # 55% and below scores nothing; anything above 55% scores the full
    # gross profit weightage.
    "gross_profit_ladder": {54.9: 0.0, 55.0: 100.0},
    "estimate_to_approval_ladder": {74.9: 0.0, 75.0: 100.0},
}

REPORT_FILTERS = {}

SOURCE_REPORT = None


def get_leading_columns():
    """Columns shown before the source report's own columns."""
    return [
        {
            "label": frappe._("Bodyshop Estimator ID"),
            "fieldname": "bodyshop_estimator_id",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150,
        },
        {
            "label": frappe._("Bodyshop Estimator Name"),
            "fieldname": "bodyshop_estimator_name",
            "fieldtype": "Data",
            "width": 150,
        },
        {
            "label": "Sales Amount",
            "fieldname": "total_sales_amount",
            "fieldtype": "Currency",
            "width": 100,
        },
    ]


def get_trailing_columns():
    """Columns shown after the source report's own columns."""
    return []


# Trailing comma is required: ("Completed") is a str, not a tuple, and breaks
# `in %(...)s`
COMPLETED_PROJECT_STATUSES = ("Completed",)


def fetch_estimator_employee(fetch_id_name=False):
    settings = frappe.get_cached_doc("Incentive Calculation Setttings")
    designations = [
        d.designation
        for d in (settings.bodyshop_estimator_designation or [])
        if d.designation
    ]
    if not designations:
        return None

    filters = {
        "status": "Active",
        "designation": ["in", designations],
    }

    if fetch_id_name:
        return frappe.get_all(
            "Employee",
            filters=filters,
            fields=[
                "name as bodyshop_estimator_id",
                "employee_name as bodyshop_estimator_name",
            ],
        )

    return frappe.get_all("Employee", filters=filters, pluck="name")


def fetch_approved_estimate(filters):
    """Estimates raised in the period, and which of them became a submitted
    Sales Order — the estimate-to-approval ratio."""
    estimators = fetch_estimator_employee()
    if not estimators:
        return []

    conditions = ""
    values = {
        "from_dt": filters.get("from_date"),
        "to_dt": filters.get("to_date"),
        "estimators": tuple(estimators),
    }

    if filters.get("company"):
        conditions += " and q.company = %(company)s"
        values["company"] = filters.get("company")

    rows = frappe.db.sql(
        f"""
		select
			q.estimator_id as employee,
			q.estimator_name as employee_name,
			q.name as quotation,
			q.transaction_date as quotation_date,
			q.status as quotation_status,
			q.project,
			q.base_net_total as estimate_net_amount,
			q.base_grand_total as estimate_grand_amount,
			ifnull(approved.sales_order_count, 0) as sales_order_count,
			ifnull(approved.approved_net_amount, 0) as approved_net_amount,
			case when ifnull(approved.sales_order_count, 0) > 0 then 1 else 0 end as is_approved
		from
			`tabQuotation` q
		left join (
			select
				soi.quotation as quotation,
				count(distinct so.name) as sales_order_count,
				sum(soi.base_net_amount) as approved_net_amount
			from
				`tabSales Order Item` soi
			join
				`tabSales Order` so
			on
				so.name = soi.parent
			where
				so.docstatus = 1
				and ifnull(soi.quotation, '') != ''
			group by
				soi.quotation
		) approved
		on
			approved.quotation = q.name
		where
			q.docstatus = 1
			and q.transaction_date between %(from_dt)s and %(to_dt)s
			and q.estimator_id in %(estimators)s
			{conditions}
		""",
        values,
        as_dict=True,
    )

    groups = {}
    for row in rows:
        bodyshop_estimator_id = row.get("employee")
        bodyshop_estimator_name = row.get("employee_name")
        group = groups.setdefault(
            bodyshop_estimator_id,
            frappe._dict(
                {
                    "employee": bodyshop_estimator_id,
                    "totals": frappe._dict(
                        {
                            "employee": bodyshop_estimator_id,
                            "employee_name": bodyshop_estimator_name,
                            "total_estimate_count": 0,
                            "total_approved_estimate_count": 0,
                            "total_estimate_net_amount": 0.0,
                            "total_approved_net_amount": 0.0,
                            "estimate_to_approval_ratio": 0.0,
                            "estimate_to_approval_amount_ratio": 0.0,
                        }
                    ),
                    "rows": [],
                }
            ),
        )
        group["rows"].append(row)

        totals = group["totals"]
        totals["total_estimate_count"] += 1
        totals["total_estimate_net_amount"] += flt(row.get("estimate_net_amount"))
        if row.get("is_approved"):
            totals["total_approved_estimate_count"] += 1
            totals["total_approved_net_amount"] += flt(row.get("approved_net_amount"))

    for group in groups.values():
        totals = group["totals"]
        if totals["total_estimate_count"]:
            totals["estimate_to_approval_ratio"] = flt(
                (
                    totals["total_approved_estimate_count"]
                    / totals["total_estimate_count"]
                )
                * 100.0,
                3,
            )
        if totals["total_estimate_net_amount"]:
            totals["estimate_to_approval_amount_ratio"] = flt(
                (
                    totals["total_approved_net_amount"]
                    / totals["total_estimate_net_amount"]
                )
                * 100.0,
                3,
            )

    return [frappe._dict({"rows": list(groups.values())})]


def fetch_invoiced_ro(filters):
    """Submitted sales invoices raised in the period against the ROs behind the
    estimator's quotations."""
    estimators = fetch_estimator_employee()
    if not estimators:
        return []

    conditions = ""
    values = {
        "from_dt": filters.get("from_date"),
        "to_dt": filters.get("to_date"),
        "estimators": tuple(estimators),
    }

    if filters.get("company"):
        conditions += " and si.company = %(company)s"
        values["company"] = filters.get("company")

    rows = frappe.db.sql(
        f"""
		select
			q.estimator_id as employee,
			q.estimator_name as employee_name,
			q.name as quotation,
			q.transaction_date as quotation_date,
			q.status as quotation_status,
			q.net_total as quotation_net_total,
			p.name as project,
			p.project_date,
			p.project_type as service_type,
			p.project_status,
			si.name as sales_invoice,
			si.posting_date,
			si.base_net_total as invoiced_net_amount,
			si.base_grand_total as invoiced_grand_amount
		from
			`tabQuotation` q
		join
			`tabProject` p
		on
			p.name = q.project
		join
			`tabSales Invoice` si
		on
			si.project = p.name
		where
			si.docstatus = 1
			and si.posting_date between %(from_dt)s and %(to_dt)s
			and q.estimator_id in %(estimators)s
			{conditions}
		""",
        values,
        as_dict=True,
    )

    groups = {}
    for row in rows:
        bodyshop_estimator_id = row.get("employee")
        bodyshop_estimator_name = row.get("employee_name")
        group = groups.setdefault(
            bodyshop_estimator_id,
            frappe._dict(
                {
                    "employee": bodyshop_estimator_id,
                    "totals": frappe._dict(
                        {
                            "employee": bodyshop_estimator_id,
                            "employee_name": bodyshop_estimator_name,
                            "total_invoiced_net_amount": 0.0,
                            "total_invoiced_grand_amount": 0.0,
                            "total_ro_count": 0,
                            "total_quotation_count": 0,
                            "total_sales_invoice_count": 0,
                        }
                    ),
                    "rows": [],
                    "_projects": set(),
                    "_quotations": set(),
                }
            ),
        )
        group["rows"].append(row)
        group["_projects"].add(row.get("project"))
        group["_quotations"].add(row.get("quotation"))

        totals = group["totals"]
        totals["total_invoiced_net_amount"] += flt(row.get("invoiced_net_amount"))
        totals["total_invoiced_grand_amount"] += flt(row.get("invoiced_grand_amount"))
        totals["total_sales_invoice_count"] += 1

    for group in groups.values():
        totals = group["totals"]
        totals["total_ro_count"] = len(group.pop("_projects"))
        totals["total_quotation_count"] = len(group.pop("_quotations"))

    return [frappe._dict({"rows": list(groups.values())})]


def fetch_gross_profit_margin(filters):
    """Gross margin over sales amount across the completed ROs behind the
    estimator's quotations."""
    estimators = fetch_estimator_employee()
    if not estimators:
        return []

    conditions = ""
    values = {
        "from_dt": filters.get("from_date"),
        "to_dt": filters.get("to_date"),
        "estimators": tuple(estimators),
        "completed_statuses": COMPLETED_PROJECT_STATUSES,
    }

    if filters.get("company"):
        conditions += " and p.company = %(company)s"
        values["company"] = filters.get("company")

    rows = frappe.db.sql(
        f"""
		select
			q.estimator_id as employee,
			max(q.estimator_name) as employee_name,
			p.name as project,
			max(p.project_date) as project_date,
			max(p.status) as status,
			max(p.project_status) as project_status,
			max(p.project_type) as service_type,
			max(p.total_sales_amount) as total_sales_amount,
			max(p.gross_margin) as gross_margin,
			max(p.per_gross_margin) as per_gross_margin
		from
			`tabQuotation` q
		join
			`tabProject` p
		on
			p.name = q.project
		where
			q.docstatus = 1
			and p.status in %(completed_statuses)s
			and p.project_date between %(from_dt)s and %(to_dt)s
			and q.estimator_id in %(estimators)s
			{conditions}
		group by
			q.estimator_id, p.name
		""",
        values,
        as_dict=True,
    )

    groups = {}
    for row in rows:
        bodyshop_estimator_id = row.get("employee")
        bodyshop_estimator_name = row.get("employee_name")
        group = groups.setdefault(
            bodyshop_estimator_id,
            frappe._dict(
                {
                    "employee": bodyshop_estimator_id,
                    "totals": frappe._dict(
                        {
                            "employee": bodyshop_estimator_id,
                            "employee_name": bodyshop_estimator_name,
                            "total_completed_ro_count": 0,
                            "total_sales_amount": 0.0,
                            "total_gross_margin": 0.0,
                            "gross_profit_margin_percentage": 0.0,
                        }
                    ),
                    "rows": [],
                }
            ),
        )
        group["rows"].append(row)

        totals = group["totals"]
        totals["total_completed_ro_count"] += 1
        totals["total_sales_amount"] += flt(row.get("total_sales_amount"))
        totals["total_gross_margin"] += flt(row.get("gross_margin"))

    for group in groups.values():
        totals = group["totals"]
        if totals["total_sales_amount"]:
            totals["gross_profit_margin_percentage"] = flt(
                (totals["total_gross_margin"] / totals["total_sales_amount"]) * 100.0,
                3,
            )

    return [frappe._dict({"rows": list(groups.values())})]


def prepare_lookups(filters):
    return {
        "estimators": fetch_estimator_employee(fetch_id_name=True),
        "invoiced_ro": fetch_invoiced_ro(filters),
        "approved_estimate": fetch_approved_estimate(filters),
        "gross_profit_margin": fetch_gross_profit_margin(filters),
    }


def process_rows(filters, source_data, qc_task_types, lookups):
    # TODO: score invoiced_ro / approved_estimate / gross_profit_margin against
    # their ladders and total them into calculated_incentive. For now the rows
    # are listed unscored.
    for each_estimator in lookups.get("estimators") or []:
        yield each_estimator
