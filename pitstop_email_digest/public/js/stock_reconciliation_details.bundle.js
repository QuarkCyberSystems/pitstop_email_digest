import { createApp } from "vue";
import App from "./stock_reconciliation_details/App.vue";

class StockReconciliationDetails {
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
frappe.ui.StockReconciliationDetails = StockReconciliationDetails;
export default StockReconciliationDetails;
