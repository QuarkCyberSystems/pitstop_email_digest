// Copyright (c) 2025, QCS and contributors
// For license information, please see license.txt

frappe.query_reports["Campaign Revenue Report"] = {
  filters: [
    {
      fieldname: "from_date",
      label: __("From Date"),
      fieldtype: "Date",
      default: frappe.datetime.get_today(),
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
    },
    {
      fieldname: "campaign",
      label: __("Campaign"),
      fieldtype: "Link",
      options: "Campaign",
      reqd: 0,
    },
  ],
};
