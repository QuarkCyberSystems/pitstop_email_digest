import frappe
from frappe import _


@frappe.whitelist()
def enqueue_update_estimator_details(employee):
    frappe.only_for("System Manager")

    user_id = frappe.db.get_value("Employee", employee, "user_id")
    if not user_id:
        frappe.throw(_("Employee {0} has no User ID linked").format(employee))

    frappe.enqueue(
        update_estimator_details,
        queue="long",
        timeout=1500,
        job_id=f"update_estimator_details::{employee}",
        deduplicate=True,
        employee=employee,
    )
    frappe.msgprint(
        _("Estimator Details update for {0} has been queued").format(employee),
        alert=True,
    )


def update_estimator_details(employee):
    """Set the Employee as Estimator on Quotations created by their User,
    and refresh Estimator Name on Quotations already linked to them."""
    employee_name, user_id = frappe.db.get_value(
        "Employee", employee, ["employee_name", "user_id"]
    )
    if not user_id:
        return

    Quotation = frappe.qb.DocType("Quotation")

    (
        frappe.qb.update(Quotation)
        .set(Quotation.estimator_id, employee)
        .set(Quotation.estimator_name, employee_name)
        .where(Quotation.owner == user_id)
        .where((Quotation.estimator_id.isnull()) | (Quotation.estimator_id == ""))
    ).run()

    (
        frappe.qb.update(Quotation)
        .set(Quotation.estimator_name, employee_name)
        .where(Quotation.estimator_id == employee)
    ).run()

    frappe.db.commit()
