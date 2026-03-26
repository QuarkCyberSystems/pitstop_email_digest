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
    (
        condition_values_dict,
        condition,
        doc_permission_condition,
        has_role_condition,
    ) = get_conditions_and_values(filters)

    return frappe.db.sql(
        f"""
		SELECT
			u.name AS user,
			u.role_profile_name,
			hr.role AS user_role,
			dp.parenttype,
			dp.parent AS doctype,
			dp.role,
			dp.permlevel,
			dp.`read` as read_perm,
			dp.`write` as write_perm,
			dp.`create` as create_perm,
			dp.`submit` as submit_perm,
			dp.`cancel` as cancel_perm,
			dp.`amend` as amend_perm,
			dp.`delete` as delete_perm,
			dp.`report`,
			dp.`export`,
			dp.`import`,
			dp.`share`,
			dp.`print`,
			dp.`email`,
			dp.`if_owner` as if_owner
		FROM `tabUser` u
		JOIN `tabHas Role` hr
			ON hr.parent = u.name
			AND hr.parenttype = 'User' {has_role_condition}
		JOIN (
			SELECT
				'DocType' AS parenttype,
				parent,
				role,
				permlevel,
				`read`,
				`write`,
				`create`,
				`submit`,
				`cancel`,
				`amend`,
				`delete`,
				`report`,
				`export`,
				`import`,
				`share`,
				`print`,
				`email`,
				`if_owner`
			FROM `tabCustom DocPerm`
			UNION ALL
			SELECT
				dp.parenttype,
				dp.parent,
				dp.role,
				dp.permlevel,
				dp.`read`,
				dp.`write`,
				dp.`create`,
				dp.`submit`,
				dp.`cancel`,
				dp.`amend`,
				dp.`delete`,
				dp.`report`,
				dp.`export`,
				dp.`import`,
				dp.`share`,
				dp.`print`,
				dp.`email`,
				dp.`if_owner`
			FROM `tabDocPerm` dp
			WHERE NOT EXISTS (
				SELECT 1
				FROM `tabCustom DocPerm` cdp
				WHERE cdp.parent = dp.parent
				AND cdp.permlevel = dp.permlevel
			)
		) dp
			ON dp.role = hr.role {doc_permission_condition}
		WHERE u.enabled = 1 {condition}
		ORDER BY u.name, hr.role, dp.parent;
	""",
        condition_values_dict,
        as_dict=True,
    )


def get_conditions_and_values(filters):
    condition_values_dict = {}
    condition = ""
    doc_permission_condition = ""
    has_role_condition = ""
    if filters.get("user"):
        condition += "and u.name = %(user)s"
        condition_values_dict["user"] = filters.get("user")

    if filters.get("doctype"):
        doc_permission_condition += "and dp.parent = %(doctype)s"
        condition_values_dict["doctype"] = filters.get("doctype")

    if filters.get("submit_permission"):
        doc_permission_condition += "and dp.`submit` = %(submit_permission)s"
        condition_values_dict["submit_permission"] = filters.get("submit_permission")

    if filters.get("cancel_permission"):
        doc_permission_condition += "and dp.`cancel` = %(cancel_permission)s"
        condition_values_dict["cancel_permission"] = filters.get("cancel_permission")

    if filters.get("amend_permission"):
        doc_permission_condition += "and dp.`amend` = %(amend_permission)s"
        condition_values_dict["amend_permission"] = filters.get("amend_permission")

    if filters.get("write_permission"):
        doc_permission_condition += "and dp.`write` = %(write_permission)s"
        condition_values_dict["write_permission"] = filters.get("write_permission")

    if filters.get("read_permission"):
        doc_permission_condition += "and dp.`read` = %(read_permission)s"
        condition_values_dict["read_permission"] = filters.get("read_permission")

    if filters.get("create_permission"):
        doc_permission_condition += "and dp.`create` = %(create_permission)s"
        condition_values_dict["create_permission"] = filters.get("create_permission")

    if filters.get("role"):
        has_role_condition += "and hr.role = %(role)s"
        condition_values_dict["role"] = filters.get("role")

    return (
        condition_values_dict,
        condition,
        doc_permission_condition,
        has_role_condition,
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
