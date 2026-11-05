// Tailwind needs full class names written out, so keep them as literals here.
export const STATUSES = ["Active", "Expired", "Upcoming", "Disabled"];

export const STATUS_STYLES = {
	All: { dot: "bg-gray-700", pill: "bg-gray-100 text-gray-700" },
	Active: { dot: "bg-green-500", pill: "bg-green-100 text-green-800" },
	Expired: { dot: "bg-orange-500", pill: "bg-orange-100 text-orange-800" },
	Upcoming: { dot: "bg-blue-500", pill: "bg-blue-100 text-blue-800" },
	Disabled: { dot: "bg-gray-400", pill: "bg-gray-100 text-gray-600" },
};

export const RATE_BASED_ON = [
	"",
	"Rate",
	"Discount Percentage",
	"Discount Amount",
	"Price List Rate",
	"Valuation Rate",
	"Last Purchase Rate",
	"Higher of Valuation / Last Purchase Rate",
];

export const money = (value, currency) => format_currency(value, currency);

export function benefitText(r) {
	if (r.price_or_product_discount === "Product") {
		const item = r.same_item ? __("same item") : r.free_item || __("free item");
		return `🎁 ${__("Free")} ${item} × ${flt(r.free_qty)}`;
	}
	switch (r.rate_or_discount) {
		case "Rate":
			return `${__("Fixed rate")} ${money(r.rate, r.currency)}`;
		case "Discount Percentage":
			return `${flt(r.discount_percentage)}% ${__("off")}`;
		case "Discount Amount":
			return `${money(r.discount_amount, r.currency)} ${__("off")}`;
		case "Price List Rate":
			return `${__("Rate from")} ${r.from_price_list}`;
		default:
			return r.rate_or_discount ? __(r.rate_or_discount) : __("No price change");
	}
}

export function marginText(r) {
	if (!flt(r.margin_rate_or_amount)) return "";
	return r.margin_type === "Percentage"
		? `${flt(r.margin_rate_or_amount)}%`
		: money(r.margin_rate_or_amount, r.currency);
}

export function scopeText(r) {
	if (r.apply_on === "Transaction") return __("Whole transaction");
	const values = r.scope_values || [];
	const more = values.length > 3 ? ` +${values.length - 3} ${__("more")}` : "";
	return `${__(r.apply_on)}: ${values.slice(0, 3).join(", ") || "–"}${more}`;
}

export function partyText(r) {
	if (!r.applicable_for) return __("All customers");
	return `${__(r.applicable_for)}: ${r[frappe.scrub(r.applicable_for)] || "–"}`;
}

export function rangeText(r) {
	const parts = [];
	if (flt(r.min_qty) || flt(r.max_qty))
		parts.push(`${__("Qty")} ${flt(r.min_qty)} – ${flt(r.max_qty) || "∞"}`);
	if (flt(r.min_amt) || flt(r.max_amt))
		parts.push(`${__("Amt")} ${flt(r.min_amt)} – ${flt(r.max_amt) || "∞"}`);
	return parts.join(" · ") || __("Any");
}

export function validityText(r) {
	const d = (v) => (v ? frappe.datetime.str_to_user(v) : null);
	if (!r.valid_from && !r.valid_upto) return __("Always");
	return `${d(r.valid_from) || __("Start")} → ${d(r.valid_upto) || __("No end date")}`;
}
