import frappe
from automotive.automotive.report.vehicle_service_feedback.vehicle_service_feedback import (
    VehicleServiceFeedback,
)
from crm.crm.doctype.customer_feedback.customer_feedback import make_feedback_doc
from frappe.utils import add_days, get_time, getdate, now_datetime, today

# Only individual customers are surveyed, and Tesla vehicles are excluded.
FEEDBACK_CUSTOMER_GROUP = "Individual"
EXCLUDED_BRAND = "TESLA"


def create_pending_customer_feedback():
    """Scheduled daily at midnight. Create a Customer Feedback for the previous day's
    due Repair Orders that do not have one yet."""

    company = frappe.defaults.get_global_default("company")
    if not company:
        return

    previous_date = add_days(getdate(today()), -1)

    filters = frappe._dict(
        {
            "company": company,
            "date_type": "Feedback Due Date",
            "from_date": previous_date,
            "to_date": previous_date,
            "feedback_filter": "Pending Feedback",
            "customer_group": FEEDBACK_CUSTOMER_GROUP,
        }
    )

    data = VehicleServiceFeedback(filters).run()[1]

    cur_dt = now_datetime()
    cur_date = getdate(cur_dt)
    cur_time = get_time(cur_dt)

    visited_projects = set()

    for d in data:
        # a project can appear on multiple rows (one per Vehicle Gate Pass)
        if not d.project or d.project in visited_projects:
            continue

        visited_projects.add(d.project)

        brand = (
            frappe.get_cached_value("Item", d.variant_item_code, "brand")
            if d.variant_item_code
            else None
        )
        if brand and brand.upper() == EXCLUDED_BRAND:
            continue

        if frappe.db.exists(
            "Customer Feedback",
            {"reference_doctype": "Project", "reference_name": d.project},
        ):
            continue

        try:
            feedback_doc = make_feedback_doc("Project", d.project)
            feedback_doc.feedback_type = "Post-Service Survey"
            feedback_doc.feedback_status = "Feedback pending"
            feedback_doc.contact_date = cur_date
            feedback_doc.contact_time = cur_time
            feedback_doc.insert(ignore_permissions=True)
        except Exception:
            frappe.log_error(
                title="Error creating Customer Feedback",
                reference_doctype="Project",
                reference_name=d.project,
            )
