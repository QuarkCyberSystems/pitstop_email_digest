// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Extended Warranty Configure Details", {
	default(frm, cdt, cdn) {
		console.log("here we go");
		const row = locals[cdt][cdn];

		if (row.default) {
			frm.doc.extended_warranty_configure_details.forEach((d) => {
				if (d.name !== row.name) {
					if (d.default) {
						row.default = 0;
						frappe.msgprint("Only one raw can be default check box");
					}
				}
			});

			frm.refresh_field("extended_warranty_configure_details");
		}
	},
});
