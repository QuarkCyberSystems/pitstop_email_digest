import click
import frappe
from frappe.utils.fixtures import sync_fixtures


def execute():
    """Backfill Quotation's Estimator Details (estimator_id / estimator_name)."""
    # Fixtures sync after patches during migrate, so make sure the custom fields exist first
    sync_fixtures("pitstop_email_digest")
    if not frappe.db.has_column("Quotation", "estimator_id"):
        return

    click.echo("Backfilling Estimator on Quotation from creator's Employee record...")
    frappe.db.sql(
        """
        update `tabQuotation` q
        inner join `tabEmployee` e on e.user_id = q.owner and e.status = 'Active'
        set q.estimator_id = e.name,
            q.estimator_name = e.employee_name
        where ifnull(q.estimator_id, '') = ''
    """
    )

    click.echo("Filling missing Estimator Name where Estimator ID is already set...")
    frappe.db.sql(
        """
        update `tabQuotation` q
        inner join `tabEmployee` e on e.name = q.estimator_id
        set q.estimator_name = e.employee_name
        where ifnull(q.estimator_id, '') != ''
            and ifnull(q.estimator_name, '') = ''
    """
    )
