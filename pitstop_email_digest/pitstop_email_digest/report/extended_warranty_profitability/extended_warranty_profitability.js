// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Extended Warranty Profitability"] = {
	filters: [
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
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company"),
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname === "profit" && data) {
			if (data.profit < 0) {
				value = `<span style="color: var(--red-500); font-weight: bold;">${value}</span>`;
			} else if (data.profit > 0) {
				value = `<span style="color: var(--green-500); font-weight: bold;">${value}</span>`;
			}
		}

		return value;
	},
	onload: function (report) {
		frappe.breadcrumbs.add("Accounts");
	},
};
