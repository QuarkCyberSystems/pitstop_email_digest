<template>
	<div class="w-full p-2">
		<div class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
			<!-- Header + filters -->
			<div class="space-y-3 p-3">
				<div class="flex items-center justify-between">
					<h3 class="m-0 text-sm font-semibold text-gray-900">Vehicle Movement Year to Year</h3>
					<button
						@click="loadData"
						:disabled="loading"
						title="Refresh"
						class="inline-flex h-7 w-7 items-center justify-center rounded-md border-0 bg-gray-900 text-white transition hover:bg-gray-700 disabled:cursor-not-allowed disabled:opacity-60"
					>
						<svg
							class="h-3.5 w-3.5"
							:class="{ 'animate-spin': loading }"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							stroke-linecap="round"
							stroke-linejoin="round"
						>
							<path d="M21 12a9 9 0 11-3-6.7L21 8" />
							<path d="M21 3v5h-5" />
						</svg>
					</button>
				</div>

				<div class="grid grid-cols-2 gap-2">
					<div v-for="f in yearFilters" :key="f.label" class="flex flex-col">
						<label class="mb-1 text-[10px] font-medium uppercase tracking-wide text-gray-500">
							{{ f.label }}
						</label>
						<div class="relative">
							<select
								v-model="f.model.value"
								@change="onYearChange"
								class="h-8 w-full cursor-pointer appearance-none rounded-md border border-gray-300 bg-white pl-2 pr-7 text-xs text-gray-900 outline-none transition focus:border-gray-900 focus:ring-2 focus:ring-gray-900/10"
							>
								<option v-for="year in fiscalYears" :key="year" :value="year">
									{{ year }}
								</option>
							</select>
							<svg
								class="pointer-events-none absolute right-2 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M5.23 7.21a.75.75 0 011.06.02L10 11.17l3.71-3.94a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
									clip-rule="evenodd"
								/>
							</svg>
						</div>
					</div>
				</div>
			</div>

			<!-- Table -->
			<table class="m-0 w-full border-collapse text-xs">
				<thead>
					<tr class="bg-gray-50">
						<th
							v-for="(col, i) in columns"
							:key="col"
							class="border-0 border-y border-solid border-gray-200 px-3 py-2 text-[10px] font-semibold uppercase tracking-wide text-gray-500"
							:class="i === 0 ? 'text-left' : 'text-right'"
						>
							{{ col }}
						</th>
					</tr>
				</thead>
				<tbody>
					<tr v-if="loading">
						<td :colspan="columns.length" class="px-3 py-6 text-center">
							<img
								src="/assets/pitstop_email_digest/gifs/gears_gif.gif"
								class="inline-block h-10"
							/>
						</td>
					</tr>
					<tr v-else-if="!rows.length">
						<td :colspan="columns.length" class="px-3 py-6 text-center text-gray-500">No Data</td>
					</tr>
					<tr
						v-else
						v-for="row in rows"
						:key="row.label"
						class="transition-colors hover:bg-gray-50"
					>
						<td class="border-0 border-b border-solid border-gray-100 px-3 py-2">
							<div class="font-semibold text-gray-900">{{ row.title }}</div>
							<div class="text-[10px] text-gray-500">{{ row.subtitle }}</div>
						</td>
						<td class="border-0 border-b border-solid border-gray-100 px-3 py-2 text-right">
							<span
								class="inline-flex min-w-8 justify-center rounded-full bg-green-50 px-2 py-0.5 font-semibold text-green-700"
							>
								{{ row.cars_in }}
							</span>
						</td>
						<td class="border-0 border-b border-solid border-gray-100 px-3 py-2 text-right">
							<span
								class="inline-flex min-w-8 justify-center rounded-full bg-blue-50 px-2 py-0.5 font-semibold text-blue-700"
							>
								{{ row.cars_out }}
							</span>
						</td>
						<td
							class="whitespace-nowrap border-0 border-b border-solid border-gray-100 px-3 py-2 text-right font-semibold text-gray-900"
						>
							{{ row.average
							}}<span class="ml-0.5 text-[10px] font-normal text-gray-500">d</span>
						</td>
					</tr>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";

const props = defineProps({
	customerFilters: { type: Object, required: true },
});
const hasCustomerFilter = () =>
	Boolean(props.customerFilters.customer || props.customerFilters.customer_group);
const API = "pitstop_email_digest.pitstop_email_digest.page.vehicle_movement.vehicle_movement";

const columns = ["Span", "In", "Out", "Avg Deliver"];

const fiscalYears = ref([]);
const fromYear = ref("");
const toYear = ref("");
const rows = ref([]);
const loading = ref(false);

const yearFilters = [
	{ label: "From Year", model: fromYear },
	{ label: "To Year", model: toYear },
];

function onYearChange() {
	if (fromYear.value && toYear.value && toYear.value < fromYear.value) {
		frappe.msgprint(__("From Year should be before the To Year"));
		return;
	}
	loadData();
}

function buildRow(title, subtitle, data) {
	return {
		label: title,
		title,
		subtitle,
		cars_in: data.number_of_vehicle_in,
		cars_out: data.number_of_vehicle_out,
		average: data.average_time_delivery?.[0]?.average ?? 0,
	};
}

async function loadData() {
	if (!hasCustomerFilter()) return;

	if (!fromYear.value || !toYear.value) {
		frappe.msgprint(__("From Year and To Year are mandatory"));
		return;
	}

	loading.value = true;
	try {
		const { message } = await frappe.call({
			method: `${API}.get_vehicle_movement`,
			args: {
				customer: props.customerFilters.customer,
				customer_group: props.customerFilters.customer_group,
				from_year: fromYear.value,
				to_year: toYear.value,
			},
		});

		const today = new Date();
		const monthName = today.toLocaleString("default", { month: "long" });
		const result = [];

		if (message?.Daily) {
			result.push(
				buildRow("Today", moment(frappe.datetime.get_today()).format("DD-MM-YYYY"), message.Daily)
			);
		}
		if (message?.Monthly) {
			result.push(buildRow("MTD", `${monthName} ${today.getFullYear()}`, message.Monthly));
		}
		if (message?.Yearly) {
			result.push(buildRow("YTD", `${fromYear.value} – ${toYear.value}`, message.Yearly));
		}
		rows.value = result;
	} finally {
		loading.value = false;
	}
}

onMounted(async () => {
	const { message } = await frappe.call({ method: `${API}.fetch_fiscal_year` });
	fiscalYears.value = message || [];

	if (fiscalYears.value.length) {
		fromYear.value = fiscalYears.value[fiscalYears.value.length - 1];
		toYear.value = fiscalYears.value[0];
	} else {
		const year = String(new Date().getFullYear());
		fiscalYears.value = [year];
		fromYear.value = toYear.value = year;
	}

	loadData();
});
watch(() => [props.customerFilters.customer, props.customerFilters.customer_group], loadData);
</script>
