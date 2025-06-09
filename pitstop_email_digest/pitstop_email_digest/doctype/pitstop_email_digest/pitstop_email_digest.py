# Copyright © 2025, QCS
# License: GPL-3.0

import frappe
from frappe import _
from collections import OrderedDict
from datetime import timedelta
from frappe.utils import getdate, today, flt
from erpnext.accounts.utils import get_balance_on
from erpnext.setup.doctype.email_digest.email_digest import EmailDigest as CoreDigest
from erpnext.setup.doctype.item_group.item_group import get_item_group_subtree
from erpnext.stock.doctype.item.item import convert_item_uom_for

# ──────────────────────────────────────────────────────────────
# Currency helper – always '1,234.00' (string, no AED suffix)
# Template still appends “ AED”.
# ──────────────────────────────────────────────────────────────
def round_dirham(val) -> str:
    return f"{round(flt(val or 0)):,.0f}.00"

# ──────────────────────────────────────────────────────────────
# Fallbacks for Projects Settings
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
    try:
        doc = frappe.get_cached_doc("Projects Settings", None)
    except Exception:
        doc = frappe._dict()
    return frappe._dict({k: doc.get(k) or PROJECTS_DEFAULTS[k] for k in PROJECTS_DEFAULTS})

# ──────────────────────────────────────────────────────────────
# Date helpers
# ──────────────────────────────────────────────────────────────
def _server_today():
    return getdate(today())

def _fy_start(d):
    fy = frappe.db.get_value(
        "Fiscal Year",
        {"year_start_date": ("<=", d), "year_end_date": (">=", d)},
        "year_start_date",
    )
    return fy or getdate(f"{d.year}-01-01")

# ──────────────────────────────────────────────────────────────
# Main Digest class
# ──────────────────────────────────────────────────────────────
class PitstopEmailDigest(CoreDigest):

    # -----------------------------------------------------------
    def _as_of_date(self):
        return getdate(self.as_of_date) if getattr(self, "as_of_date", None) else _server_today()

    # -----------------------------------------------------------
    def get_msg_html(self):
        ctx = frappe._dict()
        ctx.update(self.__dict__)
        self.set_title(ctx)
        self.set_style(ctx)
        ctx.title = _("Pitstop Daily Matrix")

        ctx.kpi_table      = self._mini_kpi_table()
        ctx.insights_table = self._expanded_kpi_table()
        ctx.branch_revenue = self._branch_revenue()  # values already rounded

        return frappe.render_template(
            "pitstop_email_digest/doctype/pitstop_email_digest/templates/default.html",
            ctx, is_path=True
        )

    # =================  MINI KPI (RO + Revenue)  ======================
    def _mini_kpi_table(self):
        d   = self._as_of_date()
        m0  = getdate(f"{d.year}-{d.month:02d}-01")
        y0  = _fy_start(d)

        def _vals(start, end):
            ro = frappe.db.count(
                "Project",
                {"ready_to_close": 1,
                 "status": ("not in", ("Draft", "Cancelled")),
                 "final_invoice_date": ["between", (start, end)]},
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
                """, (start, end)
            )[0][0] or 0
            return ro, round_dirham(rev)

        d_ro, d_rev = _vals(d, d)
        m_ro, m_rev = _vals(m0, d)
        y_ro, y_rev = _vals(y0, d)

        return [
            ["Metric",     "Daily", "MTD",  "YTD"],
            ["No. of ROs", d_ro,    m_ro,   y_ro],
            ["Revenue",    d_rev,   m_rev,  y_rev],
        ]

    # =================  EXPANDED KPI TABLE  ===========================
    def _expanded_kpi_table(self):
        d   = self._as_of_date()
        m0  = getdate(f"{d.year}-{d.month:02d}-01")
        y0  = _fy_start(d)

        daily = self._build_kpi(d,  d)
        mtd   = self._build_kpi(m0, d)
        ytd   = self._build_kpi(y0, d)

        int_fmt = lambda v: f"{int(v):,}"
        ratio   = lambda row: f"1 : {flt(row.parts_to_labour):,.2f}"

        return [
            ["Metric",               "Daily",                         "MTD",                          "YTD"],
            ["No. of ROs",           int_fmt(daily.ro_count),         int_fmt(mtd.ro_count),          int_fmt(ytd.ro_count)],
            ["Labour Hours",         round_dirham(daily.labour_hours), round_dirham(mtd.labour_hours), round_dirham(ytd.labour_hours)],
            ["Revenue",              round_dirham(daily.revenue),     round_dirham(mtd.revenue),      round_dirham(ytd.revenue)],
            ["Labour Amount",        round_dirham(daily.labour_amount),round_dirham(mtd.labour_amount),round_dirham(ytd.labour_amount)],
            ["Parts Amount",         round_dirham(daily.parts_amount), round_dirham(mtd.parts_amount), round_dirham(ytd.parts_amount)],
            ["Effective Labour Rate",round_dirham(daily.labour_rate),  round_dirham(mtd.labour_rate),  round_dirham(ytd.labour_rate)],
            ["Hours per RO",         round_dirham(daily.hours_per_ro), round_dirham(mtd.hours_per_ro), round_dirham(ytd.hours_per_ro)],
            ["Parts : Labour Ratio", ratio(daily),                    ratio(mtd),                     ratio(ytd)],
        ]

    # ------------------------------------------------------------------
    # Branch-wise revenue (rounded strings)
    # ------------------------------------------------------------------
    def _branch_revenue(self):
        d  = self._as_of_date()
        y0 = _fy_start(d)
        m0 = getdate(f"{d.year}-{d.month:02d}-01")
        ps = get_projects_settings()

        def _rev(branch, start, end):
            return frappe.db.sql(
                """
                SELECT COALESCE(SUM(i.base_net_amount),0)
                  FROM `tabSales Invoice` inv
                  JOIN `tabSales Invoice Item` i ON i.parent = inv.name
                  JOIN `tabProject` p            ON p.name   = i.project
                 WHERE inv.docstatus = 1
                   AND p.ready_to_close = 1
                   AND p.branch = %s
                   AND p.final_invoice_date BETWEEN %s AND %s
                   AND i.item_code != %s
                """, (branch, start, end, ps.insurance_excess_item)
            )[0][0] or 0

        branches = frappe.get_all(
            "Project",
            filters={
                "ready_to_close": 1,
                "status": ("not in", ("Draft", "Cancelled")),
                "final_invoice_date": [">=", y0],
            },
            distinct=True,
            pluck="branch",
        )
        branches = sorted([b for b in branches if b])

        od, td, tm, ty = OrderedDict(), 0, 0, 0
        for br in branches:
            dv = _rev(br, d, d)
            mv = _rev(br, m0, d)
            yv = _rev(br, y0, d)
            od[br] = {"daily": round_dirham(dv), "mtd": round_dirham(mv), "ytd": round_dirham(yv)}
            td += dv; tm += mv; ty += yv

        od["TOTAL"] = {"daily": round_dirham(td), "mtd": round_dirham(tm), "ytd": round_dirham(ty)}
        return od

    # ------------------------------------------------------------------
    # Heavy KPI builder (unchanged)
    # ------------------------------------------------------------------
    def _build_kpi(self, start_date, end_date):
        ps = get_projects_settings()

        ro_count = frappe.db.count(
            "Project",
            {
                "ready_to_close": 1,
                "status": ("not in", ("Draft", "Cancelled")),
                "final_invoice_date": ["between", (start_date, end_date)],
            },
        )

        rows = frappe.db.sql(
            """
            SELECT
                i.item_code, i.qty, i.uom, i.stock_uom, i.conversion_factor,
                i.item_group, i.is_stock_item, i.base_net_amount AS net_amount
            FROM `tabSales Invoice Item` i
            JOIN `tabSales Invoice` inv ON inv.name = i.parent AND inv.docstatus = 1
            JOIN `tabProject`       p   ON p.name  = i.project
            WHERE p.ready_to_close            = 1
              AND p.final_invoice_date BETWEEN %s AND %s
              AND i.item_code                != %s
            """,
            (start_date, end_date, ps.insurance_excess_item),
            as_dict=True,
        )

        mats   = get_item_group_subtree(ps.materials_item_group)   or []
        lubes  = get_item_group_subtree(ps.lubricants_item_group)  or []
        cons   = get_item_group_subtree(ps.consumables_item_group) or []
        paints = get_item_group_subtree(ps.paint_item_group)       or []
        subs   = get_item_group_subtree(ps.sublet_item_group)      or []

        revenue = labour_amt = parts_amt = sold_time = 0

        for r in rows:
            revenue += r.net_amount

            # Parts bucket
            if (
                r.uom != "Hour" or r.stock_uom != "Hour"
                or r.item_group in mats + lubes + cons + paints + subs
            ):
                parts_amt += r.net_amount
            else:
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

    # ------------------------------------------------------------------
    # Scheduler helpers
    # ------------------------------------------------------------------
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

# Hooks aliases
auto_send_daily  = PitstopEmailDigest.auto_send_daily
auto_send_weekly = PitstopEmailDigest.auto_send_weekly

@frappe.whitelist()
def get_digest_msg(name):
    return frappe.get_doc("Pitstop Email Digest", name).get_msg_html()
