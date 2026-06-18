# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ExtendedWarrantyConfigure(Document):
    def validate(self):
        default_rows = [
            d for d in self.extended_warranty_configure_details if d.default
        ]
        if len(default_rows) > 1:
            frappe.throw("Only one row can be marked as Default")
