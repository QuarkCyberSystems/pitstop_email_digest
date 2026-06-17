<template>
	<div class="p-2 space-y-4">
		<div class="rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
			<div class="flex flex-col md:flex-row gap-4">
				<div class="w-48">
					<label class="block mb-1 text-sm font-medium text-gray-700 px-3"> From Date </label>
					<input
						v-model="fromDate"
						type="date"
						class="w-full rounded-md border border-gray-300 px-3 py-2"
					/>
				</div>

				<div class="w-48">
					<label class="block mb-1 text-sm font-medium text-gray-700 px-3"> To Date </label>
					<input
						v-model="toDate"
						type="date"
						class="w-full rounded-md border border-gray-300 px-3 py-2"
					/>
				</div>

				<div class="flex items-end px-5">
					<button
						@click="loadItems"
						style="background-color: black"
						class="rounded-md px-4 py-2 text-white hover:bg-gray-900"
					>
						Refresh
					</button>
				</div>
			</div>
		</div>

		<div class="flex flex-col md:flex-row gap-4 py-4">
			<div v-if="loading" class="w-full rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
				<div class="animate-pulse space-y-3">
					<div class="h-8 w-48 rounded bg-gray-200"></div>

					<div v-for="n in 8" :key="n" class="flex items-center justify-between">
						<div class="h-4 w-56 rounded bg-gray-200"></div>
						<div class="h-4 w-12 rounded bg-gray-200"></div>
					</div>
				</div>
			</div>

			<div v-else class="w-full rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
				<h4 class="mb-4 text-lg font-semibold text-gray-800">Customer Feedback Response Table</h4>

				<div class="flex flex-col lg:flex-row gap-4">
					<div class="lg:w-1/3 px-3">
						<LeftTable :items="items" />
					</div>

					<div class="lg:w-1/2 px-4">
						<CFRScatter :items="items" />
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import LeftTable from "./LeftTable.vue";
import CFRScatter from "./CFRScatter.vue";

const items = ref({});

const fromDate = ref("");
const toDate = ref("");

const loading = ref(false);

async function loadItems() {
	if (!fromDate.value || !toDate.value) {
		frappe.msgprint("From Date and To Date are mandatory");
		return;
	}

	if (fromDate.value > toDate.value) {
		frappe.msgprint("From Date must be less than or equal to To Date");
		return;
	}
	loading.value = true;
	try {
		const response = await frappe.call({
			method: "pitstop_email_digest.pitstop_email_digest.page.cfb_analysis.cfb_analysis.get_cfb_analysis_data",
			args: {
				from_date: fromDate.value,
				to_date: toDate.value,
			},
		});
		items.value = response.message || {};
	} finally {
		loading.value = false;
	}
}

onMounted(() => {
	const today = new Date();

	const oneMonthAgo = new Date(today);
	oneMonthAgo.setMonth(oneMonthAgo.getMonth() - 1);

	toDate.value = formatDate(today);
	fromDate.value = formatDate(oneMonthAgo);

	loadItems();
});

function formatDate(date) {
	return date.toISOString().split("T")[0];
}
</script>
