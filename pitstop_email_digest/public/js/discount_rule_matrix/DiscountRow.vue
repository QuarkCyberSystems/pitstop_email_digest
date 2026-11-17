<template>
	<div
		class="-mx-2 flex cursor-pointer items-center justify-between gap-3 rounded-lg px-2 py-2 transition hover:bg-white/60"
		:title="rule.name"
		@click="openRule"
	>
		<div class="min-w-0">
			<div class="truncate text-base text-[#3c4043]">{{ itemLabel }}</div>
			<div v-if="extraFilters" class="truncate text-xs text-[#5f6368]">{{ extraFilters }}</div>
		</div>
		<div class="whitespace-nowrap text-3xl font-semibold leading-none" :class="color.text">
			{{ maxDiscount }}%
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	rule: { type: Object, required: true },
	color: { type: Object, required: true },
});

const maxDiscount = computed(() => flt(props.rule.max_discount));

function openRule() {
	frappe.set_route("Form", "Discount Rule", props.rule.name);
}

const itemLabel = computed(() => {
	const r = props.rule;
	return r.item_group || r.item_name || r.item_code || r.brand || r.item_source || __("All Items");
});

// filters not already shown in the row title
const extraFilters = computed(() => {
	const r = props.rule;
	const parts = [];
	if (r.item_group && (r.item_code || r.brand)) {
		parts.push(r.item_name || r.item_code || r.brand);
	}
	const appliesTo =
		r.applies_to_item_name || r.applies_to_item || r.applies_to_item_group || r.applies_to_item_brand;
	if (appliesTo) {
		parts.push(__("Applies to: {0}", [appliesTo]));
	}
	if (r.user) {
		parts.push(__("User: {0}", [r.user]));
	}
	return parts.join(" · ");
});
</script>
