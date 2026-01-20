// Copyright (c) 2025, QCS and contributors
// For license information, please see license.txt

const group_by_options_wsturnover = [
	"",
	"Group by Vehicle Workshop",
	"Group by Branch",
	"Group by Workshop Division",
	"Group by Cost Center",
	"Group by Service Advisor",
	"Group by Customer Group",
];

frappe.query_reports["Workshop Turnover Segmentation"] = {
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
			fieldname: "segmentation",
			label: __("Segmentation"),
			fieldtype: "Select",
			options: ["BRAC-QIC", "BRAC-CASH", "BRAC-MECH.", "TESLA", "AGMC-GEELY"],
			reqd: 0,
		},
		{
			fieldname: "vehicle_workshop",
			label: __("Vehicle Workshop"),
			fieldtype: "Link",
			options: "Vehicle Workshop",
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
		},
		{
			fieldname: "vehicle_workshop_division",
			label: __("Workshop Division"),
			fieldtype: "Link",
			options: "Vehicle Workshop Division",
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
			get_query: () => {
				return {
					filters: { company: frappe.query_report.get_filter_value("company") },
				};
			},
		},
		{
			fieldname: "service_advisor",
			label: __("Service Advisor"),
			fieldtype: "Link",
			options: "Sales Person",
			get_query: () => {
				return { filters: { is_group: 0 } };
			},
		},
		{
			fieldname: "customer_group",
			label: __("Customer Group"),
			fieldtype: "Link",
			options: "Customer Group",
		},
		{
			fieldname: "group_by_1",
			label: __("Group By Level 1"),
			fieldtype: "Select",
			options: group_by_options_wsturnover,
			default: "Group by Vehicle Workshop",
		},
		{
			fieldname: "group_by_2",
			label: __("Group By Level 2"),
			fieldtype: "Select",
			options: group_by_options_wsturnover,
		},
		{
			fieldname: "totals_only",
			label: __("Group Totals Only"),
			fieldtype: "Check",
			default: 1,
		},
	],

	initial_depth: 1,
	onload: function (report) {
		frappe.breadcrumbs.add({
			type: "Custom",
			label: __("Workshop"),
			route: "/app/workshop",
		});
	},
};
