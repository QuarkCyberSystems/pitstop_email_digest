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
