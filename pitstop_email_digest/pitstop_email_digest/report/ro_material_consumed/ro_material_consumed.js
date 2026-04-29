// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["RO Material Consumed"] = {
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
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.now_date(),
			reqd: 1,
		},
		{
			fieldname: "ro_status",
			label: __("RO Status"),
			fieldtype: "Link",
			options: "Project Status",
			default: "Completed",
			reqd: 0,
		},
	],
	onload: function (report) {
		frappe.breadcrumbs.add({
			type: "Custom",
			label: __("Workshop"),
			route: "/app/workshop",
		});
	},
};
