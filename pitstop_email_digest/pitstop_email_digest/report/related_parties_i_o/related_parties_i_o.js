// Copyright (c) 2025, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Related Parties I_O"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1
		},
		{
			fieldname: "workshop_division",
			label: __("Workshop Division"),
			fieldtype: "Link",
			options: "Vehicle Workshop Division",
			reqd: 0
		},
		{
			fieldname: "project_status",
			label: __("Project Status"),
			fieldtype: "Link",
			options: "Project Status",
			reqd: 0
		},
		{
			fieldname: "billing_type",
			label: __("Billing Type"),
			fieldtype: "Select",
			options: ["", "Customer", "Insurance"],
			reqd: 0
		}
	]
};
