frappe.pages["cfb-analysis"].on_page_load = function (wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Customer Feed Back Analysis",
		single_column: true,
	});

	frappe.require("cfb_analysis.bundle.js").then(() => {
		new frappe.ui.VuePage({ wrapper: page.body, page });
	});
};
