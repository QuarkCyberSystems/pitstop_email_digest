// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Aged Pending Purchase Orders"] = {
	filters: [
		{
			fieldname: "as_on_date",
			label: __("As On Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "min_age",
			label: __("Minimum Age (Days)"),
			fieldtype: "Int",
			default: 90,
			reqd: 1,
		},
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
		},
	],

	onload: function (report) {
		report.page.add_inner_button(__("Close"), function () {
			let data = frappe.query_report.get_checked_items() || [];
			let names = [...new Set(data.map((d) => d.purchase_order).filter(Boolean))];

			if (!names.length) {
				frappe.msgprint(__("Please select at least one Purchase Order."));
				return;
			}

			frappe.confirm(
				__("Are you sure you want to close {0} Purchase Order(s)?", [names.length]),
				function () {
					frappe.call({
						method: "erpnext.buying.doctype.purchase_order.purchase_order.close_or_unclose_purchase_orders",
						args: {
							names: JSON.stringify(names),
							status: "Closed",
						},
						freeze: true,
						freeze_message: __("Closing Purchase Orders..."),
						callback: function () {
							frappe.show_alert({
								message: __("{0} Purchase Order(s) closed", [names.length]),
								indicator: "green",
							});
							frappe.query_report.refresh();
						},
					});
				}
			);
		});
		frappe.breadcrumbs.add("Buying");
	},

	get_datatable_options(options) {
		return Object.assign(options, {
			checkboxColumn: true,
		});
	},
};
