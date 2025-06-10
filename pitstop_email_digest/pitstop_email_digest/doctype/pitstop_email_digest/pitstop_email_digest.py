# Copyright © 2025, QCS
# License: GPL-3.0

import frappe
from frappe import _
from collections import OrderedDict
from frappe.utils import getdate, today, flt
from erpnext.setup.doctype.email_digest.email_digest import EmailDigest as CoreDigest
from erpnext.setup.doctype.item_group.item_group import get_item_group_subtree
from erpnext.stock.doctype.item.item import convert_item_uom_for

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
def round_dirham(val) -> str:
    """Return '1,234.00' (two trailing zeros, no AED suffix)."""
    return f"{round(flt(val or 0)):,.0f}.00"

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
# Main Digest
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

        ctx.insights_table = self._expanded_kpi_table()
        # ctx.kpi_table      = self._mini_kpi_table()
        # ctx.branch_revenue = self._branch_revenue()

        return frappe.render_template(
            "pitstop_email_digest/doctype/pitstop_email_digest/templates/default.html",
            ctx, is_path=True
        )

    # ------------------------------------------------------------------
    #  KPI bucket for any span
    # ------------------------------------------------------------------
    def _build_kpi(self, start_date, end_date):
        ps = get_projects_settings()

        rows = frappe.db.sql(
            """
            SELECT
                i.item_code,
                i.qty, i.uom, i.stock_uom, i.conversion_factor,
                i.item_group, i.is_stock_item,
                i.base_net_amount AS net_amount,
                i.project
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

        revenue = labour_amt = parts_amt = cons_amt = sold_time = 0
        ro_projects = set()

        for r in rows:
            revenue += r.net_amount
            ro_projects.add(r.project)

            if r.uom == "Hour" or r.stock_uom == "Hour":
                labour_amt += r.net_amount
            else:
                if (
                    r.is_stock_item
                    or r.item_group in mats
                    or r.item_group in lubes
                    or r.item_group in paints
                    or r.item_group in subs
                ):
                    parts_amt += r.net_amount
                else:
                    cons_amt += r.net_amount

            hrs = convert_item_uom_for(
                r.qty, r.item_code, r.uom, "Hour",
                conversion_factor=(r.conversion_factor if r.stock_uom == "Hour" else None),
                null_if_not_convertible=True,
            )
            if hrs is not None:
                sold_time += flt(hrs)

        ro_count     = len(ro_projects)
        labour_rate  = labour_amt / sold_time if sold_time else 0
        hours_per_ro = sold_time / ro_count   if ro_count else 0
        parts_ratio  = parts_amt / labour_amt if labour_amt else 0

        return frappe._dict(
            ro_count        = ro_count,
            labour_hours    = sold_time,
            revenue         = revenue,
            labour_amount   = labour_amt,
            parts_amount    = parts_amt,
            cons_amount     = cons_amt,
            labour_rate     = labour_rate,
            hours_per_ro    = hours_per_ro,
            parts_to_labour = parts_ratio,
        )

    # ------------------------------------------------------------------
    # Extended KPI table (Daily / MTD / YTD) – includes Consumables row
    # ------------------------------------------------------------------
    def _expanded_kpi_table(self):
        today = self._as_of_date()
        m0    = getdate(f"{today.year}-{today.month:02d}-01")
        y0    = _fy_start(today)

        daily = self._build_kpi(today,  today)
        mtd   = self._build_kpi(m0,     today)
        ytd   = self._build_kpi(y0,     today)

        f2   = lambda v: f"{flt(v):,.2f}"
        i0   = lambda v: f"{int(v):,}"
        pct  = lambda row: f"1 : {f2(row.parts_to_labour)}"

        return [
            ["Details",               "Daily",                          "MTD",                           "YTD"],
            ["No. of ROs",           i0(daily.ro_count),               i0(mtd.ro_count),                i0(ytd.ro_count)],
            ["Labour Hours",         round_dirham(daily.labour_hours),  round_dirham(mtd.labour_hours),  round_dirham(ytd.labour_hours)],
            ["Revenue",              round_dirham(daily.revenue),       round_dirham(mtd.revenue),       round_dirham(ytd.revenue)],
            ["Labour Amount",        round_dirham(daily.labour_amount), round_dirham(mtd.labour_amount), round_dirham(ytd.labour_amount)],
            ["Parts Amount",         round_dirham(daily.parts_amount),  round_dirham(mtd.parts_amount),  round_dirham(ytd.parts_amount)],
            ["Consumables & Others", round_dirham(daily.cons_amount),   round_dirham(mtd.cons_amount),   round_dirham(ytd.cons_amount)],
            ["Effective Labour Rate",round_dirham(daily.labour_rate),   round_dirham(mtd.labour_rate),   round_dirham(ytd.labour_rate)],
            ["Hours per RO",         round_dirham(daily.hours_per_ro),  round_dirham(mtd.hours_per_ro),  round_dirham(ytd.hours_per_ro)],
            ["Parts : Labour Ratio", pct(daily),                        pct(mtd),                        pct(ytd)],
        ]

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
