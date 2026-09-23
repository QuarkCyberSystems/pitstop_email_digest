// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Physical Stock Snapshot", {
	refresh(frm) {
		frm.set_query("assigned_to", () => ({
			filters: { status: "Active" },
		}));
	},
});
