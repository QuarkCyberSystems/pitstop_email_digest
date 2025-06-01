# Copyright (c) 2025, QCS
# License: GPL-v3

import frappe
from frappe import _
from datetime import timedelta
from collections import OrderedDict
from erpnext.accounts.utils import get_balance_on
from erpnext.setup.doctype.email_digest.email_digest import EmailDigest as CoreDigest
from frappe.utils import getdate, today, get_link_to_report

# ──────────────────────────────────────────────────────────────
# Helpers – dates
# ──────────────────────────────────────────────────────────────
def _system_today():
    """Server date (YYYY-MM-DD) → datetime.date"""
    return getdate(today())


def _fiscal_year_start(d):
    fy_start = frappe.db.get_value(
        "Fiscal Year",
        {"year_start_date": ("<=", d), "year_end_date": (">=", d)},
        "year_start_date",
    )
    return fy_start or getdate(f"{d.year}-01-01")


# ──────────────────────────────────────────────────────────────
# Main class
# ──────────────────────────────────────────────────────────────
class PitstopEmailDigest(CoreDigest):
    """
    Custom digest that supports an optional **as_of_date** field
    on the DocType. If filled, all KPIs are calculated up to that
    date; otherwise the current server date is used.
    """

    # ------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------ #
    def _as_of_date(self):
        """Return the effective 'today' date for this instance."""
        return getdate(self.as_of_date) if getattr(self, "as_of_date", None) else _system_today()

    # ------------------------------------------------------ #
    # HTML builder
    # ------------------------------------------------------ #
    def get_msg_html(self):
        ctx = frappe._dict()
        ctx.update(self.__dict__)

        self.set_title(ctx)
        self.set_style(ctx)
        ctx.title = _("Pitstop Daily Matrix")

        ctx.kpi_table       = self._get_workshop_kpi_table()
        ctx.insights_table  = self._get_expanded_kpi_table()
        ctx.branch_revenue  = self._get_branch_revenue()

        return frappe.render_template(
            "pitstop_email_digest/doctype/pitstop_email_digest/templates/default.html",
            ctx,
            is_path=True,
        )

    # ------------------------------------------------------ #
    # 1. Simple KPI (ROs + Revenue)
    # ------------------------------------------------------ #
    def _get_workshop_kpi_table(self):
        d        = self._as_of_date()
        fy_start = _fiscal_year_start(d)
        m_start  = getdate(f"{d.year}-{d.month:02d}-01")

        def _vals(start, end):
            ro = frappe.db.count(
                "Sales Invoice",
                {"docstatus": 1, "posting_date": ["between", (start, end)]},
            )
            rev = frappe.db.sql(
                """SELECT COALESCE(SUM(net_total),0)
                     FROM `tabSales Invoice`
                    WHERE docstatus=1
                      AND posting_date BETWEEN %s AND %s""",
                (start, end),
            )[0][0] or 0
            return ro, rev

        y_ro, y_rev = _vals(fy_start, d)
        m_ro, m_rev = _vals(m_start, d)
        d_ro, d_rev = _vals(d, d)

        money2 = lambda v: f"{v:,.2f}"

        return [
            ["Desc", "Daily", "MTD", "YTD"],
            ["No. of ROs",     d_ro,          m_ro,          y_ro],
            ["Revenue Booked", money2(d_rev), money2(m_rev), money2(y_rev)],
        ]

    # ------------------------------------------------------ #
    # 2. Expanded KPI matrix (two-decimal)
    # ------------------------------------------------------ #
    def _get_expanded_kpi_table(self):
        d        = self._as_of_date()
        fy_start = _fiscal_year_start(d)
        m_start  = getdate(f"{d.year}-{d.month:02d}-01")

        def get_vals(start_date, end_date):
            ro_count = frappe.db.count(
                "Sales Invoice",
                {"docstatus": 1, "posting_date": ["between", (start_date, end_date)]},
            )

            labour = frappe.db.sql(
                """
                SELECT COALESCE(SUM(qty),0)  AS hrs,
                       COALESCE(SUM(amount),0) AS amt
                  FROM `tabSales Invoice Item`
                 WHERE item_group = 'Hourly Labour'
                   AND parent IN (
                       SELECT name FROM `tabSales Invoice`
                        WHERE docstatus = 1
                          AND posting_date BETWEEN %s AND %s
                 )
                """,
                (start_date, end_date),
                as_dict=True,
            )[0]

            parts_amt = frappe.db.sql(
                """
                SELECT COALESCE(SUM(amount),0)
                  FROM `tabSales Invoice Item`
                 WHERE item_group IN (
                       SELECT name FROM `tabItem Group`
                        WHERE parent_item_group = 'Parts'
                 )
                   AND parent IN (
                       SELECT name FROM `tabSales Invoice`
                        WHERE docstatus = 1
                          AND posting_date BETWEEN %s AND %s
                 )
                """,
                (start_date, end_date),
            )[0][0] or 0

            revenue = frappe.db.sql(
                """
                SELECT COALESCE(SUM(net_total),0)
                  FROM `tabSales Invoice`
                 WHERE docstatus = 1
                   AND posting_date BETWEEN %s AND %s
                """,
                (start_date, end_date),
            )[0][0] or 0

            hrs, amt = labour.hrs or 0, labour.amt or 0
            ratio = round(parts_amt / amt, 2) if amt else 0

            return {
                "ro_count":        ro_count,
                "labour_hours":    hrs,
                "labour_amount":   amt,
                "parts_amount":    parts_amt,
                "revenue":         revenue,
                "labour_rate":     (amt / hrs) if hrs else 0,
                "hours_per_ro":    (hrs / ro_count) if ro_count else 0,
                "parts_to_labour": f"1 : {ratio}",
            }

        daily = get_vals(d,        d)
        mtd   = get_vals(m_start,  d)
        ytd   = get_vals(fy_start, d)

        fmt2 = lambda v: f"{v:,.2f}" if isinstance(v, (int, float)) else v

        rows = [["Metric", "Daily", "MTD", "YTD"]]
        metrics = [
            ("No. of Repair Orders",  "ro_count"),
            ("Labour Hours",          "labour_hours"),
            ("Revenue",               "revenue"),
            ("Labour Amount",         "labour_amount"),
            ("Parts Amount",          "parts_amount"),
            ("Effective Labour Rate", "labour_rate"),
            ("Hours per RO",          "hours_per_ro"),
            ("Parts : Labour Ratio",  "parts_to_labour"),
        ]

        for label, key in metrics:
            rows.append([label, fmt2(daily[key]), fmt2(mtd[key]), fmt2(ytd[key])])

        return rows

    # ------------------------------------------------------ #
    # 3. Branch-wise revenue (totals row)
    # ------------------------------------------------------ #
    def _get_branch_revenue(self):
        d        = self._as_of_date()
        fy_start = _fiscal_year_start(d)
        m_start  = getdate(f"{d.year}-{d.month:02d}-01")

        def _rev(branch, start, end):
            return frappe.db.sql(
                """
                SELECT COALESCE(SUM(net_total),0)
                  FROM `tabSales Invoice`
                 WHERE docstatus = 1
                   AND branch = %s
                   AND posting_date BETWEEN %s AND %s
                """,
                (branch, start, end),
            )[0][0] or 0

        branches = frappe.get_all(
            "Sales Invoice",
            filters={"docstatus": 1, "posting_date": [">=", fy_start]},
            distinct=True,
            pluck="branch",
        )
        branches.sort()

        od = OrderedDict()
        td = tm = ty = 0

        for br in branches:
            dv = _rev(br, d,        d)
            mv = _rev(br, m_start,  d)
            yv = _rev(br, fy_start, d)

            od[br] = {"daily": dv, "mtd": mv, "ytd": yv}
            td += dv; tm += mv; ty += yv

        od["TOTAL"] = {"daily": td, "mtd": tm, "ytd": ty}
        return od

    # ------------------------------------------------------ #
    # 4. Scheduler helpers
    # ------------------------------------------------------ #
    @staticmethod
    def _auto_send(freq):
        for d in frappe.get_all(
            "Pitstop Email Digest",
            filters={"enabled": 1, "frequency": freq},
            pluck="name",
        ):
            frappe.get_doc("Pitstop Email Digest", d).send()

    @staticmethod
    def auto_send_daily():
        PitstopEmailDigest._auto_send("Daily")

    @staticmethod
    def auto_send_weekly():
        PitstopEmailDigest._auto_send("Weekly")


# ──────────────────────────────────────────────────────────────
# Aliases for scheduler dotted paths
# ──────────────────────────────────────────────────────────────
auto_send_daily  = PitstopEmailDigest.auto_send_daily
auto_send_weekly = PitstopEmailDigest.auto_send_weekly


# ──────────────────────────────────────────────────────────────
# Desk preview helper
# ──────────────────────────────────────────────────────────────
@frappe.whitelist()
def get_digest_msg(name):
    return frappe.get_doc("Pitstop Email Digest", name).get_msg_html()
