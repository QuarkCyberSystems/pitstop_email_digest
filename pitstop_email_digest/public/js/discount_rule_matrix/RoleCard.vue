<template>
	<div class="rounded-2xl border border-solid border-gray-200 bg-white px-6 pt-5 pb-4 shadow-sm">
		<div
			class="flex items-center justify-between gap-3 border-0 border-b border-solid border-gray-200 pb-4"
		>
			<h2 class="m-0 text-xl font-semibold text-gray-900">
				{{ __("Role: {0}", [role || __("All Roles")]) }}
			</h2>
			<span
				class="whitespace-nowrap rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-600"
			>
				{{ ruleCount == 1 ? __("1 Active Rule") : __("{0} Active Rules", [ruleCount]) }}
			</span>
		</div>

		<!-- One card per Customer / Customer Group -->
		<div
			class="grid gap-4 border-0 border-b border-solid border-gray-200 py-5"
			:style="{ gridTemplateColumns: GRID_COLUMNS }"
		>
			<CustomerCard
				v-for="(group, i) in customerGroups"
				:key="group.label"
				:label="group.label"
				:rules="group.rules"
				:color="CARD_COLORS[i % CARD_COLORS.length]"
			/>
		</div>

		<div class="flex items-center justify-between gap-3 pt-4">
			<span class="text-sm text-gray-500">
				{{ role ? __("All limits are role-specific") : __("Limits apply to all roles") }}
			</span>
			<span class="text-xs text-gray-500">{{ companies.join(", ") }}</span>
		</div>
	</div>
</template>

<script setup>
import CustomerCard from "./CustomerCard.vue";

const CARD_COLORS = [
	{ bg: "bg-[#edf3ec]", text: "text-[#2e6b34]" },
	{ bg: "bg-[#eaeef9]", text: "text-[#2a63c6]" },
	{ bg: "bg-[#f1edf9]", text: "text-[#6a43b8]" },
	{ bg: "bg-[#fbf3e6]", text: "text-[#a2620a]" },
	{ bg: "bg-[#e8f4f2]", text: "text-[#1d7368]" },
];

// 1/4 width cards (gap-4 = 1rem x 3 gaps), wrapping to fewer columns once a card would be under 220px
const GRID_COLUMNS = "repeat(auto-fill, minmax(max(220px, calc((100% - 3rem) / 4)), 1fr))";

defineProps({
	role: { type: String, default: null },
	ruleCount: { type: Number, required: true },
	companies: { type: Array, default: () => [] },
	customerGroups: { type: Array, required: true },
});
</script>
