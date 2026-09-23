# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

from frappe.model.document import Document
from frappe.utils import flt

STATUS_BY_DOCSTATUS = {0: "Draft", 1: "Submitted", 2: "Cancelled"}


class PhysicalStockSnapshot(Document):
    def validate(self):
        self.set_total_qty()

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
