// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Quotation RO Analysis"] = {
	filters: [
		{
			fieldname: "quotation",
			label: __("Quotation"),
			fieldtype: "Link",
			options: "Quotation",
			reqd: 0,
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
			reqd: 0,
		},
		{
			fieldname: "quotation_status",
			label: __("Quotation Status"),
			fieldtype: "Select",
			options: ["", "Draft", "Open", "Ordered", "Lost", "Expired", "Cancelled"],
			reqd: 0,
		},
		{
			fieldname: "ro_status",
			label: __("Repair Order Status"),
			fieldtype: "Link",
			options: "Project Status",
			reqd: 0,
		},
		{
			fieldname: "quotation_service_advisor",
			label: __("Quotation Service Advisor"),
			fieldtype: "Link",
			options: "Sales Person",
			reqd: 0,
		},
	],
	onload: function (report) {
		frappe.breadcrumbs.add("Selling");
	},
	get_datatable_options(options) {
		return Object.assign(options, {
			hooks: {
				columnTotal: function (values, column, type) {
					if (in_list(["per_gross_margin", "gross_margin"], column.column.fieldname)) {
						return "";
					} else {
						return frappe.utils.report_column_total(values, column, type);
					}
				},
			},
		});
	},
};
