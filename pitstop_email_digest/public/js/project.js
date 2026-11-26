// Repair Order "Status Log" (Status tab): Draft -> ... -> Completed, with the
// time the job spent at each status. UI lives in status_log/StatusLog.vue.

frappe.ui.form.on("Project", {
	refresh(frm) {
		const status_tab = (frm.layout.tabs || []).find((tab) => tab.df.fieldname === "status_section");
		if (!status_tab) return;

		let $section = status_tab.wrapper.find(".ps-status-log-section");
		if (frm.is_new()) {
			$section.addClass("hide");
			return;
		}

		if (!$section.length) {
			// Not a `.form-section`: Layout.refresh_sections() hides any form-section
			// without frappe controls in it, so the card is drawn by the component.
			$section = $(`
				<div class="ps-status-log-section"><div class="ps-status-log"></div></div>
			`).appendTo(status_tab.wrapper);
		}
		$section.removeClass("hide");

		const project = frm.doc.name;
		frappe.require("status_log.bundle.js").then(() => {
			const el = $section.find(".ps-status-log").get(0);
			if (frm.status_log && frm.status_log.el === el) {
				frm.status_log.set_project(project);
			} else {
				frm.status_log = frappe.provide("pitstop_email_digest").mount_status_log(el, project);
			}
		});
	},
});
