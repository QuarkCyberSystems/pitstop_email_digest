"""Insurance BD incentive calculation.

Built from the Insurance BD's own quotations and what became of them: the ROs they
were invoiced on, the estimates that turned into sales orders, and the gross
margin of the ROs that completed.
"""

import frappe
from erpnext.setup.doctype.item_group.item_group import get_item_group_subtree
from frappe.utils import flt, getdate

from .util_employee_incentive_calculation import (
    compute_incentive,
    get_ladder_result,
    get_rate_ladder_result,
    weightage_amount,
)

TEMPLATE_DATA = {
    "weightages": {
        "invoiced_ro": 50,
        "gross_profit": 20,
        "labour_parts_mix": 30,
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
    "gross_profit_ladder": {19.9: 0.0, 20.0: 100.0},
    "labour_parts_mix_ladder": {29.9: 0.0, 30.0: 100.0},
}

REPORT_FILTERS = {}

SOURCE_REPORT = None

COMPLETED_PROJECT_STATUSES = ("Completed",)


def get_leading_columns():
    """Columns shown before the source report's own columns."""
    return [
        {
            "label": frappe._("Insurance BD ID"),
            "fieldname": "insurance_bd_id",
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150,
        },
        {
            "label": frappe._("Insurance BD Name"),
            "fieldname": "insurance_bd_name",
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
            "fieldname": "ibd_target_revenue",
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
            "label": "Labour Revenue Percentage",
            "fieldname": "labour_perc_of_total_sales",
            "fieldtype": "Percentage",
            "width": 140,
        },
    ]


def get_trailing_columns():
    """Columns shown after the source report's own columns."""
    return []


def fetch_insurance_bd_employee(fetch_id_name=False):
    settings = frappe.get_cached_doc("Incentive Calculation Setttings")
    designations = [
        d.designation
        for d in (settings.insurance_bd_designation or [])
        if d.designation
    ]
    if not designations:
        return None

    filters = {"status": "Active", "designation": ["in", designations]}

    if fetch_id_name:
        return frappe.get_all(
            "Employee",
            filters=filters,
            fields=[
                "name as insurance_bd_id",
                "employee_name as insurance_bd_name",
            ],
        )

    return frappe.get_all("Employee", filters=filters, pluck="name")


def compute_revenue_amount(filters, totals):
    totals["invoiced_ro_amt"] = 0.0

    revenue_percentage = (
        flt(
            (
                flt(totals.get("total_sales_amount"))
                / flt(totals.get("ibd_target_revenue"))
            )
            * 100.0,
            3,
        )
        if flt(totals.get("ibd_target_revenue"))
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


def fetch_gross_profit_margin(filters):
    """Gross margin over sales amount across the completed ROs behind the
    insurance_bd's quotations."""
    insurance_bds = fetch_insurance_bd_employee()
    if not insurance_bds:
        return []

    conditions = ""
    values = {
        "from_dt": filters.get("from_date"),
        "to_dt": filters.get("to_date"),
        "estimators": tuple(insurance_bds),
        "completed_statuses": COMPLETED_PROJECT_STATUSES,
    }

    if filters.get("company"):
        conditions += " and p.company = %(company)s"
        values["company"] = filters.get("company")

    rows = frappe.db.sql(
        f"""
		select
			q.estimator_id as insurance_bd_id,
			q.estimator_name as insurance_bd_id_name,
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
        insurance_bd_id = row.get("insurance_bd_id")
        insurance_bd_id_name = row.get("insurance_bd_id_name")
        group = groups.setdefault(
            insurance_bd_id,
            frappe._dict(
                {
                    "insurance_bd_id": insurance_bd_id,
                    "totals": frappe._dict(
                        {
                            "insurance_bd_id": insurance_bd_id,
                            "insurance_bd_id_name": insurance_bd_id_name,
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
    `totals`: 20% and below scores nothing, anything above it scores the full
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


def apply_labour_parts_mix(filters, totals):
    """Rate the labour_parts_mix percentage against `labour_parts_mix_ladder`.

    The percentage comes from `fetch_labour_parts_revenue`, already merged into
    `totals`: 70% and below scores nothing, anything above it scores the full
    gross labour_parts_mix weightage.
    """
    totals["labour_parts_mix_amt"] = 0.0

    percentage = flt(totals.get("labour_perc_of_total_sales"), 3)
    if not percentage:
        return

    result = get_rate_ladder_result(
        based_on=filters.get("based_on"),
        percentage=percentage,
        ladder_field="labour_parts_mix_ladder",
        top_cap=100.0,
    )

    if result:
        totals["labour_parts_mix_amt"] = flt(
            weightage_amount(filters, "labour_parts_mix") * (result / 100.0), 3
        )


def fetch_targets(filters):
    to_date = getdate(filters.get("to_date") or getdate())
    year = to_date.year
    month_field = to_date.strftime("%B").lower()

    settings = frappe.get_cached_doc("Incentive Calculation Setttings")
    designations = [
        d.designation
        for d in (settings.insurance_bd_designation or [])
        if d.designation
    ]
    if not designations:
        return None

    rows = frappe.db.sql(
        f"""
		select
			tr.employee as insurance_bd_id,
			trd.{month_field} as target_amount
		from
			`tabTarget Role Details` trd
		inner join
			`tabTarget Role` tr on tr.name = trd.parent
		where
			trd.parenttype = 'Target Role'
			and trd.parentfield = 'targets'
			and trd.year = %(year)s
			and tr.employee is not null
			and tr.employee != ''
            and tr.designation in %(designations)s
		""",
        {"year": year, "designations": tuple(designations)},
        as_dict=True,
    )

    return {row.get("insurance_bd_id"): flt(row.get("target_amount")) for row in rows}


def fetch_invoiced_ro(filters):
    """Submitted sales invoices raised in the period against the ROs behind the
    insurance_bd's quotations."""
    insurance_bd = fetch_insurance_bd_employee()
    if not insurance_bd:
        return []

    conditions = ""
    values = {
        "from_dt": filters.get("from_date"),
        "to_dt": filters.get("to_date"),
        "insurance_bds": tuple(insurance_bd),
    }

    if filters.get("company"):
        conditions += " and si.company = %(company)s"
        values["company"] = filters.get("company")

    rows = frappe.db.sql(
        f"""
		select
			q.estimator_id as insurance_bd_id,
			q.estimator_name as insurance_bd_id_name,
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
			si.docstatus = 1 and q.docstatus = 1
			and si.posting_date between %(from_dt)s and %(to_dt)s
			and q.estimator_id in %(insurance_bds)s
			{conditions}
		""",
        values,
        as_dict=True,
    )

    groups = {}
    for row in rows:
        insurance_bd_id = row.get("insurance_bd_id")
        insurance_bd_id_name = row.get("insurance_bd_id_name")
        group = groups.setdefault(
            insurance_bd_id,
            frappe._dict(
                {
                    "insurance_bd_id": insurance_bd_id,
                    "totals": frappe._dict(
                        {
                            "insurance_bd_id": insurance_bd_id,
                            "insurance_bd_id_name": insurance_bd_id_name,
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


def get_labour_and_parts_item_groups():
    """Item group subtrees that classify an invoice line as labour or parts."""
    settings = frappe.get_cached_doc("Projects Settings", None)

    labour_groups = set()
    for item_group in ("Lumpsum Labour", "AutoCare Services"):
        labour_groups.update(get_item_group_subtree(item_group) or [item_group])

    parts_groups = set()
    for fieldname in ("materials_item_group", "paint_item_group"):
        item_group = settings.get(fieldname)
        if item_group:
            parts_groups.update(get_item_group_subtree(item_group) or [item_group])

    return labour_groups, parts_groups


def fetch_labour_parts_revenue(filters):
    """Submitted sales invoice lines raised in the period against the ROs behind
    the insurance_bd's quotations, split into labour, parts and other sales."""
    insurance_bd = fetch_insurance_bd_employee()
    if not insurance_bd:
        return []

    conditions = ""
    values = {
        "from_dt": filters.get("from_date"),
        "to_dt": filters.get("to_date"),
        "insurance_bds": tuple(insurance_bd),
    }

    if filters.get("company"):
        conditions += " and si.company = %(company)s"
        values["company"] = filters.get("company")

    rows = frappe.db.sql(
        f"""
		select
			q.estimator_id as insurance_bd_id,
			q.estimator_name as insurance_bd_id_name,
			q.name as quotation,
			p.name as project,
			p.project_type as service_type,
			si.name as sales_invoice,
			si.posting_date,
			sii.item_code,
			sii.item_group,
			sii.uom,
			sii.stock_uom,
			sii.base_net_amount as net_amount
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
		join
			`tabSales Invoice Item` sii
		on
			sii.parent = si.name
		where
			si.docstatus = 1 and q.docstatus = 1
			and si.posting_date between %(from_dt)s and %(to_dt)s
			and q.estimator_id in %(insurance_bds)s
			{conditions}
		""",
        values,
        as_dict=True,
    )

    labour_groups, parts_groups = get_labour_and_parts_item_groups()

    groups = {}
    for row in rows:
        insurance_bd_id = row.get("insurance_bd_id")
        insurance_bd_id_name = row.get("insurance_bd_id_name")
        group = groups.setdefault(
            insurance_bd_id,
            frappe._dict(
                {
                    "insurance_bd_id": insurance_bd_id,
                    "totals": frappe._dict(
                        {
                            "insurance_bd_id": insurance_bd_id,
                            "insurance_bd_id_name": insurance_bd_id_name,
                            "lp_total_sales_amount": 0.0,
                            "labour_sales_amount": 0.0,
                            "parts_sales_amount": 0.0,
                            "other_sales_amount": 0.0,
                            "labour_perc_of_total_sales": 0.0,
                        }
                    ),
                    "rows": [],
                }
            ),
        )
        group["rows"].append(row)

        net_amount = flt(row.get("net_amount"))
        item_group = row.get("item_group")

        totals = group["totals"]
        totals["lp_total_sales_amount"] += net_amount

        if (
            row.get("uom") == "Hour"
            or row.get("stock_uom") == "Hour"
            or item_group in labour_groups
        ):
            totals["labour_sales_amount"] += net_amount
        elif item_group in parts_groups:
            totals["parts_sales_amount"] += net_amount
        else:
            totals["other_sales_amount"] += net_amount

    for group in groups.values():
        totals = group["totals"]
        if totals["lp_total_sales_amount"]:
            totals["labour_perc_of_total_sales"] = flt(
                (totals["labour_sales_amount"] / totals["lp_total_sales_amount"])
                * 100.0,
                3,
            )

    return [frappe._dict({"rows": list(groups.values())})]


def prepare_lookups(filters):
    return {
        "insurance_bd": fetch_insurance_bd_employee(fetch_id_name=True),
        "invoiced_ro": fetch_invoiced_ro(filters),
        "target": fetch_targets(filters),
        "gross_profit_margin": fetch_gross_profit_margin(filters),
        "labour_parts_revenue": fetch_labour_parts_revenue(filters),
    }


def process_rows(filters, source_data, qc_task_types, lookups):
    insurance_bd = lookups.get("insurance_bd") or []
    invoiced_ro = lookups.get("invoiced_ro") or []
    target = lookups.get("target") or {}
    gross_profit_margin = lookups.get("gross_profit_margin") or []
    labour_parts_revenue = lookups.get("labour_parts_revenue") or []
    for each_insurance_bd in insurance_bd:
        each_insurance_bd.update(
            {
                "total_sales_amount": 0.0,
                "gp_gross_profit_margin_percentage": 0.0,
                "labour_sales_amount": 0.0,
                "parts_sales_amount": 0.0,
                "other_sales_amount": 0.0,
                "labour_perc_of_total_sales": 0.0,
            }
        )
        insurance_bd = each_insurance_bd.get("insurance_bd_id")
        for each_row in invoiced_ro:
            for each_sub_row in each_row.rows:
                if each_sub_row.get("insurance_bd_id") == insurance_bd:
                    each_insurance_bd.update(each_sub_row.get("totals"))
                    break
        for each_row_gpm in gross_profit_margin:
            for each_row_gpm_sub_row in each_row_gpm.rows:
                if each_row_gpm_sub_row.get("insurance_bd_id") == insurance_bd:
                    each_insurance_bd.update(each_row_gpm_sub_row.get("totals"))
                    break
        for each_row_lpr in labour_parts_revenue:
            for each_row_lpr_sub_row in each_row_lpr.rows:
                if each_row_lpr_sub_row.get("insurance_bd_id") == insurance_bd:
                    each_insurance_bd.update(each_row_lpr_sub_row.get("totals"))
                    break
        each_insurance_bd["ibd_target_revenue"] = target.get(insurance_bd, 0.0)
        compute_revenue_amount(filters, each_insurance_bd)
        apply_gross_profit_margin(filters, each_insurance_bd)
        apply_labour_parts_mix(filters, each_insurance_bd)
        each_insurance_bd["calculated_incentive"] = compute_incentive(
            each_insurance_bd, filters.get("based_on")
        )
        yield each_insurance_bd
