# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from erpnext.stock.doctype.item.item import convert_item_uom_for
from frappe import _
from frappe.utils import flt, getdate


class ROSoldHours(object):
    def __init__(self, filters=None):
        self.filters = frappe._dict(filters or {})

        if self.filters.from_date and self.filters.to_date:
            if getdate(self.filters.from_date) > getdate(self.filters.to_date):
                frappe.throw(_("From Date cannot be after To Date"))

        self.data = []

    def run(self):
        self.get_repair_orders()

        if self.data:
            self.get_clocked_hours()
            self.get_billed_sold_hours()
            self.get_billable_sold_hours()

        self.process_data()

        return self.get_columns(), self.data

    def get_conditions(self):
        conditions = []

        if self.filters.company:
            conditions.append("p.company = %(company)s")

        if self.filters.from_date:
            conditions.append("p.project_date >= %(from_date)s")

        if self.filters.to_date:
            conditions.append("p.project_date <= %(to_date)s")

        if self.filters.repair_order:
            conditions.append("p.name = %(repair_order)s")

        if self.filters.branch:
            conditions.append("p.branch = %(branch)s")

        if self.filters.not_completed_ro_status:
            conditions.append("p.project_status != 'Completed'")
        elif self.filters.ro_status:
            conditions.append("p.project_status = %(ro_status)s")

        return "and {0}".format(" and ".join(conditions)) if conditions else ""

    def get_repair_orders(self):
        conditions = self.get_conditions()

        self.data = frappe.db.sql(
            """
			select
				p.name as repair_order,
				p.project_status as repair_order_status
			from `tabProject` p
			where p.status != 'Cancelled' {0}
			order by p.project_date, p.creation
		""".format(conditions),
            self.filters,
            as_dict=1,
        )

        self.repair_orders = [d.repair_order for d in self.data]
        self.ro_map = {d.repair_order: d for d in self.data}

    def get_clocked_hours(self):
        clocked_data = frappe.db.sql(
            """
			select tsd.project, sum(tsd.hours) as hours
			from `tabTimesheet Detail` tsd
			where tsd.docstatus < 2 and tsd.project in %(repair_orders)s
			group by tsd.project
		""",
            {"repair_orders": self.repair_orders},
            as_dict=1,
        )

        for d in clocked_data:
            row = self.ro_map.get(d.project)
            if row:
                row.clocked_hours = flt(d.hours)

    def get_billed_sold_hours(self):
        """Hours billed against the Repair Order (Sales Invoice)"""
        items = frappe.db.sql(
            """
			select i.project, i.item_code, i.qty, i.uom, i.stock_uom, i.conversion_factor
			from `tabSales Invoice Item` i
			inner join `tabSales Invoice` p on p.name = i.parent
			where p.docstatus = 1 and i.project in %(repair_orders)s
		""",
            {"repair_orders": self.repair_orders},
            as_dict=1,
        )

        self.add_sold_hours(items, "billed_sold_hours")

    def get_billable_sold_hours(self):
        """Hours sold on the Repair Order (Sales Order)"""
        items = frappe.db.sql(
            """
			select p.project, i.item_code, i.qty, i.uom, i.stock_uom, i.conversion_factor
			from `tabSales Order Item` i
			inner join `tabSales Order` p on p.name = i.parent
			where p.docstatus = 1 and p.project in %(repair_orders)s
		""",
            {"repair_orders": self.repair_orders},
            as_dict=1,
        )

        self.add_sold_hours(items, "billable_sold_hours")

    def add_sold_hours(self, items, fieldname):
        for d in items:
            row = self.ro_map.get(d.project)
            if not row:
                continue

            hours = convert_item_uom_for(
                d.qty,
                d.item_code,
                d.uom,
                "Hour",
                conversion_factor=d.conversion_factor
                if d.stock_uom == "Hour"
                else None,
                null_if_not_convertible=True,
            )

            if hours is not None:
                row[fieldname] = flt(row.get(fieldname)) + flt(hours)

    def process_data(self):
        for d in self.data:
            d.clocked_hours = flt(d.clocked_hours)
            d.billed_sold_hours = flt(d.billed_sold_hours)
            d.billable_sold_hours = flt(d.billable_sold_hours)
            d.hours_difference = d.billed_sold_hours - d.clocked_hours

    def get_columns(self):
        return [
            {
                "label": _("Repair Order"),
                "fieldname": "repair_order",
                "fieldtype": "Link",
                "options": "Project",
                "width": 150,
            },
            {
                "label": _("Repair Order Status"),
                "fieldname": "repair_order_status",
                "fieldtype": "Data",
                "width": 140,
            },
            {
                "label": _("Billable Sold Hours"),
                "fieldname": "billable_sold_hours",
                "fieldtype": "Float",
                "precision": 2,
                "width": 150,
            },
            {
                "label": _("Clocked Hours"),
                "fieldname": "clocked_hours",
                "fieldtype": "Float",
                "precision": 2,
                "width": 120,
            },
            {
                "label": _("Billed Sold Hours"),
                "fieldname": "billed_sold_hours",
                "fieldtype": "Float",
                "precision": 2,
                "width": 140,
            },
            {
                "label": _("Difference Clocked Hours and Billed Hours"),
                "fieldname": "hours_difference",
                "fieldtype": "Float",
                "precision": 2,
                "width": 270,
            },
        ]


def execute(filters=None):
    return ROSoldHours(filters).run()
