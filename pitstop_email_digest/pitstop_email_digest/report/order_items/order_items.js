// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Order Items"] = {
	filters: [
		{
			fieldname: "order_voucher_type",
			label: __("Order Voucher Type"),
			fieldtype: "Select",
			options: ["Sales Order", "Purchase Order"],
			default: "Sales Order",
			reqd: 1,
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			bold: 1,
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
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
			reqd: 0,
			depends_on: "eval:doc.order_voucher_type=='Sales Order'",
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
			reqd: 0,
			depends_on: "eval:doc.order_voucher_type=='Purchase Order'",
		},
		{
			fieldname: "item_code",
			label: __("Item Code"),
			fieldtype: "Link",
			options: "Item",
			reqd: 0,
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
			reqd: 0,
			get_query: function () {
				return {
					query: "pitstop_email_digest.pitstop_email_digest.report.order_items.order_items.get_branches",
				};
			},
		},
	],
	onload: function (report) {
		frappe.breadcrumbs.add("Stock");
	},
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "base_rate" && data) {
			value = `<span style="color:var(--red-500)">${value}</span>`;
		}
		return value;
	},
};
