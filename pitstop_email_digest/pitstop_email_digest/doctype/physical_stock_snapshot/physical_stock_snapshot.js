// Copyright (c) 2026, QCS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Physical Stock Snapshot", {
	refresh(frm) {
		frm.set_query("assigned_to", () => ({
			filters: { status: "Active" },
		}));
	},
});

frappe.ui.form.on("Physical Stock Snapshot Item", {
	item_code: set_stock_qty,
	uom: set_stock_qty,
	available_qty: set_stock_qty,
});

// mirrors set_stock_uom_and_qty() in the python controller, which is the
// authoritative one -- this only keeps the grid honest before a save
function set_stock_qty(frm, cdt, cdn) {
	const row = locals[cdt][cdn];

	if (!row.item_code) {
		frappe.model.set_value(cdt, cdn, { stock_uom: null, stock_qty: 0 });
		return;
	}

	frappe.db.get_value("Item", row.item_code, "stock_uom").then((r) => {
		const stock_uom = (r.message && r.message.stock_uom) || null;
		const uom = row.uom || stock_uom;

		frappe.model.set_value(cdt, cdn, { stock_uom, uom });

		if (!uom || uom === stock_uom) {
			frappe.model.set_value(cdt, cdn, "stock_qty", flt(row.available_qty));
			return;
		}

		frappe.call({
			method: "erpnext.stock.get_item_details.get_conversion_factor",
			args: { item_code: row.item_code, uom },
			callback(res) {
				const conversion = res.message || {};

				// leave the server to raise on a UOM that cannot convert, rather
				// than writing a figure that looks right
				if (conversion.not_convertible) {
					frappe.model.set_value(cdt, cdn, "stock_qty", 0);
					return;
				}

				const factor = flt(conversion.conversion_factor) || 1;
				frappe.model.set_value(cdt, cdn, "stock_qty", flt(row.available_qty) * factor);
			},
		});
	});
}
