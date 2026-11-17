<template>
	<div class="tw-scope">
		<div class="flex flex-col gap-6 p-2">
			<div v-if="loading && !rules.length" class="py-10 text-center">
				<img src="/assets/pitstop_email_digest/gifs/gears_gif.gif" class="inline-block h-10" />
			</div>

			<div
				v-else-if="!roleGroups.length"
				class="rounded-xl border border-dashed border-gray-300 bg-white px-4 py-10 text-center text-sm text-gray-500"
			>
				{{ __("No Discount Rules found.") }}
			</div>

			<RoleCard
				v-for="group in roleGroups"
				:key="group.role || ''"
				:role="group.role"
				:rule-count="group.ruleCount"
				:companies="group.companies"
				:customer-groups="group.customerGroups"
			/>
		</div>
	</div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import RoleCard from "./RoleCard.vue";

const API = "pitstop_email_digest.pitstop_email_digest.page.discount_rule_matrix.discount_rule_matrix";

const props = defineProps({
	page: { type: Object, required: true },
});

const rules = ref([]);
const loading = ref(false);
const fields = {};

// Role -> Customer / Customer Group -> rules
const roleGroups = computed(() => {
	const roles = {};

	for (const rule of rules.value) {
		const roleKey = rule.role || "";
		if (!roles[roleKey]) {
			roles[roleKey] = { role: rule.role, ruleCount: 0, companies: [], customerGroups: {} };
		}

		const roleGroup = roles[roleKey];
		roleGroup.ruleCount += 1;
		if (rule.company && !roleGroup.companies.includes(rule.company)) {
			roleGroup.companies.push(rule.company);
		}

		const customerLabel = getCustomerLabel(rule);
		if (!roleGroup.customerGroups[customerLabel]) {
			roleGroup.customerGroups[customerLabel] = { label: customerLabel, rules: [] };
		}
		roleGroup.customerGroups[customerLabel].rules.push(rule);
	}

	// named roles first, "All Roles" last
	return Object.values(roles)
		.sort((a, b) => !a.role - !b.role)
		.map((roleGroup) => ({
			...roleGroup,
			customerGroups: Object.values(roleGroup.customerGroups),
		}));
});

function getCustomerLabel(rule) {
	if (rule.customer) {
		return rule.customer_name || rule.customer;
	}
	const label = rule.customer_group || __("All Customers");
	return rule.territory ? `${label} (${rule.territory})` : label;
}

async function load() {
	loading.value = true;
	try {
		const { message } = await frappe.call({
			method: `${API}.get_discount_rules`,
			args: {
				company: fields.company.get_value(),
				role: fields.role.get_value(),
			},
		});
		rules.value = message || [];
	} finally {
		loading.value = false;
	}
}

onMounted(() => {
	fields.company = props.page.add_field({
		fieldname: "company",
		label: __("Company"),
		fieldtype: "Link",
		options: "Company",
		change: () => load(),
	});

	fields.role = props.page.add_field({
		fieldname: "role",
		label: __("Role"),
		fieldtype: "Link",
		options: "Role",
		change: () => load(),
	});

	props.page.set_primary_action(__("Refresh"), () => load(), "refresh");
	load();
});
</script>
