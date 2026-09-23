# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from erpnext.stock.report.stock_balance.stock_balance import (
    execute as stock_balance_execute,
)
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
    return SystemVsPhysicalStockComparison(filters).run()


class SystemVsPhysicalStockComparison:
    """System stock for a branch, taken straight from the Stock Balance report.

    A branch reaches its stock through `Warehouse.branch`, so the report resolves
    the branch to its warehouses and keeps only the Stock Balance rows sitting in
    them, rolled up per item.
    """

    def __init__(self, filters=None):
        self.filters = frappe._dict(filters or {})

    def run(self):
        self.validate_filters()

        warehouses = self.get_branch_warehouses()
        if not warehouses:
            return self.get_columns(), [], self.get_no_warehouse_message()

        rows = self.get_system_stock(warehouses)

        if self.filters.hide_balance_qty:
            # the column stays, so the sheet can be printed and counted against by
            # hand, but the system figure is left blank rather than shown
            for row in rows:
                row.balance_qty = None

        return self.get_columns(), rows

    def validate_filters(self):
        for fieldname, label in (
            ("company", _("Company")),
            ("branch", _("Branch")),
            ("date", _("Date")),
        ):
            if not self.filters.get(fieldname):
                frappe.throw(_("{0} is required").format(frappe.bold(label)))

        self.filters.date = getdate(self.filters.date)

    def get_branch_warehouses(self):
        """Warehouses the branch owns, plus everything beneath them.

        Stock sits in the leaf bins under a branch's warehouse, not on the
        warehouse the branch is tagged against, so the subtree is what counts.
        """
        tagged = frappe.get_all(
            "Warehouse",
            filters={"branch": self.filters.branch, "company": self.filters.company},
            fields=["name", "lft", "rgt"],
        )
        if not tagged:
            return set()

        warehouses = set()
        for row in tagged:
            warehouses.update(
                frappe.db.sql_list(
                    """
					select name from `tabWarehouse`
					where lft >= %(lft)s and rgt <= %(rgt)s
					""",
                    {"lft": row.lft, "rgt": row.rgt},
                )
            )

        return warehouses

    def get_system_stock(self, warehouses):
        """Stock Balance as at the date, narrowed to the branch.

        Rows are kept per warehouse rather than rolled up to the branch, so the
        report says where each quantity actually sits.
        """
        _columns, data = stock_balance_execute(
            frappe._dict(
                {
                    "company": self.filters.company,
                    "from_date": self.filters.date,
                    "to_date": self.filters.date,
                }
            )
        )[:2]

        totals = {}
        for row in data or []:
            row = frappe._dict(row)
            if row.warehouse not in warehouses:
                continue

            key = (row.item_code, row.warehouse, row.uom)
            total = totals.setdefault(
                key,
                frappe._dict(
                    item_code=row.item_code,
                    item_name=row.item_name,
                    warehouse=row.warehouse,
                    uom=row.uom,
                    balance_qty=0.0,
                ),
            )
            total.balance_qty += flt(row.bal_qty)

        return sorted(
            totals.values(),
            key=lambda d: (d.item_code or "", d.warehouse or "", d.uom or ""),
        )

    def get_no_warehouse_message(self):
        return _(
            "No warehouse is linked to Branch {0} for {1}. Set the Branch field on the "
            "relevant Warehouse records for this report to find their stock."
        ).format(frappe.bold(self.filters.branch), frappe.bold(self.filters.company))

    def get_columns(self):
        columns = [
            {
                "label": _("Item Code"),
                "fieldname": "item_code",
                "fieldtype": "Link",
                "options": "Item",
                "width": 160,
            },
            {
                "label": _("Item Name"),
                "fieldname": "item_name",
                "fieldtype": "Data",
                "width": 240,
            },
            {
                "label": _("Warehouse"),
                "fieldname": "warehouse",
                "fieldtype": "Link",
                "options": "Warehouse",
                "width": 220,
            },
            {
                "label": _("UOM"),
                "fieldname": "uom",
                "fieldtype": "Link",
                "options": "UOM",
                "width": 100,
            },
            {
                "label": _("Balance Qty"),
                "fieldname": "balance_qty",
                "fieldtype": "Float",
                "width": 130,
            },
        ]

        return columns
