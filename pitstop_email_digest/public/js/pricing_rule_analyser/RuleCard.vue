<template>
	<div class="flex flex-col gap-3 rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
		<div class="flex items-start justify-between gap-2">
			<a
				:href="`/app/pricing-rule/${encodeURIComponent(rule.name)}`"
				class="font-semibold text-gray-900 hover:underline"
			>
				{{ rule.title || rule.name }}
			</a>
			<span
				class="whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium"
				:class="STATUS_STYLES[rule.status].pill"
			>
				{{ __(rule.status) }}
			</span>
		</div>

		<div class="text-lg font-semibold text-gray-900">
			{{ benefitText(rule) }}
			<span v-if="markupText(rule)" class="text-sm font-normal text-gray-500">
				(+ {{ markupText(rule) }} {{ __("markup") }})
			</span>
		</div>

		<PricingBreakdown v-if="rule.pricing" :pricing="rule.pricing" :currency="rule.currency" />

		<dl class="flex flex-col gap-1 text-sm">
			<div v-for="[label, value] in rows" :key="label" class="flex justify-between gap-4">
				<dt class="text-gray-500">{{ label }}</dt>
				<dd class="text-right text-gray-800">{{ value }}</dd>
			</div>
		</dl>

		<ConditionBox v-if="rule.condition" :condition="rule.condition" :smc-package="rule.smc_package" />

		<div
			v-if="rule.reasons && rule.reasons.length"
			class="rounded-md bg-green-50 p-2 text-sm text-green-900"
		>
			<div class="font-semibold">{{ __("Why it matched") }}</div>
			<div v-for="reason in rule.reasons" :key="reason">✓ {{ reason }}</div>
		</div>

		<div v-if="tags.length" class="flex flex-wrap gap-1">
			<span
				v-for="tag in tags"
				:key="tag"
				class="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700"
			>
				{{ tag }}
			</span>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import PricingBreakdown from "./PricingBreakdown.vue";
import ConditionBox from "./ConditionBox.vue";
import {
	STATUS_STYLES,
	benefitText,
	markupText,
	scopeText,
	partyText,
	rangeText,
	validityText,
} from "./utils";

const props = defineProps({
	rule: { type: Object, required: true },
});

const rows = computed(() => {
	const r = props.rule;
	return [
		[
			__("Rate based on"),
			r.price_or_product_discount === "Product" ? __("Free item") : r.rate_or_discount || __("Not set"),
		],
		[__("Applies on"), scopeText(r)],
		[__("For"), partyText(r)],
		[__("Qty / Amount"), rangeText(r)],
		[__("Valid"), validityText(r)],
		[__("Priority"), r.priority || __("Not set")],
	];
});

const tags = computed(() => {
	const r = props.rule;
	return [
		r.is_smc && __("SMC"),
		r.apply_multiple_pricing_rules && __("Stacks with others"),
		r.for_price_list && `${__("Price List")}: ${r.for_price_list}`,
		r.warehouse && `${__("Warehouse")}: ${r.warehouse}`,
		r.company,
	].filter(Boolean);
});
</script>
