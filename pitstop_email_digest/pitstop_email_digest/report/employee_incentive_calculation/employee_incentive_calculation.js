// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Employee Incentive Calculation"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
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
			fieldname: "based_on",
			label: __("Based On"),
			fieldtype: "Select",
			options: ["Technician"],
			default: "Technician",
			reqd: 1,
		},
		{
			fieldname: "base_incentive",
			label: __("Base Incentive"),
			fieldtype: "Float",
			reqd: 0,
		},
		{
			label: "Below 85%",
			fieldname: "below_85",
			fieldtype: "Float",
			reqd: 0,
		},
		{
			label: "Between 85 and 100",
			fieldname: "between_85_and_100",
			fieldtype: "Float",
			reqd: 0,
		},
		{
			label: "Between 100 and 115",
			fieldname: "between_100_and_115",
			fieldtype: "Float",
			reqd: 0,
		},
		{
			label: "Between 115 and 125",
			fieldname: "between_115_and_125",
			fieldtype: "Float",
			reqd: 0,
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		let style = {};
		if (column.fieldname === "below_85" && data && data.per_efficiency < 85) {
			style["background-color"] = "#a0edff";
		} else if (
			column.fieldname === "between_85_and_100" &&
			data &&
			data.per_efficiency >= 85 &&
			data.per_efficiency < 100
		) {
			style["background-color"] = "#a0edff";
		} else if (
			column.fieldname === "between_100_and_115" &&
			data &&
			data.per_efficiency >= 100 &&
			data.per_efficiency < 115
		) {
			style["background-color"] = "#a0edff";
		} else if (
			column.fieldname === "between_115_and_125" &&
			data &&
			data.per_efficiency >= 115 &&
			data.per_efficiency <= 125
		) {
			style["background-color"] = "#a0edff";
		}

		return default_formatter(value, row, column, data, { css: style });
	},
	get_datatable_options(options) {
		return Object.assign(options, {
			hooks: {
				columnTotal: function (values, column, type) {
					if (
						in_list(
							[
								"base_incentive",
								"below_85",
								"between_85_and_100",
								"between_100_and_115",
								"between_115_and_125",
								"per_efficiency",
							],
							column.column.fieldname
						)
					) {
						return "";
					} else {
						return frappe.utils.report_column_total(values, column, type);
					}
				},
			},
		});
	},
	onload: function (report) {
		frappe.breadcrumbs.add("HR");
	},
};
