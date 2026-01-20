// Copyright (c) 2025, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Vehicle WIP Aging"] = {
	filters: [
		{
			fieldname: "vehicle_workshop",
			label: __("Workshop"),
			fieldtype: "Link",
			options: "Vehicle Workshop",
			width: "150px",
		},
		{
			fieldname: "as_of",
			label: __("Age As Of"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
	],
};
