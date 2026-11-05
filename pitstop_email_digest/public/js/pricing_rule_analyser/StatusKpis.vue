<template>
	<!-- Sizes mirror the original desk-styled KPI cards (Frappe spacing vars) -->
	<div class="grid grid-cols-[repeat(auto-fit,minmax(140px,1fr))] gap-[10px]">
		<div
			v-for="status in ['All', ...STATUSES]"
			:key="status"
			class="cursor-pointer rounded-[10px] border bg-white p-[15px] transition-colors hover:border-gray-400"
			:class="selected === status ? 'border-blue-500 ring-1 ring-blue-500' : 'border-gray-200'"
			@click="emit('select', status)"
		>
			<div class="flex items-center gap-2 text-[13px] text-gray-500">
				<span class="inline-block h-2 w-2 rounded-full" :class="STATUS_STYLES[status].dot"></span>
				{{ status === "All" ? __("Total Rules") : __(status) }}
			</div>
			<div class="text-[1.75rem] font-semibold leading-tight text-gray-900">{{ counts[status] }}</div>
		</div>
	</div>
</template>

<script setup>
import { STATUSES, STATUS_STYLES } from "./utils";

defineProps({
	counts: { type: Object, required: true },
	selected: { type: String, required: true },
});

const emit = defineEmits(["select"]);
</script>
