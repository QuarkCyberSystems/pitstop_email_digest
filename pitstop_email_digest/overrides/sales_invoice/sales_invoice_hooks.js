frappe.ui.form.on("Sales Invoice Item", {
	item_code: function (frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		console.log(row);
		// frappe.call({
		//     method: "erpnext.accounts.party.get_contact_details",
		//     args: {
		//         contact: row.contact || ""
		//     },
		//     callback: function(r) {
		//         if (r.message) {
		//             frappe.model.set_value(row.doctype, row.name, r.message);
		//         }
		//     }
		// });
	},
});
