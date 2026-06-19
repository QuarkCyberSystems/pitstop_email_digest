<template>
	<div class="w-full rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
		<h4 class="mb-4 text-lg font-semibold text-gray-800">Customer Feedback Response Table</h4>

		<div class="flex flex-col lg:flex-row gap-4">
			<div class="lg:w-1/3 px-3" ref="tableWrapper">
				<CFRTable :items="items" />
			</div>

			<div class="lg:w-1/2 px-4">
				<CFRScatter v-if="Object.keys(items).length" :items="items" :height="scatterHeight" />
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from "vue";
import CFRTable from "./CFRTable.vue";
import CFRScatter from "./CFRScatter.vue";

const tableWrapper = ref(null);
const scatterHeight = ref(400);

defineProps({
	items: {
		type: Object,
		default: () => ({}),
	},
});

let ro = null;

onMounted(async () => {
	await nextTick();
	// Observe the CFRTable's root element, not the wrapper
	const tableEl = tableWrapper.value?.firstElementChild;
	if (!tableEl) return;

	ro = new ResizeObserver((entries) => {
		const height = entries[0].contentRect.height;
		// Only update if meaningfully different to avoid micro-loops
		if (Math.abs(height - scatterHeight.value - 100) > 2) {
			console.log(height);
			console.log(tableEl);
			scatterHeight.value = height;
		}
	});

	ro.observe(tableEl);
});

onBeforeUnmount(() => ro?.disconnect());
</script>
