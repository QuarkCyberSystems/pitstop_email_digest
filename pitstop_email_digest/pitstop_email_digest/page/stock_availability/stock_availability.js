frappe.pages["stock-availability"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Stock Availability",
		single_column: true,
	});

	frappe.breadcrumbs.add("Stock");

	const LOADING_GIF = "/assets/pitstop_email_digest/gifs/gears_gif.gif";

	const ITEM_COLUMNS = [
		{ fieldname: "item_code", label: __("Item Code"), fieldtype: "Data" },
		{ fieldname: "item_name", label: __("Item Name"), fieldtype: "Data" },
	];
	const REQUIRED_COLUMNS = [
		{ fieldname: "req_uom", label: __("UOM"), fieldtype: "Data" },
		{ fieldname: "req_qty", label: __("Qty"), fieldtype: "Float" },
		{ fieldname: "req_stock_uom", label: __("Stock UOM"), fieldtype: "Data" },
		{ fieldname: "req_stock_qty", label: __("Stock Qty"), fieldtype: "Float" },
	];
	const BALANCE_COLUMNS = [
		{ fieldname: "warehouse", label: __("Warehouse"), fieldtype: "Data" },
		{ fieldname: "uom", label: __("UOM"), fieldtype: "Data" },
		{ fieldname: "bal_qty", label: __("Balance Qty"), fieldtype: "Float" },
	];
	const COLUMNS = [...ITEM_COLUMNS, ...REQUIRED_COLUMNS, ...BALANCE_COLUMNS];

	const TXN_COLUMNS = [
		{ fieldname: "item_code", label: __("Item Code"), fieldtype: "Data" },
		{ fieldname: "item_name", label: __("Item Name"), fieldtype: "Data" },
		{ fieldname: "last_in_warehouse", label: __("Last In Warehouse"), fieldtype: "Data" },
		{ fieldname: "last_out_warehouse", label: __("Last Out Warehouse"), fieldtype: "Data" },
	];

	const maybe_auto_fetch = () => {
		const filters = get_filters();
		if (filters.voucher_type && filters.voucher_no && filters.to_date) {
			fetch_and_render();
		}
	};

	const voucher_type_field = page.add_field({
		label: __("Voucher Type"),
		fieldtype: "Link",
		fieldname: "voucher_type",
		options: "DocType",
		reqd: 1,
		change() {
			if (voucher_no_field) voucher_no_field.set_value("");
		},
	});

	const voucher_no_field = page.add_field({
		label: __("Voucher No"),
		fieldtype: "Dynamic Link",
		fieldname: "voucher_no",
		get_options: () => voucher_type_field.get_value() || "",
		reqd: 1,
		change() {
			maybe_auto_fetch();
		},
	});

	page.add_field({
		label: __("From Date"),
		fieldtype: "Date",
		fieldname: "from_date",
		default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		reqd: 1,
		change() {
			maybe_auto_fetch();
		},
	});

	page.add_field({
		label: __("Date"),
		fieldtype: "Date",
		fieldname: "to_date",
		default: frappe.datetime.get_today(),
		reqd: 1,
		change() {
			maybe_auto_fetch();
		},
	});

	const route_options = frappe.route_options || {};

	if (route_options.voucher_type) {
		voucher_type_field.set_value(route_options.voucher_type);

		setTimeout(() => {
			if (route_options.voucher_no) {
				voucher_no_field.set_value(route_options.voucher_no);
			}
		}, 300);
	}

	page.set_primary_action(__("Refresh"), () => fetch_and_render(), "refresh");

	const build_thead = (columns) => `
		<thead class="bg-gray-100 sticky top-0">
			<tr>
				${columns
					.map(
						(c) => `
					<th class="px-3 py-2 text-left text-xs font-bold tracking-wide whitespace-nowrap">
						${frappe.utils.escape_html(c.label)}
					</th>`
					)
					.join("")}
			</tr>
		</thead>`;

	const th_cell = (label, attrs = "") => `
		<th ${attrs} class="px-3 py-2 text-left text-xs font-bold tracking-wide whitespace-nowrap border border-gray-200">
			${frappe.utils.escape_html(label)}
		</th>`;

	const build_grouped_thead = () => `
		<thead class="bg-gray-100 sticky top-0">
			<tr>
				${ITEM_COLUMNS.map((c) => th_cell(c.label, 'rowspan="2"')).join("")}
				${th_cell(__("Required"), `colspan="${REQUIRED_COLUMNS.length}"`)}
				${th_cell(__("Available"), `colspan="${BALANCE_COLUMNS.length}"`)}
			</tr>
			<tr>
				${REQUIRED_COLUMNS.map((c) => th_cell(c.label)).join("")}
				${BALANCE_COLUMNS.map((c) => th_cell(c.label)).join("")}
			</tr>
		</thead>`;

	$(page.body).append(`
		<div id="stock-avail-container" class="p-4 space-y-3">
			<h3 class="text-base font-semibold text-gray-800 border-b border-gray-200 pb-2">
				${__("Stock Availability")}
			</h3>
			<div id="stock-avail-table-wrap" class="inline-block overflow-hidden overflow-x-auto rounded-lg border border-gray-200 shadow-sm bg-white max-w-full">
				<table class="w-auto text-sm" style="border-collapse: collapse;">
					${build_grouped_thead()}
					<tbody id="stock-avail-tbody">${state_row(COLUMNS, __("Select filters to load data."))}</tbody>
				</table>
			</div>

			<h3 class="text-base font-semibold text-gray-800 border-b border-gray-200 pb-2 pt-4">
				${__("Stock Transaction")}
			</h3>
			<div id="stock-txn-table-wrap" class="inline-block overflow-hidden overflow-x-auto rounded-lg border border-gray-200 shadow-sm bg-white max-w-full">
				<table class="w-auto text-sm" style="border-collapse: collapse;">
					${build_thead(TXN_COLUMNS)}
					<tbody id="stock-txn-tbody">${state_row(
						TXN_COLUMNS,
						__("Select filters and click Get Stock to load data.")
					)}</tbody>
				</table>
			</div>
		</div>
	`);

	function state_row(columns, message, opts = {}) {
		const content = opts.loading
			? `<img src="${LOADING_GIF}" alt="${__(
					"Loading"
			  )}" class="inline-block h-5 w-5" style="height:2cm;" />
			   <div class="mt-2">${frappe.utils.escape_html(message)}</div>`
			: `<span>${frappe.utils.escape_html(message)}</span>`;
		return `
			<tr style="height:3cm;">
				<td colspan="${columns.length}" class="px-3 py-10 text-center text-gray-500">
					${content}
				</td>
			</tr>`;
	}

	function get_filters() {
		const values = page.fields_dict;
		return {
			voucher_type: values.voucher_type.get_value(),
			voucher_no: values.voucher_no.get_value(),
			from_date: values.from_date.get_value(),
			to_date: values.to_date.get_value(),
		};
	}

	function fetch_and_render() {
		const filters = get_filters();
		if (!filters.voucher_type || !filters.voucher_no || !filters.to_date) {
			frappe.msgprint(__("Voucher Type, Voucher No and Date are required."));
			return;
		}

		$(wrapper)
			.find("#stock-avail-tbody")
			.html(state_row(COLUMNS, __("Loading stock balance..."), { loading: true }));
		$(wrapper)
			.find("#stock-txn-tbody")
			.html(state_row(TXN_COLUMNS, __("Loading stock transactions..."), { loading: true }));

		frappe.call({
			method: "pitstop_email_digest.pitstop_email_digest.page.stock_availability.stock_availability.get_items_balance",
			args: filters,
			callback: (r) => {
				const rows = r && r.message && r.message.rows ? r.message.rows : [];
				const items_dict = (r && r.message && r.message.items_dict) || [];
				render_rows(rows, items_dict);
			},
			error: () => {
				$(wrapper)
					.find("#stock-avail-tbody")
					.html(state_row(COLUMNS, __("Failed to load data.")));
			},
		});

		frappe.call({
			method: "pitstop_email_digest.pitstop_email_digest.page.stock_availability.stock_availability.get_items_stock_transaction",
			args: filters,
			callback: (r) => {
				const rows = r && r.message && r.message.rows ? r.message.rows : [];
				render_txn_rows(rows);
			},
			error: () => {
				$(wrapper)
					.find("#stock-txn-tbody")
					.html(state_row(TXN_COLUMNS, __("Failed to load data.")));
			},
		});
	}

	function render_rows(rows, items_dict) {
		const $tbody = $(wrapper).find("#stock-avail-tbody");

		if (!rows.length) {
			$tbody.html(state_row(COLUMNS, __("No Data")));
			return;
		}

		const sorted_rows = rows.slice().sort((a, b) => {
			const ac = (a.item_code || "").toString();
			const bc = (b.item_code || "").toString();
			if (ac === bc) {
				return (a.warehouse || "").toString().localeCompare((b.warehouse || "").toString());
			}
			return ac.localeCompare(bc);
		});

		const required_by_item = build_required_by_item(items_dict);
		$tbody.html(build_availability_rows(sorted_rows, required_by_item));
	}

	function build_required_by_item(items_dict) {
		const map = {};
		(items_dict || []).forEach((it) => {
			const ic = it.item_code;
			if (!ic) return;
			if (!map[ic]) {
				map[ic] = {
					req_uom: it.uom,
					req_qty: 0,
					req_stock_uom: it.stock_uom,
					req_stock_qty: 0,
				};
			}
			map[ic].req_qty += flt(it.qty);
			map[ic].req_stock_qty += flt(it.stock_qty);
		});
		return map;
	}

	function build_availability_rows(sorted_rows, required_by_item) {
		const group_bg = ["#ffffff", "#eff6ff"];
		const groups = [];
		const group_index = {};
		sorted_rows.forEach((row) => {
			const ic = row.item_code;
			if (!(ic in group_index)) {
				group_index[ic] = groups.length;
				groups.push({ item_code: ic, rows: [] });
			}
			groups[group_index[ic]].rows.push(row);
		});

		const td_style_base = "padding: 8px 12px; border-bottom: 1px solid #d1d5db; white-space: nowrap;";

		return groups
			.map((group, gi) => {
				const bg = group_bg[gi % group_bg.length];
				const required = required_by_item[group.item_code] || {};
				const rowspan = group.rows.length;
				const top_border = gi > 0 ? "border-top: 2px solid #1f2937;" : "";

				return group.rows
					.map((row, ri) => {
						const td_style = `${td_style_base} ${ri === 0 ? top_border : ""}`;
						const merged_td_style = `${td_style} vertical-align: top;`;
						const cells = [];

						if (ri === 0) {
							ITEM_COLUMNS.forEach((c) => {
								cells.push(
									`<td rowspan="${rowspan}" style="${merged_td_style}">${format_cell(
										row,
										c
									)}</td>`
								);
							});
							REQUIRED_COLUMNS.forEach((c) => {
								cells.push(
									`<td rowspan="${rowspan}" style="${merged_td_style}">${format_cell(
										required,
										c
									)}</td>`
								);
							});
						}

						BALANCE_COLUMNS.forEach((c) => {
							cells.push(`<td style="${td_style}">${format_cell(row, c)}</td>`);
						});

						return `<tr style="background-color: ${bg};">${cells.join("")}</tr>`;
					})
					.join("");
			})
			.join("");
	}

	function flt(v) {
		const n = Number(v);
		return isNaN(n) ? 0 : n;
	}

	function render_txn_rows(rows) {
		const $tbody = $(wrapper).find("#stock-txn-tbody");

		if (!rows.length) {
			$tbody.html(state_row(TXN_COLUMNS, __("No Data")));
			return;
		}

		const sorted_rows = rows
			.slice()
			.sort((a, b) => (a.item_code || "").toString().localeCompare((b.item_code || "").toString()));

		$tbody.html(build_grouped_rows(sorted_rows, TXN_COLUMNS));
	}

	function build_grouped_rows(sorted_rows, columns) {
		const group_bg = ["#ffffff", "#eff6ff"];
		let group_idx = -1;
		let prev_item = null;

		return sorted_rows
			.map((row, idx) => {
				const is_new_group = row.item_code !== prev_item;
				if (is_new_group) {
					group_idx += 1;
					prev_item = row.item_code;
				}
				const bg = group_bg[group_idx % group_bg.length];
				const top_border = is_new_group && idx > 0 ? "border-top: 2px thin #1f2937;" : "";
				const td_style = `padding: 8px 12px; border-bottom: 1px solid #d1d5db; white-space: nowrap; ${top_border}`;

				return `
					<tr style="background-color: ${bg};">
						${columns.map((c) => `<td style="${td_style}">${format_cell(row, c)}</td>`).join("")}
					</tr>`;
			})
			.join("");
	}

	function format_cell(row, column) {
		let value = row[column.fieldname];
		if (value === null || value === undefined || value === "") return "";

		const ft = column.fieldtype;
		if (ft === "Float" || ft === "Currency" || ft === "Int") {
			const num = Number(value);
			if (isNaN(num)) return frappe.utils.escape_html(String(value));
			return ft === "Int" ? num.toLocaleString() : format_number(num, null, ft === "Currency" ? 2 : 3);
		}
		if (ft === "Date") {
			return frappe.datetime.str_to_user(value);
		}
		return frappe.utils.escape_html(String(value));
	}
};
