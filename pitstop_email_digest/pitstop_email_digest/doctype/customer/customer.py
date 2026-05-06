import frappe


def cusomter_validation(doc, method=None):
    role_and_customer_group = frappe.db.get_values(
        "Custom Customer Settings", None, ["parts_role", "customer_group"], as_dict=True
    )
    if (
        role_and_customer_group
        and role_and_customer_group[0].get("parts_role")
        and role_and_customer_group[0].get("customer_group")
    ):
        if role_and_customer_group[0].get("parts_role") in frappe.get_roles(
            frappe.session.user
        ):
            allowed_groups = [role_and_customer_group[0].get("customer_group")]
            if doc.customer_group not in allowed_groups:
                frappe.throw(
                    f"""You are only allowed to select specific Customer Group <b>{role_and_customer_group[0].get("customer_group")}</b>"""
                )
