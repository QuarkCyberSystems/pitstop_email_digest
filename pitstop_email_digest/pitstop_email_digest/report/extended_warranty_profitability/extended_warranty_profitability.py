# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Sales Invoice"),
            "fieldname": "sales_invoice",
            "fieldtype": "Link",
            "options": "Sales Invoice",
            "width": 180,
        },
        {
            "label": _("Income"),
            "fieldname": "income",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Expense"),
            "fieldname": "expense",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Profit"),
            "fieldname": "profit",
            "fieldtype": "Currency",
            "width": 140,
        },
        {
            "label": _("Journal Entries"),
            "fieldname": "journal_entries",
            "fieldtype": "Data",
            "width": 260,
        },
    ]


def get_data(filters):
    conditions = get_conditions(filters)

    data = frappe.db.sql(
        """
        SELECT
            si.posting_date,
            si.name AS sales_invoice,
            SUM(sii.base_net_amount) AS income,
            COALESCE(
                (
                    SELECT SUM(jea.credit_in_account_currency)
                    FROM `tabJournal Entry Account` jea
                    INNER JOIN `tabJournal Entry` je
                        ON je.name = jea.parent
                    WHERE je.extended_warranty_voucher = si.name
                      AND je.docstatus = 1
                ),
                0
            ) AS expense,
            SUM(sii.base_net_amount) -
            COALESCE(
                (
                    SELECT SUM(jea.credit_in_account_currency)
                    FROM `tabJournal Entry Account` jea
                    INNER JOIN `tabJournal Entry` je
                        ON je.name = jea.parent
                    WHERE je.extended_warranty_voucher = si.name
                      AND je.docstatus = 1
                ),
                0
            ) AS profit,
            GROUP_CONCAT(
                DISTINCT linked_je.name
                SEPARATOR ', '
            ) AS journal_entries
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii
            ON sii.parent = si.name
            AND sii.is_extended_warranty = 1
        LEFT JOIN `tabJournal Entry` linked_je
            ON linked_je.extended_warranty_voucher = si.name
            AND linked_je.docstatus = 1
        WHERE si.docstatus = 1
          {conditions}
        GROUP BY
            si.posting_date,
            si.name
        ORDER BY si.posting_date DESC
        """.format(conditions=conditions),
        filters,
        as_dict=True,
    )

    return data


def get_conditions(filters):
    conditions = []

    if filters.get("from_date"):
        conditions.append("AND si.posting_date >= %(from_date)s")

    if filters.get("to_date"):
        conditions.append("AND si.posting_date <= %(to_date)s")

    return " ".join(conditions)
