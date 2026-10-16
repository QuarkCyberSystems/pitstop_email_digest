import frappe


def execute():
    """Move Target Role's `branch` from the Custom Field to the standard DocType field."""
    custom_field = "Target Role-branch"
    if not frappe.db.exists("Custom Field", custom_field):
        return

    # Snapshot existing values before removing the custom field
    existing = {}
    if frappe.db.has_column("Target Role", "branch"):
        existing = dict(
            frappe.db.sql(
                "select name, branch from `tabTarget Role` where ifnull(branch, '') != ''"
            )
        )

    frappe.delete_doc("Custom Field", custom_field, ignore_permissions=True, force=True)
    frappe.reload_doc("pitstop_email_digest", "doctype", "target_role", force=True)

    # Map old values onto the standard field wherever it is still empty
    for name, branch in existing.items():
        if not frappe.db.get_value("Target Role", name, "branch"):
            frappe.db.set_value(
                "Target Role", name, "branch", branch, update_modified=False
            )
