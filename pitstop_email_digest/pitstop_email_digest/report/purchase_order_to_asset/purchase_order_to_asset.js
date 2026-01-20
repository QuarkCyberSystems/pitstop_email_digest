// Copyright (c) 2025, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Purchase Order To Asset"] = {
	filters: [
		{
			fieldtype: "Date",
			label: __("From Date"),
			fieldname: "from_date",
			reqd: 1,
		},
		{
			fieldtype: "Date",
			label: __("To Date"),
			fieldname: "to_date",
			reqd: 1,
		},
		{
			fieldtype: "Link",
			label: __("Item"),
			fieldname: "item_code",
			options: "Item",
			reqd: 0,
			get_query: () => {
				return {
					filters: {
						is_fixed_asset: 1,
					},
				};
			},
		},
		{
			fieldtype: "Link",
			label: __("Asset"),
			fieldname: "asset",
			options: "Asset",
			reqd: 0,
			hidden: 1,
		},
		{
			fieldtype: "Link",
			label: __("Asset Category"),
			fieldname: "asset",
			options: "Asset Category",
			reqd: 0,
			hidden: 1,
		},
	],
};
