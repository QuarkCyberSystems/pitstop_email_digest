# Copyright (c) 2025, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from erpnext.setup.doctype.naming_series.naming_series import NamingSeries


class PaymentEntrySettings(Document):
	def validate(self):
		for each_row in self.auto_reference_number_details:
			if not frappe.db.exists("Series", each_row.series):
				frappe.db.sql(
					"INSERT INTO `tabSeries` (name, current) VALUES (%s, %s)",
					(each_row.series, 0)
				)
