# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from erpnext.stock.get_item_details import get_conversion_factor
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
        self._conversion_factors = {}

    def run(self):
        self.validate_filters()

        warehouses = self.get_branch_warehouses()
        if not warehouses:
            return self.get_columns(), [], self.get_no_warehouse_message()

        rows = self.get_system_stock(warehouses)
        rows = self.add_physical_stock(rows)

        # built before the loop below blanks balance_qty, so the totals read the
        # system figures rather than what was wiped for printing
        message = self.get_totals_message(rows)

        for row in rows:
            # erpnext's Item link formatter falls back to the row's item_name
            # whenever a Link-to-Item cell is empty, which would print the system
            # item name into the physical column of every uncounted row. The
            # report carries its own item name columns, so the formatter is off.
            row.disable_item_formatter = 1

            if self.filters.hide_balance_qty:
                # the columns stay, so the sheet can be printed and counted
                # against by hand, but the system figures are left blank. Both
                # quantities go -- leaving the stock one would hand back what the
                # filter exists to hide. The UOMs stay, being useful on a count
                # sheet and giving nothing away.
                row.balance_qty = None
                row.stock_balance_qty = None

        return self.get_columns(), rows, message

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
                    stock_uom=frappe.get_cached_value(
                        "Item", row.item_code, "stock_uom"
                    ),
                    stock_balance_qty=0.0,
                ),
            )
            total.balance_qty += flt(row.bal_qty)
            total.stock_balance_qty += flt(
                row.bal_qty
            ) * self.get_stock_conversion_factor(
                row.item_code, row.uom, total.stock_uom
            )

        return sorted(
            totals.values(),
            key=lambda d: (d.item_code or "", d.warehouse or "", d.uom or ""),
        )

    def get_stock_conversion_factor(self, item_code, uom, stock_uom):
        """Factor taking a Stock Balance quantity into the item's stock UOM.

        Stock Balance already reports in the stock UOM unless its `qty_field`
        filter asks for contents qty, so this is normally 1. It is computed
        anyway so the stock columns stay right if that ever stops holding.
        """
        if not uom or not stock_uom or uom == stock_uom:
            return 1.0

        if (item_code, uom) not in self._conversion_factors:
            conversion = get_conversion_factor(item_code, uom)
            self._conversion_factors[(item_code, uom)] = (
                flt(conversion.get("conversion_factor")) or 1.0
            )

        return self._conversion_factors[(item_code, uom)]

    def add_physical_stock(self, rows):
        """Fold the counted snapshot into the system rows.

        A counted line is matched to the system row for the same item code and
        warehouse; what it counted against nothing the system knows about is
        appended, so a surplus on the floor is visible rather than dropped.
        """
        if not self.filters.physical_stock_snapshot:
            return rows

        counted = self.get_snapshot_items()

        for row in rows:
            # every row carries the physical fields, blank unless a counted row
            # matched it -- an absent key and an empty one render differently
            row.update(self.blank_physical_fields())
            row.update(counted.pop((row.item_code, row.warehouse), {}))

        # anything left counted a place the system holds no stock in, so those
        # rows are the mirror image: physical fields only, system side blank
        uncounted = sorted(
            counted.values(),
            key=lambda d: (d.physical_item_code or "", d.physical_warehouse or ""),
        )
        for row in uncounted:
            for fieldname in (
                "item_code",
                "item_name",
                "warehouse",
                "uom",
                "balance_qty",
                "stock_uom",
                "stock_balance_qty",
            ):
                row.setdefault(fieldname, None)

        return rows + uncounted

    @staticmethod
    def blank_physical_fields():
        return frappe._dict(
            physical_item_code=None,
            physical_item_name=None,
            physical_warehouse=None,
            physical_uom=None,
            physical_stock_uom=None,
            physical_balance_qty=None,
            physical_stock_balance_qty=None,
        )

    def get_snapshot_items(self):
        """Counted quantities keyed by item code and warehouse.

        The snapshot calls the warehouse `location`, and may repeat an item
        across rows, so the quantities are summed per item and warehouse.

        Branch sits on the snapshot rather than on its rows, so the query runs
        against the parent and pulls the child fields through the join -- a
        snapshot belonging to another branch then yields nothing.
        """
        items = frappe.db.sql(
            """
            select
                psi.item_code as physical_item_code,
                psi.item_name as physical_item_name,
                psi.uom as physical_uom,
                psi.stock_uom as physical_stock_uom,
                psi.location as physical_warehouse,
                psi.available_qty as available_qty,
                psi.stock_qty as stock_available_qty
            from `tabPhysical Stock Snapshot Item` AS psi
            inner join `tabPhysical Stock Snapshot` AS pss
                on psi.parent = pss.name
            where pss.name = %(physical_stock_snapshot)s
                and pss.branch = %(branch)s
            """,
            {
                "physical_stock_snapshot": self.filters.physical_stock_snapshot,
                "branch": self.filters.branch,
            },
            as_dict=True,
        )

        counted = {}
        for item in items:
            key = (item.physical_item_code, item.physical_warehouse)
            entry = counted.setdefault(
                key,
                frappe._dict(
                    physical_item_code=item.physical_item_code,
                    physical_item_name=item.physical_item_name,
                    physical_warehouse=item.physical_warehouse,
                    physical_uom=item.physical_uom,
                    physical_stock_uom=item.physical_stock_uom,
                    physical_balance_qty=0.0,
                    physical_stock_balance_qty=0.0,
                ),
            )
            entry.physical_balance_qty += flt(item.available_qty)
            entry.physical_stock_balance_qty += flt(item.stock_available_qty)

        return counted

    def get_totals_message(self, rows):
        """The two stock-UOM totals and how far the count sits from the system.

        Both sides are already restated in the item's stock UOM, so they are the
        only pair that can be summed across rows and compared.
        """
        if not self.filters.physical_stock_snapshot:
            # nothing counted yet, so there is no comparison to draw
            return None

        physical_total = sum(flt(row.get("physical_stock_balance_qty")) for row in rows)
        figures = [
            (
                _("Total Stock Balance Qty (Physical)"),
                self.format_qty(physical_total),
                None,
            )
        ]

        if self.filters.hide_balance_qty:
            # the system figure is deliberately off the sheet, so its total and
            # the variance against it would hand straight back what was hidden
            return self.build_totals_message(figures)

        system_total = sum(flt(row.get("stock_balance_qty")) for row in rows)
        figures.insert(
            0, (_("Total Stock Balance Qty"), self.format_qty(system_total), None)
        )
        figures.append(self.get_difference_figure(system_total, physical_total))

        return self.build_totals_message(figures)

    def get_difference_figure(self, system_total, physical_total):
        """The count as a percentage swing away from the system figure."""
        label = _("Difference")

        if not system_total:
            # a zero system total has no scale to express the swing against, so
            # the percentage is withheld rather than reported as 0% or infinite
            return (label, _("Not applicable"), None)

        difference = physical_total - system_total

        # rounded before the sign is read, so the colour never claims a variance
        # the printed figure does not show
        difference = round(difference, 2)

        if difference > 0:
            return (label, "+{:.2f}".format(difference), "var(--orange-600)")

        if difference < 0:
            return (label, "{:.2f}".format(difference), "var(--red-600)")

        return (label, "0.00%", "var(--green-600)")

    @staticmethod
    def build_totals_message(figures):
        parts = []
        for label, value, colour in figures:
            style = ' style="color: {0}"'.format(colour) if colour else ""
            parts.append("{0}: <strong{1}>{2}</strong>".format(label, style, value))

        return '<div style="display: flex; flex-wrap: wrap; gap: 0 1.5rem">{0}</div>'.format(
            "".join("<span>{0}</span>".format(part) for part in parts)
        )

    @staticmethod
    def format_qty(value):
        return frappe.format_value(flt(value), {"fieldtype": "Float"})

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
            {
                "label": _("Stock UOM"),
                "fieldname": "stock_uom",
                "fieldtype": "Link",
                "options": "UOM",
                "width": 100,
            },
            {
                "label": _("Stock Balance Qty"),
                "fieldname": "stock_balance_qty",
                "fieldtype": "Float",
                "width": 130,
            },
            {
                "label": _("Item Code (Physical)"),
                "fieldname": "physical_item_code",
                "fieldtype": "Link",
                "options": "Item",
                "width": 160,
            },
            {
                "label": _("Item Name (Physical)"),
                "fieldname": "physical_item_name",
                "fieldtype": "Data",
                "options": "Item",
                "width": 240,
            },
            {
                "label": _("Warehouse (Physical)"),
                "fieldname": "physical_warehouse",
                "fieldtype": "Link",
                "options": "Warehouse",
                "width": 220,
            },
            {
                "label": _("UOM (Physical)"),
                "fieldname": "physical_uom",
                "fieldtype": "Link",
                "options": "UOM",
                "width": 100,
            },
            {
                "label": _("Balance Qty (Physical)"),
                "fieldname": "physical_balance_qty",
                "fieldtype": "Float",
                "width": 130,
            },
            {
                "label": _("Stock UOM (Physical)"),
                "fieldname": "physical_stock_uom",
                "fieldtype": "Link",
                "options": "UOM",
                "width": 100,
            },
            {
                "label": _("Stock Balance Qty (Physical)"),
                "fieldname": "physical_stock_balance_qty",
                "fieldtype": "Float",
                "width": 130,
            },
        ]

        return columns
