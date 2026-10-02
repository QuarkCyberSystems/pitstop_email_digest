# Copyright (c) 2025, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.query_report import group_report_data

GROUP_BY_FIELD_MAP = {
    "Group By Role Profile": "role_profile_name",
    "Group By Role": "user_role",
    "Group By Doctype": "doctype",
}

PERMISSION_FIELDS = [
    "if_owner",
    "read_perm",
    "write_perm",
    "create_perm",
    "submit_perm",
    "cancel_perm",
    "amend_perm",
    "delete_perm",
]

# Filters bound into the query. Blank ones are passed as NULL, which switches
# their condition off.
FILTER_FIELDS = (
    "user",
    "role",
    "doctype",
    "read_permission",
    "write_permission",
    "create_permission",
    "submit_permission",
    "cancel_permission",
    "amend_permission",
    "delete_permission",
)


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_column(filters)
    data = get_data(filters)

    group_field = GROUP_BY_FIELD_MAP.get(filters.get("group_by_1"))
    if group_field:
        data = group_report_data(
            data,
            [None, group_field],
            calculate_totals=calculate_group_totals,
        )
        return columns, data

    data = post_process(data)
    return columns, data


def calculate_group_totals(data, group_field, group_value, grouped_by):
    totals = frappe._dict()
    for f, g in grouped_by.items():
        totals[f] = g

    for f in PERMISSION_FIELDS:
        totals[f] = 1 if any(row.get(f) for row in data) else 0

    return totals


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
        {
            "label": _("Delete Permission"),
            "fieldname": "delete_perm",
            "fieldtype": "Check",
            "width": 85,
        },
    ]
    return columns


def get_data(filters):
    return frappe.db.sql(
        """
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
			AND hr.parenttype = 'User'
			AND (%(role)s is null or hr.role = %(role)s)
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
			ON dp.role = hr.role
			AND (%(doctype)s is null or dp.parent = %(doctype)s)
			AND (%(read_permission)s is null or dp.`read` = %(read_permission)s)
			AND (%(write_permission)s is null or dp.`write` = %(write_permission)s)
			AND (%(create_permission)s is null or dp.`create` = %(create_permission)s)
			AND (%(submit_permission)s is null or dp.`submit` = %(submit_permission)s)
			AND (%(cancel_permission)s is null or dp.`cancel` = %(cancel_permission)s)
			AND (%(amend_permission)s is null or dp.`amend` = %(amend_permission)s)
			AND (%(delete_permission)s is null or dp.`delete` = %(delete_permission)s)
		WHERE u.enabled = 1
			AND (%(user)s is null or u.name = %(user)s)
		ORDER BY u.name, hr.role, dp.parent;
	""",
        get_filter_values(filters),
        as_dict=True,
    )


def get_filter_values(filters):
    """Bind every supported filter, passing NULL for the ones left blank."""
    filters = filters or {}

    return {fieldname: filters.get(fieldname) or None for fieldname in FILTER_FIELDS}


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
