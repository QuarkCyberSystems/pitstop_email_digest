// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["RO Sold Hours"] = {
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
			fieldname: "repair_order",
			label: __("Repair Order"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
		},
		{
			fieldname: "ro_status",
			label: __("RO Status"),
			fieldtype: "Link",
			options: "Project Status",
		},
		{
			fieldname: "not_completed_ro_status",
			label: __("Not Completed RO"),
			fieldtype: "Check",
			on_change: function () {
				let show_status = !frappe.query_report.get_filter_value("not_completed_ro_status");
				frappe.query_report.get_filter("ro_status").toggle(show_status);
			},
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		let style = {};
		if (column.fieldname === "hours_difference" && data) {
			let difference = flt(data.hours_difference);

			if (difference > 0) {
				style["background-color"] = "var(--bg-green)";
				style["color"] = "var(--text-on-green)";
			} else if (difference < 0) {
				style["background-color"] = "var(--bg-red)";
				style["color"] = "var(--text-on-red)";
			}
		}

		value = default_formatter(value, row, column, data, { css: style });

		return value;
	},
	onload: function (report) {
		frappe.breadcrumbs.add({
			type: "Custom",
			label: __("Workshop"),
			route: "/app/workshop",
		});

		let show_status = !report.get_filter_value("not_completed_ro_status");
		frappe.query_report.get_filter("ro_status").toggle(show_status);
	},
};
