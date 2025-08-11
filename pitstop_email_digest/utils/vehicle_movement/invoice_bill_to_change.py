import frappe
from erpnext.accounts.general_ledger import delete_gl_entries

from erpnext.projects.doctype.project.project import get_bill_to_details

from .invoice_data_list_file import get_invoice_data_list

from erpnext.accounts.party import _get_party_details


def update_bill_to_sales_invoice(invoice_number, bill_to):
	delete_gl_entries(voucher_type="Sales Invoice", voucher_no=invoice_number)
	sinv_doc = frappe.get_doc("Sales Invoice", invoice_number)
	sinv_doc.load_doc_before_save()
	sinv_doc.bill_to = bill_to
	sinv_doc.set_missing_lead_customer_details()
	sinv_doc.set_user_and_timestamp()
	sinv_doc.db_update()
	sinv_doc.make_gl_entries(repost_future_gle=False, from_repost=True)
	sinv_doc.save_version()

def update_bill_to_project(project_number, bill_to):
	ro_doc = frappe.get_doc("Project", project_number)
	ro_doc.load_doc_before_save()
	ro_doc.bill_to = bill_to
	args_dict = ro_doc.as_dict()
	bill_to_details = get_bill_to_details(args_dict)
	for k, v in bill_to_details.items():
		if ro_doc.meta.has_field(k) and not ro_doc.get(k) or k in ro_doc.force_customer_fields:
			ro_doc.set(k, v)
	ro_doc.set_user_and_timestamp()
	ro_doc.db_update()
	ro_doc.save_version()

def check_ro_billto_customer():

	invoices = get_invoice_data_list()
	print(len(invoices))
	# frappe.throw("stop")

	no_existng_invoice = []
	not_able_edit_ro = []
	payment_entry_invoice = []
	is_pos = []
	for i, each_invoice in enumerate(invoices):
		print(f"{i+1}/{len(invoices)}: {each_invoice}")
		if frappe.db.exists("Sales Invoice", each_invoice.get("sales_invoice")):
			repair_order, outstanding_amount, rounded_total, pos_profile = frappe.db.get_value("Sales Invoice", each_invoice.get("sales_invoice"), ["project", "outstanding_amount", "rounded_total", "pos_profile"])

			payment_entry = frappe.db.sql("""
				select 
						tpe.name
				from 
					`tabPayment Entry Reference` tper
				join
					`tabPayment Entry` tpe
				on
					tpe.name = tper.parent
				where tpe.docstatus = 1 and tper.reference_name = '{reference_name}'            
			""".format(reference_name=each_invoice.get("sales_invoice")), as_dict=True)

			if payment_entry:
				payment_entry_invoice.append(each_invoice.get("sales_invoice"))
				continue
			if outstanding_amount != rounded_total:
				payment_entry_invoice.append(each_invoice.get("sales_invoice"))
				continue

			if pos_profile:
				is_pos.append(each_invoice.get("sales_invoice"))
				continue #not need to update pos invoices
			
			if not repair_order:
				update_bill_to_sales_invoice(each_invoice.get("sales_invoice"), each_invoice.get("bill_to"))
			else:
				update_bill_to_project(repair_order, each_invoice.get("bill_to"))
				update_bill_to_sales_invoice(each_invoice.get("sales_invoice"), each_invoice.get("bill_to"))
		else:
			no_existng_invoice.append(each_invoice.get("sales_invoice"))

	print("no_existng_invoice")
	print(len(no_existng_invoice))
	print(no_existng_invoice)

	print("not able to edit ro")
	print(len(not_able_edit_ro))
	print(not_able_edit_ro)

	print("payment_entry_invoice")
	print(len(payment_entry_invoice))
	print(payment_entry_invoice)

	print("is_pos")
	print(len(is_pos))
	print(is_pos)
	