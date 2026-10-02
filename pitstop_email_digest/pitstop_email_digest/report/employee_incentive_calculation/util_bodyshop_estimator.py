"""Bodyshop Estimator incentive calculation.

Built from the estimator's own quotations and what became of them: the ROs they
were invoiced on, the estimates that turned into sales orders, and the gross
margin of the ROs that completed.
"""

import frappe
from frappe import qb
from frappe.query_builder import Case
from frappe.query_builder.functions import Count, IfNull, Max, Sum
from frappe.utils import flt

from .util_employee_incentive_calculation import (
    compute_incentive,
    fetch_month_targets,
    get_ladder_result,
    get_rate_ladder_result,
    weightage_amount,
)

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
        {
            "label": "Sales Target Amount",
            "fieldname": "bse_target_revenue",
            "fieldtype": "Currency",
            "width": 100,
        },
        {
            "label": "Gross Margin Percentage",
            "fieldname": "gp_gross_profit_margin_percentage",
            "fieldtype": "Percentage",
            "width": 140,
        },
        {
            "label": "Estimate To Appoval Ration Percentage",
            "fieldname": "estimate_to_approval_ratio",
            "fieldtype": "Percentage",
            "width": 140,
        },
    ]


def get_trailing_columns():
    """Columns shown after the source report's own columns."""
    return []


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
        "vehicle_workshop_division": "Body Shop",
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

    Quotation = qb.DocType("Quotation")
    SalesOrder = qb.DocType("Sales Order")
    SalesOrderItem = qb.DocType("Sales Order Item")

    approved = (
        qb.from_(SalesOrderItem)
        .inner_join(SalesOrder)
        .on(SalesOrder.name == SalesOrderItem.parent)
        .select(
            SalesOrderItem.quotation.as_("quotation"),
            Count(SalesOrder.name).distinct().as_("sales_order_count"),
            Sum(SalesOrderItem.base_net_amount).as_("approved_net_amount"),
        )
        .where(SalesOrder.docstatus == 1)
        .where(IfNull(SalesOrderItem.quotation, "") != "")
        .groupby(SalesOrderItem.quotation)
    ).as_("approved")

    query = (
        qb.from_(Quotation)
        .left_join(approved)
        .on(approved.quotation == Quotation.name)
        .select(
            Quotation.estimator_id.as_("bodyshop_estimator_id"),
            Quotation.estimator_name.as_("bodyshop_estimator_name"),
            Quotation.name.as_("quotation"),
            Quotation.transaction_date.as_("quotation_date"),
            Quotation.status.as_("quotation_status"),
            Quotation.project,
            Quotation.base_net_total.as_("estimate_net_amount"),
            Quotation.base_grand_total.as_("estimate_grand_amount"),
            IfNull(approved.sales_order_count, 0).as_("sales_order_count"),
            IfNull(approved.approved_net_amount, 0).as_("approved_net_amount"),
            Case()
            .when(IfNull(approved.sales_order_count, 0) > 0, 1)
            .else_(0)
            .as_("is_approved"),
        )
        .where(Quotation.docstatus == 1)
        .where(
            Quotation.transaction_date.between(
                filters.get("from_date"), filters.get("to_date")
            )
        )
        .where(Quotation.estimator_id.isin(estimators))
    )

    if filters.get("company"):
        query = query.where(Quotation.company == filters.get("company"))

    rows = query.run(as_dict=True)

    groups = {}
    for row in rows:
        bodyshop_estimator_id = row.get("bodyshop_estimator_id")
        bodyshop_estimator_name = row.get("bodyshop_estimator_name")
        group = groups.setdefault(
            bodyshop_estimator_id,
            frappe._dict(
                {
                    "bodyshop_estimator_id": bodyshop_estimator_id,
                    "totals": frappe._dict(
                        {
                            "bodyshop_estimator_id": bodyshop_estimator_id,
                            "bodyshop_estimator_name": bodyshop_estimator_name,
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

    Quotation = qb.DocType("Quotation")
    Project = qb.DocType("Project")
    Invoice = qb.DocType("Sales Invoice")

    query = (
        qb.from_(Quotation)
        .inner_join(Project)
        .on(Project.name == Quotation.project)
        .inner_join(Invoice)
        .on(Invoice.project == Project.name)
        .select(
            Quotation.estimator_id.as_("bodyshop_estimator_id"),
            Quotation.estimator_name.as_("bodyshop_estimator_name"),
            Quotation.name.as_("quotation"),
            Quotation.transaction_date.as_("quotation_date"),
            Quotation.status.as_("quotation_status"),
            Quotation.net_total.as_("quotation_net_total"),
            Project.name.as_("project"),
            Project.project_date,
            Project.project_type.as_("service_type"),
            Project.project_status,
            Invoice.name.as_("sales_invoice"),
            Invoice.posting_date,
            Invoice.base_net_total.as_("invoiced_net_amount"),
            Invoice.base_grand_total.as_("invoiced_grand_amount"),
        )
        .where(Invoice.docstatus == 1)
        .where(Quotation.docstatus == 1)
        .where(
            Invoice.posting_date.between(
                filters.get("from_date"), filters.get("to_date")
            )
        )
        .where(Quotation.estimator_id.isin(estimators))
    )

    if filters.get("company"):
        query = query.where(Invoice.company == filters.get("company"))

    rows = query.run(as_dict=True)

    groups = {}
    for row in rows:
        bodyshop_estimator_id = row.get("bodyshop_estimator_id")
        bodyshop_estimator_name = row.get("bodyshop_estimator_name")
        group = groups.setdefault(
            bodyshop_estimator_id,
            frappe._dict(
                {
                    "bodyshop_estimator_id": bodyshop_estimator_id,
                    "totals": frappe._dict(
                        {
                            "bodyshop_estimator_id": bodyshop_estimator_id,
                            "bodyshop_estimator_name": bodyshop_estimator_name,
                            "total_sales_amount": 0.0,
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
        totals["total_sales_amount"] += flt(row.get("invoiced_net_amount"))
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

    Quotation = qb.DocType("Quotation")
    Project = qb.DocType("Project")

    query = (
        qb.from_(Quotation)
        .inner_join(Project)
        .on(Project.name == Quotation.project)
        .select(
            Quotation.estimator_id.as_("bodyshop_estimator_id"),
            Quotation.estimator_name.as_("bodyshop_estimator_name"),
            Project.name.as_("project"),
            Max(Project.project_date).as_("project_date"),
            Max(Project.status).as_("status"),
            Max(Project.project_status).as_("project_status"),
            Max(Project.project_type).as_("service_type"),
            Max(Project.total_sales_amount).as_("total_sales_amount"),
            Max(Project.gross_margin).as_("gross_margin"),
            Max(Project.per_gross_margin).as_("per_gross_margin"),
        )
        .where(Quotation.docstatus == 1)
        .where(Project.status.isin(list(COMPLETED_PROJECT_STATUSES)))
        .where(
            Project.project_date.between(
                filters.get("from_date"), filters.get("to_date")
            )
        )
        .where(Quotation.estimator_id.isin(estimators))
        .groupby(Quotation.estimator_id, Project.name)
    )

    if filters.get("company"):
        query = query.where(Project.company == filters.get("company"))

    rows = query.run(as_dict=True)

    groups = {}
    for row in rows:
        bodyshop_estimator_id = row.get("bodyshop_estimator_id")
        bodyshop_estimator_name = row.get("bodyshop_estimator_name")
        group = groups.setdefault(
            bodyshop_estimator_id,
            frappe._dict(
                {
                    "bodyshop_estimator_id": bodyshop_estimator_id,
                    "totals": frappe._dict(
                        {
                            "bodyshop_estimator_id": bodyshop_estimator_id,
                            "bodyshop_estimator_name": bodyshop_estimator_name,
                            "total_completed_ro_count": 0,
                            "gp_total_sales_amount": 0.0,
                            "gp_total_gross_margin": 0.0,
                            "gp_gross_profit_margin_percentage": 0.0,
                        }
                    ),
                    "rows": [],
                }
            ),
        )
        group["rows"].append(row)

        totals = group["totals"]
        totals["total_completed_ro_count"] += 1
        totals["gp_total_sales_amount"] += flt(row.get("total_sales_amount"))
        totals["gp_total_gross_margin"] += flt(row.get("gross_margin"))

    for group in groups.values():
        totals = group["totals"]
        if totals["gp_total_sales_amount"]:
            totals["gp_gross_profit_margin_percentage"] = flt(
                (totals["gp_total_gross_margin"] / totals["gp_total_sales_amount"])
                * 100.0,
                3,
            )

    return [frappe._dict({"rows": list(groups.values())})]


def apply_gross_profit_margin(filters, totals):
    """Rate the gross profit margin percentage against `gross_profit_ladder`.

    The percentage comes from `fetch_gross_profit_margin`, already merged into
    `totals`: 55% and below scores nothing, anything above it scores the full
    gross profit weightage.
    """
    totals["gross_profit_amt"] = 0.0

    percentage = flt(totals.get("gp_gross_profit_margin_percentage"), 3)
    if not percentage:
        return

    result = get_rate_ladder_result(
        based_on=filters.get("based_on"),
        percentage=percentage,
        ladder_field="gross_profit_ladder",
        top_cap=100.0,
    )

    if result:
        totals["gross_profit_amt"] = flt(
            weightage_amount(filters, "gross_profit") * (result / 100.0), 3
        )


def apply_approved_estimate(filters, totals):
    """Rate the estimate-to-approval ratio against `estimate_to_approval_ladder`.

    The ratio comes from `fetch_approved_estimate`, already merged into
    `totals`: below 75% of estimates turning into submitted sales orders scores
    nothing, at or above it scores the full estimate-to-approval weightage.
    """
    totals["estimate_to_approval_amt"] = 0.0

    ratio = flt(totals.get("estimate_to_approval_ratio"), 3)
    if not ratio:
        return

    result = get_rate_ladder_result(
        based_on=filters.get("based_on"),
        percentage=ratio,
        ladder_field="estimate_to_approval_ladder",
        top_cap=100.0,
    )

    if result:
        totals["estimate_to_approval_amt"] = flt(
            weightage_amount(filters, "estimate_to_approval") * (result / 100.0), 3
        )


def fetch_targets(filters):
    settings = frappe.get_cached_doc("Incentive Calculation Setttings")
    designations = [
        d.designation
        for d in (settings.bodyshop_estimator_designation or [])
        if d.designation
    ]
    if not designations:
        return None

    return fetch_month_targets(
        designations, filters.get("to_date"), "bodyshop_estimator_id"
    )


def compute_revenue_amount(filters, totals):
    totals["invoiced_ro_amt"] = 0.0

    revenue_percentage = (
        flt(
            (
                flt(totals.get("total_sales_amount"))
                / flt(totals.get("bse_target_revenue"))
            )
            * 100.0,
            3,
        )
        if flt(totals.get("bse_target_revenue"))
        else 0.0
    )

    result = get_ladder_result(
        based_on=filters.get("based_on"),
        sold_hrs_percentage=revenue_percentage,
        ladder_field="invoiced_ro_ladder",
        top_cap=125.0,
    )

    if result:
        totals["invoiced_ro_amt"] = flt(
            weightage_amount(filters, "invoiced_ro") * (result / 100.0), 3
        )


def prepare_lookups(filters):
    return {
        "estimators": fetch_estimator_employee(fetch_id_name=True),
        "invoiced_ro": fetch_invoiced_ro(filters),
        "approved_estimate": fetch_approved_estimate(filters),
        "gross_profit_margin": fetch_gross_profit_margin(filters),
        "target": fetch_targets(filters),
    }


def process_rows(filters, source_data, qc_task_types, lookups):
    invoiced_ro = lookups.get("invoiced_ro") or []
    target = lookups.get("target") or {}
    gross_profit_margin = lookups.get("gross_profit_margin") or []
    approved_estimate = lookups.get("approved_estimate") or []

    for each_estimator in lookups.get("estimators") or []:
        each_estimator.update(
            {
                "total_sales_amount": 0.0,
                "total_ro_count": 0.0,
                "total_quotation_count": 0.0,
                "total_sales_invoice_count": 0.0,
                "gross_profit_margin_percentage": 0.0,
                "total_completed_ro_count": 0.0,
                "gp_total_sales_amount": 0.0,
                "gp_total_gross_margin": 0.0,
                "gp_gross_profit_margin_percentage": 0.0,
                "total_estimate_count": 0,
                "total_approved_estimate_count": 0,
                "total_estimate_net_amount": 0.0,
                "total_approved_net_amount": 0.0,
                "estimate_to_approval_ratio": 0.0,
            }
        )
        bodyshop_estimator = each_estimator.get("bodyshop_estimator_id")
        for each_row in invoiced_ro:
            for each_sub_row in each_row.rows:
                if each_sub_row.get("bodyshop_estimator_id") == bodyshop_estimator:
                    each_estimator.update(each_sub_row.get("totals"))
                    break
        for each_row_gpm in gross_profit_margin:
            for each_row_gpm_sub_row in each_row_gpm.rows:
                if (
                    each_row_gpm_sub_row.get("bodyshop_estimator_id")
                    == bodyshop_estimator
                ):
                    each_estimator.update(each_row_gpm_sub_row.get("totals"))
                    break
        for each_row_ae in approved_estimate:
            for each_row_ae_sub_row in each_row_ae.rows:
                if (
                    each_row_ae_sub_row.get("bodyshop_estimator_id")
                    == bodyshop_estimator
                ):
                    each_estimator.update(each_row_ae_sub_row.get("totals"))
                    break

        each_estimator["bse_target_revenue"] = target.get(bodyshop_estimator, 0.0)
        compute_revenue_amount(filters, each_estimator)
        apply_gross_profit_margin(filters, each_estimator)
        apply_approved_estimate(filters, each_estimator)

        each_estimator["calculated_incentive"] = compute_incentive(
            each_estimator, filters.get("based_on")
        )

        yield each_estimator
