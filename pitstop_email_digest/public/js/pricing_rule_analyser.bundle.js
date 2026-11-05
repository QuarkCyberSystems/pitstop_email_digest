import { createApp } from "vue";
import App from "./pricing_rule_analyser/App.vue";

class PricingRuleAnalyser {
	constructor({ wrapper, page }) {
		this.page = page;
		// page.body also holds the filter bar, so mount into our own child element.
		this.$wrapper = $('<div class="pra-app"></div>').appendTo(wrapper);
		this.app = createApp(App, { page });
		this.app.config.globalProperties.__ = window.__;
		this.app.mount(this.$wrapper.get(0));
	}

	destroy() {
		if (this.app) this.app.unmount();
		this.$wrapper && this.$wrapper.remove();
	}
}

frappe.provide("frappe.ui");
frappe.ui.PricingRuleAnalyser = PricingRuleAnalyser;
export default PricingRuleAnalyser;
