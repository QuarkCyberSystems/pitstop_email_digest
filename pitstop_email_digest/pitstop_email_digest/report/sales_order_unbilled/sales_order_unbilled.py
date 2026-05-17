# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import getdate


def execute(filters=None):
    return SalesOrderUnbilled(filters).run()


class SalesOrderUnbilled:
    def __init__(self, filters=None):
        self.filters = frappe._dict(filters)

    def run(self):
        self.validate_filters()
        self.get_data()
        columns = self.get_columns()
        return columns, self.data

    def validate_filters(self):
        self.filters.from_date = getdate(self.filters.from_date)
        self.filters.to_date = getdate(self.filters.to_date)

        if self.filters.from_date > self.filters.to_date:
            frappe.throw(_("From Date must be before To Date"))

    def get_columns(self):
        return [
            {
                "label": _("Order Date"),
                "fieldname": "transaction_date",
                "fieldtype": "Date",
                "width": 120,
            },
            {
                "label": _("Sales Order"),
                "fieldname": "sales_order",
                "fieldtype": "Link",
                "options": "Sales Order",
                "width": 120,
            },
            {
                "label": _("Status"),
                "fieldname": "status",
                "fieldtype": "Data",
                "width": 130,
                "hidden": 1,
            },
            {
                "label": _("Repair Order"),
                "fieldname": "project",
                "fieldtype": "Link",
                "options": "Project",
                "width": 120,
            },
            {
                "label": _("Order Amount"),
                "fieldname": "order_amount",
                "fieldtype": "Currency",
                "width": 150,
            },
            {
                "label": _("Billed Amount"),
                "fieldname": "billed_amount",
                "fieldtype": "Currency",
                "width": 150,
            },
            {
                "label": _("Balance Amount"),
                "fieldname": "balance_amount",
                "fieldtype": "Currency",
                "width": 150,
            },
        ]

    def get_conditions(self, prefix):
        conditions = []
        date_field = "transaction_date" if prefix == "so" else "posting_date"

        if self.filters.company:
            conditions.append(f"{prefix}.company = %(company)s")
        if self.filters.from_date:
            conditions.append(f"{prefix}.{date_field} >= %(from_date)s")
        if self.filters.to_date:
            conditions.append(f"{prefix}.{date_field} <= %(to_date)s")

        return conditions

    def get_data(self):
        so_conditions = self.get_conditions("so")
        so_conditions_str = (
            "and {0}".format(" and ".join(so_conditions)) if so_conditions else ""
        )
        si_conditions = self.get_conditions("si")
        si_conditions_str = (
            "and {0}".format(" and ".join(si_conditions)) if si_conditions else ""
        )

        self.data = frappe.db.sql(
            f"""
			select
				so.name as sales_order,
                so.transaction_date,
                so.status,
				so.company,
				so.project,
				-- Sales Order Amount
				coalesce((
					select sum(soi.base_net_amount)
					from `tabSales Order Item` soi
					where soi.parent = so.name
				),0) as order_amount,
				coalesce((
					select sum(sii.base_net_amount)
					from `tabSales Invoice Item` sii
					inner join `tabSales Invoice` si
						on si.name = sii.parent
					where
						sii.sales_order = so.name
						and si.docstatus = 1
						{si_conditions_str}
				), 0) as billed_amount,
				-- Balance Amount
				coalesce((
					select sum(soi.base_net_amount)
					from `tabSales Order Item` soi
					where soi.parent = so.name
				), 0)
				-
				coalesce((
					select sum(sii.base_net_amount)
					from `tabSales Invoice Item` sii
					inner join `tabSales Invoice` si
						on si.name = sii.parent
					where
						sii.sales_order = so.name
						and si.docstatus = 1
						{si_conditions_str}
				), 0) as balance_amount
			from `tabSales Order` so
			where
				so.docstatus = 1
				{so_conditions_str}
			order by
				so.transaction_date,
				so.name
			""",
            self.filters,
            as_dict=1,
        )
