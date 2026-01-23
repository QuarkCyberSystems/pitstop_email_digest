import frappe

from .cashier_dashboard_helper import (
    fetch_cashier_data_sql,
    fetch_group_by_payment_mode_data,
)


@frappe.whitelist()
def fetch_cashier_dashboard_data(selected_date):
    summary_data = frappe.db.sql(fetch_cashier_data_sql(selected_date), as_dict=True)
    payment_mode_data = fetch_mode_of_payments_closed_tills(summary_data, selected_date)
    return {"summary_data": summary_data, "payment_mode_data": payment_mode_data}


def fetch_mode_of_payments_closed_tills(fetched_pos_opening_data, selected_date):
    pos_opening_entry_list = []
    for row in fetched_pos_opening_data:
        if row.get("status") == "Closed":
            if row.get("name") not in pos_opening_entry_list:
                pos_opening_entry_list.append(row.get("name"))
    # Important: Avoid empty IN ()
    if not pos_opening_entry_list:
        return []
    placeholders = ", ".join(["%s"] * len(pos_opening_entry_list))

    return frappe.db.sql(
        fetch_group_by_payment_mode_data(placeholders),
        tuple(pos_opening_entry_list),
        as_dict=True,
    )
