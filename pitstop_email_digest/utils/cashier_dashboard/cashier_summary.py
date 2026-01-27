import frappe

from ..report_summary.report_summary import get_send_date
from .cashier_dashboard import fetch_cashier_dashboard_data
from .cashier_dashboard_helper import generate_summary_data_payment_data


def send_cashier_dashboard(email_digest, show_html=False):
    required_date = get_send_date(email_digest)
    cashiers_data = fetch_cashier_dashboard_data(required_date)
    summary_data, payment_mode_data = generate_summary_data_payment_data(cashiers_data)

    return frappe.render_template(
        "utils/report_summary/templates/cashier_dashboard.html",
        {
            "title": "Cashier Dashboard Summary",
            "date": frappe.utils.today(),
            "h1": "font-size:20px; color:#333;",
            "h2": "font-size:16px; color:#666;",
            "summary_data": summary_data,
            "payment_mode_data": payment_mode_data,
        },
        is_path=True,
    )
