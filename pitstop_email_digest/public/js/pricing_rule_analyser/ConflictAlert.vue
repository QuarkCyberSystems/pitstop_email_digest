<template>
	<div
		v-if="clashes.length"
		class="rounded-lg border border-orange-200 bg-orange-50 p-4 text-sm text-orange-900"
	>
		<div class="font-semibold">{{ __("Possible conflict") }}</div>
		<div v-for="[priority, list] in clashes" :key="priority" class="mt-1">
			{{
				__("{0} active price rules share priority {1}: {2}", [
					list.length,
					priority,
					list.map((r) => r.title || r.name).join(", "),
				])
			}}
		</div>
		<div class="mt-2 text-xs text-orange-800">
			{{
				__(
					"If quantity/amount ranges also overlap, ERPNext may show “Multiple Price Rules exists”. Set different priorities to make the winner explicit."
				)
			}}
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	rules: { type: Array, required: true },
});

// ERPNext refuses to pick between active rules with the same priority unless they allow multiple rules.
// Rules with a condition (e.g. SMC packages) only apply when the condition holds, so leave them out.
const clashes = computed(() => {
	const byPriority = {};
	props.rules
		.filter(
			(r) =>
				r.status === "Active" &&
				!r.condition &&
				!r.apply_multiple_pricing_rules &&
				r.price_or_product_discount === "Price"
		)
		.forEach((r) => (byPriority[r.priority || "–"] ||= []).push(r));
	return Object.entries(byPriority).filter(([, list]) => list.length > 1);
});
</script>
