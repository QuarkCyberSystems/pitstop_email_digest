<template>
	<div class="w-full rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
		<h4 class="mb-4 text-lg font-semibold text-gray-800">Customer Feedback Complaints Table</h4>

		<!-- <div class="flex flex-col lg:flex-row gap-4">
            <div class="lg:w-1/3 px-3">
                <LeftTable :items="items" />
            </div>

            <div class="lg:w-1/2 px-4">
                <CFRScatter :items="items" />
            </div>
        </div> -->
	</div>
</template>

<script setup>
defineProps({
	items: {
		type: Object,
		default: () => ({}),
	},
});
</script>
