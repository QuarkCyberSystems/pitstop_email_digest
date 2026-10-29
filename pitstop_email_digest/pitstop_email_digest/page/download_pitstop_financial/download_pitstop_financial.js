frappe.pages["download-pitstop-financial"].on_page_load = function (wrapper) {
	new DownloadPitstopFinancial(wrapper);
};

const PITSTOP_FINANCIAL_SHEETS = [
	{ fieldname: "balance_sheet", label: __("Summarized Balance Sheet") },
	{ fieldname: "profit_and_loss", label: __("Summarized Profit and Loss") },
	{ fieldname: "cash_flow", label: __("Summarized Cash Flow") },
	{ fieldname: "fixed_assets", label: __("Fixed Assets Statement") },
	{ fieldname: "changes_in_equity", label: __("Statement of Changes in Equity") },
];

class DownloadPitstopFinancial {
	constructor(wrapper) {
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Download Pitstop Financial"),
			single_column: true,
		});
		frappe.breadcrumbs.add("Accounts");

		this.make_form();
		this.page.set_primary_action(__("Generate Excel"), () => this.generate(), "es-line-download");
		this.setup_realtime();
	}

	make_form() {
		const sheet_fields = [];
		PITSTOP_FINANCIAL_SHEETS.forEach((d, i) => {
			if (i && i % 2 === 0) {
				sheet_fields.push({ fieldtype: "Column Break" });
			}
			sheet_fields.push({
				fieldname: d.fieldname,
				label: d.label,
				fieldtype: "Check",
				default: 1,
				change: () => this.update_select_all(),
			});
		});

		this.form = new frappe.ui.FieldGroup({
			parent: $('<div class="pitstop-financial-form"></div>').appendTo(this.page.main),
			fields: [
				{
					fieldname: "company",
					label: __("Company"),
					fieldtype: "Link",
					options: "Company",
					default: frappe.defaults.get_user_default("Company"),
					reqd: 1,
				},
				{
					fieldname: "report_date",
					label: __("To Date"),
					fieldtype: "Date",
					default: frappe.datetime.month_end(
						frappe.datetime.add_months(frappe.datetime.get_today(), -1)
					),
					reqd: 1,
				},
				{ fieldtype: "Column Break" },
				{
					fieldname: "cost_center",
					label: __("Cost Center"),
					fieldtype: "Link",
					options: "Cost Center",
					get_query: () => ({ filters: { company: this.form.get_value("company") } }),
				},
				{
					fieldname: "tree_view",
					label: __("Show Sub Groups (Tree View)"),
					fieldtype: "Check",
					default: 1,
				},
				{ fieldtype: "Section Break", label: __("Reports") },
				{
					fieldname: "select_all",
					label: __("Select All"),
					fieldtype: "Check",
					default: 1,
					change: () => this.toggle_all(),
				},
				{ fieldtype: "Section Break" },
				...sheet_fields,
				{ fieldtype: "Section Break" },
				{
					fieldname: "mandatory_sheets_note",
					fieldtype: "HTML",
					options: `<p class="text-muted small">${__(
						"MoM Trial Balance and Account Group MoM are always included."
					)}</p>`,
				},
				{ fieldname: "status", fieldtype: "HTML" },
			],
		});
		this.form.make();
	}

	toggle_all() {
		if (this._updating) return;

		const checked = this.form.get_value("select_all") ? 1 : 0;
		this._updating = true;
		PITSTOP_FINANCIAL_SHEETS.forEach((d) => this.form.set_value(d.fieldname, checked));
		this._updating = false;
	}

	update_select_all() {
		if (this._updating) return;

		const all_checked = PITSTOP_FINANCIAL_SHEETS.every((d) => this.form.get_value(d.fieldname));
		if (cint(this.form.get_value("select_all")) !== cint(all_checked)) {
			this._updating = true;
			this.form.set_value("select_all", all_checked ? 1 : 0).then(() => (this._updating = false));
		}
	}

	generate() {
		const values = this.form.get_values();
		if (!values) return;

		const sheets = PITSTOP_FINANCIAL_SHEETS.filter((d) => values[d.fieldname]).map((d) => d.fieldname);

		frappe.call({
			method: "pitstop_email_digest.pitstop_email_digest.page.download_pitstop_financial.download_pitstop_financial.enqueue_download",
			args: {
				filters: {
					company: values.company,
					report_date: values.report_date,
					cost_center: values.cost_center,
					tree_view: values.tree_view,
					sheets: sheets,
				},
			},
			freeze: true,
			callback: (r) => {
				if (r.message) {
					frappe.show_alert({ message: r.message, indicator: "blue" });
					this.set_status(`<span class="indicator-pill blue">${r.message}</span>`);
				}
			},
		});
	}

	setup_realtime() {
		frappe.realtime.on("pitstop_financial_ready", (data) => {
			if (data.file_url) {
				const link = `<a href="${encodeURI(
					data.file_url
				)}" target="_blank">${frappe.utils.escape_html(data.file_name)}</a>`;
				this.set_status(
					`<span class="indicator-pill green">${data.message}</span><p class="mt-3">${__(
						"Download"
					)}: ${link}</p>`
				);
				frappe.show_alert({ message: data.message, indicator: "green" });
			} else {
				this.set_status(`<span class="indicator-pill red">${data.message}</span>`);
				frappe.show_alert({ message: data.message, indicator: "red" });
			}
		});
	}

	set_status(html) {
		this.form.get_field("status").$wrapper.html(html);
	}
}
