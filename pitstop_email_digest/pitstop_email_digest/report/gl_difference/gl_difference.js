// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["GL Difference"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "view",
			label: __("View"),
			fieldtype: "Select",
			options: ["Ledger Movement", "Cancelled Vouchers"],
			default: "Ledger Movement",
			reqd: 1,
		},
		{
			fieldname: "account",
			label: __("Ledger"),
			fieldtype: "Link",
			options: "Account",
			get_query: function () {
				return {
					filters: {
						company: frappe.query_report.get_filter_value("company"),
						is_group: 0,
					},
				};
			},
		},
		{
			fieldname: "show_zero_values",
			label: __("Show Zero Difference"),
			fieldtype: "Check",
			default: 0,
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname == "amount" && data && data.amount && !data.voucher_no) {
			value = `<span style="color: ${data.amount > 0 ? "green" : "red"}">${value}</span>`;
		}
		return value;
	},
	onload: function (report) {
		frappe.breadcrumbs.add("Accounts");
	},
};
