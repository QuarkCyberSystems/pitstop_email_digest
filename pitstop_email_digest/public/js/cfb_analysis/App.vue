<template>
	<div class="p-2 space-y-4">
		<CFFilters v-model:fromDate="fromDate" v-model:toDate="toDate" @refresh="loadItems" />

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
			<div v-else>
				<CFResponse :items="items" />
				<div class="py-4">
					<CFComplaints :items="items" />
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import CFResponse from "./CFResponse.vue";
import CFFilters from "./CFFilters.vue";
import CFComplaints from "./CFComplaints.vue";

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
