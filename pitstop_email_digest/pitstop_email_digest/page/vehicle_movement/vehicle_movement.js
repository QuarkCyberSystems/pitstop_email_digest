frappe.pages["vehicle_movement"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Vehicle Movement"),
		single_column: true,
	});

	frappe.breadcrumbs.add({
		type: "Custom",
		label: __("Workshop"),
		route: "/app/workshop",
	});

	// mount Vue in its own container, page.body also holds the page filter form
	const $container = $("<div>").appendTo(page.body);

	frappe.require("vehicle_movement.bundle.js").then(() => {
		new frappe.ui.VuePage({ wrapper: $container, page });
	});
};
