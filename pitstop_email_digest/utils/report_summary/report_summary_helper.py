import frappe
from automotive.automotive.report.workshop_productivity.workshop_productivity import (
    execute as WorkshopProductivityReportExecute,
)
from automotive.automotive.report.workshop_turnover.workshop_turnover import (
    execute as WorkshopTurnoverReportExecute,
)


def get_workshop_productivity_summary_details(start_date, end_date, company=None):
    """
    Get the workshop turnover summary details for the given date range.
    """
    filters = {
        "from_date": start_date,
        "to_date": end_date,
        "company": company or frappe.get_cached_value("Global Defaults", None, "default_company"),
    }
    totals_summaryreport = WorkshopProductivityReportExecute(filters)

    return totals_summaryreport[-1]


def get_workshop_turnover_summary_details(start_date, end_date, company=None):
    """
    Get the workshop turnover summary details for the given date range.
    """
    filters = {
        "from_date": start_date,
        "to_date": end_date,
        "company": company or frappe.get_cached_value("Global Defaults", None, "default_company"),
    }
    totals_summaryreport = WorkshopTurnoverReportExecute(filters)

    return totals_summaryreport[-1]
