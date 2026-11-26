# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, now_datetime

ACCOUNT_METHOD = "Update Account Number and Name"
USER_METHOD = "Rename User"

METHOD_DOCTYPE = {
    ACCOUNT_METHOD: "Account",
    USER_METHOD: "User",
}


class ScheduleJob(Document):
    def validate(self):
        self.validate_editable()
        self.set_defaults()
        self.validate_reference()
        self.validate_duplicate()

        if self.method == ACCOUNT_METHOD:
            self.validate_account_update()
        elif self.method == USER_METHOD:
            self.validate_user_rename()

    def on_trash(self):
        if self.status == "Completed":
            frappe.throw(_("Completed Schedule Job cannot be deleted"))

    def validate_editable(self):
        if self.is_new():
            return

        db_status = frappe.db.get_value(self.doctype, self.name, "status")
        if db_status == "Completed":
            frappe.throw(
                _("Schedule Job {0} is already executed and cannot be modified").format(
                    self.name
                )
            )

    def set_defaults(self):
        if self.method not in METHOD_DOCTYPE:
            frappe.throw(_("Invalid Method {0}").format(self.method))
        self.reference_doctype = METHOD_DOCTYPE[self.method]

    def validate_reference(self):
        if not frappe.db.exists(self.reference_doctype, self.reference_name):
            frappe.throw(
                _("{0} {1} does not exist").format(
                    _(self.reference_doctype), self.reference_name
                )
            )

    def validate_duplicate(self):
        duplicate = frappe.db.get_value(
            self.doctype,
            {
                "reference_doctype": self.reference_doctype,
                "reference_name": self.reference_name,
                "status": "Pending",
                "name": ["!=", self.name],
            },
        )
        if duplicate:
            frappe.throw(
                _("A pending Schedule Job {0} already exists for {1} {2}").format(
                    frappe.get_desk_link(self.doctype, duplicate),
                    _(self.reference_doctype),
                    self.reference_name,
                )
            )

    def validate_account_update(self):
        self.new_account_name = cstr(self.new_account_name).strip()
        self.new_account_number = cstr(self.new_account_number).strip()

        if not self.new_account_name:
            frappe.throw(_("New Account Name is mandatory"))

        self.current_account_name, self.current_account_number = frappe.db.get_value(
            "Account", self.reference_name, ["account_name", "account_number"]
        )

        if self.new_account_name == cstr(
            self.current_account_name
        ) and self.new_account_number == cstr(self.current_account_number):
            frappe.throw(
                _("New Account Number and Name are the same as the current values")
            )

    def validate_user_rename(self):
        from frappe.utils import validate_email_address

        frappe.only_for("System Manager")
        self.new_user_id = cstr(self.new_user_id).strip()

        if not self.new_user_id:
            frappe.throw(_("New User ID is mandatory"))
        if self.reference_name in frappe.STANDARD_USERS:
            frappe.throw(_("User {0} cannot be renamed").format(self.reference_name))

        validate_email_address(self.new_user_id, throw=True)

        if self.new_user_id.lower() == self.reference_name.lower():
            frappe.throw(_("New User ID must be different from the current User ID"))
        if frappe.db.exists("User", self.new_user_id):
            frappe.throw(_("User {0} already exists").format(self.new_user_id))

    @frappe.whitelist()
    def retry(self):
        self.check_permission("write")
        if self.status != "Failed":
            frappe.throw(_("Only Failed Schedule Job can be retried"))

        self.status = "Pending"
        self.error_log = None
        self.save()

    def execute(self):
        """Runs the job once. Returns False if postponed because the system is not idle."""
        if self.status != "Pending":
            return True

        self.db_set({"last_attempt_on": now_datetime()}, update_modified=False)
        frappe.db.commit()

        try:
            if not is_gl_idle():
                frappe.db.rollback()
                return False

            old_name = self.reference_name
            if self.method == ACCOUNT_METHOD:
                from erpnext.accounts.doctype.account.account import (
                    update_account_number,
                )

                new_name = (
                    update_account_number(
                        self.reference_name,
                        self.new_account_name,
                        self.new_account_number,
                    )
                    or old_name
                )
            else:
                # User after_rename updates owner / modified_by in all tables, so it also needs idle GL
                new_name = frappe.rename_doc(
                    "User", self.reference_name, self.new_user_id, show_alert=False
                )

            # reload as renaming updates the Dynamic Link of this document
            self.reload()
            self.db_set(
                {
                    "status": "Completed",
                    "executed_on": now_datetime(),
                    "old_name": old_name,
                    "renamed_to": new_name,
                    "error_log": None,
                }
            )
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            self.db_set(
                {
                    "status": "Failed",
                    "executed_on": now_datetime(),
                    "error_log": frappe.get_traceback(),
                }
            )
            frappe.db.commit()

        return True


def is_gl_idle():
    """Same rule as erpnext Account _ensure_idle_system (no GL Entry update in last 5 minutes),
    but returns a bool instead of throwing. Keeps GL Entry locked within the current transaction."""
    from erpnext.accounts.doctype.account.account import _ensure_idle_system

    try:
        _ensure_idle_system()
    except frappe.ValidationError:
        frappe.clear_last_message()
        return False

    return True


def process_scheduled_jobs():
    """Runs daily at 00:00 (see hooks.py)"""
    names = frappe.get_all(
        "Schedule Job",
        filters={"status": "Pending"},
        order_by="creation asc",
        pluck="name",
    )

    for name in names:
        doc = frappe.get_doc("Schedule Job", name)
        if not doc.execute():
            # system is in use, remaining jobs stay Pending for the next night
            break
