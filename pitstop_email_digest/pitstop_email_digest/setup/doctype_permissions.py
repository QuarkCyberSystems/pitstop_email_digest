import frappe

# Roles that get read-only access to the DocType doctype, and the ptypes each one gets.
DOCTYPE_READ_ROLES = {
    "Customer & Vehicle Viewer": ("read", "report", "export"),
}

PTYPES = (
    "read",
    "write",
    "create",
    "delete",
    "submit",
    "cancel",
    "amend",
    "report",
    "export",
    "import",
    "print",
    "email",
    "share",
    "select",
    "if_owner",
)


def apply_doctype_read_permissions():
    """Grant the configured roles read-only access to the DocType doctype.

    DocType is in frappe's `Meta.special_doctypes`, so `Meta.process()` returns before
    `set_custom_permissions()` runs - Custom DocPerm and the
    `additional_doctype_permissions` hook are both ignored for it. Only standard DocPerm
    rows count, and migrate rebuilds those from frappe's own
    core/doctype/doctype/doctype.json, so they have to be re-applied on every migrate.
    """
    changed = False

    for role, allowed in DOCTYPE_READ_ROLES.items():
        if not frappe.db.exists("Role", role):
            continue

        # every flag is explicit - DocPerm defaults write/create/delete and
        # report/export/share/print/email to 1
        values = {ptype: int(ptype in allowed) for ptype in PTYPES}
        name = frappe.db.get_value(
            "DocPerm", {"parent": "DocType", "role": role, "permlevel": 0}
        )

        if not name:
            frappe.get_doc(
                {
                    "doctype": "DocPerm",
                    "parent": "DocType",
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    "role": role,
                    "permlevel": 0,
                    **values,
                }
            ).insert(ignore_permissions=True)
            changed = True
            continue

        current = frappe.db.get_value("DocPerm", name, list(values), as_dict=True) or {}
        if any(
            int(current.get(ptype) or 0) != value for ptype, value in values.items()
        ):
            frappe.db.set_value("DocPerm", name, values, update_modified=False)
            changed = True

    if changed:
        frappe.clear_cache(doctype="DocType")
