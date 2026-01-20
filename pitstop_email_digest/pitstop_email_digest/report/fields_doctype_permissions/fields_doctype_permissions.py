# Copyright (c) 2025, QCS and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "DocType", "fieldname": "doctype", "fieldtype": "Data", "width": 180},
        {
            "label": "Fieldname",
            "fieldname": "fieldname",
            "fieldtype": "Data",
            "width": 160,
        },
        {
            "label": "Field Label",
            "fieldname": "label",
            "fieldtype": "Data",
            "width": 180,
        },
        {
            "label": "Fieldtype",
            "fieldname": "fieldtype",
            "fieldtype": "Data",
            "width": 120,
        },
        {"label": "Role", "fieldname": "role", "fieldtype": "Data", "width": 160},
        {
            "label": "Perm Level",
            "fieldname": "permlevel",
            "fieldtype": "Int",
            "width": 90,
        },
        {"label": "Read", "fieldname": "read", "fieldtype": "Check", "width": 60},
        {"label": "Write", "fieldname": "write", "fieldtype": "Check", "width": 60},
        {"label": "Create", "fieldname": "create", "fieldtype": "Check", "width": 60},
        {"label": "Submit", "fieldname": "submit", "fieldtype": "Check", "width": 60},
        {"label": "Cancel", "fieldname": "cancel", "fieldtype": "Check", "width": 60},
        {"label": "Amend", "fieldname": "amend", "fieldtype": "Check", "width": 60},
    ]


def get_data(filters):
    condition = ""
    if filters.get("doctype"):
        condition += " and dt.name = '{doctype}'".format(doctype=filters.get("doctype"))

    if filters.get("permlevel"):
        condition += " and p.permlevel = '{permlevel}'".format(permlevel=filters.get("permlevel"))

    if filters.get("role"):
        condition += " and p.role = '{role}'".format(role=filters.get("role"))

    return frappe.db.sql(
        """
		SELECT
			dt.name AS doctype,
			df.fieldname,
			df.label,
			df.fieldtype,
			p.role,
			p.permlevel,
			p.read,
			p.write,
			p.create,
			p.submit,
			p.cancel,
			p.amend
		FROM tabDocType dt
		INNER JOIN tabDocField df
			ON df.parent = dt.name
		LEFT JOIN tabDocPerm p
			ON p.parent = dt.name
		WHERE
			dt.istable = 0
			AND dt.custom = 0 {condition}
		ORDER BY
			dt.name, df.idx, p.permlevel
	""".format(condition=condition),
        as_dict=True,
    )
