// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Converted Opportunity Sales Person Revenue"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company"),
		},
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
			fieldname: "opportunity_type",
			label: __("Opportunity Type"),
			fieldtype: "Link",
			options: "Opportunity Type",
			reqd: 0,
		},
		{
			fieldname: "sales_person",
			label: __("Sales Person"),
			fieldtype: "Link",
			options: "Sales Person",
			reqd: 0,
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
			reqd: 0,
			get_query: function () {
				var company_selected = frappe.query_report.get_filter_value("company");
				return {
					filters: { is_group: 0, company: company_selected },
				};
			},
		},
		{
			fieldname: "pdi_non_pdi",
			label: __("PDI/NON PDI"),
			fieldtype: "Select",
			options: ["", "PDI", "NON PDI", "BPS"],
			reqd: 0,
		},
		{
			fieldname: "bill_to_customer_group",
			label: __("Bill To Group"),
			fieldtype: "Link",
			options: "Customer Group",
			reqd: 0,
		},
	],
	onload: function (report) {
		frappe.breadcrumbs.add("CRM");
	},
};
