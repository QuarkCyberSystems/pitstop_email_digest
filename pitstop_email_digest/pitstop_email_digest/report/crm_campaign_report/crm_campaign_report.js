// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["CRM Campaign Report"] = {
	filters: [
		{
			fieldname: "campaign",
			label: __("Campaign"),
			fieldtype: "Link",
			options: "Campaign",
			reqd: 0,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 0,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 0,
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
			reqd: 0,
		},
	],
	onload: function (report) {
		frappe.breadcrumbs.add("CRM");
	},
};
