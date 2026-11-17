<template>
	<div class="flex h-full flex-col rounded-2xl px-5 py-4" :class="color.bg">
		<div class="flex items-start justify-between gap-2">
			<h3 class="m-0 truncate text-lg font-semibold text-gray-900" :title="label">{{ label }}</h3>
			<span class="whitespace-nowrap text-xs text-[#5f6368]">
				{{ rules.length == 1 ? __("1 Rule") : __("{0} Rules", [rules.length]) }}
			</span>
		</div>

		<div class="mt-3 flex flex-col">
			<DiscountRow
				v-for="(rule, i) in rules"
				:key="rule.name"
				:rule="rule"
				:color="color"
				:class="{ 'border-0 border-t border-solid border-black/5': i > 0 }"
			/>
		</div>

		<div class="mt-auto pt-3 text-sm text-[#5f6368]">{{ __("Maximum discount") }}</div>
	</div>
</template>

<script setup>
import DiscountRow from "./DiscountRow.vue";

defineProps({
	label: { type: String, required: true },
	rules: { type: Array, required: true },
	color: { type: Object, required: true },
});
</script>
