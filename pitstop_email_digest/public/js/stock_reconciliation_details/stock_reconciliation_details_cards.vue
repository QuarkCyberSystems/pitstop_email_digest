<template>
	<div class="srd-cards">
		<div v-for="card in cards" :key="card.key" class="srd-card">
			<div class="srd-card-label">{{ card.label }}</div>
			<div :class="['srd-card-value', card.diff ? sign_class(card.value) : '']">
				{{ card.formatted }}
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { format_value, sign_class } from "./utils.js";

const props = defineProps({
	totals: { type: Object, required: true },
	currency: { type: String, default: "" },
});

const cards = computed(() => {
	const t = props.totals;
	return [
		{ key: "row_count", label: __("Items"), value: t.row_count, type: "int" },
		{ key: "physical_qty", label: __("Total Physical Qty"), value: t.physical_qty, type: "qty" },
		{ key: "system_qty", label: __("Total System Qty"), value: t.system_qty, type: "qty" },
		{ key: "added_qty", label: __("Total Added Qty"), value: t.added_qty, type: "qty", diff: true },
		{ key: "minus_qty", label: __("Total Minus Qty"), value: t.minus_qty, type: "qty", diff: true },
		{
			key: "qty_difference",
			label: __("Total Qty Difference"),
			value: t.qty_difference,
			type: "qty",
			diff: true,
		},
		{
			key: "added_amount",
			label: __("Total Added Amount"),
			value: t.added_amount,
			type: "currency",
			diff: true,
		},
		{
			key: "minus_amount",
			label: __("Total Minus Amount"),
			value: t.minus_amount,
			type: "currency",
			diff: true,
		},
		{
			key: "amount_difference",
			label: __("Total Amount Difference"),
			value: t.amount_difference,
			type: "currency",
			diff: true,
		},
	].map((card) => ({ ...card, formatted: format_value(card.value, card.type, props.currency) }));
});
</script>

<style scoped>
.srd-cards {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
	gap: var(--margin-sm);
	margin-bottom: var(--margin-md);
}

.srd-card {
	padding: var(--padding-sm) var(--padding-md);
	background: var(--card-bg);
	border: 1px solid var(--border-color);
	border-radius: var(--border-radius-md);
	box-shadow: var(--shadow-xs);
}

.srd-card-label {
	font-size: var(--text-xs);
	color: var(--text-muted);
}

.srd-card-value {
	margin-top: 4px;
	font-size: var(--text-xl);
	font-weight: 600;
	font-variant-numeric: tabular-nums;
	color: var(--heading-color);
}

.srd-positive {
	color: var(--green-600);
}

.srd-negative {
	color: var(--red-600);
}
</style>
