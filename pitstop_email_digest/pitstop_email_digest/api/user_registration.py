from typing import Any

import frappe
from frappe import _
from frappe.permissions import add_user_permission
from frappe.utils import cint, escape_html


@frappe.whitelist(allow_guest=True)
def sign_up(
    email: str, full_name: str, password: str, mobile_no: str
) -> dict[str, Any]:
    result = check_customer(email=email, mobile_no=mobile_no, password=password)
    if result and result.get("customer_id"):
        user_created = create_user(full_name, email, mobile_no, password)
        if user_created:
            add_user_permission(
                "Customer", result["customer_id"], email, ignore_permissions=True
            )
            return {"success": True, "message": "User created successfully"}
    else:
        return {"success": False, "message": _("Customer Not Exists")}


def create_user(full_name, email, mobile_no, password, **kwargs):
    user = frappe.db.get("User", {"email": email})
    if user:
        if user.enabled:
            return {"success": False, "message": _("Already Registered")}
        else:
            return {"success": False, "message": _("Registered but disabled")}
    else:
        max_signups_allowed_per_hour = cint(
            frappe.get_system_settings("max_signups_allowed_per_hour") or 300
        )
        users_created_past_hour = frappe.db.get_creation_count("User", 60)
        if users_created_past_hour >= max_signups_allowed_per_hour:
            frappe.respond_as_web_page(
                _("Temporarily Disabled"),
                _(
                    "Too many users signed up recently, so the registration is disabled. Please try back in an hour"
                ),
                http_status_code=429,
            )

        user = frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": escape_html(full_name),
                "phone": mobile_no,
                "enabled": 1,
                "new_password": password,
                "user_type": "Website User",
            }
        )
        user.flags.ignore_permissions = True
        user.flags.ignore_password_policy = True
        user.insert()

        # set default signup role as per Portal Settings
        default_role = frappe.get_single_value("Portal Settings", "default_role")
        if default_role:
            user.add_roles(default_role)
    return True


def check_customer(email, mobile_no, **kwargs):
    existing = False
    if email:
        existing = frappe.db.exists("Customer", {"email_id": email})
    if not existing and mobile_no:
        existing = frappe.db.exists("Customer", {"mobile_no": mobile_no})

    if existing:
        customer_doc = frappe.get_doc("Customer", existing)
        return {
            "customer_id": customer_doc.name,
            "customer": customer_doc.customer_name,
            "email_id": email,
            "phone": mobile_no,
        }
