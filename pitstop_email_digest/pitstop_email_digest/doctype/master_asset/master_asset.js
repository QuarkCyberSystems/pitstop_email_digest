frappe.ui.form.on("Master Asset", {
	refresh(frm) {
		frm.trigger("render_linked_assets");
		frm.set_query("purchase_order", () => ({ filters: { docstatus: 1 } }));

		if (!frm.is_new()) {
			frm.add_custom_button(__("View Assets"), () => {
				frappe.set_route("List", "Asset", { master_asset: frm.doc.name });
			});
		}
	},

	render_linked_assets(frm) {
		const wrapper = frm.get_field("assets_html").$wrapper;
		wrapper.empty();

		const rows = (frm.doc.__onload && frm.doc.__onload.linked_assets) || [];
		if (!rows.length) {
			wrapper.append(`<div class="text-muted">${__("No assets linked to this Master Asset.")}</div>`);
			return;
		}

		const header = `
			<thead><tr>
				<th>${__("Asset")}</th>
				<th>${__("Asset Name")}</th>
				<th>${__("Item Code")}</th>
				<th>${__("Status")}</th>
				<th class="text-right">${__("Gross Amount")}</th>
				<th>${__("Location")}</th>
			</tr></thead>`;

		const body = rows
			.map((r) => {
				const link = `<a href="/app/asset/${encodeURIComponent(r.name)}">${frappe.utils.escape_html(
					r.name
				)}</a>`;
				const amount = format_currency(r.gross_purchase_amount || 0);
				return `<tr>
					<td>${link}</td>
					<td>${frappe.utils.escape_html(r.asset_name || "")}</td>
					<td>${frappe.utils.escape_html(r.item_code || "")}</td>
					<td>${frappe.utils.escape_html(r.status || "")}</td>
					<td class="text-right">${amount}</td>
					<td>${frappe.utils.escape_html(r.location || "")}</td>
				</tr>`;
			})
			.join("");

		wrapper.append(
			`<table class="table table-bordered table-sm">${header}<tbody>${body}</tbody></table>`
		);
	},
});
