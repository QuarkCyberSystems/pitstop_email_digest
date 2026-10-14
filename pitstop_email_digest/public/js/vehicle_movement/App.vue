<template>
	<div class="tw-scope">
		<VehicleMovementFilters
			:page="page"
			v-model:customer-group="customerFilters.customer_group"
			v-model:customer="customerFilters.customer"
		/>

		<div v-if="!hasCustomerFilter" class="p-2">
			<div class="rounded-xl border border-dashed border-gray-300 bg-white px-4 py-10 text-center">
				<p class="m-0 text-sm font-medium text-gray-900">Select a Customer or Customer Group</p>
				<p class="m-0 mt-1 text-xs text-gray-500">
					Use the filters at the top of the page to load vehicle movement data.
				</p>
			</div>
		</div>

		<div v-show="hasCustomerFilter" class="flex flex-wrap items-start">
			<!-- 1/4 column: Year to Year above a Day -->
			<div class="w-full lg:w-1/4">
				<VehicleMovementYearToYear :customer-filters="customerFilters" />
				<VehicleMovementADay :customer-filters="customerFilters" />
			</div>
			<VehicleMovementWorkshopDivision :customer-filters="customerFilters" />
		</div>
	</div>
</template>

<script setup>
import { reactive, computed } from "vue";
import VehicleMovementFilters from "./vehicle_movement_filters.vue";
import VehicleMovementYearToYear from "./vehicle_movement_year_to_year.vue";
import VehicleMovementADay from "./vehicle_movement_a_day.vue";
import VehicleMovementWorkshopDivision from "./vehicle_movement_workshop_division.vue";

defineProps({
	page: { type: Object, required: true },
});

// Customer or Customer Group is mandatory, every card loads its data for these
const customerFilters = reactive({ customer: "", customer_group: "All Customer Groups" });
const hasCustomerFilter = computed(() => Boolean(customerFilters.customer || customerFilters.customer_group));
</script>
