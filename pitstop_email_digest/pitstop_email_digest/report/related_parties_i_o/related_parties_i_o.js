// Copyright (c) 2025, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Related Parties I_O"] = {
	"filters": [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1
		},
		{
			fieldname: "workshop_division",
			label: __("Workshop Division"),
			fieldtype: "Link",
			options: "Vehicle Workshop Division",
			reqd: 0
		},
		{
			fieldname: "project_status",
			label: __("Project Status"),
			fieldtype: "Link",
			options: "Project Status",
			reqd: 0
		},
		{
			fieldname: "current_task_type",
			label: __("Current Task Type"),
			fieldtype: "Link",
			options: "Task Type",
			reqd: 0
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
			reqd: 0
		},
		{
			fieldname: "billing_type",
			label: __("Billing Type"),
			fieldtype: "Select",
			options: ["", "Customer", "Insurance"],
			reqd: 0
		},
		{
			fieldname: "workspace",
			label: __("Workspace"),
			fieldtype: "Link",
			options:"Workspace",
			reqd: 0,
			hidden: 1,
			read_only: 1
		},
		{
			fieldname: "report_link_access_roles_vehicle_mobility_field",
			label: __("Link Access Role"),
			fieldtype: "Data",
			reqd: 0,
			hidden: 1,
			read_only: 1
		}
	],
	onload: function(report) {
		let the_workspace = report.get_filter_value("workspace");
		if(the_workspace) {
			let the_workspace_link = frappe.scrub(the_workspace).replace(/_/g, "-");
			frappe.breadcrumbs.add({
				type: "Custom",
				label: __(the_workspace),
				route: "/app/"+the_workspace_link,
			});
		}
	}
};
