frappe.listview_settings["Schedule Job"] = {
	get_indicator(doc) {
		const colors = { Pending: "orange", Completed: "green", Failed: "red" };
		return [__(doc.status), colors[doc.status], "status,=," + doc.status];
	},
};
