<template>
	<div class="srd-table-wrapper">
		<table class="srd-table">
			<thead>
				<tr>
					<th
						v-for="col in columns"
						:key="col.field"
						:class="{ 'text-right': col.type !== 'data', sorted: sort.field === col.field }"
						@click="toggle_sort(col.field)"
					>
						{{ col.label }}
						<span class="srd-sort">{{ sort_icon(col.field) }}</span>
					</th>
				</tr>
			</thead>
			<tbody>
				<tr v-for="row in sorted_items" :key="row.sr_no">
					<td
						v-for="col in columns"
						:key="col.field"
						:class="[
							{ 'text-right': col.type !== 'data', 'srd-wrap': col.wrap },
							col.diff ? sign_class(row[col.field]) : '',
						]"
					>
						{{ format_cell(row, col) }}
					</td>
				</tr>
				<tr v-if="!sorted_items.length">
					<td :colspan="columns.length" class="srd-empty">{{ __("No items") }}</td>
				</tr>
			</tbody>
		</table>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { format_value, strip_abbr, sign_class } from "./utils.js";

const props = defineProps({
	items: { type: Array, required: true },
	// visible columns: { field, label, type: data | int | qty | currency, wrap?, diff? }
	columns: { type: Array, required: true },
	currency: { type: String, default: "" },
	// kept by the parent, so the sort survives a reload for new filters
	sort: { type: Object, default: () => ({ field: null, order: null }) },
});
const emit = defineEmits(["update:sort"]);

const sorted_items = computed(() => {
	const items = [...props.items];
	const { field, order } = props.sort;
	// a column hidden after sorting on it leaves the original order
	const col = props.columns.find((c) => c.field === field);
	if (!col) return items;

	const direction = order === "asc" ? 1 : -1;

	return items.sort((a, b) => {
		if (col.type === "data") {
			return direction * (a[field] || "").localeCompare(b[field] || "", undefined, { numeric: true });
		}
		return direction * (flt(a[field]) - flt(b[field]));
	});
});

// Header click cycles ascending -> descending -> original order
function toggle_sort(field) {
	const { field: current, order } = props.sort;
	if (current !== field) {
		emit("update:sort", { field, order: "asc" });
	} else if (order === "asc") {
		emit("update:sort", { field, order: "desc" });
	} else {
		emit("update:sort", { field: null, order: null });
	}
}

function sort_icon(field) {
	if (props.sort.field !== field) return "↕";
	return props.sort.order === "asc" ? "↑" : "↓";
}

function format_cell(row, col) {
	if (col.field === "warehouse") return strip_abbr(row.warehouse);
	return format_value(row[col.field], col.type, props.currency);
}
</script>

<style scoped>
.srd-table-wrapper {
	overflow: auto;
	max-height: calc(100vh - 340px);
	background: var(--card-bg);
	border: 1px solid var(--border-color);
	border-radius: var(--border-radius-md);
}

.srd-table {
	width: 100%;
	border-collapse: collapse;
	font-size: var(--text-sm);
}

.srd-table th,
.srd-table td {
	padding: 6px 10px;
	border-bottom: 1px solid var(--border-color);
	white-space: nowrap;
}

.srd-table th {
	position: sticky;
	top: 0;
	z-index: 1;
	background: var(--subtle-fg);
	font-weight: 600;
	color: var(--text-color);
	cursor: pointer;
	user-select: none;
}

.srd-table th:hover,
.srd-table th.sorted {
	background: var(--gray-200);
}

.srd-sort {
	margin-left: 2px;
	font-size: var(--text-xs);
	color: var(--text-muted);
}

.srd-table td {
	font-variant-numeric: tabular-nums;
}

/* Long text (Item Name) wraps onto the next line instead of widening the column */
.srd-table td.srd-wrap {
	min-width: 180px;
	max-width: 260px;
	white-space: normal;
	word-break: break-word;
}

.srd-table tbody tr:hover {
	background: var(--highlight-color);
}

.srd-empty {
	padding: var(--padding-xl);
	text-align: center;
	color: var(--text-muted);
}

.srd-positive {
	color: var(--green-600);
}

.srd-negative {
	color: var(--red-600);
}
</style>
