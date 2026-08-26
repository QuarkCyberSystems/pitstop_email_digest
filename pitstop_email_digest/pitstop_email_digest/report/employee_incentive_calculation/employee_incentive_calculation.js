// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

const DEFAULT_INCENTIVE_AMT_MAP = {
	Technician: 350.0,
	"Reporting Authority": 600.0,
};

frappe.query_reports["Employee Incentive Calculation"] = {
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
			fieldname: "based_on",
			label: __("Based On"),
			fieldtype: "Select",
			options: ["Technician", "Reporting Authority", "Service Advisor"], // "Reporting Manager"
			default: "Technician",
			reqd: 1,
			on_change: function () {
				const based_on = frappe.query_report.get_filter_value("based_on");
				const default_amt = DEFAULT_INCENTIVE_AMT_MAP[based_on];
				if (default_amt !== undefined) {
					frappe.query_report.set_filter_value("base_incentive", default_amt);
				}
			},
		},
		{
			fieldname: "base_incentive",
			label: __("Base Incentive"),
			fieldtype: "Float",
			default: 350.0,
			reqd: 0,
		},
	],
	onload: function (report) {
		frappe.breadcrumbs.add("HR");

		const original_refresh = report.refresh.bind(report);
		report.refresh = function () {
			if (report.$status) {
				report.$status.hide();
			}
			return original_refresh();
		};
	},
};
