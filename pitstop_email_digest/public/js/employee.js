frappe.ui.form.on("Employee", {
	refresh(frm) {
		frm.trigger("add_update_estimator_details_button");
	},

	add_update_estimator_details_button(frm) {
		if (frm.is_new() || !frm.doc.user_id || !frappe.user.has_role("System Manager")) {
			return;
		}

		frm.add_custom_button(__("Update Estimator Details"), () => {
			frappe.confirm(
				__("Update Estimator Details on Quotations created by {0}?", [frm.doc.user_id]),
				() => {
					frappe.call({
						method: "pitstop_email_digest.overrides.employee.employee_hooks.enqueue_update_estimator_details",
						args: { employee: frm.doc.name },
						freeze: true,
					});
				}
			);
		});
	},
});
