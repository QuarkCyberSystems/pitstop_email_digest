import frappe
from frappe.utils.pdf import get_pdf


def fetch_cashier_data_sql(selected_date):
    return f"""
			SELECT
				name,
				pos_profile,
				status,
				CASE WHEN rn = 1 THEN sales_invoice_count ELSE NULL END AS sales_invoice_count,
				CASE WHEN rn = 1 THEN payment_entry_count ELSE NULL END AS payment_entry_count,
				CASE WHEN rn = 1 THEN total_no_of_transactions ELSE NULL END AS total_no_of_transactions,
				CASE WHEN rn = 1 THEN sales_invoice_collected_amount ELSE NULL END AS sales_invoice_collected_amount,
				CASE WHEN rn = 1 THEN payment_entry_collected_amount ELSE NULL END AS payment_entry_collected_amount,
				CASE WHEN rn = 1 THEN total_collected ELSE NULL END AS total_collected,
				CASE WHEN rn = 1 THEN total_amount_pos_close_collected ELSE NULL END AS total_amount_pos_close_collected
			FROM (SELECT
				tpoe.name,
				tpoe.pos_profile,
				tpoe.user,
				tpoe.user_name,
				tpoe.branch,
				tpoe.status,
				COALESCE(si_data.sales_invoice_count, 0) AS sales_invoice_count,
				COALESCE(pe_data.payment_entry_count, 0) AS payment_entry_count,
				(
					COALESCE(si_data.sales_invoice_count, 0)
					+
					COALESCE(pe_data.payment_entry_count, 0)
				) AS total_no_of_transactions,
				COALESCE(si_data.sales_invoice_collected_amount, 0) AS sales_invoice_collected_amount,
				COALESCE(pe_data.payment_entry_collected_amount, 0) AS payment_entry_collected_amount,
				(
					COALESCE(si_data.sales_invoice_collected_amount, 0)
					+
					COALESCE(pe_data.payment_entry_collected_amount, 0)
				) AS total_collected,
				pos_close_data.pos_close_collected_amount as total_amount_pos_close_collected,
				ROW_NUMBER() OVER (
					PARTITION BY tpoe.pos_profile
					ORDER BY tpoe.name
				) AS rn
			FROM `tabPOS Opening Entry` tpoe
			LEFT JOIN (
				SELECT
						tsi.pos_profile,
						COUNT(DISTINCT tsi.name) AS sales_invoice_count,
						SUM(tsip.base_amount) AS sales_invoice_collected_amount
					FROM `tabSales Invoice` tsi
					JOIN `tabSales Invoice Payment` tsip
						ON tsip.parent = tsi.name
					WHERE
						tsi.posting_date = '{selected_date}'
						AND tsi.docstatus = 1
					GROUP BY tsi.pos_profile
				) si_data
					ON si_data.pos_profile = tpoe.pos_profile
				LEFT JOIN (
					SELECT
						pos_profile,
						COUNT(name) AS payment_entry_count,
						SUM(base_paid_amount) AS payment_entry_collected_amount
					FROM `tabPayment Entry`
					WHERE
						posting_date = '{selected_date}'
						AND docstatus = 1
					GROUP BY pos_profile
				) pe_data
					ON pe_data.pos_profile = tpoe.pos_profile
				LEFT JOIN (
					SELECT
						tpce.pos_profile,
						SUM(tpced.paid_amount) AS pos_close_collected_amount
					FROM
						`tabPOS Closing Entry` tpce
					JOIN
						`tabPOS Closing Entry Detail` tpced
					ON
						tpced.parent = tpce.name
					WHERE
						tpce.period_start_date = '{selected_date}'
						AND tpce.docstatus = 1
					GROUP BY tpce.pos_profile
				) pos_close_data
					ON pos_close_data.pos_profile = tpoe.pos_profile
				WHERE
					tpoe.docstatus = 1
					AND tpoe.period_start_date = '{selected_date}'
				group by
					tpoe.name, tpoe.pos_profile, tpoe.status) as x;
			"""


def fetch_group_by_payment_mode_data(placeholders):
    return f"""
		select
			tpced.mode_of_payment,
			sum(tpced.paid_amount) as total_paid_amount
		from
			`tabPOS Closing Entry Detail` tpced
		join
			`tabPOS Closing Entry` tpce
			on tpced.parent = tpce.name
		where
			tpce.pos_opening_entry in ({placeholders}) and tpce.docstatus = 1
		group by
			tpced.mode_of_payment
	"""


def generate_summary_data_payment_data(cashiers_data):
    """
    Generate the array for the mail digest
    """
    summary_data = []
    payment_mode_data = []
    total_number_of_transactions = 0
    total_number_of_tills_closed = 0
    total_amount_collected = 0
    total_amount_pos_closed_collected = 0
    branch_summary_data_array = []

    for each_message_summary_data in cashiers_data.get("summary_data"):
        if each_message_summary_data.get("status") == "Closed":
            total_number_of_tills_closed += 1
        total_number_of_transactions += (
            each_message_summary_data.get("total_no_of_transactions")
            if each_message_summary_data.get("total_no_of_transactions")
            else 0
        )
        total_amount_collected += (
            each_message_summary_data.get("total_collected")
            if each_message_summary_data.get("total_collected")
            else 0
        )
        total_amount_pos_closed_collected += (
            each_message_summary_data.get("total_amount_pos_close_collected")
            if each_message_summary_data.get("total_amount_pos_close_collected")
            else 0
        )

        pos_profile_found = None

        for each_branch_summary_data_array in branch_summary_data_array:
            if (
                each_branch_summary_data_array.get("pos_profile")
                == each_message_summary_data.pos_profile
            ):
                each_branch_summary_data_array["total_no_of_transactions"] += (
                    each_message_summary_data.get("total_no_of_transactions")
                    if each_message_summary_data.get("total_no_of_transactions")
                    else 0
                )
                each_branch_summary_data_array["total_collected"] += (
                    each_message_summary_data.get("total_collected")
                    if each_message_summary_data.get("total_collected")
                    else 0
                )
                each_branch_summary_data_array["total_amount_pos_close_collected"] += (
                    each_message_summary_data.get("total_amount_pos_close_collected")
                    if each_message_summary_data.get("total_amount_pos_close_collected")
                    else 0
                )
                pos_profile_found = each_message_summary_data
                break

        if not pos_profile_found:
            pos_profile_found = {
                "pos_profile": each_message_summary_data.get("pos_profile"),
                "total_no_of_transactions": each_message_summary_data.get(
                    "total_no_of_transactions"
                ),
                "total_collected": each_message_summary_data.get("total_collected"),
                "total_amount_pos_close_collected": each_message_summary_data.get(
                    "total_amount_pos_close_collected"
                ),
                "status": each_message_summary_data.get("status"),
            }
            branch_summary_data_array.append(pos_profile_found)

    summary_data.append(
        {"datatype": "Section Break", "label": "Branch Summary", "colspan": 5}
    )
    summary_data.append(
        {
            "datatype": "Header",
            "labels": [
                "Branch",
                "Total No. Of Transactions",
                "Total Collected",
                "Total Amount POS Not Closed",
                "Status",
            ],
            "colspan": 1,
        }
    )

    for each_branch_summary_data_array in branch_summary_data_array:
        check_status = any(
            each_data
            for each_data in cashiers_data.get("summary_data")
            if each_data.get("status") == "Open"
            and each_data.get("pos_profile")
            == each_branch_summary_data_array.get("pos_profile")
        )

        total_amount_pos_not_closed = (
            each_branch_summary_data_array["total_collected"]
            if each_branch_summary_data_array["total_collected"]
            else 0
        ) - (
            each_branch_summary_data_array["total_amount_pos_close_collected"]
            if each_branch_summary_data_array["total_amount_pos_close_collected"]
            else 0
        )

        summary_data.append(
            {
                "key": each_branch_summary_data_array["pos_profile"],
                "label": f"{each_branch_summary_data_array['pos_profile']} - Total Transactions",
                "total_no_of_transactions": each_branch_summary_data_array[
                    "total_no_of_transactions"
                ]
                if each_branch_summary_data_array.get("total_no_of_transactions")
                else 0,
                "total_collected": each_branch_summary_data_array["total_collected"]
                if each_branch_summary_data_array.get("total_collected")
                else 0,
                "total_amount_pos_not_closed": total_amount_pos_not_closed,
                "status": "Open" if check_status else "Closed",
            }
        )

    summary_data.append(
        {
            "datatype": "Total",
            "label": "Total",
            "total_no_of_transactions": total_number_of_transactions,
            "total_collected": total_amount_collected,
            "total_amount_pos_not_closed": (
                total_amount_collected - total_amount_pos_closed_collected
            ),
            "colspan": 4,
        }
    )

    # Section: Payment Mode
    if cashiers_data.get("payment_mode_data"):
        payment_mode_data.append(
            {
                "datatype": "Section Break",
                "label": "Collection Break Up Payment Mode Basis",
                "colspan": 4,
            }
        )
        payment_mode_data.append(
            {"datatype": "Header", "labels": ["Payment Mode", "Amount"], "colspan": 1}
        )
        for payment in cashiers_data.get("payment_mode_data"):
            payment_mode_data.append(
                {
                    "label": payment["mode_of_payment"],
                    "value": payment["total_paid_amount"]
                    if payment.get("total_paid_amount")
                    else 0,
                }
            )
        payment_mode_data.append(
            {"datatype": "Total", "label": "Total", "value": total_amount_collected}
        )

    return summary_data, payment_mode_data


@frappe.whitelist()
def download_cashier_dashboard_pdf(selected_date):
    from .cashier_dashboard import fetch_cashier_dashboard_data

    cashiers_data = fetch_cashier_dashboard_data(selected_date)
    summary_data, payment_mode_data = generate_summary_data_payment_data(cashiers_data)
    local = frappe.local

    html = frappe.render_template(
        "utils/report_summary/templates/cashier_dashboard.html",
        {
            "title": "Cashier Dashboard Summary",
            "date": selected_date,
            "h1": "font-size:20px; color:#333;",
            "h2": "font-size:16px; color:#666;",
            "summary_data": summary_data,
            "payment_mode_data": payment_mode_data,
        },
        is_path=True,
    )

    pdf = get_pdf(html)
    local.letter_head = "Pitstop Letterhead"

    frappe.local.response.filename = "cashier_dashboard_summary.pdf"
    frappe.local.response.filecontent = pdf
    frappe.local.response.type = "download"
