<template>
	<div
		class="flex flex-col rounded-xl border border-solid bg-white p-3 shadow-sm"
		:class="pkg.applicable ? 'border-gray-200' : 'border-dashed border-gray-300 opacity-70'"
	>
		<div class="flex items-start justify-between gap-2">
			<a
				:href="`/app/service-maintenance-package/${encodeURIComponent(pkg.package)}`"
				class="text-sm font-semibold leading-snug text-gray-900"
			>
				{{ pkg.package }}
			</a>
		</div>

		<div class="mt-1.5 flex flex-wrap gap-1">
			<span class="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-600">
				{{ __("{0} months", [pkg.validity_duration]) }}
			</span>
			<span class="rounded-full bg-gray-100 px-2 py-0.5 text-[10px] font-medium text-gray-600">
				{{ formatInt(pkg.validity_mileage) }} km
			</span>
			<span
				v-if="!pkg.applicable"
				class="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-700"
			>
				{{ __("Not applicable") }}
			</span>
			<span
				v-else-if="pricing && hasUnpricedItems"
				class="rounded-full bg-red-50 px-2 py-0.5 text-[10px] font-semibold text-red-700"
				:title="__('Some items have no rate on this price list')"
			>
				{{ __("Missing prices") }}
			</span>
		</div>

		<!-- Price -->
		<div class="mt-3 flex-1">
			<p v-if="!pkg.applicable" class="m-0 text-xs text-gray-500">
				{{ __("No items for: {0}", [pkg.missing_templates.join(", ")]) }}
			</p>
			<div v-else-if="pkg.status === 'error'" class="text-xs text-red-600">
				{{ __("Could not price this package.") }}
			</div>
			<div v-else-if="!pricing" class="space-y-1.5">
				<div class="h-6 w-32 animate-pulse rounded bg-gray-100"></div>
				<div class="h-3 w-48 animate-pulse rounded bg-gray-100"></div>
			</div>
			<template v-else>
				<div class="text-xl font-semibold text-gray-900">{{ money(pricing.rounded_total) }}</div>
				<div class="mt-0.5 text-xs text-gray-500">
					{{
						__("Net {0} + Tax {1}", [
							money(pricing.net_total),
							money(pricing.total_taxes_and_charges),
						])
					}}
				</div>
			</template>
		</div>

		<div v-if="pricing" class="mt-3 flex items-center gap-2">
			<button
				class="h-7 rounded-md border border-solid border-gray-300 bg-white px-2.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
				@click="expanded = !expanded"
			>
				{{ expanded ? __("Hide breakdown") : __("Show breakdown") }}
			</button>
			<button
				class="h-7 rounded-md border-0 bg-gray-900 px-2.5 text-xs font-medium text-white hover:bg-gray-700"
				@click="newQuotation"
			>
				{{ __("New Quotation") }}
			</button>
		</div>

		<!-- Breakdown: each template with its items -->
		<div
			v-if="pricing && expanded"
			class="mt-3 space-y-2 border-0 border-t border-solid border-gray-100 pt-2"
		>
			<div v-for="t in pricing.templates" :key="t.service_template">
				<div class="flex items-baseline justify-between gap-2 text-xs">
					<span class="font-semibold text-gray-900">
						{{ t.service_template_name || t.service_template }}
						<span class="font-normal text-gray-500">x {{ t.template_qty }}</span>
					</span>
					<span class="font-semibold text-gray-900">{{ money(t.amount) }}</span>
				</div>
				<table class="m-0 mt-1 w-full border-collapse text-[11px]">
					<tbody>
						<tr v-for="(item, i) in itemsOf(t)" :key="i" class="text-gray-600">
							<td class="py-0.5 pr-2" :title="item.item_code">
								{{ item.item_name || item.item_code }}
							</td>
							<td class="whitespace-nowrap py-0.5 pr-2 text-right">
								{{ item.qty }} {{ item.uom }} x {{ money(item.rate) }}
							</td>
							<td
								class="whitespace-nowrap py-0.5 text-right"
								:class="{ 'text-red-600': !item.rate }"
							>
								{{ money(item.amount) }}
							</td>
						</tr>
					</tbody>
				</table>
			</div>
			<div v-if="pricing.taxes_and_charges" class="text-[11px] text-gray-500">
				{{ __("Taxes: {0}", [pricing.taxes_and_charges]) }}
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
	pkg: { type: Object, required: true },
	currency: { type: String, default: "" },
	vehicle: { type: String, required: true },
	customer: { type: String, default: "" },
});

const expanded = ref(false);
const pricing = computed(() => props.pkg.pricing);
const hasUnpricedItems = computed(() => pricing.value.items.some((d) => !d.rate));

function money(value) {
	return format_currency(value, props.currency);
}

function formatInt(value) {
	return format_number(value, null, 0);
}

function itemsOf(template) {
	return pricing.value.items.filter((d) => d.service_template === template.service_template);
}

function newQuotation() {
	const values = {
		applies_to_vehicle: props.vehicle,
		service_maintenance_package: props.pkg.package,
	};
	if (props.customer) {
		Object.assign(values, { quotation_to: "Customer", party_name: props.customer });
	}
	frappe.new_doc("Service Maintenance Quotation", values);
}
</script>
