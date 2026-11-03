<template>
	<div class="rounded-xl border border-solid border-gray-200 bg-white p-3 shadow-sm">
		<div class="flex flex-wrap items-baseline gap-x-3 gap-y-1">
			<a
				:href="`/app/vehicle/${encodeURIComponent(vehicle.name)}`"
				class="text-base font-semibold text-gray-900"
			>
				{{ vehicle.item_name || vehicle.item_code }}
			</a>
			<span class="text-xs text-gray-500">{{ vehicle.name }}</span>
			<span
				v-if="vehicle.current_package"
				class="rounded-full px-2 py-0.5 text-[10px] font-semibold"
				:class="
					vehicle.smc_status === 'Active'
						? 'bg-emerald-50 text-emerald-700'
						: 'bg-gray-100 text-gray-600'
				"
			>
				{{ __("SMC {0}", [vehicle.smc_status || ""]) }}: {{ vehicle.current_package }}
			</span>
		</div>

		<div class="mt-2 grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs sm:grid-cols-4 lg:grid-cols-7">
			<div v-for="f in details" :key="f.label" class="min-w-0">
				<div class="text-[10px] font-medium uppercase tracking-wide text-gray-500">{{ f.label }}</div>
				<div class="truncate font-medium text-gray-900" :title="f.value">{{ f.value || "-" }}</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	data: { type: Object, required: true },
});

const vehicle = computed(() => props.data.vehicle);

const details = computed(() => {
	const fuel = props.data.fuel_type;
	return [
		{ label: __("Model"), value: vehicle.value.variant_of },
		{ label: __("License Plate"), value: vehicle.value.license_plate },
		{ label: __("Chassis No"), value: vehicle.value.chassis_no },
		{
			label: __("Fuel Type"),
			value: fuel && fuel !== vehicle.value.fuel_type ? __("{0} (filter)", [fuel]) : fuel,
		},
		{ label: __("Customer"), value: props.data.customer_name || props.data.customer || __("None") },
		{ label: __("Customer Group"), value: props.data.customer_group },
		{ label: __("Price List"), value: props.data.selling_price_list },
	];
});
</script>
