# Copyright © 2025, QCS
# License: GPL-3.0

import frappe
from frappe import _
from collections import OrderedDict
from frappe.utils import getdate, today, flt, add_days
from erpnext.setup.doctype.email_digest.email_digest import EmailDigest as CoreDigest
from erpnext.setup.doctype.item_group.item_group import get_item_group_subtree
from erpnext.stock.doctype.item.item import convert_item_uom_for

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
def round_dirham(val) -> str:
    return f"{round(flt(val or 0)):,.0f}.00"

PROJECTS_DEFAULTS = {
    "insurance_excess_item":  "INS-EXS",
    "materials_item_group":   "Parts",
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

    def _as_of_date(self):
        return getdate(self.as_of_date) if getattr(self, "as_of_date", None) else _server_today()

    def get_msg_html(self, custom_method=None):
        if not custom_method:
            ctx = frappe._dict()
            ctx.update(self.__dict__)
            self.set_title(ctx)
            self.set_style(ctx)
            ctx.title = _("Pitstop Daily Matrix")
            ctx.insights_table = self._expanded_kpi_table()
            return frappe.render_template(
                "pitstop_email_digest/doctype/pitstop_email_digest/templates/default.html",
                ctx, is_path=True
            )
        else:
            # Custom method is defined, so we call it
            try:
                return frappe.get_attr(custom_method)(self, show_html=True)
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), _("Error in custom method HTML for Pitstop Email Digest"))
                return f"<p>Error executing custom method: {str(e)}</p>"

    # ------------------------------------------------------------------
    # KPI bucket for any span
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
            LEFT JOIN `tabProject`      p ON p.name  = i.project
            WHERE inv.posting_date BETWEEN %s AND %s
            """,
            (start_date, end_date),
            as_dict=True,
        )

        # Stock / parts trees
        mats   = get_item_group_subtree(ps.materials_item_group)   or []
        lubes  = get_item_group_subtree(ps.lubricants_item_group)  or []
        cons   = get_item_group_subtree(ps.consumables_item_group) or []
        paints = get_item_group_subtree(ps.paint_item_group)       or []
        subs   = get_item_group_subtree(ps.sublet_item_group)      or []

        # Labour extra groups
        lumpsum_group   = get_item_group_subtree("Lumpsum Labour") or ["Lumpsum Labour"]
        autocare_group  = get_item_group_subtree("AutoCare Services") or ["AutoCare Services"]
        labour_groups   = set(lumpsum_group + autocare_group)

        revenue = labour_amt = parts_amt = cons_amt = sold_time = 0
        ro_projects = set()

        for r in rows:
            revenue += r.net_amount
            if r.project:
                ro_projects.add(r.project)

            # ---------------- Labour bucket --------------------------
            if (
                r.uom == "Hour"
                or r.stock_uom == "Hour"
                or r.item_group in labour_groups
            ):
                labour_amt += r.net_amount

            # ---------------- Parts bucket ---------------------------
            elif (
                #r.is_stock_item
                r.item_group in mats
                or r.item_group in paints
                #or r.item_group in subs
            ):
                parts_amt += r.net_amount

            # ---------------- Consumables & Others -------------------
            elif (
                r.item_group in cons
                or r.item_group in lubes 
                or r.item_group in subs
            ):
                cons_amt += r.net_amount

            # Hour conversion
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
    # Extended KPI table (includes Consumables row)
    # ------------------------------------------------------------------
    def _expanded_kpi_table(self):
        today = self._as_of_date()
        m0    = getdate(f"{today.year}-{today.month:02d}-01")
        y0    = _fy_start(today)

        daily = self._build_kpi(today,  today)
        mtd   = self._build_kpi(m0,     today)
        ytd   = self._build_kpi(y0,     today)

        f2  = lambda v: f"{flt(v):,.2f}"
        i0  = lambda v: f"{int(v):,}"
        ratio = lambda row: f"1 : {f2(row.parts_to_labour)}"

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
            ["Parts : Labour Ratio", ratio(daily),                      ratio(mtd),                      ratio(ytd)],
        ]
    
    @frappe.whitelist()
    def custom_method_send(self):
        """
        Custom method to send the email digest.
        This method can be overridden in the custom method field of the Pitstop Email Digest.
        """
        if self.method:
            try:
                frappe.get_attr(self.method)(self, show_html=False)
            except Exception as e:
                frappe.log_error(frappe.get_traceback(), _("Error in custom method for Pitstop Email Digest"))

    # ------------------------------------------------------------------
    # Scheduler helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _auto_send(freq):
        for each_dict in frappe.get_all(
            "Pitstop Email Digest",
            filters={"enabled": 1, "frequency": freq},
            fields=["name", "enable_custom_method"]
        ):
            email_digest_record = frappe.get_doc("Pitstop Email Digest", each_dict.get("name"))
            if not email_digest_record.enable_custom_method:
                email_digest_record.send()
            else:
                if email_digest_record.method:
                    try:
                        frappe.get_attr(email_digest_record.method)(email_digest_record, show_html=False)
                    except Exception as e:
                        frappe.log_error(frappe.get_traceback(), _("Error in custom method for Pitstop Email Digest"))

    @staticmethod
    def auto_send_daily():
        PitstopEmailDigest._auto_send("Daily")
        # Check if today is the last day of the month
        # If so, send the monthly digest
        today_date = today()
        tomorrow = getdate(add_days(today_date, 1))

        # if tomorrow is the 1st, today is the last day of the month
        if tomorrow.day == 1:
            # Call your actual monthly method
            PitstopEmailDigest._auto_send("Monthly")

    @staticmethod
    def auto_send_weekly():
        PitstopEmailDigest._auto_send("Weekly")


# Scheduler aliases
auto_send_daily  = PitstopEmailDigest.auto_send_daily
auto_send_weekly = PitstopEmailDigest.auto_send_weekly

@frappe.whitelist()
def get_digest_msg(name):
    email_digest_record = frappe.get_doc("Pitstop Email Digest", name)
    if email_digest_record.enable_custom_method:
        return frappe.get_doc("Pitstop Email Digest", name).get_msg_html(email_digest_record.method)
    else:
        return frappe.get_doc("Pitstop Email Digest", name).get_msg_html()
