# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns, data = get_columns(filters), get_data(filters)
    return columns, data


def get_columns(filters):
    columns = [
        {
            "label": _("Campaign"),
            "fieldname": "campaign",
            "fieldtype": "Link",
            "options": "Campaign",
            "width": 120,
        },
        {
            "label": _("Opportunity Count"),
            "fieldname": "opportunity_count",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("New Customer Count"),
            "fieldname": "new_customer_count",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": _("Appointment Count"),
            "fieldname": "appointment_count",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Repair Order Count"),
            "fieldname": "project_count",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": _("Net Revenue"),
            "fieldname": "net_revenue",
            "fieldtype": "Currency",
            "width": 120,
            "default": 0.0,
        },
    ]
    return columns


def get_data(filters):
    condition_dict, condition = get_condition(filters)

    return frappe.db.sql(
        f"""
		select
			tc.name as campaign,
			count(to2.name) as opportunity_count,
			count(ta.name) as appointment_count,
			count(tp.name) as project_count,
			COALESCE(sum(tsii.base_net_amount), 0) as net_revenue,
			count(distinct
				case
					when to2.opportunity_from = 'Customer'
						and cust_direct.creation > to2.creation
					then cust_direct.name

					when to2.opportunity_from = 'Lead'
						and cust_from_lead.creation > to2.creation
					then cust_from_lead.name

					else null
				end
			) as new_customer_count
		from
			tabCampaign tc
		left join
			tabOpportunity to2
		on
			to2.campaign = tc.name
		left join
			tabAppointment ta
		on
			ta.campaign = tc.name  and ta.docstatus = 1 and ta.opportunity = to2.name
		left join
			tabProject tp
		on
			tp.appointment = ta.name
		left join
			`tabSales Invoice Item` tsii
		on
			tsii.project = tp.name and tsii.docstatus = 1
		left join
			`tabSales Invoice` tsi
		on
			tsi.name = tsii.parent and tsi.docstatus = 1
		left join
			tabCustomer cust_direct
		on
			cust_direct.name = to2.party_name and to2.opportunity_from = 'Customer'
		left join
			tabLead tl
		on
			tl.name = to2.party_name and to2.opportunity_from = 'Lead'
		left join
			tabCustomer cust_from_lead
		on
			cust_from_lead.name = tl.customer
		where
			1=1 {condition}
		group by
			tc.name;
	""",
        condition_dict,
        as_dict=True,
    )


def get_condition(filters):
    condition_dict = {
        "campaign": filters.get("campaign"),
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "cost_center": filters.get("cost_center"),
    }
    condition = ""
    if filters.get("campaign"):
        condition += " and tc.name = %(campaign)s"

    if filters.get("from_date"):
        condition += " and to2.transaction_date >= %(from_date)s"

    if filters.get("to_date"):
        condition += " and to2.transaction_date <= %(to_date)s"

    if filters.get("cost_center"):
        condition += " and tp.cost_center <= %(cost_center)s"
    return condition_dict, condition
