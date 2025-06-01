# Copyright (c) 2025, QCS
# License: GPL-v3

import frappe
from frappe import _
from collections import OrderedDict
from datetime import timedelta

from erpnext.accounts.utils import get_balance_on
from erpnext.setup.doctype.email_digest.email_digest import EmailDigest as CoreDigest

# utils / helpers
from frappe.utils import getdate, today, get_link_to_report, flt
from erpnext.setup.doctype.item_group.item_group import get_item_group_subtree
from erpnext.stock.doctype.item.item import convert_item_uom_for


# ──────────────────────────────────────────────────────────────
# Default fallbacks if “Projects Settings” is absent / incomplete
# ──────────────────────────────────────────────────────────────
PROJECTS_DEFAULTS = {
    "insurance_excess_item":  "INS-EXS",
    "materials_item_group":   "Material Categories",
    "lubricants_item_group":  "Lubricants",
    "consumables_item_group": "Consumables",
    "paint_item_group":       "Paint",
    "sublet_item_group":      "Sublet Jobs",
}


def get_projects_settings():
    """
    Return a frappe._dict with all keys from PROJECTS_DEFAULTS.
    Falls back to defaults where the singleton or a field is missing.
    """
    try:
        doc = frappe.get_cached_doc("Projects Settings", None)
    except Exception:  # DocType or table missing
        doc = frappe._dict()

    out = {k: (doc.get(k) or PROJECTS_DEFAULTS[k]) for k in PROJECTS_DEFAULTS}
    return frappe._dict(out)


# ──────────────────────────────────────────────────────────────
# Date helpers
# ──────────────────────────────────────────────────────────────
def _server_today():
    return getdate(today())


def _fiscal_year_start(d):
    fy = frappe.db.get_value(
        "Fiscal Year",
        {"year_start_date": ("<=", d), "year_end_date": (">=", d)},
        "year_start_date",
    )
    return fy or getdate(f"{d.year}-01-01")


# ──────────────────────────────────────────────────────────────
# Main Digest Class
# ──────────────────────────────────────────────────────────────
class PitstopEmailDigest(CoreDigest):
    """Pitstop-specific digest with eight-metric KPI matrix"""

    # ---------------------------------------------------
    # Which “today”?
    # ---------------------------------------------------
    def _as_of_date(self):
        return getdate(self.as_of_date) if getattr(self, "as_of_date", None) else _server_today()

    # ---------------------------------------------------
    # Render full HTML
    # ---------------------------------------------------
    def get_msg_html(self):
        ctx = frappe._dict()
        ctx.update(self.__dict__)

        self.set_title(ctx)
        self.set_style(ctx)
        ctx.title = _("Pitstop Daily Matrix")

        #ctx.kpi_table       = self._get_workshop_kpi_table()
        ctx.insights_table  = self._get_expanded_kpi_table()
        ctx.branch_revenue  = self._get_branch_revenue()

        return frappe.render_template(
            "pitstop_email_digest/doctype/pitstop_email_digest/templates/default.html",
            ctx,
            is_path=True,
        )

    # ---------------------------------------------------
    # Simple RO + Revenue cards
    # ---------------------------------------------------
    def _get_workshop_kpi_table(self):
        d        = self._as_of_date()
        m_start  = getdate(f"{d.year}-{d.month:02d}-01")
        fy_start = _fiscal_year_start(d)

        def _vals(start, end):
            ro = frappe.db.count(
                "Project",
                {
                    "ready_to_close": 1,
                    "status": ("not in", ("Draft", "Cancelled")),
                    "final_invoice_date": ["between", (start, end)],
                },
            )
            rev = frappe.db.sql(
                """
                SELECT COALESCE(SUM(i.base_net_amount),0)
                  FROM `tabSales Invoice` inv
                  JOIN `tabSales Invoice Item` i ON i.parent = inv.name
                  JOIN `tabProject` p            ON p.name   = i.project
                 WHERE inv.docstatus = 1
                   AND p.ready_to_close = 1
                   AND p.final_invoice_date BETWEEN %s AND %s
                """,
                (start, end),
            )[0][0] or 0
            return ro, rev

        d_ro, d_rev = _vals(d, d)
        m_ro, m_rev = _vals(m_start, d)
        y_ro, y_rev = _vals(fy_start, d)

        money = lambda v: f"{flt(v):,.2f}"

        return [
            ["Desc", "Daily", "MTD", "YTD"],
            ["No. of ROs",     d_ro,  m_ro,  y_ro],
            ["Revenue",        money(d_rev), money(m_rev), money(y_rev)],
        ]

    # ---------------------------------------------------
    # Build KPI bucket for any span (8 metrics)
    # ---------------------------------------------------
    def _build_kpi(self, start_date, end_date):
        ps = get_projects_settings()

        # 1) Closed-RO count
        ro_count = frappe.db.count(
            "Project",
            {
                "ready_to_close": 1,
                "status": ("not in", ("Draft", "Cancelled")),
                "final_invoice_date": ["between", (start_date, end_date)],
            },
        )

        # 2) Fetch invoice lines (skip Insurance Excess item)
        rows = frappe.db.sql(
            """
            SELECT
                i.item_code, i.qty, i.uom, i.stock_uom, i.conversion_factor,
                i.item_group, i.is_stock_item, i.base_net_amount AS net_amount
            FROM `tabSales Invoice Item` i
            JOIN `tabSales Invoice` inv ON inv.name = i.parent AND inv.docstatus = 1
            JOIN `tabProject` p         ON p.name  = i.project
            WHERE p.ready_to_close = 1
              AND p.final_invoice_date BETWEEN %s AND %s
              AND i.item_code != %s
            """,
            (start_date, end_date, ps.insurance_excess_item),
            as_dict=True,
        )

        # 3) Item-group buckets
        mats   = get_item_group_subtree(ps.materials_item_group)   if ps.materials_item_group   else []
        lubes  = get_item_group_subtree(ps.lubricants_item_group)  if ps.lubricants_item_group  else []
        cons   = get_item_group_subtree(ps.consumables_item_group) if ps.consumables_item_group else []
        paints = get_item_group_subtree(ps.paint_item_group)       if ps.paint_item_group       else []

        revenue = labour_amt = parts_amt = sold_time = 0

        for r in rows:
            revenue += r.net_amount

            if r.is_stock_item or r.item_group in mats:
                if r.item_group not in lubes + cons + paints:
                    parts_amt += r.net_amount
            else:
                if r.uom == "Hour" or r.stock_uom == "Hour":
                    labour_amt += r.net_amount

            hrs = convert_item_uom_for(
                r.qty, r.item_code, r.uom, "Hour",
                conversion_factor=(r.conversion_factor if r.stock_uom == "Hour" else None),
                null_if_not_convertible=True,
            )
            if hrs is not None:
                sold_time += flt(hrs)

        labour_rate  = labour_amt / sold_time if sold_time else 0
        hours_per_ro = sold_time / ro_count   if ro_count   else 0
        parts_ratio  = parts_amt / labour_amt if labour_amt else 0

        return frappe._dict(
            ro_count        = ro_count,
            labour_hours    = sold_time,
            revenue         = revenue,
            labour_amount   = labour_amt,
            parts_amount    = parts_amt,
            labour_rate     = labour_rate,
            hours_per_ro    = hours_per_ro,
            parts_to_labour = parts_ratio,
        )

    # ---------------------------------------------------
    # Extended KPI table (Daily / MTD / YTD)
    # ---------------------------------------------------
    def _get_expanded_kpi_table(self):
        d   = self._as_of_date()
        m0  = getdate(f"{d.year}-{d.month:02d}-01")
        y0  = _fiscal_year_start(d)

        daily = self._build_kpi(d,  d)
        mtd   = self._build_kpi(m0, d)
        ytd   = self._build_kpi(y0, d)

        f2 = lambda v: f"{flt(v):,.2f}"
        i0 = lambda v: f"{int(v):,}"

        def ratio(row):
            return f"1 : {f2(row.parts_to_labour)}"

        return [
            ["Metric",              "Daily",                  "MTD",                   "YTD"],
            ["No. of Repair Orders", i0(daily.ro_count),       i0(mtd.ro_count),        i0(ytd.ro_count)],
            ["Labour Hours",         f2(daily.labour_hours),   f2(mtd.labour_hours),    f2(ytd.labour_hours)],
            ["Revenue",              f2(daily.revenue),        f2(mtd.revenue),         f2(ytd.revenue)],
            ["Labour Amount",        f2(daily.labour_amount),  f2(mtd.labour_amount),   f2(ytd.labour_amount)],
            ["Parts Amount",         f2(daily.parts_amount),   f2(mtd.parts_amount),    f2(ytd.parts_amount)],
            ["Effective Labour Rate",f2(daily.labour_rate),    f2(mtd.labour_rate),     f2(ytd.labour_rate)],
            ["Hours per RO",         f2(daily.hours_per_ro),   f2(mtd.hours_per_ro),    f2(ytd.hours_per_ro)],
            ["Parts : Labour Ratio", ratio(daily),             ratio(mtd),              ratio(ytd)],
        ]

    # ---------------------------------------------------
    # Branch-wise revenue (Daily / MTD / YTD) – same logic
    # ---------------------------------------------------
    def _get_branch_revenue(self):
        d        = self._as_of_date()
        fy_start = _fiscal_year_start(d)
        m_start  = getdate(f"{d.year}-{d.month:02d}-01")

        ps = get_projects_settings()          # pulls defaults if singleton absent

        # ---------- SQL helper -----------------------------------------
        def _revenue_for(branch, start, end):
            return frappe.db.sql(
                """
                SELECT COALESCE(SUM(i.base_net_amount),0)
                  FROM `tabSales Invoice`       inv
                  JOIN `tabSales Invoice Item` i ON i.parent = inv.name
                  JOIN `tabProject`            p ON p.name   = i.project
                 WHERE inv.docstatus       = 1
                   AND p.ready_to_close    = 1
                   AND p.branch            = %s
                   AND p.final_invoice_date BETWEEN %s AND %s
                   AND i.item_code        != %s
                """,
                (branch, start, end, ps.insurance_excess_item),
            )[0][0] or 0

        # ---------- gather distinct branches exactly like KPI ----------
        branches = frappe.get_all(
            "Project",
            filters={
                "ready_to_close": 1,
                "status": ("not in", ("Draft", "Cancelled")),
                "final_invoice_date": [">=", fy_start],
            },
            pluck="branch",
            distinct=True,
        )
        branches = sorted([b for b in branches if b])  # drop None / empty

        # ---------- build OrderedDict with totals ----------------------
        od, td, tm, ty = OrderedDict(), 0, 0, 0

        for br in branches:
            dv = _revenue_for(br, d,        d)
            mv = _revenue_for(br, m_start,  d)
            yv = _revenue_for(br, fy_start, d)

            od[br] = {"daily": dv, "mtd": mv, "ytd": yv}
            td += dv; tm += mv; ty += yv

        od["TOTAL"] = {"daily": td, "mtd": tm, "ytd": ty}
        return od

    # ---------------------------------------------------
    # Scheduler helpers
    # ---------------------------------------------------
    @staticmethod
    def _auto_send(freq):
        for name in frappe.get_all(
            "Pitstop Email Digest",
            filters={"enabled": 1, "frequency": freq},
            pluck="name",
        ):
            frappe.get_doc("Pitstop Email Digest", name).send()

    @staticmethod
    def auto_send_daily():
        PitstopEmailDigest._auto_send("Daily")

    @staticmethod
    def auto_send_weekly():
        PitstopEmailDigest._auto_send("Weekly")


# Aliases so hooks.py can keep using “…auto_send_daily”
auto_send_daily  = PitstopEmailDigest.auto_send_daily
auto_send_weekly = PitstopEmailDigest.auto_send_weekly


# Desk preview API
@frappe.whitelist()
def get_digest_msg(name):
    return frappe.get_doc("Pitstop Email Digest", name).get_msg_html()
