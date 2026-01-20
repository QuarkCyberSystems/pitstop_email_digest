// Copyright (c) 2025, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["User Access Report"] = {
	filters: [
		{
			fieldname: "user",
			label: __("User"),
			fieldtype: "Link",
			options: "User",
			reqd: 0,
		},
		{
			fieldname: "role",
			label: __("Role"),
			fieldtype: "Link",
			options: "Role",
			reqd: 0,
		},
		{
			fieldname: "doctype",
			label: __("Doctype"),
			fieldtype: "Link",
			options: "DocType",
			reqd: 0,
		},
		{
			fieldname: "create_permission",
			label: __("Create"),
			fieldtype: "Check",
			reqd: 0,
		},
		{
			fieldname: "submit_permission",
			label: __("Submit"),
			fieldtype: "Check",
			reqd: 0,
		},
		{
			fieldname: "cancel_permission",
			label: __("Cancel"),
			fieldtype: "Check",
			reqd: 0,
		},
		{
			fieldname: "amend_permission",
			label: __("Amend"),
			fieldtype: "Check",
			reqd: 0,
		},
		{
			fieldname: "write_permission",
			label: __("Write"),
			fieldtype: "Check",
			reqd: 0,
		},
		{
			fieldname: "read_permission",
			label: __("Read"),
			fieldtype: "Check",
			reqd: 0,
		},
	],
};
