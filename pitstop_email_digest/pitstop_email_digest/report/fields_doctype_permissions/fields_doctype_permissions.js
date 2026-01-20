// Copyright (c) 2025, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Fields Doctype Permissions"] = {
	filters: [
		{
			fieldname: "doctype",
			label: __("DocType"),
			fieldtype: "Link",
			options: "DocType",
			reqd: 0,
		},
		{
			fieldname: "permlevel",
			label: __("Permission Level"),
			fieldtype: "Select",
			options: ["", 1, 2, 3, 4, 5, 6, 7, 8, 9],
			reqd: 0,
		},
		{
			fieldname: "role",
			label: __("Role"),
			fieldtype: "Link",
			options: "Role",
			reqd: 0,
		},
	],
};
