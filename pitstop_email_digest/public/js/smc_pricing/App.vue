<template>
	<div class="tw-scope">
		<div v-if="!filters.vehicle" class="p-2">
			<div class="rounded-xl border border-dashed border-gray-300 bg-white px-4 py-10 text-center">
				<p class="m-0 text-sm font-medium text-gray-900">{{ __("Select a Vehicle") }}</p>
				<p class="m-0 mt-1 text-xs text-gray-500">
					{{ __("Every Service Maintenance Package for the vehicle is listed with its price.") }}
				</p>
			</div>
		</div>

		<div v-else class="space-y-3 p-2">
			<VehicleCard v-if="data" :data="data" />

			<!-- Toolbar -->
			<div v-if="data" class="flex flex-wrap items-center gap-2">
				<input
					v-model="search"
					type="search"
					:placeholder="__('Search packages')"
					class="h-8 w-full rounded-md border border-solid border-gray-300 bg-white px-2 text-xs text-gray-900 outline-none focus:border-gray-900 sm:w-64"
				/>
				<select
					v-model="sortBy"
					class="h-8 rounded-md border border-solid border-gray-300 bg-white px-2 text-xs text-gray-900 outline-none focus:border-gray-900"
				>
					<option value="name">{{ __("Sort: Name") }}</option>
					<option value="price_asc">{{ __("Sort: Price, low to high") }}</option>
					<option value="price_desc">{{ __("Sort: Price, high to low") }}</option>
					<option value="validity">{{ __("Sort: Validity") }}</option>
				</select>
				<label class="m-0 inline-flex cursor-pointer items-center gap-1.5 text-xs text-gray-600">
					<input v-model="showNotApplicable" type="checkbox" class="m-0" />
					{{ __("Show not applicable ({0})", [notApplicableCount]) }}
				</label>

				<span class="ml-auto text-xs text-gray-500">
					<template v-if="pricedCount < applicableCount">
						{{ __("Pricing {0} of {1} packages...", [pricedCount, applicableCount]) }}
					</template>
					<template v-else>
						{{ __("{0} applicable packages", [applicableCount]) }}
					</template>
				</span>
			</div>

			<div v-if="loading" class="py-10 text-center">
				<img src="/assets/pitstop_email_digest/gifs/gears_gif.gif" class="inline-block h-10" />
			</div>

			<div
				v-else-if="data && !visiblePackages.length"
				class="rounded-xl border border-dashed border-gray-300 bg-white px-4 py-10 text-center text-sm text-gray-500"
			>
				{{
					applicableCount
						? __("No packages match the search.")
						: __("No package applies to this vehicle with these filters.")
				}}
			</div>

			<div v-else class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
				<PackageCard
					v-for="pkg in visiblePackages"
					:key="pkg.package"
					:pkg="pkg"
					:currency="data.currency"
					:vehicle="filters.vehicle"
					:customer="filters.customer"
				/>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import VehicleCard from "./VehicleCard.vue";
import PackageCard from "./PackageCard.vue";

const API = "pitstop_email_digest.pitstop_email_digest.page.smc_pricing.smc_pricing";
// each package takes about a second to price; a few at a time fills the page without flooding workers
const CONCURRENCY = 4;

const props = defineProps({
	page: { type: Object, required: true },
});

const filters = reactive({ vehicle: "", customer: "", fuel_type: "" });
const data = ref(null);
const packages = ref([]);
const loading = ref(false);
const search = ref("");
const sortBy = ref("name");
const showNotApplicable = ref(false);
const fields = {};

// bumped on every load, so pricing calls from an older filter set are dropped
let generation = 0;

const applicableCount = computed(() => packages.value.filter((p) => p.applicable).length);
const notApplicableCount = computed(() => packages.value.length - applicableCount.value);
const pricedCount = computed(
	() => packages.value.filter((p) => p.status === "done" || p.status === "error").length
);

const visiblePackages = computed(() => {
	const text = search.value.trim().toLowerCase();
	const rows = packages.value.filter(
		(p) => (showNotApplicable.value || p.applicable) && (!text || p.package.toLowerCase().includes(text))
	);

	const price = (p) => (p.pricing ? p.pricing.rounded_total : null);
	const byPrice = (direction) => (a, b) => {
		// unpriced packages go last either way
		if (price(a) === null || price(b) === null) return (price(a) === null) - (price(b) === null);
		return direction * (price(a) - price(b));
	};
	const sorters = {
		name: (a, b) => a.package.localeCompare(b.package),
		price_asc: byPrice(1),
		price_desc: byPrice(-1),
		validity: (a, b) =>
			a.validity_duration - b.validity_duration || a.validity_mileage - b.validity_mileage,
	};

	// applicable packages first, then the chosen order
	return rows.sort((a, b) => b.applicable - a.applicable || sorters[sortBy.value](a, b));
});

function makeFilters() {
	fields.vehicle = props.page.add_field({
		fieldname: "vehicle",
		label: __("Vehicle"),
		fieldtype: "Link",
		options: "Vehicle",
		reqd: 1,
		change: () => onFilterChange("vehicle"),
	});

	fields.customer = props.page.add_field({
		fieldname: "customer",
		label: __("Customer"),
		fieldtype: "Link",
		options: "Customer",
		change: () => onFilterChange("customer"),
	});

	// empty means the vehicle's own fuel type
	fields.fuel_type = props.page.add_field({
		fieldname: "fuel_type",
		label: __("Fuel Type"),
		fieldtype: "Link",
		options: "Vehicle Fuel Type",
		change: () => onFilterChange("fuel_type"),
	});
}

function onFilterChange(fieldname) {
	const value = fields[fieldname].get_value() || "";
	if (filters[fieldname] === value) return;
	filters[fieldname] = value;
	load();
}

async function load() {
	const gen = ++generation;
	data.value = null;
	packages.value = [];
	if (!filters.vehicle) return;

	loading.value = true;
	try {
		const { message } = await frappe.call({
			method: `${API}.get_smc_packages`,
			args: { ...filters },
		});
		if (gen !== generation) return;

		data.value = message;
		packages.value = message.packages.map((p) => ({
			...p,
			status: p.applicable ? "pending" : "",
			pricing: null,
		}));
		setFuelTypePlaceholder(message.vehicle.fuel_type);
	} finally {
		if (gen === generation) loading.value = false;
	}

	priceAll(gen);
}

async function priceAll(gen) {
	// take proxies from the ref so status updates re-render the cards
	const queue = packages.value.filter((p) => p.applicable);

	async function worker() {
		while (queue.length && gen === generation) {
			const pkg = queue.shift();
			pkg.status = "loading";
			try {
				const { message } = await frappe.call({
					method: `${API}.get_smc_package_price`,
					args: { ...filters, package: pkg.package },
				});
				if (gen !== generation) return;
				pkg.pricing = message;
				pkg.status = "done";
			} catch (e) {
				if (gen === generation) pkg.status = "error";
			}
		}
	}

	await Promise.all(Array.from({ length: CONCURRENCY }, worker));
}

function setFuelTypePlaceholder(vehicleFuelType) {
	const placeholder = vehicleFuelType ? __("{0} (vehicle)", [vehicleFuelType]) : __("Fuel Type");
	fields.fuel_type.$input && fields.fuel_type.$input.attr("placeholder", placeholder);
}

onMounted(() => {
	makeFilters();
	props.page.set_primary_action(__("Refresh"), () => load(), "refresh");

	// /app/smc-pricing?vehicle=V-00001
	const vehicle = frappe.route_options && frappe.route_options.vehicle;
	if (vehicle) {
		frappe.route_options = null;
		fields.vehicle.set_value(vehicle);
	}
});
</script>
