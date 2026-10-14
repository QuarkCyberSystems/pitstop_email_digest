<template>
	<div class="w-full p-2">
		<div class="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
			<!-- Header + filters -->
			<div class="space-y-3 p-3">
				<div class="flex items-center justify-between">
					<h3 class="m-0 text-sm font-semibold text-gray-900">
						Vehicle Movement Workshop Division
					</h3>
					<div class="flex items-center gap-1.5">
						<button
							@click="downloadExcel"
							:disabled="loading"
							title="Download"
							class="inline-flex h-7 w-7 items-center justify-center rounded-md border border-solid border-gray-300 bg-white text-gray-700 transition hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-60"
						>
							<svg
								class="h-3.5 w-3.5"
								viewBox="0 0 24 24"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							>
								<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
								<path d="M7 10l5 5 5-5" />
								<path d="M12 15V3" />
							</svg>
						</button>
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
				</div>

				<div class="grid grid-cols-3 gap-2 lg:w-1/2">
					<div v-for="f in filters" :key="f.label" class="flex flex-col">
						<label class="mb-1 text-[10px] font-medium uppercase tracking-wide text-gray-500">
							{{ f.label }}
						</label>
						<div class="relative">
							<select
								v-model="f.model.value"
								@change="onFilterChange"
								class="h-8 w-full cursor-pointer appearance-none rounded-md border border-gray-300 bg-white pl-2 pr-7 text-xs text-gray-900 outline-none transition focus:border-gray-900 focus:ring-2 focus:ring-gray-900/10"
							>
								<option v-for="opt in f.options.value" :key="opt.value" :value="opt.value">
									{{ opt.label }}
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
			<div class="overflow-x-auto">
				<table ref="tableRef" class="m-0 w-full border-collapse whitespace-nowrap text-xs">
					<thead class="bg-gray-50 text-[10px] font-semibold uppercase tracking-wide text-gray-500">
						<tr>
							<th rowspan="3" :class="[th, 'text-left']">Status</th>
							<th
								v-for="g in GROUPS"
								:key="g.key"
								colspan="4"
								:class="[th, 'border-l text-center text-gray-700']"
							>
								{{ g.label }}
							</th>
						</tr>
						<tr>
							<template v-for="g in GROUPS" :key="g.key">
								<th
									v-for="ts in TIMESPANS"
									:key="ts"
									colspan="2"
									:class="[
										th,
										'text-center normal-case',
										ts === 'MTD' ? 'border-l' : 'bg-gray-100',
									]"
								>
									{{ ts }} <span class="font-normal">({{ timespanLabels[ts] }})</span>
								</th>
							</template>
						</tr>
						<tr>
							<template v-for="g in GROUPS" :key="g.key">
								<template v-for="ts in TIMESPANS" :key="ts">
									<th
										:class="[th, 'text-right', ts === 'MTD' ? 'border-l' : 'bg-gray-100']"
									>
										Cars
									</th>
									<th :class="[th, 'text-right', ts === 'YTD' && 'bg-gray-100']">
										Avg Days
									</th>
								</template>
							</template>
						</tr>
					</thead>
					<tbody>
						<tr v-if="loading">
							<td :colspan="colCount" class="px-3 py-6 text-center">
								<img
									src="/assets/pitstop_email_digest/gifs/gears_gif.gif"
									class="inline-block h-10"
								/>
							</td>
						</tr>
						<tr v-else-if="!rows.length">
							<td :colspan="colCount" class="px-3 py-6 text-center text-gray-500">No Data</td>
						</tr>
						<template v-else>
							<tr
								v-for="row in rows"
								:key="row.status"
								class="transition-colors hover:bg-gray-50"
							>
								<td :class="[td, 'font-medium text-gray-900']">{{ row.status }}</td>
								<template v-for="g in GROUPS" :key="g.key">
									<template v-for="ts in TIMESPANS" :key="ts">
										<td
											:class="[
												td,
												'text-right',
												ts === 'MTD' ? 'border-l' : 'bg-gray-50/70',
											]"
										>
											<a
												@click.prevent="drillDown(row.status, g, ts)"
												href="#"
												class="font-semibold no-underline hover:underline"
												:class="
													row.cells[g.key][ts].count
														? 'text-blue-600'
														: 'text-gray-400'
												"
											>
												{{ row.cells[g.key][ts].count }}
											</a>
										</td>
										<td
											:class="[
												td,
												'text-right text-gray-600',
												ts === 'YTD' && 'bg-gray-50/70',
											]"
										>
											{{ row.cells[g.key][ts].avg }}
										</td>
									</template>
								</template>
							</tr>
							<tr class="bg-gray-100 font-semibold text-gray-900">
								<td class="px-3 py-2">Total</td>
								<template v-for="g in GROUPS" :key="g.key">
									<template v-for="ts in TIMESPANS" :key="ts">
										<td
											class="px-3 py-2 text-right"
											:class="
												ts === 'MTD' &&
												'border-0 border-l border-solid border-gray-200'
											"
										>
											{{ totals[g.key][ts].count }}
										</td>
										<td class="px-3 py-2 text-right">{{ totals[g.key][ts].avg }}</td>
									</template>
								</template>
							</tr>
						</template>
					</tbody>
				</table>
			</div>
		</div>

		<VehicleMovementDetailsDialog
			:open="details.open"
			:title="details.title"
			:tags="details.tags"
			:filters="details.filters"
			@close="details.open = false"
		/>
	</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue";
import VehicleMovementDetailsDialog from "./vehicle_movement_details_dialog.vue";

const props = defineProps({
	customerFilters: { type: Object, required: true },
});
const hasCustomerFilter = () =>
	Boolean(props.customerFilters.customer || props.customerFilters.customer_group);
const CUSTOM_ORDER_FIELD = "job_status_workshop_division_brac_vehicle_mobility";
const API = "pitstop_email_digest.pitstop_email_digest.page.vehicle_movement.vehicle_movement";

// `insertAt` is where task-type statuses (e.g. "Assigned (Maintenance)") are slotted into the custom order
const GROUPS = [
	{
		key: "mechanical_category",
		label: "Mech.",
		workshop_division: "Mechanical",
		billing_type: null,
		insertAt: 4,
	},
	{
		key: "body_shop_cash_category",
		label: "BS - Cash",
		workshop_division: "Body Shop",
		billing_type: "Customer",
		insertAt: 5,
	},
	{
		key: "body_shop_insurance_category",
		label: "BS - Insurance",
		workshop_division: "Body Shop",
		billing_type: "Insurance",
		insertAt: 6,
	},
	{ key: "all_category", label: "Total", workshop_division: null, billing_type: null, insertAt: 7 },
];
const TIMESPANS = ["MTD", "YTD"];
const colCount = 1 + GROUPS.length * TIMESPANS.length * 2;

const th = "border-0 border-b border-solid border-gray-200 px-3 py-2";
const td = "border-0 border-b border-solid border-gray-100 px-3 py-2";

const fiscalYears = ref([]);
const branches = ref([]);
const fromYear = ref("");
const toYear = ref("");
const branch = ref("");

const tableRef = ref(null);
const rows = ref([]);
const loading = ref(false);
// filters + task type mapping the current table was loaded with, used for drill down
const loaded = ref({
	fromYear: "",
	toYear: "",
	branch: "",
	customer: "",
	customerGroup: "",
	dateRanges: {},
	taskTypes: {},
});

const yearOptions = computed(() => fiscalYears.value.map((y) => ({ value: y, label: y })));
const branchOptions = computed(() => [
	{ value: "", label: "All" },
	...branches.value.map((b) => ({ value: b, label: b })),
]);

const filters = [
	{ label: "From Year", model: fromYear, options: yearOptions },
	{ label: "To Year", model: toYear, options: yearOptions },
	{ label: "Branch", model: branch, options: branchOptions },
];

const timespanLabels = computed(() => {
	const today = new Date();
	return {
		MTD: `${today.toLocaleString("default", { month: "short" })}-${today.getFullYear()}`,
		YTD: `${loaded.value.fromYear}-${loaded.value.toYear}`,
	};
});

function emptyCells() {
	return Object.fromEntries(
		GROUPS.map((g) => [g.key, Object.fromEntries(TIMESPANS.map((ts) => [ts, { count: 0, time: 0 }]))])
	);
}

function avg(count, time) {
	return count > 0 ? Math.ceil(time / count) : 0;
}

const totals = computed(() => {
	const acc = emptyCells();
	for (const row of rows.value) {
		for (const g of GROUPS) {
			for (const ts of TIMESPANS) {
				acc[g.key][ts].count += row.cells[g.key][ts].count;
				acc[g.key][ts].time += row.cells[g.key][ts].time;
			}
		}
	}
	for (const g of GROUPS) {
		for (const ts of TIMESPANS) acc[g.key][ts].avg = avg(acc[g.key][ts].count, acc[g.key][ts].time);
	}
	return acc;
});

function buildRows(message) {
	const order = [...(message.custom_order_field || [])];
	const taskTypes = {};
	const data = {};

	for (const g of GROUPS) {
		data[g.key] = (message[g.key] || []).map((item) => {
			if (!item.current_task_type) return item;
			const status = `${item.project_status} (${item.current_task_type})`;
			if (!order.includes(status)) order.splice(g.insertAt, 0, status);
			taskTypes[status] = {
				project_status: item.original_project_status,
				current_task_type: item.current_task_type,
			};
			return { ...item, project_status: status };
		});
	}

	const result = order.map((status) => {
		const cells = emptyCells();
		for (const g of GROUPS) {
			for (const item of data[g.key]) {
				if (item.project_status !== status || !cells[g.key][item.timespan]) continue;
				cells[g.key][item.timespan].count += item.total_ro || 0;
				cells[g.key][item.timespan].time += item.total_time_take || 0;
			}
			for (const ts of TIMESPANS)
				cells[g.key][ts].avg = avg(cells[g.key][ts].count, cells[g.key][ts].time);
		}
		return { status, cells };
	});

	return { result, taskTypes };
}

function onFilterChange() {
	if (fromYear.value && toYear.value && toYear.value < fromYear.value) {
		frappe.msgprint(__("From Year should be before the To Year"));
		return;
	}
	loadData();
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
			method: `${API}.get_vehicle_movement_workshop_division`,
			args: {
				branch: branch.value,
				from_year: fromYear.value,
				to_year: toYear.value,
				customer: props.customerFilters.customer,
				customer_group: props.customerFilters.customer_group,
				custom_order_field: CUSTOM_ORDER_FIELD,
			},
		});
		const { result, taskTypes } = message ? buildRows(message) : { result: [], taskTypes: {} };
		rows.value = result;
		loaded.value = {
			fromYear: fromYear.value,
			toYear: toYear.value,
			branch: branch.value,
			customer: props.customerFilters.customer,
			customerGroup: props.customerFilters.customer_group,
			dateRanges: message?.date_ranges || {},
			taskTypes,
		};
	} finally {
		loading.value = false;
	}
}

// drill down popup listing the repair orders behind a count
const details = reactive({ open: false, title: "", tags: [], filters: {} });

function drillDown(status, group, timespan) {
	const { branch: selectedBranch, customer, customerGroup, dateRanges, taskTypes } = loaded.value;
	const taskType = taskTypes[status];
	const [fromDate, toDate] = dateRanges[timespan] || [];

	details.filters = {
		from_date: fromDate,
		to_date: toDate,
		customer,
		customer_group: customerGroup,
		workshop_division: group.workshop_division,
		project_status: taskType ? taskType.project_status : status,
		current_task_type: taskType?.current_task_type,
		billing_type: group.billing_type,
		branch: selectedBranch,
		task_type_job_status_field: "task_type_job_status_brac_vehicle_mobility",
		link_access_roles_field: "report_link_access_roles_brac_vehicle_mobility",
	};
	details.title = status;
	details.tags = [
		group.label,
		`${timespan}: ${frappe.datetime.str_to_user(fromDate)} – ${frappe.datetime.str_to_user(toDate)}`,
		customerGroup,
		customer,
		selectedBranch,
	].filter(Boolean);
	details.open = true;
}

function downloadExcel() {
	if (!tableRef.value) return;
	open_url_post(
		`/api/method/${API}.download_excel_sheet`,
		{
			html_table: tableRef.value.outerHTML,
			filters: {
				customer: loaded.value.customer,
				customer_group: loaded.value.customerGroup,
				branch: loaded.value.branch,
				from_year: loaded.value.fromYear,
				to_year: loaded.value.toYear,
			},
		},
		true
	);
}

onMounted(async () => {
	const [years, branchList] = await Promise.all([
		frappe.call({ method: `${API}.fetch_fiscal_year` }),
		frappe.call({ method: `${API}.fetch_branch` }),
	]);
	fiscalYears.value = years.message || [];
	branches.value = branchList.message || [];

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
