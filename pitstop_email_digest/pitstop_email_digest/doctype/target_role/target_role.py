# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TargetRole(Document):
    def validate(self):
        self.validate_duplicate_years()

    def validate_duplicate_years(self):
        seen = set()
        for row in self.targets:
            if row.year in seen:
                frappe.throw(
                    _("Year {0} is repeated in row {1} of Targets").format(
                        frappe.bold(row.year), row.idx
                    )
                )
            seen.add(row.year)
