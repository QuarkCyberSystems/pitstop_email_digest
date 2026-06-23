# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ExtendedWarrantyConfigure(Document):
    def validate(self):
        self.check_extended_warranty_items()
        self.check_duplicate_item_supplier()
        self.check_single_default()

    def check_single_default(self):
        default_rows = [
            d for d in self.extended_warranty_configure_details if d.default
        ]
        if len(default_rows) > 1:
            frappe.throw("Only one row can be marked as Default")

    def check_duplicate_item_supplier(self):
        supplier_item_code_set = set()
        for row in self.extended_warranty_configure_details:
            key = (row.warranty_item, row.extended_warranty_supplier)
            if key in supplier_item_code_set:
                frappe.throw(
                    "Duplicate entry found at Row #{0}: "
                    "Item <b>{1}</b> with Supplier <b>{2}</b> already exists.".format(
                        row.idx, row.warranty_item, row.extended_warranty_supplier
                    )
                )
            supplier_item_code_set.add(key)

    def check_extended_warranty_items(self):
        invalid_items = []

        for row in self.extended_warranty_configure_details:
            is_extended_warranty = frappe.get_cached_value(
                "Item", row.warranty_item, "is_extended_warranty"
            )
            if not is_extended_warranty:
                invalid_items.append((row.idx, row.warranty_item))

        if invalid_items:
            frappe.throw(
                "The following items do not have <b>Is Extended Warranty</b> "
                "enabled in the Item list:<br><ul>{0}</ul>".format(
                    "".join(
                        "<li>Row #{0}: <b>{1}</b></li>".format(idx, item)
                        for idx, item in invalid_items
                    )
                )
            )
