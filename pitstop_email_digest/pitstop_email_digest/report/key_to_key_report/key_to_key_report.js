// Copyright (c) 2025, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Key To Key Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
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
			fieldname: "workshop_division",
			label: __("Workshop Division"),
			fieldtype: "Link",
			options: "Vehicle Workshop Division",
			reqd: 1,
		},
		{
			fieldname: "repair_order",
			label: __("Repair Order"),
			fieldtype: "Link",
			options: "Project",
			reqd: 0,
		},
	],
};
