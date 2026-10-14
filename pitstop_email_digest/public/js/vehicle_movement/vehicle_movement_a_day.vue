<template>
	<div class="w-full p-2">
		<div class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
			<!-- Header + filters -->
			<div class="space-y-3 p-3">
				<div class="flex items-center justify-between">
					<h3 class="m-0 text-sm font-semibold text-gray-900">Vehicle Movement a Day</h3>
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
					<div class="flex flex-col">
						<label class="mb-1 text-[10px] font-medium uppercase tracking-wide text-gray-500"
							>Job Date</label
						>
						<input
							v-model="selectedDate"
							@change="loadData"
							type="date"
							class="h-8 w-full rounded-md border border-gray-300 bg-white px-2 text-xs text-gray-900 outline-none transition focus:border-gray-900 focus:ring-2 focus:ring-gray-900/10"
						/>
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
					<template v-else>
						<tr v-for="row in rows" :key="row.status" class="transition-colors hover:bg-gray-50">
							<td
								class="border-0 border-b border-solid border-gray-100 px-3 py-2 font-medium text-gray-900"
							>
								{{ row.status }}
							</td>
							<td class="border-0 border-b border-solid border-gray-100 px-3 py-2 text-right">
								<span
									class="inline-flex min-w-8 justify-center rounded-full bg-amber-50 px-2 py-0.5 font-semibold text-amber-700"
								>
									{{ row.mechanical }}
								</span>
							</td>
							<td class="border-0 border-b border-solid border-gray-100 px-3 py-2 text-right">
								<span
									class="inline-flex min-w-8 justify-center rounded-full bg-violet-50 px-2 py-0.5 font-semibold text-violet-700"
								>
									{{ row.bodyshop }}
								</span>
							</td>
							<td
								class="border-0 border-b border-solid border-gray-100 px-3 py-2 text-right font-semibold text-gray-900"
							>
								{{ row.mechanical + row.bodyshop }}
							</td>
						</tr>
						<tr class="bg-gray-50 font-semibold text-gray-900">
							<td class="px-3 py-2">Total</td>
							<td class="px-3 py-2 text-right">{{ totals.mechanical }}</td>
							<td class="px-3 py-2 text-right">{{ totals.bodyshop }}</td>
							<td class="px-3 py-2 text-right">{{ totals.mechanical + totals.bodyshop }}</td>
						</tr>
					</template>
				</tbody>
			</table>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";

const props = defineProps({
	customerFilters: { type: Object, required: true },
});
const hasCustomerFilter = () =>
	Boolean(props.customerFilters.customer || props.customerFilters.customer_group);
const CUSTOM_ORDER_FIELD = "job_status_per_day_brac_vehicle_mobility";
const API = "pitstop_email_digest.pitstop_email_digest.page.vehicle_movement.vehicle_movement";

const columns = ["Status", "Mechanical", "Bodyshop", "Total"];

const selectedDate = ref(frappe.datetime.get_today());
const rows = ref([]);
const loading = ref(false);

const totals = computed(() =>
	rows.value.reduce(
		(acc, row) => ({
			mechanical: acc.mechanical + row.mechanical,
			bodyshop: acc.bodyshop + row.bodyshop,
		}),
		{ mechanical: 0, bodyshop: 0 }
	)
);

// Append the task type to Assigned / In Progress statuses and slot them into the custom order
function withTaskType(items, order, insertAt) {
	return items.map((item) => {
		if (!item.current_task_type) return item;
		const status = `${item.project_status} (${item.current_task_type})`;
		if (!order.includes(status)) order.splice(insertAt, 0, status);
		return { ...item, project_status: status };
	});
}

function countFor(items, status) {
	return items.filter((i) => i.project_status === status).reduce((sum, i) => sum + i.total_ro, 0);
}

function buildRows(message) {
	const order = [...(message.custom_order_field || [])];
	const bodyshop = withTaskType(message.all_bodyshop || [], order, 4);
	const mechanical = withTaskType(message.all_mechanical || [], order, 5);

	return order
		.filter((status) => [...mechanical, ...bodyshop].some((i) => i.project_status === status))
		.map((status) => ({
			status,
			mechanical: countFor(mechanical, status),
			bodyshop: countFor(bodyshop, status),
		}));
}

async function loadData() {
	if (!hasCustomerFilter()) return;

	if (!selectedDate.value) {
		frappe.msgprint(__("Please select a date."));
		return;
	}

	loading.value = true;
	try {
		const { message } = await frappe.call({
			method: `${API}.get_vehicle_movement_a_day`,
			args: {
				selected_date: selectedDate.value,
				customer: props.customerFilters.customer,
				customer_group: props.customerFilters.customer_group,
				custom_order_field: CUSTOM_ORDER_FIELD,
			},
		});
		rows.value = message ? buildRows(message) : [];
	} finally {
		loading.value = false;
	}
}

onMounted(loadData);
watch(() => [props.customerFilters.customer, props.customerFilters.customer_group], loadData);
</script>
