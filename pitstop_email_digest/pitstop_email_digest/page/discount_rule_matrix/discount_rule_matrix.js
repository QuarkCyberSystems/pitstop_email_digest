frappe.pages["discount-rule-matrix"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Discount Rule Cards"),
		single_column: true,
	});

	frappe.breadcrumbs.add({
		type: "Custom",
		label: __("Accounting"),
		route: "/app/accounting",
	});

	// mount Vue in its own container, page.body also holds the page filter form
	const $container = $("<div>").appendTo(page.body);

	frappe.require("discount_rule_matrix.bundle.js").then(() => {
		wrapper.discount_rule_matrix = new frappe.ui.DiscountRuleMatrix({ wrapper: $container, page });
	});
};
