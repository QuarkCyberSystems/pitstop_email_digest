import frappe
from frappe import _
from frappe.utils import add_days, get_month, getdate, today

from .report_summary_helper import (
    get_workshop_productivity_summary_details,
    get_workshop_turnover_summary_details,
)

REPORT_SUMMARY_DICT = {
    "Workshop Turnover": get_workshop_turnover_summary_details,
    "Workshop Productivity": get_workshop_productivity_summary_details,
}


def get_send_date(email_digest):
    """Get the date to be used in the email subject"""
    return email_digest.as_of_date or getdate(add_days(today(), -1))


def packing_data_engine(email_digest):
    """Prepare the data for the email digest"""
    summary_data, date_property, title = None, None, None
    if REPORT_SUMMARY_DICT.get(email_digest.report_reference):
        if email_digest.frequency == "Daily":
            summary_data = REPORT_SUMMARY_DICT.get(email_digest.report_reference)(
                start_date=get_send_date(email_digest),
                end_date=get_send_date(email_digest),
                company=frappe.get_cached_value(
                    "Global Defaults", None, "default_company"
                ),
            )
            date_property = "Date " + str(get_send_date(email_digest))
            title = _("Daily " + email_digest.report_reference + " Summary")
        elif email_digest.frequency == "Monthly":
            summary_data = REPORT_SUMMARY_DICT.get(email_digest.report_reference)(
                start_date=frappe.utils.get_first_day(get_send_date(email_digest)),
                end_date=get_send_date(email_digest),
                company=frappe.get_cached_value(
                    "Global Defaults", None, "default_company"
                ),
            )
            date_property = (
                "Month "
                + str(
                    get_month(get_send_date(email_digest))
                    + "(from "
                    + str(frappe.utils.get_first_day(get_send_date(email_digest)))
                )
                + " to "
                + str(get_send_date(email_digest))
                + ")"
            )
            title = _("Monthly " + email_digest.report_reference + " Summary")

    return summary_data, date_property, title


def send_report_summary(email_digest, show_html=False):
    """Send the daily workshop turnover summary email"""
    summary_data, date_property, title = packing_data_engine(email_digest)
    summary_data = frappe._dict(
        {"summary_data": summary_data, "title": title, "date": date_property}
    )
    email_digest.set_style(summary_data)

    if show_html:
        return frappe.render_template(
            "utils/report_summary/templates/report_summary.html",
            summary_data,
            is_path=True,
        )
    else:
        valid_users = [
            p[0]
            for p in frappe.db.sql(
                """select name from `tabUser`
				where enabled=1"""
            )
        ]
        recipients = list(
            filter(lambda r: r in valid_users, email_digest.recipient_list.split("\n"))
        )

        original_user = frappe.session.user

        if recipients:
            email_subject = (
                email_digest.frequency
                + " "
                + email_digest.report_reference
                + " Summary"
            )
            for user_id in recipients:
                frappe.set_user(user_id)
                frappe.set_user_lang(user_id)
                frappe.sendmail(
                    recipients=user_id,
                    subject=_(email_subject),
                    message=frappe.render_template(
                        "utils/report_summary/templates/report_summary.html",
                        summary_data,
                        is_path=True,
                    ),
                    reference_doctype=email_digest.doctype,
                    reference_name=email_digest.name,
                    unsubscribe_message=_("Unsubscribe from this Email Digest"),
                )
        frappe.set_user(original_user)
        frappe.set_user_lang(original_user)
