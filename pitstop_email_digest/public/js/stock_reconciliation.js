frappe.ui.form.on("Stock Reconciliation", {
	refresh(frm) {
		frm.trigger("add_stock_reconciliation_details_button");
	},

	add_stock_reconciliation_details_button(frm) {
		if (frm.is_new()) return;

		// Opens the Stock Reconciliation Details page with this document selected
		frm.add_custom_button(__("Stock Reconciliation Details"), () => {
			frappe.set_route("stock-reconciliation-details", frm.doc.name);
		});
	},
});
