// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Person Item Group Revenue"] = {
	filters: [
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
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "sales_person",
			label: __("Sales Person"),
			fieldtype: "Link",
			options: "Sales Person",
			get_query: () => ({
				filters: { is_group: 0 },
			}),
		},
		{
			fieldname: "department",
			label: __("Department"),
			fieldtype: "Link",
			options: "Department",
			get_query: () => ({
				query: "pitstop_email_digest.pitstop_email_digest.page.sales_person_package_revenue.sales_person_package_revenue.get_sales_person_departments",
			}),
		},
		{
			fieldname: "item_group",
			label: __("Item Group"),
			fieldtype: "Link",
			options: "Item Group",
		},
	],
	onload: function (report) {
		frappe.breadcrumbs.add("Selling");
	},
};
