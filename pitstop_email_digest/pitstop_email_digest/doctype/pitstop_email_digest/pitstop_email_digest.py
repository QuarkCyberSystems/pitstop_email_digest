# Copyright (c) 2025, QCS
# License: GPL-v3

import frappe
from frappe import _
from datetime import timedelta
from collections import OrderedDict

from erpnext.accounts.utils import get_balance_on
from erpnext.setup.doctype.email_digest.email_digest import EmailDigest as CoreDigest

from frappe.utils import (
    getdate,
    today,
    now_datetime,
    fmt_money,
    get_link_to_report,
)

# ──────────────────────────────────────────────────────────────
# Helper – dates
# ──────────────────────────────────────────────────────────────
def _today():
    return getdate(today())


def _fiscal_year_start(d):
    fy_start = frappe.db.get_value(
        "Fiscal Year",
        {"year_start_date": ("<=", d), "year_end_date": (">=", d)},
        "year_start_date",
    )
    # fall back to 1 Jan of the current year
    return fy_start or getdate(f"{d.year}-01-01")


# ──────────────────────────────────────────────────────────────
# Main class – extends ERPNext EmailDigest
# ──────────────────────────────────────────────────────────────
class PitstopEmailDigest(CoreDigest):
    """
    Adds Pitstop-specific cards and KPI tables to the standard
    ERPNext Email Digest.
    """

    # ------------------------------------------------------ #
    # Public API for “View now” button
    # ------------------------------------------------------ #

    # ------------------------------------------------------ #
    # HTML builder
    # ------------------------------------------------------ #
    def get_msg_html(self):
        ctx = frappe._dict()
        ctx.update(self.__dict__)          # inherit parent attrs

        # -------------------------------------------------- #
        # titles / colours from parent
        # -------------------------------------------------- #
        self.set_title(ctx)
        self.set_style(ctx)
        ctx.title = _("Pitstop Daily Matrix")

        # ----------------- KPI cards ---------------------- #
        #ctx.cards = [
        #    self._annual_card("Income",  _("Annual Income")),
        #   self._annual_card("Expense", _("Annual Expense")),
        #]

        # ----------------- tables ------------------------- #
        #ctx.kpi_table       = self._get_workshop_kpi_table()
        ctx.insights_table  = self._get_expanded_kpi_table()
        ctx.branch_revenue  = self._get_branch_revenue()

        # ----------------- render ------------------------- #
        return frappe.render_template(
            "pitstop_email_digest/doctype/pitstop_email_digest/templates/default.html",
            ctx,
            is_path=True,
        )

    # ------------------------------------------------------ #
    #     1. Annual Income / Expense cards
    # ------------------------------------------------------ #
    def _annual_card(self, root_type: str, label: str):
        value = self._root_balance(root_type)
        link  = get_link_to_report("Profit and Loss Statement", label=label)
        return frappe._dict(label=link, value=frappe.format_value(value, "Currency"))

    def _root_balance(self, root_type: str):
        d        = _today()
        fy_start = _fiscal_year_start(d)

        accounts = frappe.get_all(
            "Account",
            filters={"root_type": root_type, "is_group": 0, "company": self.company},
            pluck="name",
        )

        bal = 0
        for acc in accounts:
            bal += get_balance_on(acc, date=d) - get_balance_on(acc, date=fy_start - timedelta(days=1))
        return bal

    # ------------------------------------------------------ #
    #     2. Original KPI table (ROs + Revenue only)
    # ------------------------------------------------------ #
    def _get_workshop_kpi_table(self):
        d        = _today()
        fy_start = _fiscal_year_start(d)
        m_start  = getdate(f"{d.year}-{d.month:02d}-01")

        def _vals(start, end):
            ro  = frappe.db.count("Sales Invoice", {"docstatus": 1, "posting_date": ["between", (start, end)]})
            rev = frappe.db.sql("""
                    SELECT COALESCE(SUM(net_total),0)
                      FROM `tabSales Invoice`
                     WHERE docstatus=1
                       AND posting_date BETWEEN %s AND %s
                """, (start, end))[0][0] or 0
            return ro, rev

        y_ro, y_rev = _vals(fy_start, d)
        m_ro, m_rev = _vals(m_start, d)
        d_ro, d_rev = _vals(d, d)

        fmt = frappe.format_value
        return [
            ["Desc",           "Daily",                 "MTD",                "YTD"],
            ["No. of ROs",     d_ro,                    m_ro,                 y_ro],
            ["Revenue Booked", fmt(d_rev, "Currency"),  fmt(m_rev, "Currency"), fmt(y_rev, "Currency")],
        ]

    # ------------------------------------------------------ #
    #     3. **NEW** expanded KPI table (labour, parts, etc.)
    # ------------------------------------------------------ #
    def _get_expanded_kpi_table(self):
        d        = _today()
        fy_start = _fiscal_year_start(d)
        m_start  = getdate(f"{d.year}-{d.month:02d}-01")

        # ---------- helper --------------------------------------------------
        def get_values(start_date, end_date):
            ro_count = frappe.db.count("Sales Invoice", {
                "docstatus": 1,
                "posting_date": ["between", (start_date, end_date)],
            })

            labour = frappe.db.sql("""
                SELECT COALESCE(SUM(qty),0)  AS hrs,
                       COALESCE(SUM(amount),0) AS amt
                  FROM `tabSales Invoice Item`
                 WHERE item_group = 'Hourly Labour'
                   AND parent IN (
                       SELECT name FROM `tabSales Invoice`
                        WHERE docstatus = 1
                          AND posting_date BETWEEN %s AND %s
                 )
            """, (start_date, end_date), as_dict=True)[0]

            parts_amt = frappe.db.sql("""
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
            """, (start_date, end_date))[0][0] or 0

            revenue = frappe.db.sql("""
                SELECT COALESCE(SUM(net_total),0)
                  FROM `tabSales Invoice`
                 WHERE docstatus = 1
                   AND posting_date BETWEEN %s AND %s
            """, (start_date, end_date))[0][0] or 0

            hrs = labour.hrs or 0
            amt = labour.amt or 0
            ratio = round(parts_amt / amt, 2) if amt else 0

            return {
                "ro_count":        ro_count,
                "labour_hours":    hrs,
                "labour_amount":   amt,
                "parts_amount":    parts_amt,
                "revenue":         revenue,
                "labour_rate":     round(amt / hrs, 2) if hrs else 0,
                "hours_per_ro":    round(hrs / ro_count, 2) if ro_count else 0,
                "parts_to_labour": f"1 : {ratio}",
            }

        # ---------- three periods -----------------------------------------
        daily = get_values(d,        d)
        mtd   = get_values(m_start,  d)
        ytd   = get_values(fy_start, d)

        def fmt_if_money(v):
            return frappe.format_value(v, "Currency") if isinstance(v, (int, float)) and abs(v) >= 1 else v

        rows = [["Metric", "Daily", "MTD", "YTD"]]          # <-- NEW column order
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
            rows.append([
                label,
                fmt_if_money(daily.get(key)),
                fmt_if_money(mtd.get(key)),
                fmt_if_money(ytd.get(key)),
            ])

        return rows

    # ------------------------------------------------------ #
    #     4. Branch-wise Revenue matrix
    # ------------------------------------------------------ #
    def _get_branch_revenue(self):
        d        = _today()
        fy_start = _fiscal_year_start(d)
        m_start  = getdate(f"{d.year}-{d.month:02d}-01")

        def _rev(branch, start, end):
            return frappe.db.sql("""
                SELECT COALESCE(SUM(net_total),0)
                  FROM `tabSales Invoice`
                 WHERE docstatus=1
                   AND branch=%s
                   AND posting_date BETWEEN %s AND %s
            """, (branch, start, end))[0][0] or 0

        branches = frappe.get_all(
            "Sales Invoice",
            filters={"docstatus": 1, "posting_date": [">=", fy_start]},
            pluck="branch",
            distinct=True,
        )
        branches.sort()

        od = OrderedDict()
        for br in branches:
            od[br] = {
                "daily": _rev(br, d,       d),
                "mtd":   _rev(br, m_start, d),
                "ytd":   _rev(br, fy_start, d),
            }
        return od

    # ------------------------------------------------------ #
    #     5. Scheduler hooks
    # ------------------------------------------------------ #
    def _auto_send(freq):
        for d in frappe.get_all(
            "Pitstop Email Digest", filters={"enabled": 1, "frequency": freq}, pluck="name"
        ):
            frappe.get_doc("Pitstop Email Digest", d).send()

    @staticmethod
    def auto_send_daily():
        PitstopEmailDigest._auto_send("Daily")

    @staticmethod
    def auto_send_weekly():
        PitstopEmailDigest._auto_send("Weekly")


@frappe.whitelist()
def get_digest_msg(name):
    return frappe.get_doc("Pitstop Email Digest", name).get_msg_html()
