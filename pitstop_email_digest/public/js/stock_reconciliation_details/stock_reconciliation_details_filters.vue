<template>
	<!-- renders nothing itself, the fields are added to the Frappe page filter form -->
	<span class="hidden"></span>
</template>

<script setup>
import { onMounted, watch } from "vue";

const props = defineProps({
	page: { type: Object, required: true },
	stockReconciliation: { type: String, default: "" },
	itemCode: { type: String, default: "" },
	// items on the selected document, offered by the Item Code filter
	itemCodes: { type: Array, default: () => [] },
	ignoredItemGroup: { type: String, default: "" },
	discrepancy: { type: Number, default: 0 },
	basedOn: { type: String, default: "Any Difference" },
	showStockUom: { type: Number, default: 0 },
	showLooseUom: { type: Number, default: 0 },
});
const emit = defineEmits([
	"update:stockReconciliation",
	"update:itemCode",
	"update:ignoredItemGroup",
	"update:discrepancy",
	"update:basedOn",
	"update:showStockUom",
	"update:showLooseUom",
]);

onMounted(() => {
	// change() can fire inside add_field (when a default is set), before the const below is assigned,
	// so handlers read their own value from `this` (the control)
	let basedOnField;
	let itemCodeField;

	props.page.add_field({
		fieldtype: "Link",
		fieldname: "stock_reconciliation",
		label: __("Stock Reconciliation"),
		options: "Stock Reconciliation",
		default: props.stockReconciliation,
		change() {
			emit("update:stockReconciliation", this.get_value() || "");
		},
	});

	// Only shown once a Stock Reconciliation is selected, and lists only that document's items
	itemCodeField = props.page.add_field({
		fieldtype: "Link",
		fieldname: "item_code",
		label: __("Item Code"),
		options: "Item",
		default: props.itemCode,
		get_query() {
			return { filters: { name: ["in", props.itemCodes] } };
		},
		change() {
			emit("update:itemCode", this.get_value() || "");
		},
	});
	itemCodeField.$wrapper.toggle(Boolean(props.stockReconciliation));

	// A different document has different items: clear the Item Code and hide it when none is selected
	watch(
		() => props.stockReconciliation,
		(name) => {
			itemCodeField.$wrapper.toggle(Boolean(name));
			if (itemCodeField.get_value()) itemCodeField.set_value("");
		}
	);

	props.page.add_field({
		fieldtype: "Link",
		fieldname: "ignored_item_group",
		label: __("Ignored Item Group"),
		options: "Item Group",
		default: props.ignoredItemGroup,
		change() {
			emit("update:ignoredItemGroup", this.get_value() || "");
		},
	});

	props.page.add_field({
		fieldtype: "Check",
		fieldname: "discrepancy",
		label: __("Discrepancy"),
		default: props.discrepancy,
		change() {
			const discrepancy = cint(this.get_value());
			basedOnField?.$wrapper.toggle(Boolean(discrepancy));
			emit("update:discrepancy", discrepancy);
		},
	});

	// Based On only applies to a Discrepancy view
	basedOnField = props.page.add_field({
		fieldtype: "Select",
		fieldname: "based_on",
		label: __("Based On"),
		options: ["Any Difference", "Qty Difference", "Amount Difference"],
		default: props.basedOn,
		change() {
			emit("update:basedOn", this.get_value() || "Any Difference");
		},
	});
	basedOnField.$wrapper.toggle(Boolean(props.discrepancy));

	// Column toggles, unchecked by default
	props.page.add_field({
		fieldtype: "Check",
		fieldname: "show_stock_uom",
		label: __("Show Stock UOM"),
		default: props.showStockUom,
		change() {
			emit("update:showStockUom", cint(this.get_value()));
		},
	});

	props.page.add_field({
		fieldtype: "Check",
		fieldname: "show_loose_uom",
		label: __("Show Loose UOM"),
		default: props.showLooseUom,
		change() {
			emit("update:showLooseUom", cint(this.get_value()));
		},
	});
});
</script>
