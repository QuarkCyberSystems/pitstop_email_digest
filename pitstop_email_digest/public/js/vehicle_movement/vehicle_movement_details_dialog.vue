<template>
	<Teleport to="body">
		<div v-if="open" class="tw-scope">
			<div
				class="fixed inset-0 z-[1050] flex items-center justify-center bg-black/40 p-4"
				@click.self="emit('close')"
			>
				<div
					class="flex max-h-[90vh] w-full max-w-6xl flex-col overflow-hidden rounded-xl bg-white shadow-2xl"
				>
					<!-- Header -->
					<div
						class="flex items-start justify-between gap-4 border-0 border-b border-solid border-gray-200 p-4"
					>
						<div class="min-w-0">
							<h3 class="m-0 text-base font-semibold text-gray-900">{{ title }}</h3>
							<div class="mt-2 flex flex-wrap gap-1.5">
								<span
									v-for="tag in tags"
									:key="tag"
									class="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-600"
								>
									{{ tag }}
								</span>
							</div>
						</div>
						<div class="flex shrink-0 items-center gap-1.5">
							<button
								@click="downloadExcel"
								:disabled="loading || !filteredRows.length"
								title="Download as Excel"
								class="inline-flex h-8 items-center gap-1.5 rounded-md border border-solid border-gray-300 bg-white px-2.5 text-xs font-medium text-gray-700 transition hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-60"
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
								@click="emit('close')"
								title="Close"
								class="inline-flex h-8 w-8 items-center justify-center rounded-md border-0 bg-transparent text-gray-500 transition hover:bg-gray-100 hover:text-gray-900"
							>
								<svg
									class="h-4 w-4"
									viewBox="0 0 24 24"
									fill="none"
									stroke="currentColor"
									stroke-width="2"
									stroke-linecap="round"
								>
									<path d="M18 6L6 18M6 6l12 12" />
								</svg>
							</button>
						</div>
					</div>

					<!-- Summary + search -->
					<div class="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
						<div class="flex gap-6">
							<div>
								<div class="text-[10px] font-medium uppercase tracking-wide text-gray-500">
									Repair Orders
								</div>
								<div class="text-lg font-semibold text-gray-900">{{ rows.length }}</div>
							</div>
							<div>
								<div class="text-[10px] font-medium uppercase tracking-wide text-gray-500">
									Avg. Time in Days
								</div>
								<div class="text-lg font-semibold text-gray-900">
									{{ averageDays }}
									<span class="text-xs font-normal text-gray-500"
										>({{ totalDays }} / {{ rows.length }})</span
									>
								</div>
							</div>
						</div>
						<input
							v-model="search"
							type="search"
							placeholder="Search repair order, customer, chassis, plate…"
							class="h-8 w-full rounded-md border border-solid border-gray-300 bg-white px-3 text-xs text-gray-900 outline-none transition focus:border-gray-900 focus:ring-2 focus:ring-gray-900/10 sm:w-72"
						/>
					</div>

					<!-- Table -->
					<div class="min-h-0 flex-1 overflow-auto border-0 border-t border-solid border-gray-200">
						<table ref="tableRef" class="m-0 w-full border-collapse whitespace-nowrap text-xs">
							<thead class="sticky top-0 bg-gray-50">
								<tr>
									<th
										v-for="col in COLUMNS"
										:key="col.field"
										class="border-0 border-b border-solid border-gray-200 px-3 py-2 text-[10px] font-semibold uppercase tracking-wide text-gray-500"
										:class="col.align === 'right' ? 'text-right' : 'text-left'"
									>
										{{ col.label }}
									</th>
								</tr>
							</thead>
							<tbody>
								<tr v-if="loading">
									<td :colspan="COLUMNS.length" class="px-3 py-8 text-center">
										<img
											src="/assets/pitstop_email_digest/gifs/gears_gif.gif"
											class="inline-block h-10"
										/>
									</td>
								</tr>
								<tr v-else-if="!filteredRows.length">
									<td :colspan="COLUMNS.length" class="px-3 py-8 text-center text-gray-500">
										No Data
									</td>
								</tr>
								<tr
									v-else
									v-for="(row, i) in filteredRows"
									:key="row.repair_order + '-' + i"
									class="hover:bg-gray-50"
								>
									<td
										v-for="col in COLUMNS"
										:key="col.field"
										class="border-0 border-b border-solid border-gray-100 px-3 py-2 text-gray-700"
										:class="
											col.align === 'right'
												? 'text-right font-semibold text-gray-900'
												: ''
										"
									>
										<a
											v-if="col.field === 'repair_order' && canOpenRepairOrder"
											:href="`/app/project/${encodeURIComponent(row.repair_order)}`"
											target="_blank"
											class="font-medium text-blue-600 no-underline hover:underline"
										>
											{{ row.repair_order }}
										</a>
										<template v-else>{{ display(row, col) }}</template>
									</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			</div>
		</div>
	</Teleport>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";

const API = "pitstop_email_digest.pitstop_email_digest.page.vehicle_movement.vehicle_movement";

const COLUMNS = [
	{ field: "repair_order", label: "Repair Order" },
	{ field: "project_status", label: "Job Status" },
	{ field: "current_task_type", label: "Task Type" },
	{ field: "vehicle_workshop_division", label: "Division" },
	{ field: "customer_name", label: "Customer" },
	{ field: "insurance_company_name", label: "Insurance Company" },
	{ field: "project_date", label: "Job Date", type: "date" },
	{ field: "vehicle_receive_date", label: "Received", type: "date" },
	{ field: "vehicle_chassis_no", label: "Chassis No" },
	{ field: "vehicle_license_plate", label: "Plate No" },
	{ field: "vehicle_model", label: "Model" },
	{ field: "gate_pass_posting_date", label: "Gate Pass", type: "date" },
	{ field: "timespend", label: "Days", align: "right" },
];
const SEARCH_FIELDS = [
	"repair_order",
	"customer_name",
	"insurance_company_name",
	"vehicle_chassis_no",
	"vehicle_license_plate",
	"vehicle_model",
];

const props = defineProps({
	open: { type: Boolean, default: false },
	title: { type: String, default: "" },
	tags: { type: Array, default: () => [] },
	// args for get_vehicle_movement_details
	filters: { type: Object, default: () => ({}) },
});
const emit = defineEmits(["close"]);

const rows = ref([]);
const canOpenRepairOrder = ref(false);
const loading = ref(false);
const tableRef = ref(null);
const search = ref("");

const totalDays = computed(() => rows.value.reduce((sum, row) => sum + (row.timespend || 0), 0));
const averageDays = computed(() => (rows.value.length ? Math.ceil(totalDays.value / rows.value.length) : 0));

const filteredRows = computed(() => {
	const term = search.value.trim().toLowerCase();
	if (!term) return rows.value;
	return rows.value.filter((row) =>
		SEARCH_FIELDS.some((f) =>
			String(row[f] || "")
				.toLowerCase()
				.includes(term)
		)
	);
});

// exports the rows currently shown (search applied) with the drill down filters on top
function downloadExcel() {
	if (!tableRef.value || !filteredRows.value.length) return;

	const f = props.filters;
	const filters = Object.fromEntries(
		Object.entries({
			status: props.title,
			group: props.tags[0],
			from_date: f.from_date,
			to_date: f.to_date,
			customer_group: f.customer_group,
			customer: f.customer,
			branch: f.branch,
			billing_type: f.billing_type,
			search: search.value.trim(),
		}).filter(([, value]) => value)
	);

	open_url_post(
		`/api/method/${API}.download_excel_sheet`,
		{ html_table: tableRef.value.outerHTML, filters },
		true
	);
}

function display(row, col) {
	const value = row[col.field];
	if (value === null || value === undefined || value === "") return "-";
	return col.type === "date" ? frappe.datetime.str_to_user(value) : value;
}

async function loadData() {
	rows.value = [];
	search.value = "";
	loading.value = true;
	try {
		const { message } = await frappe.call({
			method: `${API}.get_vehicle_movement_details`,
			// only pass filters that have a value
			args: Object.fromEntries(Object.entries(props.filters).filter(([, value]) => value)),
		});
		rows.value = message?.data || [];
		canOpenRepairOrder.value = Boolean(message?.can_open_repair_order);
	} finally {
		loading.value = false;
	}
}

function onKeydown(e) {
	if (e.key === "Escape" && props.open) emit("close");
}

watch(
	() => props.open,
	(open) => open && loadData()
);

onMounted(() => document.addEventListener("keydown", onKeydown));
onBeforeUnmount(() => document.removeEventListener("keydown", onKeydown));
</script>
