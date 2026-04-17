// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

const INCENTIVE_FIELD_MAP = {
	below_85: [null, 85],
	between_85_and_100: [85, 100],
	between_100_and_115: [100, 115],
	between_115_and_125: [115, 125],
	above_125: [125, null],
};

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
			options: ["Technician"], // Team Lead
			default: "Technician",
			reqd: 1,
		},
		{
			fieldname: "base_incentive",
			label: __("Base Incentive"),
			fieldtype: "Float",
			default: 350.0,
			reqd: 0,
		},
		{
			label: "Below 85%",
			fieldname: "below_85",
			fieldtype: "Float",
			default: 1.0,
			reqd: 0,
		},
		{
			label: "Between 85 and 100",
			fieldname: "between_85_and_100",
			fieldtype: "Float",
			default: 1.1,
			reqd: 0,
		},
		{
			label: "Between 100 and 115",
			fieldname: "between_100_and_115",
			fieldtype: "Float",
			default: 1.15,
			reqd: 0,
		},
		{
			label: "Between 115 and 125",
			fieldname: "between_115_and_125",
			fieldtype: "Float",
			default: 1.2,
			reqd: 0,
		},
		{
			label: "Above 125",
			fieldname: "above_125",
			fieldtype: "Float",
			default: 1.2,
			reqd: 0,
		},
		{
			label: "Efficiency Filter",
			fieldname: "efficiency_filter",
			fieldtype: "Select",
			options: [
				"",
				"below_85",
				"between_85_and_100",
				"between_100_and_115",
				"between_115_and_125",
				"above_125",
			],
			reqd: 0,
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		if (data && column.fieldname === "customer_overall_rating") {
			if (data.ro_count_cfb) {
				let convert_into_out_of_five = data.customer_overall_rating_value
					? (data.customer_overall_rating_value / 0.2).toFixed(1)
					: 0.0;
				value = default_formatter(value, row, column, data);
				let updated_value = value;
				updated_value = updated_value.replace(
					'<div class="rating">',
					`<div class="rating">
						<span style="font-weight:600; margin-right:6px;">
							${convert_into_out_of_five}
						</span>`
				);

				return updated_value.replace(
					"</div>",
					`
						<span style="font-weight:600; margin-left:6px;">
							(${data.ro_count_cfb})
						</span>
					</div>
					`
				);
			} else {
				return default_formatter(value, row, column, data);
			}
		}

		let style = {};
		if (data) {
			const efficiency = data.per_efficiency || 0;
			const efficiency_cap = getEfficiencyCap(efficiency);

			if (efficiency_cap === column.fieldname) {
				style["background-color"] = "#a0edff";
			}
		}

		return default_formatter(value, row, column, data);
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
								"above_125",
								"customer_overall_rating",
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

function getEfficiencyCap(efficiency) {
	for (const [key, [min, max]] of Object.entries(INCENTIVE_FIELD_MAP)) {
		if (min !== null && efficiency < min) continue;
		if (max !== null && efficiency >= max) continue;
		return key;
	}
	return null;
}
