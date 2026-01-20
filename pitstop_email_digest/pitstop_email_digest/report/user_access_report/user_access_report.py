# Copyright (c) 2025, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
    columns, data = [], []
    columns = get_column(filters)
    data = get_data(filters)
    data = post_process(data)
    return columns, data


def get_column(filters):
    columns = [
        {
            "label": _("User"),
            "fieldname": "user",
            "fieldtype": "Link",
            "options": "User",
            "width": 200,
        },
        {
            "label": _("Role Profile"),
            "fieldname": "role_profile_name",
            "fieldtype": "Link",
            "options": "Role Profile",
            "width": 200,
        },
        {
            "label": _("Role"),
            "fieldname": "user_role",
            "fieldtype": "Link",
            "options": "Role",
            "width": 150,
        },
        {
            "label": _("Doctype"),
            "fieldname": "doctype",
            "fieldtype": "Link",
            "options": "Doctype",
            "width": 100,
        },
        {
            "label": _("If Owner"),
            "fieldname": "if_owner",
            "fieldtype": "Check",
            "width": 70,
        },
        {
            "label": _("Permission Level"),
            "fieldname": "permlevel",
            "fieldtype": "Data",
            "width": 90,
        },
        {
            "label": _("Read Permission"),
            "fieldname": "read_perm",
            "fieldtype": "Check",
            "width": 85,
        },
        {
            "label": _("Write Permission"),
            "fieldname": "write_perm",
            "fieldtype": "Check",
            "width": 85,
        },
        {
            "label": _("Create Permission"),
            "fieldname": "create_perm",
            "fieldtype": "Check",
            "width": 85,
        },
        {
            "label": _("Submit Permission"),
            "fieldname": "submit_perm",
            "fieldtype": "Check",
            "width": 85,
        },
        {
            "label": _("Cancel Permission"),
            "fieldname": "cancel_perm",
            "fieldtype": "Check",
            "width": 85,
        },
        {
            "label": _("Amend Permission"),
            "fieldname": "amend_perm",
            "fieldtype": "Check",
            "width": 85,
        },
    ]
    return columns


def get_data(filters):
    condition = ""
    if filters.get("user"):
        condition += "and u.name = '{user}'".format(user=filters.get("user"))
    if filters.get("doctype"):
        condition += "and dp.parent = '{doctype}'".format(
            doctype=filters.get("doctype")
        )
    if filters.get("submit_permission"):
        condition += "and dp.`submit` = '{submit_permission}'".format(
            submit_permission=filters.get("submit_permission")
        )
    if filters.get("cancel_permission"):
        condition += "and dp.`cancel` = '{cancel_permission}'".format(
            cancel_permission=filters.get("cancel_permission")
        )
    if filters.get("amend_permission"):
        condition += "and dp.`amend` = '{amend_permission}'".format(
            amend_permission=filters.get("amend_permission")
        )
    if filters.get("write_permission"):
        condition += "and dp.`write` = '{write_permission}'".format(
            write_permission=filters.get("write_permission")
        )
    if filters.get("read_permission"):
        condition += "and dp.`read` = '{read_permission}'".format(
            read_permission=filters.get("read_permission")
        )
    if filters.get("create_permission"):
        condition += "and dp.`create` = '{create_permission}'".format(
            create_permission=filters.get("create_permission")
        )
    if filters.get("role"):
        condition += "and hr.role = '{role}'".format(role=filters.get("role"))

    return frappe.db.sql(
        """
		SELECT
			u.name AS user,
			u.role_profile_name,
			hr.role AS user_role,
			dp.parent AS doctype,
			dp.`read` AS read_perm,
			dp.`write` AS write_perm,
			dp.`create` AS create_perm,
			dp.`submit` AS submit_perm,
			dp.`cancel` AS cancel_perm,
			dp.`amend` AS amend_perm,
			dp.`if_owner` AS if_owner,
			dp.permlevel AS permlevel
		FROM `tabUser` u
		LEFT JOIN `tabHas Role` hr
			ON hr.parent = u.name AND hr.parenttype = 'User'
		LEFT JOIN `tabDocPerm` dp
			ON dp.role = hr.role
		WHERE u.enabled = 1 and dp.parent is not null {condition}
		ORDER BY u.name, hr.role, dp.parent;
	""".format(condition=condition),
        as_dict=True,
    )


def post_process(data):
    last_user = last_role_profile_name = last_user_role = None
    for row in data:
        if (
            row.user == last_user
            and row.role_profile_name == last_role_profile_name
            and row.user_role == last_user_role
        ):
            row.user = None
            row.role_profile_name = None
            row.user_role = None
        elif row.user == last_user and row.role_profile_name == last_role_profile_name:
            last_user_role = row.user_role
            row.user = None
            row.role_profile_name = None
        elif row.user == last_user:
            row.user = None
            last_role_profile_name = row.role_profile_name
            last_user_role = row.user_role
        else:
            last_user = row.user
            last_role_profile_name = row.role_profile_name
            last_user_role = row.user_role
    return data
