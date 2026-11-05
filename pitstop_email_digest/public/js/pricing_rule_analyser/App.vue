<template>
	<div class="tw-scope">
		<div class="flex flex-col gap-4 py-4" :class="{ 'opacity-60': loading }">
			<ContextBar :context="context" />

			<StatusKpis :counts="counts" :selected="statusFilter" @select="selectStatus" />

			<ConflictAlert v-if="context.item_code" :rules="rules" />

			<div class="text-sm font-semibold text-gray-800">
				{{ statusFilter === "All" ? __("All rules") : __("{0} rules", [__(statusFilter)]) }}
				<span class="font-normal text-gray-500">({{ visibleRules.length }})</span>
			</div>

			<div v-if="loading && !rules.length" class="py-10 text-center text-gray-500">
				{{ __("Loading pricing rules…") }}
			</div>
			<div v-else-if="!visibleRules.length" class="py-10 text-center text-gray-500">
				{{ __("No pricing rules match these filters.") }}
			</div>
			<div v-else class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
				<RuleCard v-for="rule in visibleRules.slice(0, limit)" :key="rule.name" :rule="rule" />
			</div>

			<div v-if="visibleRules.length > limit" class="text-center">
				<button
					class="rounded-md border border-gray-300 bg-white px-4 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
					@click="limit += PAGE_SIZE"
				>
					{{ __("Show more ({0} of {1} shown)", [limit, visibleRules.length]) }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import ContextBar from "./ContextBar.vue";
import StatusKpis from "./StatusKpis.vue";
import ConflictAlert from "./ConflictAlert.vue";
import RuleCard from "./RuleCard.vue";
import { STATUSES, RATE_BASED_ON } from "./utils";

const PAGE_SIZE = 60;
const METHOD =
	"pitstop_email_digest.pitstop_email_digest.page.pricing_rule_analyser.pricing_rule_analyser.get_pricing_rules";

const props = defineProps({
	page: { type: Object, required: true },
});

const rules = ref([]);
const context = ref({});
const loading = ref(false);
const statusFilter = ref("Active");
const limit = ref(PAGE_SIZE);
const fields = {};

const counts = computed(() => {
	const result = { All: rules.value.length };
	STATUSES.forEach((s) => (result[s] = rules.value.filter((r) => r.status === s).length));
	return result;
});

const visibleRules = computed(() =>
	statusFilter.value === "All" ? rules.value : rules.value.filter((r) => r.status === statusFilter.value)
);

function selectStatus(status) {
	statusFilter.value = status;
	limit.value = PAGE_SIZE;
}

function makeFilters() {
	const add = (df) => (fields[df.fieldname] = props.page.add_field({ ...df, change: () => load() }));
	add({ fieldname: "item_code", label: __("Item Code"), fieldtype: "Link", options: "Item" });
	add({ fieldname: "customer", label: __("Customer"), fieldtype: "Link", options: "Customer" });
	add({
		fieldname: "customer_group",
		label: __("Customer Group"),
		fieldtype: "Link",
		options: "Customer Group",
	});
	add({
		fieldname: "rate_based_on",
		label: __("Rate Based On"),
		fieldtype: "Select",
		options: RATE_BASED_ON,
	});
	add({ fieldname: "show_smc", label: __("Show SMC Price List"), fieldtype: "Check", default: 0 });
}

function filterValues() {
	const values = {};
	for (const [key, field] of Object.entries(fields)) values[key] = field.get_value() || null;
	values.show_smc = fields.show_smc.get_value() ? 1 : 0;
	return values;
}

async function load() {
	loading.value = true;
	try {
		const { message } = await frappe.call({ method: METHOD, args: filterValues() });
		rules.value = message.rules || [];
		context.value = message.context || {};
		limit.value = PAGE_SIZE;
	} finally {
		loading.value = false;
	}
}

onMounted(() => {
	makeFilters();
	props.page.set_primary_action(__("Refresh"), () => load(), "refresh");
	load();
});
</script>
