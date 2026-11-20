<template>
	<div class="srd">
		<StockReconciliationDetailsFilters
			:page="page"
			v-model:stock-reconciliation="stockReconciliation"
			v-model:item-code="filters.item_code"
			:item-codes="item_codes"
			v-model:ignored-item-group="filters.ignored_item_group"
			v-model:discrepancy="filters.discrepancy"
			v-model:based-on="filters.based_on"
			v-model:show-stock-uom="display.show_stock_uom"
			v-model:show-loose-uom="display.show_loose_uom"
		/>

		<div v-if="!stockReconciliation" class="srd-empty">
			{{ __("Select a Stock Reconciliation to view its details") }}
		</div>

		<div v-else-if="loading" class="srd-empty">{{ __("Loading...") }}</div>

		<template v-else-if="data">
			<!-- Document details -->
			<div class="srd-header">
				<div class="srd-header-item">
					<span class="srd-label">{{ __("Document No") }}</span>
					<a class="srd-value" :href="doc_url">{{ data.header.name }}</a>
					<span :class="['indicator-pill', status.color]">{{ status.label }}</span>
				</div>
				<div class="srd-header-item">
					<span class="srd-label">{{ __("Location") }}</span>
					<span class="srd-value">{{ strip_abbr(data.header.default_warehouse) || "-" }}</span>
				</div>
				<div class="srd-header-item">
					<span class="srd-label">{{ __("Posting Date/Time") }}</span>
					<span class="srd-value">{{ posting_datetime }}</span>
				</div>
				<div class="srd-header-item">
					<span class="srd-label">{{ __("Purpose") }}</span>
					<span class="srd-value">{{ data.header.purpose }}</span>
				</div>
			</div>

			<StockReconciliationDetailsCards :totals="data.totals" :currency="data.header.currency" />

			<StockReconciliationDetailsTable
				:items="data.items"
				:columns="columns"
				:currency="data.header.currency"
				v-model:sort="sort"
			/>
		</template>
	</div>
</template>

<script setup>
import { ref, reactive, computed, watch } from "vue";
import StockReconciliationDetailsFilters from "./stock_reconciliation_details_filters.vue";
import StockReconciliationDetailsCards from "./stock_reconciliation_details_cards.vue";
import StockReconciliationDetailsTable from "./stock_reconciliation_details_table.vue";
import { strip_abbr } from "./utils.js";

defineProps({
	page: { type: Object, required: true },
});

// Open with a document from /app/stock-reconciliation-details/<name> or frappe.route_options
const stockReconciliation = ref(
	frappe.get_route()[1] || (frappe.route_options && frappe.route_options.stock_reconciliation) || ""
);
frappe.route_options = null;

// Row filters for the selected document, chosen on the page (the document's own print settings are not used)
const filters = reactive({
	item_code: "",
	ignored_item_group: "",
	discrepancy: 0,
	based_on: "Any Difference",
});

// Optional columns, hidden by default (only change what is shown, no reload)
const display = reactive({ show_stock_uom: 0, show_loose_uom: 0 });

const data = ref(null);
// Kept apart from data, which is cleared while reloading, so the Item Code options stay available
const item_codes = ref([]);
const loading = ref(false);
// Kept here, not in the table, which is re-created on every reload
const sort = ref({ field: null, order: null });

const all_columns = [
	{ field: "sr_no", label: __("#"), type: "int" },
	{ field: "warehouse", label: __("Location"), type: "data" },
	{ field: "item_code", label: __("Item Code"), type: "data" },
	{ field: "oe_no", label: __("OE No"), type: "data" },
	{ field: "item_name", label: __("Item Name"), type: "data", wrap: true },
	{ field: "stock_uom", label: __("Stock UOM"), type: "data", show: "show_stock_uom" },
	{ field: "loose_uom", label: __("Loose UOM"), type: "data", show: "show_loose_uom" },
	{ field: "qty", label: __("Physical Qty"), type: "qty" },
	{ field: "current_qty", label: __("System Qty"), type: "qty" },
	{ field: "quantity_difference", label: __("Qty Difference"), type: "qty", diff: true },
	{ field: "amount", label: __("Amount"), type: "currency" },
	{ field: "current_amount", label: __("System Amount"), type: "currency" },
	{ field: "amount_difference", label: __("Amount Difference"), type: "currency", diff: true },
];

const columns = computed(() => all_columns.filter((col) => !col.show || display[col.show]));

// Declared before the immediate watch below, which calls load() straight away
let last_request = 0;

// Item Code belongs to one document: reset it with the document, before the load watch below
// runs (watchers run in the order they are created), so only one request goes out
watch(stockReconciliation, () => {
	filters.item_code = "";
	item_codes.value = [];
});

watch([stockReconciliation, filters], () => load(stockReconciliation.value), { immediate: true });

function load(name) {
	const request = ++last_request;
	data.value = null;
	loading.value = false;
	if (!name) return;

	loading.value = true;
	frappe.call({
		method: "pitstop_email_digest.pitstop_email_digest.page.stock_reconciliation_details.stock_reconciliation_details.get_details",
		args: { stock_reconciliation: name, ...filters },
		callback(r) {
			// Ignore a late response for a previous document or filter selection
			if (request !== last_request) return;
			data.value = r.message;
			item_codes.value = r.message.header.item_codes;
		},
		always() {
			// frappe.call returns a jQuery Deferred, which has no .finally()
			if (request === last_request) loading.value = false;
		},
	});
}

const doc_url = computed(() => frappe.utils.get_form_link("Stock Reconciliation", data.value.header.name));

const status = computed(() => {
	return {
		0: { label: __("Draft"), color: "red" },
		1: { label: __("Submitted"), color: "blue" },
		2: { label: __("Cancelled"), color: "gray" },
	}[data.value.header.docstatus];
});

const posting_datetime = computed(() => {
	const { posting_date, posting_time } = data.value.header;
	return [
		frappe.datetime.str_to_user(posting_date),
		posting_time && frappe.datetime.str_to_user(posting_time, true),
	]
		.filter(Boolean)
		.join(" ");
});
</script>

<style scoped>
.srd {
	padding: var(--padding-md) 0;
}

.srd-empty {
	padding: var(--padding-xl);
	text-align: center;
	color: var(--text-muted);
}

.srd-header {
	display: flex;
	flex-wrap: wrap;
	gap: var(--margin-md) var(--margin-xl);
	padding: var(--padding-md);
	margin-bottom: var(--margin-md);
	background: var(--card-bg);
	border: 1px solid var(--border-color);
	border-radius: var(--border-radius-md);
}

.srd-header-item {
	display: flex;
	flex-direction: column;
	gap: 2px;
}

.srd-header-item .indicator-pill {
	align-self: flex-start;
	margin-top: 4px;
}

.srd-label {
	font-size: var(--text-xs);
	color: var(--text-muted);
	text-transform: uppercase;
	letter-spacing: 0.03em;
}

.srd-value {
	font-weight: 600;
	color: var(--text-color);
}
</style>
