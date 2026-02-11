// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Non-Stock Purchase Document"] = {
	filters: [
		{
			fieldname: "purchase_document",
			label: __("Purchase Document"),
			fieldtype: "Select",
			options: ["Purchase Order", "Purchase Invoice", "Purchase Receipt"],
			default: "Purchase Order",
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
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
			fieldname: "document_status",
			label: __("Document Status"),
			fieldtype: "Select",
			options: ["Submitted", "Draft", "Cancelled", ""],
			default: "Submitted",
			reqd: 0,
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
			reqd: 0,
		},
		{
			fieldname: "is_stock",
			label: __("Stock Item"),
			fieldtype: "Check",
			default: 1,
		},
	],
	onload: function (report) {
		frappe.breadcrumbs.add("Buying");
	},
};
