import frappe
from frappe import _
from frappe.model.naming import make_autoname
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry

class CustomPaymentEntry(PaymentEntry):
	
	def custom_validate_transaction_reference(self):
		if ((not self.reference_no or not self.reference_date) and (self.docstatus == 1)):
			bank_account = self.paid_to if self.payment_type == "Receive" else self.paid_from
			bank_account_type = frappe.get_cached_value("Account", bank_account, "account_type")
			if bank_account_type == "Bank":
				if not self.reference_no:
					frappe.throw(_("Reference No is mandatory for Bank transaction"))
				elif not self.reference_date:
					frappe.throw(_("Reference Date is mandatory for Bank transaction"))
				elif (not self.reference_no and not self.reference_date):
					frappe.throw(_("Reference No and Reference Date is mandatory for Bank transaction"))

		mode = frappe.get_cached_doc("Mode of Payment", self.mode_of_payment) if self.mode_of_payment else frappe._dict()

		if ((not self.reference_no and mode.reference_no_mandatory) and (self.docstatus == 1)):
			frappe.throw(_("Reference No is mandatory for Mode of Payment {0}").format(
				frappe.bold(self.mode_of_payment)
			))

		if ((not self.reference_date and mode.reference_date_mandatory) and (self.docstatus == 1)):
			frappe.throw(_("Reference Date is mandatory for Mode of Payment {0}").format(
				frappe.bold(self.mode_of_payment)
			))

		if not self.card_type and self.mode_of_payment_type == "Card" and mode.card_type_mandatory:
			frappe.throw(_("Card Type is mandatory for Mode of Payment {0}").format(
				frappe.bold(self.mode_of_payment)
			))

		if not self.party_bank and self.mode_of_payment_type in ("Bank", "Cheque") and mode.party_bank_mandatory:
			frappe.throw(_("Party Bank is mandatory for Mode of Payment {0}").format(
				frappe.bold(self.mode_of_payment)
			))

	def validate(self):

		self.setup_party_account_field()
		self.set_missing_values()
		self.validate_payment_type()
		self.validate_pos()
		self.validate_party_details()
		self.validate_bank_accounts()
		self.set_exchange_rate()
		self.validate_mandatory()
		self.validate_reference_documents()
		self.set_refund_amount()
		self.set_amounts()
		self.clear_unallocated_reference_document_rows()
		self.validate_payment_against_negative_invoice()

		if self.docstatus == 1:
			reference_doc = check_payment_reference_no_automation(self.payment_type, self.mode_of_payment)
			if reference_doc:
				self.reference_no = make_autoname("{0}".format(reference_doc[2]))
		
		self.custom_validate_transaction_reference()
		self.set_title()
		self.validate_duplicate_entry()
		self.validate_allocated_amount()
		self.ensure_supplier_is_not_blocked(is_payment=True)
		self.set_status()
		self.set_original_reference()

@frappe.whitelist()
def check_payment_reference_no_automation(payment_type, mode_of_payment):
	if frappe.db.exists(
		"Reference Number Details", {"payment_type":payment_type, "mode_of_payment":mode_of_payment,"parenttype": "Payment Entry Settings"}
	):
		payment_type, mode_of_payment, series = frappe.db.get_value( "Reference Number Details", 
															{"payment_type":payment_type, "mode_of_payment":mode_of_payment},
										["payment_type","mode_of_payment", "series"])
		return (payment_type, mode_of_payment, series)
