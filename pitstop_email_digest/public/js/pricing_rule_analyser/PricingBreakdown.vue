<template>
	<div class="flex flex-col gap-1 rounded-md border border-dashed border-gray-300 p-2 text-sm">
		<div class="flex justify-between gap-4">
			<span class="text-gray-500">{{ pricing.cost_label }}</span>
			<span v-if="pricing.cost" class="text-gray-800">{{ fmt(pricing.cost) }}</span>
			<span v-else class="text-gray-400">{{ __("No cost") }}</span>
		</div>

		<div v-if="pricing.missing" class="text-xs text-gray-500">{{ pricing.missing }}</div>

		<template v-else>
			<div class="flex justify-between gap-4">
				<span class="text-gray-500">{{ __("Base") }}: {{ pricing.base_label }}</span>
				<span class="text-gray-800">{{ fmt(pricing.base_rate) }}</span>
			</div>
			<div v-if="pricing.margin" class="flex justify-between gap-4">
				<span class="text-gray-500">+ {{ __("Margin") }}</span>
				<span class="text-gray-800">{{ fmt(pricing.margin) }}</span>
			</div>
			<div v-if="pricing.discount" class="flex justify-between gap-4">
				<span class="text-gray-500">− {{ __("Discount") }}</span>
				<span class="text-gray-800">{{ fmt(pricing.discount) }}</span>
			</div>
			<div
				class="flex justify-between gap-4 border-t border-gray-200 pt-1 text-base font-semibold text-gray-900"
			>
				<span>{{ __("Selling rate") }}</span>
				<span>{{ fmt(pricing.selling_rate) }}</span>
			</div>
			<div v-if="pricing.profit != null" class="flex justify-between gap-4">
				<span class="text-gray-500">{{ __("Profit vs cost") }}</span>
				<span class="font-semibold" :class="pricing.profit < 0 ? 'text-red-600' : 'text-green-600'">
					{{ pricing.profit < 0 ? "" : "+" }}{{ fmt(pricing.profit) }} ({{
						flt(pricing.profit_pct, 1)
					}}%)
				</span>
			</div>
		</template>
	</div>
</template>

<script setup>
import { money } from "./utils";

const props = defineProps({
	pricing: { type: Object, required: true },
	currency: { type: String, default: "" },
});

const fmt = (value) => money(value, props.currency);
const flt = window.flt;
</script>
