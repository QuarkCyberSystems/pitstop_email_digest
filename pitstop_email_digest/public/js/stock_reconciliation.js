frappe.ui.form.on("Stock Reconciliation", {
	refresh(frm) {
		frm.trigger("add_stock_reconciliation_details_button");
	},

	add_stock_reconciliation_details_button(frm) {
		if (frm.is_new()) return;

		// Opens the Stock Reconciliation Details page with this document selected, in a new tab
		frm.add_custom_button(__("Stock Reconciliation Details"), () => {
			window.open(`/app/stock-reconciliation-details/${encodeURIComponent(frm.doc.name)}`, "_blank");
		});
	},
});
