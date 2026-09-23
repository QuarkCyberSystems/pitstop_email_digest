// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["System vs Physical Stock Comparison"] = {
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
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
			reqd: 1,
			on_change() {
				// a snapshot belongs to one branch, so changing the branch invalidates
				// whatever was picked. Clearing the branch is already handled by the
				// depends_on below, which hides these and resets them.
				if (!frappe.query_report.get_filter_value("physical_stock_snapshot")) {
					return;
				}

				frappe.query_report.set_filter_value({
					physical_stock_snapshot: "",
					upload_date: "",
				});
			},
		},
		{
			fieldname: "date",
			label: __("Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "physical_stock_snapshot",
			label: __("Physical Stock Snapshot"),
			fieldtype: "Link",
			options: "Physical Stock Snapshot",
			// only offered once a branch is chosen; clearing the branch hides this
			// again and resets it
			depends_on: "eval: doc.branch",
			get_query() {
				const branch = frappe.query_report.get_filter_value("branch");
				return { filters: branch ? { branch } : {} };
			},
			on_change() {
				const snapshot = frappe.query_report.get_filter_value("physical_stock_snapshot");

				if (!snapshot) {
					frappe.query_report.set_filter_value("upload_date", "");
					return;
				}

				// the snapshot carries posting_date -- there is no upload_date on it
				frappe.db.get_value("Physical Stock Snapshot", snapshot, "posting_date").then((r) => {
					frappe.query_report.set_filter_value(
						"upload_date",
						(r.message && r.message.posting_date) || ""
					);
				});
			},
		},
		{
			fieldname: "upload_date",
			label: __("Upload Date"),
			fieldtype: "Date",
			read_only: 1,
			depends_on: "eval: doc.branch",
		},
		{
			fieldname: "hide_balance_qty",
			label: __("Hide Balance Qty"),
			fieldtype: "Check",
			default: 0,
		},
	],
};
