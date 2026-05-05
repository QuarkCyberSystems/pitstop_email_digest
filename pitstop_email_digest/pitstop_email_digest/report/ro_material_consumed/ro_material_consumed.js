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
			fieldname: "ro",
			label: __("Repair Order"),
			fieldtype: "Link",
			options: "Project",
			reqd: 0,
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
			reqd: 0,
		},
		{
			fieldname: "ro_status",
			label: __("RO Status"),
			fieldtype: "Link",
			options: "Project Status",
			hidden: 1,
			reqd: 0,
		},
		{
			fieldname: "ageing_ranges",
			label: __("Ageing Range"),
			fieldtype: "Data",
			default: "30, 60, 90, 120",
		},
		{
			fieldname: "not_completed_ro_status",
			label: __("Not Completed RO"),
			fieldtype: "Check",
			default: 1,
			on_change: function () {
				let show_status = !frappe.query_report.get_filter_value("not_completed_ro_status");
				let ro_status_filter = frappe.query_report.get_filter("ro_status");
				ro_status_filter.toggle(show_status);
			},
		},
	],
	onload: function (report) {
		frappe.breadcrumbs.add({
			type: "Custom",
			label: __("Workshop"),
			route: "/app/workshop",
		});
		let is_checked = !report.get_filter_value("not_completed_ro_status");
		let ro_status_filter = frappe.query_report.get_filter("ro_status");
		ro_status_filter.toggle(is_checked);
	},
};
