# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data


def get_columns(filters):
    columns = [
        {
            "label": _(f"{filters.get('purchase_document')}"),
            "fieldname": "name",
            "fieldtype": "Link",
            "options": f"{filters.get('purchase_document')}",
            "width": 120,
        },
        {
            "label": _("Posting Date"),
            "fieldname": "transaction_date",
            "fieldtype": "Date",
            "width": 120,
        },
        {
            "label": _("Supplier"),
            "fieldname": "supplier",
            "fieldtype": "Link",
            "options": "Supplier",
            "hidden": 1,
            "width": 120,
        },
        {
            "label": _("Supplier Name"),
            "fieldname": "supplier_name",
            "fieldtype": "Data",
            "hidden": 1,
            "width": 120,
        },
        {
            "label": _("Net Total"),
            "fieldname": "net_total",
            "fieldtype": "Currency",
            "options": "currency",
            "hidden": 1,
            "width": 120,
        },
        {
            "label": _("Is Stock Item"),
            "fieldname": "is_stock_item",
            "fieldtype": "Check",
            "width": 120,
        },
        {
            "label": _("Item Code"),
            "fieldname": "item_code",
            "fieldtype": "Link",
            "options": "Item",
            "width": 100,
        },
        {
            "label": _("Item Name"),
            "fieldname": "item_name",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "label": _("Qty"),
            "fieldname": "qty",
            "fieldtype": "Data",
            "hidden": 1,
            "width": 80,
        },
        {
            "label": _("Net Rate"),
            "fieldname": "base_net_rate",
            "fieldtype": "Currency",
            "hidden": 1,
            "width": 100,
        },
        {
            "label": _("Net Amount"),
            "fieldname": "base_net_amount",
            "fieldtype": "Currency",
            "hidden": 1,
            "width": 100,
        },
    ]
    return columns


def get_data(filters):
    purchase_doctype, date_field, condition_dict, condition = get_condition(filters)

    return frappe.db.sql(
        f"""
		SELECT
			CASE
				WHEN ROW_NUMBER() OVER (PARTITION BY tpo.name ORDER BY tpoi.idx) = 1
				THEN tpo.name
				ELSE ''
			END AS name,
			CASE
				WHEN ROW_NUMBER() OVER (PARTITION BY tpo.name ORDER BY tpoi.idx) = 1
				THEN tpo.{date_field}
				ELSE NULL
			END AS transaction_date,
			CASE
				WHEN ROW_NUMBER() OVER (PARTITION BY tpo.name ORDER BY tpoi.idx) = 1
				THEN tpo.supplier
				ELSE NULL
			END AS supplier,
			CASE
				WHEN ROW_NUMBER() OVER (PARTITION BY tpo.name ORDER BY tpoi.idx) = 1
				THEN tpo.supplier
				ELSE NULL
			END AS supplier_name,
			CASE
				WHEN ROW_NUMBER() OVER (PARTITION BY tpo.name ORDER BY tpoi.idx) = 1
				THEN tpo.net_total
				ELSE NULL
			END AS net_total,
			tpoi.item_code,
			tpoi.item_name,
			tpoi.qty,
			tpoi.base_net_rate,
			tpoi.base_net_amount,
			ti.is_stock_item
		FROM
			`tab{purchase_doctype}` tpo
		JOIN
			`tab{purchase_doctype} Item` tpoi
			ON tpoi.parent = tpo.name
		JOIN
			`tabItem` ti
			ON ti.name = tpoi.item_code
		WHERE
			1=1 {condition}
		ORDER BY
			tpo.name, tpoi.idx;
	""",
        condition_dict,
        as_dict=True,
    )


def get_condition(filters):
    document_status_dict = {"Submitted": 1, "Draft": 0, "Cancelled": 2}

    purchase_doctype = filters.get("purchase_document")
    # Decide date field
    if purchase_doctype in ["Purchase Invoice", "Purchase Receipt"]:
        date_field = "posting_date"
    else:
        date_field = "transaction_date"

    condition_dict = {
        "from_date": filters.get("from_date"),
        "to_date": filters.get("to_date"),
        "cost_center": filters.get("cost_center"),
        "document_status": filters.get("document_status"),
        "is_stock": filters.get("is_stock"),
    }
    condition = ""

    if filters.get("from_date"):
        condition += f" and tpo.{date_field} >= %(from_date)s"

    if filters.get("to_date"):
        condition += f" and tpo.{date_field} <= %(to_date)s"

    if filters.get("cost_center"):
        condition += " and tpo.cost_center <= %(cost_center)s"

    if filters.get("document_status"):
        condition += f" and tpo.docstatus = {document_status_dict.get(filters.get('document_status'))}"

    condition += f" and ti.is_stock_item = {filters.get('is_stock') if filters.get('is_stock') else 0}"

    return purchase_doctype, date_field, condition_dict, condition
