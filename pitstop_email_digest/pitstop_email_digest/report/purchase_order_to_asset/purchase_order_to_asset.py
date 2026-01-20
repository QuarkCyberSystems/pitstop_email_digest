# Copyright (c) 2025, QCS and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns, data = [], []
    columns = get_columns(filters)
    data = get_data(filters)
    data = post_process(data)
    return columns, data


def get_columns(filters):
    columns = [
        {
            "fieldname": "purchase_order",
            "label": "Purchase Order",
            "fieldtype": "Link",
            "options": "Purchase Order",
            "width": 120,
        },
        {
            "fieldname": "item_code",
            "label": "Item",
            "fieldtype": "Link",
            "options": "Item",
            "width": 220,
        },
        {"fieldname": "qty", "label": "Item Qty", "fieldtype": "Float", "width": 220},
        {
            "fieldname": "po_rate",
            "label": "PO Rate",
            "fieldtype": "Currency",
            "width": 220,
        },
        {
            "fieldname": "po_amount",
            "label": "PO Amount",
            "fieldtype": "Currency",
            "width": 220,
        },
        {
            "fieldname": "purchase_invoice",
            "label": "Purchase Invoice",
            "fieldtype": "Link",
            "options": "Purchase Invoice",
            "width": 120,
        },
        {
            "fieldname": "purchase_receipt",
            "label": "Purchase Receipt",
            "fieldtype": "Link",
            "options": "Purchase Receipt",
            "width": 120,
        },
        {
            "fieldname": "asset",
            "label": "Asset",
            "fieldtype": "Link",
            "options": "Asset",
            "width": 120,
        },
        {
            "fieldname": "asset_workflow_state",
            "label": "Asset Workflow State",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "fieldname": "asset_status",
            "label": "Asset Status",
            "fieldtype": "Data",
            "width": 120,
        },
        {
            "fieldname": "gross_purchase_amount",
            "label": "Gross Purchase Amount",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "fieldname": "je_amount",
            "label": "Depreciated Amount",
            "fieldtype": "Currency",
            "width": 120,
        },
        {
            "fieldname": "sale_amount",
            "label": "Sold Amount",
            "fieldtype": "Currency",
            "width": 120,
        },
    ]
    return columns


def get_data(filters):
    condition = ""
    if filters.get("from_date"):
        condition += " and tpo.transaction_date>='{from_date}'".format(
            from_date=filters.get("from_date")
        )

    if filters.get("to_date"):
        condition += " and tpo.transaction_date<='{to_date}'".format(
            to_date=filters.get("to_date")
        )

    if filters.get("item_code"):
        condition += " and tpoi.item_code ='{item_code}'".format(
            item_code=filters.get("item_code")
        )

    return frappe.db.sql(
        """
		SELECT
			tpo.name AS purchase_order,
			tpoi.item_code,
			tpoi.qty,
			tpoi.base_net_rate as po_rate,
			tpoi.base_net_amount as po_amount,
			tpii.parent AS purchase_invoice,
			tpri.parent AS purchase_receipt,
			ta.name AS asset,
			ta.workflow_state as asset_workflow_state,
			ta.status as asset_status,
			ta.gross_purchase_amount AS gross_purchase_amount,
			COALESCE(SUM(jea.credit), 0) AS je_amount,
			COALESCE(SUM(tsii.base_net_amount), 0) AS sale_amount
		FROM
			`tabPurchase Order` tpo
		JOIN
			`tabPurchase Order Item` tpoi
			ON tpoi.parent = tpo.name
		LEFT JOIN
			`tabPurchase Invoice Item` tpii
			ON tpii.purchase_order = tpo.name
			AND tpii.purchase_order_item = tpoi.name
			AND tpii.docstatus = 1
		LEFT JOIN
			`tabPurchase Receipt Item` tpri
			ON tpri.purchase_order = tpo.name
			AND tpri.purchase_order_item = tpoi.name
			AND tpri.docstatus = 1
		LEFT JOIN
			`tabAsset` ta
			ON (
				(
					(ta.purchase_invoice IS NOT NULL AND ta.purchase_invoice = tpii.parent AND ta.item_code = tpii.item_code)
					OR
					(ta.purchase_invoice IS NULL AND ta.purchase_receipt IS NOT NULL AND ta.purchase_receipt = tpri.parent AND ta.item_code = tpri.item_code)
				)
			)
		LEFT JOIN
			`tabJournal Entry Account` jea
			ON jea.reference_type = 'Asset'
			AND jea.reference_name = ta.name
			AND jea.docstatus = 1
		LEFT JOIN
			`tabSales Invoice Item` tsii
			ON tsii.asset = ta.name
			AND tsii.docstatus = 1 and ta.item_code = tsii.item_code
		WHERE
			tpoi.is_fixed_asset = 1
			AND tpo.docstatus = 1 {condition}
		GROUP BY
			tpo.name, tpoi.item_code, ta.name, tpii.parent, tpri.parent;
	""".format(condition=condition),
        as_dict=True,
    )


def post_process(data):
    last_po = last_item = None
    for row in data:
        if row.purchase_order == last_po and row.item_code == last_item:
            row.purchase_order = None
            row.item_code = None
            row.po_rate = None
            row.po_amount = None
            row.purchase_invoice = None
            row.purchase_receipt = None
            row.qty = None
        elif row.purchase_order == last_po:
            row.purchase_order = None
        else:
            last_po = row.purchase_order
            last_item = row.item_code
    return data
