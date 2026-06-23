frappe.provide("pitstop_email_digest");

pitstop_email_digest.SalesInvoicePitstopEmailDigest = class SalesInvoicePitstopEmailDigest extends (
	automotive.SalesInvoiceAuto
) {
	// Child table field method format: {childtable_fieldname}_{field_name}
	// Example: if child table fieldname is "items" and field is "item_code"
	item_code(frm, cdt, cdn) {
		super.item_code(frm, cdt, cdn);
		let row = locals[cdt][cdn]; // Get the current child row
		if (row.item_code) {
			this.fetch_extended_warranty_details(frm, cdt, cdn);
		}
	}

	extended_warranty_supplier(frm, cdt, cdn) {
		let row = locals[cdt][cdn]; // Get the current child row
		if (row.item_code) {
			this.fetch_extended_warranty_details(frm, cdt, cdn);
		}
	}

	fetch_extended_warranty_details(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		if (!row.item_code) return;

		let form = this.frm;
		frappe.call({
			method: "pitstop_email_digest.utils.extended_warranty.extended_warranty.get_extended_warranty_item_details",
			args: {
				item_code: row.item_code,
				supplier: row.extended_warranty_supplier,
			},
			callback: function (r) {
				console.log(r.message);
				if (r.message && r.message.is_extended_warranty) {
					// used object to avoide the refetch based on set value
					Object.assign(row, r.message);
				} else {
					// used object to avoide the refetch based on set value
					Object.assign(row, {
						is_extended_warranty: false,
						unearned_revenue_percentage: 0.0,
						extended_warranty_cos: "",
						extended_warranty_liability: "",
						extended_warranty_supplier: "",
						extended_warranty_supplier_name: "",
					});
				}
				form.refresh_field("items");
			},
		});
		// }
	}
};

extend_cscript(cur_frm.cscript, new pitstop_email_digest.SalesInvoicePitstopEmailDigest({ frm: cur_frm }));
