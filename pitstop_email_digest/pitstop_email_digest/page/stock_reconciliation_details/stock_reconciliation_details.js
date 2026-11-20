frappe.pages["stock-reconciliation-details"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Stock Reconciliation Details"),
		single_column: true,
	});

	frappe.breadcrumbs.add({
		type: "Custom",
		label: __("Stock"),
		route: "/app/stock",
	});

	// mount Vue in its own container, page.body also holds the page filter form
	const $container = $("<div>").appendTo(page.body);

	frappe.require("stock_reconciliation_details.bundle.js").then(() => {
		new frappe.ui.StockReconciliationDetails({ wrapper: $container, page });
	});
};

// Revisiting /app/stock-reconciliation-details/<name> switches the filter; the first load reads the route in App.vue
frappe.pages["stock-reconciliation-details"].on_page_show = function (wrapper) {
	const field = wrapper.page.fields_dict.stock_reconciliation;
	const name = frappe.get_route()[1];
	if (field && name && field.get_value() !== name) field.set_value(name);
};
