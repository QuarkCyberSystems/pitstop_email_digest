// Shared by the cards and the table of the Stock Reconciliation Details page

export function format_value(value, type, currency) {
	if (type === "currency") return format_currency(value || 0, currency, 2);
	if (type === "qty") return format_number(value || 0, null, 2);
	return value ?? "";
}

export function strip_abbr(warehouse) {
	return (warehouse || "").replace(" - PASLLC", "");
}

// Differences: green when added, red when minus
export function sign_class(value) {
	value = flt(value);
	return value > 0 ? "srd-positive" : value < 0 ? "srd-negative" : "";
}
