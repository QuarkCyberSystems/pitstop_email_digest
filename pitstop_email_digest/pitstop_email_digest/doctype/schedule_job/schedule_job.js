// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Schedule Job", {
	refresh(frm) {
		if (frm.doc.status === "Completed") {
			frm.disable_form();
			frm.set_intro(__("This job has already been executed and will not run again."), "green");
		} else if (frm.doc.status === "Failed") {
			frm.set_intro(__("Job failed. Check the error log, fix the issue and click Retry."), "red");
			frm.add_custom_button(__("Retry"), () => {
				frm.call("retry").then(() => frm.reload_doc());
			});
		} else if (!frm.is_new()) {
			frm.set_intro(
				__(
					"Will run once at 00:00 tonight, if there is no GL Entry activity in the last 5 minutes. Otherwise it will be tried again the next night."
				),
				"blue"
			);
		}
	},

	method(frm) {
		const doctypes = { "Update Account Number and Name": "Account", "Rename User": "User" };
		frm.set_value("reference_doctype", doctypes[frm.doc.method]);
		frm.set_value("reference_name", null);
		frm.set_value("new_user_id", null);
	},

	reference_name(frm) {
		if (frm.doc.method !== "Update Account Number and Name") {
			return;
		}

		if (!frm.doc.reference_name) {
			frm.set_value({
				current_account_name: null,
				current_account_number: null,
				new_account_name: null,
				new_account_number: null,
			});
			return;
		}

		frappe.db
			.get_value("Account", frm.doc.reference_name, ["account_name", "account_number"])
			.then((r) => {
				let d = r.message || {};
				frm.set_value({
					current_account_name: d.account_name,
					current_account_number: d.account_number,
					new_account_name: d.account_name,
					new_account_number: d.account_number,
				});
			});
	},
});
