import frappe
from frappe import _


def validate_extended_warranty_voucher(self):
    voucher_no = self.get("extended_warranty_voucher")

    # Nothing to validate if the field is empty
    if not voucher_no:
        return

    si = frappe.db.get_value(
        "Sales Invoice",
        voucher_no,
        ["name", "docstatus", "customer", "posting_date"],
        as_dict=True,
    )

    if not si:
        frappe.throw(
            _("Extended Warranty Voucher {0} does not exist.").format(
                frappe.bold(voucher_no)
            ),
            title=_("Invalid Voucher"),
        )

    if si.docstatus != 1:
        frappe.throw(
            _(
                "Extended Warranty Voucher {0} is not submitted. "
                "Only submitted Sales Invoices can be linked."
            ).format(frappe.bold(voucher_no)),
            title=_("Voucher Not Submitted"),
        )

    warranty_items = frappe.db.get_all(
        "Sales Invoice Item",
        filters={
            "parent": voucher_no,
            "is_extended_warranty": 1,
        },
        fields=["name", "item_code", "item_name", "base_net_amount"],
    )

    if not warranty_items:
        frappe.throw(
            _(
                "Sales Invoice {0} does not contain any Extended Warranty items. "
                "The Extended Warranty Voucher field must reference an invoice "
                "that has at least one line item with <b>Is Extended Warranty</b> enabled."
            ).format(frappe.bold(voucher_no)),
            title=_("No Extended Warranty Items Found"),
        )

    existing_jv = frappe.db.get_all(
        "Journal Entry",
        filters={
            "extended_warranty_voucher": voucher_no,
            "docstatus": 1,
            "name": ["!=", self.name],
        },
        fields=["name"],
        limit=1,
    )

    if existing_jv:
        frappe.throw(
            _(
                "Note: A Journal Entry ({0}) has already been posted "
                "against Extended Warranty Voucher {1}."
            ).format(
                frappe.bold(existing_jv[0].name),
                frappe.bold(voucher_no),
            ),
            title=_("Duplicate JV Warning"),
            indicator="red",
        )
