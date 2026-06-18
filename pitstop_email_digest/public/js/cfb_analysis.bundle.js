import { createApp } from "vue";
import App from "./cfb_analysis/App.vue";

class VuePage {
	constructor({ wrapper, page }) {
		this.$wrapper = $(wrapper);
		this.page = page;
		this.app = createApp(App, { page });
		this.app.mount(this.$wrapper.get(0));
	}

	destroy() {
		if (this.app) this.app.unmount();
	}
}

frappe.provide("frappe.ui");
frappe.ui.VuePage = VuePage;
export default VuePage;
