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
            COALESCE(opp.opportunity_count, 0) as opportunity_count,
            COALESCE(app.appointment_count, 0) as appointment_count,
            COALESCE(prj.project_count, 0) as project_count,
            COALESCE(sr.net_revenue, 0) as net_revenue,
            COALESCE(nc.new_customer_count, 0) as new_customer_count
        from
            tabCampaign tc
        left join (
            select campaign, count(distinct name) as opportunity_count
            from tabOpportunity
            group by campaign
        ) opp on opp.campaign = tc.name
        left join (
            select campaign, count(distinct name) as appointment_count
            from tabAppointment
            where docstatus = 1
            group by campaign
        ) app on app.campaign = tc.name
        left join (
            select
                ta.campaign,
                count(distinct tp.name) as project_count
            from tabAppointment ta
            join tabProject tp on tp.appointment = ta.name
            group by ta.campaign
        ) prj on prj.campaign = tc.name
        left join (
            select
                ta.campaign,
                sum(tsii.base_net_amount) as net_revenue
            from tabAppointment ta
            join tabProject tp
                on tp.appointment = ta.name
            join `tabSales Invoice Item` tsii
                on tsii.project = tp.name
                and tsii.docstatus = 1
            join `tabSales Invoice` tsi
                on tsi.name = tsii.parent
                and tsi.docstatus = 1
            group by ta.campaign
        ) sr on sr.campaign = tc.name
        left join (
            select
                to2.campaign,
                count(distinct
                    case
                        when to2.opportunity_from = 'Customer' and cust_direct.creation > to2.creation then cust_direct.name
                        when to2.opportunity_from = 'Lead' and cust_from_lead.creation > to2.creation then cust_from_lead.name
                        else null
                    end
                ) as new_customer_count
            from tabOpportunity to2
            left join tabCustomer cust_direct on cust_direct.name = to2.party_name and to2.opportunity_from = 'Customer'
            left join tabLead tl on tl.name = to2.party_name and to2.opportunity_from = 'Lead'
            left join tabCustomer cust_from_lead on cust_from_lead.name = tl.customer
            group by to2.campaign
        ) nc on nc.campaign = tc.name
        where 1=1 {condition}
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
