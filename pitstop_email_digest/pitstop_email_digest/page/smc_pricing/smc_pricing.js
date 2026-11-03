frappe.pages["smc-pricing"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("SMC Pricing"),
		single_column: true,
	});

	frappe.breadcrumbs.add({
		type: "Custom",
		label: __("Workshop"),
		route: "/app/workshop",
	});

	// mount Vue in its own container, page.body also holds the page filter form
	const $container = $("<div>").appendTo(page.body);

	frappe.require("smc_pricing.bundle.js").then(() => {
		wrapper.smc_pricing = new frappe.ui.SMCPricing({ wrapper: $container, page });
	});
};
