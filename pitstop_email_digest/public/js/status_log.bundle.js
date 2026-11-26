import { createApp, h, reactive } from "vue";
import StatusLog from "./status_log/StatusLog.vue";

// Mounts the Repair Order Status Log into `el`. Returns a handle so the form
// can point it at another project, reload it, or unmount it.
function mount_status_log(el, project) {
	const props = reactive({ project });
	let instance = null;

	const app = createApp({
		render: () => h(StatusLog, { ...props, ref: (c) => (instance = c) }),
	});
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);

	return {
		el,
		set_project(name) {
			if (props.project === name) instance?.load();
			else props.project = name;
		},
		unmount: () => app.unmount(),
	};
}

frappe.provide("pitstop_email_digest").mount_status_log = mount_status_log;
export default mount_status_log;
