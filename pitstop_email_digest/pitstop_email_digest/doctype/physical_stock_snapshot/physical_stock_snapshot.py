# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from erpnext.stock.get_item_details import get_conversion_factor
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

STATUS_BY_DOCSTATUS = {0: "Draft", 1: "Submitted", 2: "Cancelled"}


class PhysicalStockSnapshot(Document):
    def validate(self):
        self.set_stock_uom_and_qty()
        self.set_total_qty()

    def set_stock_uom_and_qty(self):
        """Restate each counted qty in the item's stock UOM.

        Counts are taken in whatever UOM the counter used, so the stock UOM
        figure -- not available_qty -- is what compares against system stock.
        """
        for row in self.items:
            if not row.item_code:
                continue

            row.stock_uom = frappe.get_cached_value("Item", row.item_code, "stock_uom")

            if not row.uom:
                # nothing was picked, so the count is already in the stock UOM
                row.uom = row.stock_uom

            row.stock_qty = flt(row.available_qty) * self.get_conversion_factor(row)

    @staticmethod
    def get_conversion_factor(row):
        if row.uom == row.stock_uom:
            return 1.0

        conversion = get_conversion_factor(row.item_code, row.uom)

        if conversion.get("not_convertible"):
            frappe.throw(
                _(
                    "Row #{0}: UOM {1} cannot be converted to stock UOM {2} for item {3}."
                ).format(
                    row.idx,
                    frappe.bold(row.uom),
                    frappe.bold(row.stock_uom),
                    frappe.bold(row.item_code),
                ),
                title=_("Missing UOM Conversion"),
            )

        return flt(conversion.get("conversion_factor")) or 1.0

    def set_total_qty(self):
        """Total counted quantity across the snapshot's item rows."""
        self.total_quantity = sum(flt(row.available_qty) for row in self.items)

    def before_save(self):
        self.set_status()

    def on_submit(self):
        self.db_set("status", "Submitted")

    def on_cancel(self):
        self.db_set("status", "Cancelled")

    def set_status(self):
        # status mirrors docstatus rather than being typed in, so the field can
        # never disagree with whether the snapshot is actually submitted
        self.status = STATUS_BY_DOCSTATUS.get(int(self.docstatus), "Draft")
