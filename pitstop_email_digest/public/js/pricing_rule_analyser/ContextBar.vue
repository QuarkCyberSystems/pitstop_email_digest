<template>
	<div v-if="!hasFilters" class="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">
		{{
			__(
				"No filters set — showing every selling pricing rule. Pick an item to see cost and selling rates, and a customer to see only the rules that would apply."
			)
		}}
	</div>

	<div v-else class="flex flex-wrap gap-x-10 gap-y-3 rounded-lg bg-gray-50 p-4 text-sm">
		<div v-if="context.item_code">
			<div class="text-xs uppercase tracking-wide text-gray-500">{{ __("Item") }}</div>
			<div class="font-semibold text-gray-900">
				{{ context.item_code }}
				<span
					v-if="context.item_name && context.item_name !== context.item_code"
					class="font-normal text-gray-600"
				>
					· {{ context.item_name }}
				</span>
			</div>
			<div class="text-xs text-gray-500">
				{{ __("Group") }}: {{ context.item_group }}
				<template v-if="context.brand"> · {{ __("Brand") }}: {{ context.brand }}</template>
			</div>
		</div>

		<div v-if="context.item_code">
			<div class="text-xs uppercase tracking-wide text-gray-500">{{ __("Cost (avg. valuation)") }}</div>
			<div class="font-semibold text-gray-900">{{ money(context.cost) }}</div>
			<div class="text-xs text-gray-500">
				{{ context.default_price_list }}:
				{{ context.list_rate != null ? money(context.list_rate) : __("no Item Price") }}
			</div>
		</div>

		<div v-if="context.customer">
			<div class="text-xs uppercase tracking-wide text-gray-500">{{ __("Customer") }}</div>
			<div class="font-semibold text-gray-900">
				{{ context.customer }}
				<span
					v-if="context.customer_name && context.customer_name !== context.customer"
					class="font-normal text-gray-600"
				>
					· {{ context.customer_name }}
				</span>
			</div>
			<div class="text-xs text-gray-500">
				{{ __("Group") }}: {{ context.customer_group }} · {{ __("Territory") }}:
				{{ context.territory }}
			</div>
		</div>
		<div v-else-if="context.customer_group">
			<div class="text-xs uppercase tracking-wide text-gray-500">{{ __("Customer Group") }}</div>
			<div class="font-semibold text-gray-900">{{ context.customer_group }}</div>
			<div class="text-xs text-gray-500">
				{{ __("Includes rules for parent groups and for customers in this group") }}
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { money } from "./utils";

const props = defineProps({
	context: { type: Object, required: true },
});

const hasFilters = computed(
	() => props.context.item_code || props.context.customer || props.context.customer_group
);
</script>
