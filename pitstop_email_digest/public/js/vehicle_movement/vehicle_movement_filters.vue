<template>
	<!-- renders nothing itself, the fields are added to the Frappe page filter form -->
	<span class="hidden"></span>
</template>

<script setup>
import { onMounted } from "vue";

const props = defineProps({
	page: { type: Object, required: true },
	customerGroup: { type: String, default: "" },
	customer: { type: String, default: "" },
});
const emit = defineEmits(["update:customerGroup", "update:customer"]);

onMounted(() => {
	const customerGroupField = props.page.add_field({
		fieldtype: "Link",
		fieldname: "customer_group",
		label: __("Customer Group"),
		options: "Customer Group",
		default: props.customerGroup,
		change() {
			emit("update:customerGroup", customerGroupField.get_value() || "");
		},
	});

	const customerField = props.page.add_field({
		fieldtype: "Link",
		fieldname: "customer",
		label: __("Customer"),
		options: "Customer",
		default: props.customer,
		get_query() {
			const group = customerGroupField.get_value();
			return group
				? { filters: [["Customer", "customer_group", "descendants of (inclusive)", group]] }
				: {};
		},
		change() {
			emit("update:customer", customerField.get_value() || "");
		},
	});
});
</script>
