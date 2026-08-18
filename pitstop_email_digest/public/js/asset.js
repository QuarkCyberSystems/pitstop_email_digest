frappe.ui.form.on("Asset", {
	refresh(frm) {
		frm.trigger("set_master_asset_query");
		frm.trigger("apply_master_asset_gates");
		frm.trigger("add_master_asset_actions");
	},

	apply_master_asset_gates(frm) {
		// Master Asset can only be attached to a submitted Asset.
		const draft = frm.doc.docstatus === 0;
		frm.set_df_property("master_asset", "read_only", draft ? 1 : 0);
		frm.set_df_property(
			"master_asset",
			"description",
			draft
				? __("Master Asset can only be linked after this Asset is submitted.")
				: __(
						"Groups this Asset under a parent Master Asset (e.g. all Assets from the same Purchase Order)."
				  )
		);
	},

	master_asset(frm) {
		frm.trigger("set_master_asset_query");
	},

	purchase_order(frm) {
		frm.trigger("set_master_asset_query");
	},

	set_master_asset_query(frm) {
		frm.set_query("master_asset", () => {
			const filters = {};
			if (frm.doc.purchase_order) {
				// Show MAs bound to this asset's PO, or unbound (manual) MAs.
				filters.purchase_order = ["in", ["", null, frm.doc.purchase_order]];
			} else {
				// Asset has no PO: only offer manual (unbound) MAs.
				filters.purchase_order = ["in", ["", null]];
			}
			return { filters };
		});
	},

	add_master_asset_actions(frm) {
		// Only submitted, unlinked Assets can get a new MA.
		if (frm.doc.__islocal || frm.doc.master_asset) return;
		if (frm.doc.docstatus !== 1) return;

		frm.add_custom_button(
			__("Create Master Asset"),
			() => frm.trigger("prompt_create_master_asset"),
			__("Master Asset")
		);
	},

	prompt_create_master_asset(frm) {
		const has_po = !!frm.doc.purchase_order;

		const dialog = new frappe.ui.Dialog({
			title: __("Create Master Asset"),
			fields: [
				{
					fieldname: "purchase_order",
					fieldtype: "Link",
					label: __("Purchase Order"),
					options: "Purchase Order",
					default: frm.doc.purchase_order || "",
					read_only: has_po ? 1 : 0,
					get_query: () => ({ filters: { docstatus: 1 } }),
					description: has_po
						? __("Locked to this Asset's Purchase Order.")
						: __("Optional. Leave blank for a manual grouping."),
				},
				{
					fieldname: "remarks",
					fieldtype: "Small Text",
					label: __("Remarks"),
				},
			],
			primary_action_label: __("Create & Link"),
			primary_action(values) {
				frappe
					.call({
						method: "pitstop_email_digest.overrides.asset.asset_hooks.create_master_asset_from_asset",
						args: {
							asset: frm.doc.name,
							purchase_order: values.purchase_order || null,
							remarks: values.remarks || null,
						},
						freeze: true,
						freeze_message: __("Creating Master Asset..."),
					})
					.then((r) => {
						if (r.message) {
							frappe.show_alert({
								message: __("Linked to Master Asset {0}", [r.message]),
								indicator: "green",
							});
							dialog.hide();
							frm.reload_doc();
						}
					});
			},
		});
		dialog.show();
	},
});
