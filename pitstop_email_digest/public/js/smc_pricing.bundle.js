import { createApp } from "vue";
import App from "./smc_pricing/App.vue";

class SMCPricing {
	constructor({ wrapper, page }) {
		this.$wrapper = $(wrapper);
		this.page = page;
		this.app = createApp(App, { page });
		this.app.config.globalProperties.__ = window.__;
		this.app.mount(this.$wrapper.get(0));
	}

	destroy() {
		if (this.app) this.app.unmount();
	}
}

frappe.provide("frappe.ui");
frappe.ui.SMCPricing = SMCPricing;
export default SMCPricing;
