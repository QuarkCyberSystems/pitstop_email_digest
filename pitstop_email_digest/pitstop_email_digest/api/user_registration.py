import frappe
from frappe import _
from frappe.permissions import add_user_permission
from frappe.utils import cint, escape_html
from frappe.utils.nestedset import get_root_of


@frappe.whitelist(allow_guest=True)
def sign_up(email: str, full_name: str, password: str, phone: str) -> tuple[int, str]:
    user = frappe.db.get("User", {"email": email})
    if user:
        result = register_customer(
            customer_name=full_name, email=email, mobile_no=phone, password=password
        )
        if result and result.get("customer_id"):
            add_user_permission(
                "Customer", result["customer_id"], email, ignore_permissions=True
            )
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
                "enabled": 1,
                "new_password": password,
                "user_type": "System User",
            }
        )
        user.flags.ignore_permissions = True
        user.flags.ignore_password_policy = True
        user.insert()

        result = register_customer(
            customer_name=full_name, email=email, mobile_no=phone, password=password
        )

        # add user permission so this user can only access their own Customer record
        if result and result.get("customer_id"):
            add_user_permission(
                "Customer", result["customer_id"], email, ignore_permissions=True
            )

        # set default signup role as per Portal Settings
        default_role = frappe.get_single_value("Portal Settings", "default_role")
        if default_role:
            user.add_roles(default_role)

    return {"success": True, "message": "User created successfully"}


def register_customer(customer_name, email, mobile_no, **kwargs):
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

    customer = frappe.get_doc(
        {
            "doctype": "Customer",
            "customer_name": customer_name,
            "customer_type": "Individual",
            "customer_group": "Individual",
            "territory": get_root_of("Territory"),
        }
    )
    customer.insert(ignore_permissions=True)

    # Optionally create linked Contact
    contact = frappe.get_doc(
        {
            "doctype": "Contact",
            "first_name": customer_name,
            "email_ids": [{"email_id": email, "is_primary": 1}],
            "phone_nos": [{"phone": mobile_no, "is_primary_mobile_no": 1}],
        }
    )
    contact.insert(ignore_permissions=True)
    contact.append("links", {"link_doctype": "Customer", "link_name": customer.name})
    contact.save(ignore_permissions=True)

    return {
        "customer_id": customer.name,
        "customer": customer.customer_name,
        "email_id": email,
        "phone": mobile_no,
    }
