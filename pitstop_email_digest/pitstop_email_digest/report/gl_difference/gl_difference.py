# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate

# Cancelled vouchers have their GL Entries deleted, so their date and amount are read from the document itself
# voucher_type: (date field used for GL posting, amount expression in company currency)
CANCELLED_VOUCHER_FIELDS = {
    "Sales Invoice": ("posting_date", "d.base_grand_total"),
    "Purchase Invoice": ("posting_date", "d.base_grand_total"),
    "Delivery Note": ("posting_date", "d.base_grand_total"),
    "Purchase Receipt": ("posting_date", "d.base_grand_total"),
    "Journal Entry": ("posting_date", "d.total_debit"),
    "Payment Entry": ("posting_date", "d.base_paid_amount"),
    "Stock Entry": (
        "posting_date",
        "greatest(d.total_outgoing_value, d.total_incoming_value)",
    ),
    "Stock Reconciliation": ("posting_date", "d.difference_amount"),
    "Service Maintenance Contract": ("posting_date", "d.base_grand_total"),
    "Service Warranty": ("posting_date", "d.warranty_provision_amount"),
    "Asset": ("available_for_use_date", "d.gross_purchase_amount"),
    "Period Closing Voucher": ("posting_date", "0"),
}


def execute(filters=None):
    filters = frappe._dict(filters or {})
    validate_filters(filters)

    if filters.view == "Cancelled Vouchers":
        return get_cancelled_voucher_columns(), get_cancelled_vouchers(filters)

    cancelled_count = len(get_cancelled_vouchers(filters))
    report_summary = [
        {
            "value": cancelled_count,
            "label": _("Cancelled Vouchers in Period"),
            "datatype": "Int",
            "indicator": "Red" if cancelled_count else "Green",
        }
    ]

    return get_columns(), get_data(filters), None, None, report_summary


def validate_filters(filters):
    if getdate(filters.from_date) > getdate(filters.to_date):
        frappe.throw(_("From Date cannot be after To Date"))


def get_columns():
    return [
        {
            "label": _("Ledger"),
            "fieldname": "account",
            "fieldtype": "Link",
            "options": "Account",
            "width": 300,
        },
        {
            "label": _("Root Type"),
            "fieldname": "root_type",
            "fieldtype": "Data",
            "width": 100,
        },
        {
            "label": _("Debit"),
            "fieldname": "debit",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 140,
        },
        {
            "label": _("Credit"),
            "fieldname": "credit",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 140,
        },
        {
            "label": _("Amount (Dr - Cr)"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 160,
        },
        {
            "label": _("Currency"),
            "fieldname": "currency",
            "fieldtype": "Link",
            "options": "Currency",
            "hidden": 1,
        },
    ]


def get_data(filters):
    conditions = ""
    if filters.account:
        conditions += " and gle.account = %(account)s"

    having = (
        ""
        if filters.show_zero_values
        else "having round(sum(gle.debit) - sum(gle.credit), 2) != 0"
    )

    # conditions and having are hardcoded fragments, filter values are passed as query parameters
    data = frappe.db.sql(  # nosemgrep: frappe-db-sql-injection
        """
		select gle.account, acc.root_type,
			sum(gle.debit) as debit, sum(gle.credit) as credit,
			sum(gle.debit) - sum(gle.credit) as amount
		from `tabGL Entry` gle
		inner join `tabAccount` acc on acc.name = gle.account
		where gle.company = %(company)s
			and gle.posting_date between %(from_date)s and %(to_date)s
			{conditions}
		group by gle.account, acc.root_type
		{having}
		order by acc.lft
	""".format(conditions=conditions, having=having),
        filters,
        as_dict=1,
    )

    currency = frappe.get_cached_value("Company", filters.company, "default_currency")
    for d in data:
        d.currency = currency
        d.amount = flt(d.amount, 2)

    return data


def get_cancelled_voucher_columns():
    return [
        {
            "label": _("Voucher Type"),
            "fieldname": "voucher_type",
            "fieldtype": "Link",
            "options": "DocType",
            "width": 150,
        },
        {
            "label": _("Voucher No"),
            "fieldname": "voucher_no",
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 180,
        },
        {
            "label": _("Posting Date"),
            "fieldname": "posting_date",
            "fieldtype": "Date",
            "width": 100,
        },
        {
            "label": _("Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "options": "currency",
            "width": 140,
        },
        {
            "label": _("Cancelled On"),
            "fieldname": "cancelled_on",
            "fieldtype": "Datetime",
            "width": 160,
        },
        {
            "label": _("Cancelled By"),
            "fieldname": "cancelled_by",
            "fieldtype": "Link",
            "options": "User",
            "width": 160,
        },
        {
            "label": _("Amended To"),
            "fieldname": "amended_to",
            "fieldtype": "Dynamic Link",
            "options": "voucher_type",
            "width": 180,
        },
        {
            "label": _("Remarks"),
            "fieldname": "remarks",
            "fieldtype": "Data",
            "width": 250,
        },
        {
            "label": _("Currency"),
            "fieldname": "currency",
            "fieldtype": "Link",
            "options": "Currency",
            "hidden": 1,
        },
    ]


def get_cancelled_vouchers(filters):
    data = []
    for voucher_type, (date_field, amount_expr) in CANCELLED_VOUCHER_FIELDS.items():
        if not frappe.db.exists("DocType", voucher_type):
            continue

        meta = frappe.get_meta(voucher_type)
        remarks_field = (
            "remarks"
            if meta.has_field("remarks")
            else "user_remark"
            if meta.has_field("user_remark")
            else None
        )
        remarks_expr = "d.{0}".format(remarks_field) if remarks_field else "''"

        # doctype, field names and expressions come from CANCELLED_VOUCHER_FIELDS, filter values are passed as query parameters
        vouchers = frappe.db.sql(  # nosemgrep: frappe-db-sql-injection
            """
			select %(voucher_type)s as voucher_type, d.name as voucher_no,
				d.{date_field} as posting_date, {amount_expr} as amount,
				d.modified as cancelled_on, d.modified_by as cancelled_by,
				{remarks_expr} as remarks
			from `tab{voucher_type}` d
			where d.docstatus = 2
				and d.company = %(company)s
				and d.{date_field} between %(from_date)s and %(to_date)s
		""".format(
                voucher_type=voucher_type,
                date_field=date_field,
                amount_expr=amount_expr,
                remarks_expr=remarks_expr,
            ),
            dict(filters, voucher_type=voucher_type),
            as_dict=1,
        )

        if vouchers:
            # doctype comes from CANCELLED_VOUCHER_FIELDS, voucher names are passed as query parameters
            amended_to = dict(
                frappe.db.sql(  # nosemgrep: frappe-db-sql-injection
                    """
				select amended_from, name
				from `tab{0}`
				where amended_from in %s and docstatus < 2
				order by creation
			""".format(voucher_type),
                    [[d.voucher_no for d in vouchers]],
                )
            )

            for d in vouchers:
                d.amended_to = amended_to.get(d.voucher_no)

        data += vouchers

    currency = frappe.get_cached_value("Company", filters.company, "default_currency")
    for d in data:
        d.currency = currency
        d.amount = flt(d.amount, 2)

    return sorted(data, key=lambda d: (d.posting_date, d.voucher_type, d.voucher_no))
