# Copyright (c) 2025, QCS
# License: GPL-v3

import frappe
from frappe import _
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from erpnext.accounts.utils import get_balance_on
from erpnext.setup.doctype.email_digest.email_digest import (
    EmailDigest as CoreDigest,
)
from collections import OrderedDict

from frappe.utils import (
    now_datetime,
    today,
    fmt_money,
    get_link_to_report   #  ← add this
)


# --------------------------------------------------------------------------
# Helper – dates for FY / month start
# --------------------------------------------------------------------------
def _today():
    return frappe.utils.getdate(frappe.utils.today())


def _fiscal_year_start(today):
    fy_start = frappe.db.get_value(
        "Fiscal Year",
        {"year_start_date": ("<=", today), "year_end_date": (">=", today)},
        "year_start_date",
    )
    return fy_start or frappe.utils.getdate(f"{today.year}-01-01")


# --------------------------------------------------------------------------
# Main class – extends core EmailDigest
# --------------------------------------------------------------------------
class PitstopEmailDigest(CoreDigest):
    """
    Thin subclass of ERPNext Email Digest that injects:

      • Annual Income / Expense cards
      • Workshop KPI table (RO + Revenue)
      • Branch-wise revenue matrix
    """

    # ------------------------------------------------------------------ #
    # Public API for “View Now” button
    # ------------------------------------------------------------------ #


    # ------------------------------------------------------------------ #
    # HTML builder
    # ------------------------------------------------------------------ #
    def get_msg_html(self):
        ctx = frappe._dict()
        ctx.update(self.__dict__)  # base attributes

        # titles / style from parent:
        self.set_title(ctx)
        self.set_style(ctx)
        ctx.title = _("Pitstop Daily KPIs")

        # ---------- KPI cards -----------------------------------------
        ctx.cards = [
            self._annual_card("Income", _("Annual Income")),
            self._annual_card("Expense", _("Annual Expense")),
        ]

        # ---------- tables --------------------------------------------
        ctx.kpi_table = self._get_workshop_kpi_table()
        ctx.branch_revenue = self._get_branch_revenue()

        # ---------- render --------------------------------------------
        return frappe.render_template(
            "pitstop_email_digest/doctype/pitstop_email_digest/templates/default.html",
            ctx,
            is_path=True,
        )

    # ------------------------------------------------------------------ #
    # Annual cards
    # ------------------------------------------------------------------ #
    def _annual_card(self, root_type: str, label: str):
        value = self._root_balance(root_type)
        link = get_link_to_report("Profit and Loss Statement", label=label)
        return frappe._dict(label=link, value=frappe.format_value(value, "Currency"))

    def _root_balance(self, root_type: str):
        today = _today()
        fy_start = _fiscal_year_start(today)
        accounts = frappe.get_all(
            "Account",
            filters={
                "root_type": root_type,
                "is_group": 0,
                "company": self.company,
            },
            pluck="name",
        )
        bal = 0
        for acc in accounts:
            bal += get_balance_on(acc, date=today) - get_balance_on(
                acc, date=fy_start - timedelta(days=1)
            )
        return bal

    # ------------------------------------------------------------------ #
    # Workshop KPI table (RO count + revenue)
    # ------------------------------------------------------------------ #
    def _get_workshop_kpi_table(self):
        today = _today()
        fy_start = _fiscal_year_start(today)
        m_start = frappe.utils.getdate(f"{today.year}-{today.month:02d}-01")

        def _vals(start, end):
            ro = frappe.db.count(
                "Sales Invoice",
                filters={
                    "docstatus": 1,
                    "posting_date": ["between", (start, end)],
                },
            )
            rev = frappe.db.sql(
                """
                SELECT COALESCE(SUM(net_total),0)
                FROM `tabSales Invoice`
                WHERE docstatus=1
                  AND posting_date BETWEEN %s AND %s
                """,
                (start, end),
            )[0][0] or 0
            return ro, rev

        y_ro, y_rev = _vals(fy_start, today)
        m_ro, m_rev = _vals(m_start, today)
        d_ro, d_rev = _vals(today, today)

        fmt = frappe.format_value
        return [
            ["Desc", "Daily", "MTD", "YTD"],
            ["No. of ROs", d_ro, m_ro, y_ro],
            ["Revenue Booked", fmt(d_rev, "Currency"), fmt(m_rev, "Currency"), fmt(y_rev, "Currency")],
        ]

    # ------------------------------------------------------------------ #
    # Branch-wise revenue matrix
    # ------------------------------------------------------------------ #
    def _get_branch_revenue(self):
        """OrderedDict {branch: {daily, mtd, ytd}}"""
        today = _today()
        fy_start = _fiscal_year_start(today)
        m_start = frappe.utils.getdate(f"{today.year}-{today.month:02d}-01")

        def _rev(branch, start, end):
            return (
                frappe.db.sql(
                    """
                    SELECT COALESCE(SUM(net_total),0)
                    FROM `tabSales Invoice`
                    WHERE docstatus=1
                      AND branch=%s
                      AND posting_date BETWEEN %s AND %s
                    """,
                    (branch, start, end),
                )[0][0]
                or 0
            )

        branches = frappe.get_all(
            "Sales Invoice",
            filters={"docstatus": 1, "posting_date": [">=", fy_start]},
            distinct=True,
            pluck="branch",
        )
        branches.sort()
        data = OrderedDict()
        for br in branches:
            data[br] = {
                "daily": _rev(br, today, today),
                "mtd": _rev(br, m_start, today),
                "ytd": _rev(br, fy_start, today),
            }
        return data

    # ------------------------------------------------------------------ #
    # Scheduler hooks
    # ------------------------------------------------------------------ #
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

@frappe.whitelist()
def get_digest_msg(name):
    return frappe.get_doc("Pitstop Email Digest", name).get_msg_html()