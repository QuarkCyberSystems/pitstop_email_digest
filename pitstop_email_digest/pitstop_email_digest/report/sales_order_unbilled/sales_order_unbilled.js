// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Order Unbilled"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			bold: 1,
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
	],
	onload: function (report) {
		frappe.breadcrumbs.add("Selling");
	},
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "balance_amount" && data && flt(data.balance_amount) > 0) {
			value = `<span style="color:var(--red-500)">${value}</span>`;
		}
		return value;
	},
};
