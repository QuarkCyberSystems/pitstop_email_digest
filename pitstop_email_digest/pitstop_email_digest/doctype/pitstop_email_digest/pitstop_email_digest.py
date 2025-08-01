# Copyright © 2025, QCS
# License: GPL-3.0

import frappe
from frappe import _
from collections import OrderedDict
from frappe.utils import getdate, today, flt, add_days, get_first_day, format_date, add_years
from erpnext.setup.doctype.email_digest.email_digest import EmailDigest as CoreDigest
from erpnext.setup.doctype.item_group.item_group import get_item_group_subtree
from erpnext.stock.doctype.item.item import convert_item_uom_for
from pitstop_email_digest.utils.report_summary.report_summary_helper import get_workshop_turnover_summary_details


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

def _server_yesterday():
    return getdate(add_days(today(), -1))

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
        return getdate(self.as_of_date) if getattr(self, "as_of_date", None) else _server_yesterday()

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
            JOIN `tabProject`      p ON p.name  = i.project
            WHERE i.project is not NULL AND inv.posting_date BETWEEN %s AND %s
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

        first_day_this_month = get_first_day(today, as_str=False)
        last_day_last_month = getdate(add_days(first_day_this_month, -1))
        first_day_last_month = get_first_day(last_day_last_month, as_str=False)

        current_month_year = today.strftime("%B-%Y")
        current_year = today.strftime("%Y")
        current_month = today.strftime("%B")
        last_month_year = first_day_last_month.strftime("%B-%Y")

        last_year_date = getdate(add_years(today, -1))
        last_year = last_year_date.strftime("%Y")
        current_month_number = f"{today.month:02d}"

        first_day_last_year = getdate(f"{str(last_year)}-{'01'}-01")
        first_month_last_year = first_day_last_year.strftime("%B")

        daily = self._build_kpi(today,  today)
        mtd   = self._build_kpi(m0,     today)
        ytd   = self._build_kpi(y0,     today)
        last_month = self._build_kpi(first_day_last_month,     last_day_last_month)

        f2  = lambda v: f"{flt(v):,.2f}"
        i0  = lambda v: f"{int(v):,}"
        ratio = lambda row: f"1 : {f2(row.parts_to_labour)}"
        

        return [
            ["Details",                      "Daily<br/>("+str(format_date(today, "dd-mm-yyyy")+")"),                              "MTD<br/>("+str(current_month_year)+")",                                           "YTD<br/>("+str(current_year)+")",                                                 "Last Month<br/>("+str(last_month_year)+")",                                                                       str(current_month)+"<br/>("+str(last_year)+")",                                                        str(first_month_last_year)+"-"+str(current_month)+"<br/>("+str(last_year)+")"],
            ["No of Repair Order Invoiced",  i0(daily.ro_count),                                                                   i0(mtd.ro_count),                                                                  i0(ytd.ro_count),                                                                  i0(last_month.ro_count),                                                                                           round_dirham(self.get_back_date_data("No of Repair Order Invoiced", last_year, current_month_number)), round_dirham(self.get_back_date_data("No of Repair Order Invoiced", last_year, current_month_number, ["01", current_month_number]))],                    
            ["Labour Hours",                 round_dirham(daily.labour_hours),                                                     round_dirham(mtd.labour_hours),                                                    round_dirham(ytd.labour_hours),                                                    round_dirham(last_month.labour_hours),                                                                             round_dirham(self.get_back_date_data("Labour Hours", last_year, current_month_number)),                round_dirham(self.get_back_date_data("Labour Hours", last_year, current_month_number, ["01", current_month_number]))],
            ["Revenue",                      round_dirham(daily.revenue),                                                          round_dirham(mtd.revenue),                                                         round_dirham(ytd.revenue),                                                         round_dirham(last_month.revenue),                                                                                  round_dirham(self.get_back_date_data("Revenue", last_year, current_month_number)),                     round_dirham(self.get_back_date_data("Revenue", last_year, current_month_number, ["01", current_month_number]))],
            ["Labour Amount",                round_dirham(daily.labour_amount),                                                    round_dirham(mtd.labour_amount),                                                   round_dirham(ytd.labour_amount),                                                   round_dirham(last_month.labour_amount),                                                                            round_dirham(self.get_back_date_data("Labour", last_year, current_month_number)),                      round_dirham(self.get_back_date_data("Labour", last_year, current_month_number, ["01", current_month_number]))],
            ["Parts Amount",                 round_dirham(daily.parts_amount),                                                     round_dirham(mtd.parts_amount),                                                    round_dirham(ytd.parts_amount),                                                    round_dirham(last_month.parts_amount),                                                                             round_dirham(self.get_back_date_data("Parts", last_year, current_month_number)),                       round_dirham(self.get_back_date_data("Parts", last_year, current_month_number, ["01", current_month_number]))],
            ["Parts GP (%)",                 round_dirham(self.get_workshop_turnover_report_details(today, today, "Parts GP (%)")),round_dirham(self.get_workshop_turnover_report_details(m0, today, "Parts GP (%)")),round_dirham(self.get_workshop_turnover_report_details(y0, today, "Parts GP (%)")),round_dirham(self.get_workshop_turnover_report_details(first_day_last_month, last_day_last_month, "Parts GP (%)")),round_dirham(self.get_back_date_data("Parts GP %", last_year, current_month_number)),                  "-"],
            ["Consumables & Others",         round_dirham(daily.cons_amount),                                                      round_dirham(mtd.cons_amount),                                                     round_dirham(ytd.cons_amount),                                                     round_dirham(last_month.cons_amount),                                                                              round_dirham(self.get_back_date_data("Consumable & Other", last_year, current_month_number)),          round_dirham(self.get_back_date_data("Consumable & Other", last_year, current_month_number, ["01", current_month_number]))],
            ["Effective Labour Rate",        round_dirham(daily.labour_rate),                                                      round_dirham(mtd.labour_rate),                                                     round_dirham(ytd.labour_rate),                                                     round_dirham(last_month.labour_rate),                                                                              round_dirham(self.get_back_date_data("Effective labour rate", last_year, current_month_number)),       round_dirham(self.get_back_date_data("Effective labour rate", last_year, current_month_number, ["01", current_month_number]))],
            ["Hours per RO",                 round_dirham(daily.hours_per_ro),                                                     round_dirham(mtd.hours_per_ro),                                                    round_dirham(ytd.hours_per_ro),                                                    round_dirham(last_month.hours_per_ro),                                                                             round_dirham(self.get_back_date_data("Hours per RO", last_year, current_month_number)),                round_dirham(self.get_back_date_data("Hours per RO", last_year, current_month_number, ["01", current_month_number]))],
            ["Parts : Labour Ratio",         ratio(daily),                                                                         ratio(mtd),                                                                        ratio(ytd),                                                                        ratio(last_month),                                                                                                 self.get_back_date_data("Parts to Labour ratio", last_year, current_month_number),                      "-"],
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
    
    def get_workshop_turnover_report_details(self, from_date, to_date, status):
        check_turnover_data = get_workshop_turnover_summary_details(from_date, to_date)
        if check_turnover_data:
            for each_data in check_turnover_data:
                if each_data.get("label") == status:
                    return each_data.get("value") or 0.0
        return 0.0

    def get_back_date_data(self, status, pre_year, month_number, month_range=None):
        last_year = pre_year
        last_year_data = frappe.get_all("Last Year", filters={"period":last_year}, fields=["*"])

        if not month_range:
            for each_ly_data_dict in last_year_data:
                if each_ly_data_dict.type == status:
                    return each_ly_data_dict.get(month_number) or 0
            else:
                return 0
        else:
            the_sum_of_value = 0.0
            month_start = int(month_range[0])  # or from your list: int(my_list[0])
            month_end = int(month_range[1])

            for range_month_number in range(month_start, month_end + 1):
                for each_ly_data_dict in last_year_data:
                    if each_ly_data_dict.type == status:
                        rqd_range_month_number = str(range_month_number).zfill(2)
                        the_sum_of_value += flt(each_ly_data_dict.get(rqd_range_month_number)) or 0
                        break
            return the_sum_of_value

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
        # Check if today is the first day of the month
        # If so, send the monthly digest
        today_date = getdate(today())

        # if today_date is the 1st, yesterday is the last day of the month
        if today_date.day == 1:
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
