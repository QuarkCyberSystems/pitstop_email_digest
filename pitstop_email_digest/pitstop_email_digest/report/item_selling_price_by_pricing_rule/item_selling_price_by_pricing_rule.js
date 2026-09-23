// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Item Selling Price by Pricing Rule"] = {
	filters: [
		{
			fieldname: "item_code",
			label: __("Item"),
			fieldtype: "Link",
			options: "Item",
			get_query: () => ({
				query: "erpnext.controllers.queries.item_query",
				filters: { include_disabled: 1 },
			}),
		},
		{
			fieldname: "posting_date",
			label: __("Posting Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
			// valuation and last purchase rate are per warehouse; leaving this empty
			// reports them across all warehouses
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (column.fieldname === "selling_price" && data && !data.selling_price) {
			// no rate could be worked out - say why instead of showing a bare 0.00
			return `<span class="text-muted">${frappe.utils.escape_html(data.based_on || "")}</span>`;
		}

		return value;
	},
};
