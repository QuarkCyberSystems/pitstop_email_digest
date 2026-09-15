"""Backfill employee_name / designation on existing Target Role records.

Both fields are now fetched from Employee, but fetch_from only populates on
save, so existing rows stay empty until they are touched.
"""

import frappe


def execute():
    if not frappe.db.table_exists("Target Role"):
        return

    for column in ("employee_name", "designation"):
        if not frappe.db.has_column("Target Role", column):
            return

    rows = frappe.db.get_all(
        "Target Role",
        filters={"employee": ["is", "set"]},
        fields=["name", "employee", "employee_name", "designation"],
    )

    for row in rows:
        employee = frappe.db.get_value(
            "Employee",
            row.employee,
            ["employee_name", "designation"],
            as_dict=True,
        )

        if not employee:
            continue

        values = {}
        if row.employee_name != employee.employee_name:
            values["employee_name"] = employee.employee_name
        if row.designation != employee.designation:
            values["designation"] = employee.designation

        if values:
            frappe.db.set_value("Target Role", row.name, values, update_modified=False)
