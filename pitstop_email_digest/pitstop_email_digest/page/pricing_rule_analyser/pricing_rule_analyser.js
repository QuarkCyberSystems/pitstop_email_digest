frappe.pages["pricing-rule-analyser"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Pricing Rule Analyser"),
		single_column: true,
	});
	frappe.breadcrumbs.add("Selling");

	frappe.require(["pricing_rule_analyser.bundle.css", "pricing_rule_analyser.bundle.js"]).then(() => {
		wrapper.pricing_rule_analyser = new frappe.ui.PricingRuleAnalyser({
			wrapper: page.body,
			page,
		});
	});
};
