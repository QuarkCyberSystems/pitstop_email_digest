<template>
	<div class="rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
		<div class="flex flex-col md:flex-row gap-4">
			<div class="w-48">
				<label class="block mb-1 text-sm font-medium text-gray-700 px-3">From Date</label>
				<input
					:value="fromDate"
					@input="$emit('update:fromDate', $event.target.value)"
					type="date"
					@change="$emit('refresh')"
					class="w-full rounded-md border border-gray-300 px-3 py-2"
				/>
			</div>

			<div class="w-48">
				<label class="block mb-1 text-sm font-medium text-gray-700 px-3">To Date</label>
				<input
					:value="toDate"
					@input="$emit('update:toDate', $event.target.value)"
					type="date"
					@change="$emit('refresh')"
					class="w-full rounded-md border border-gray-300 px-3 py-2"
				/>
			</div>

			<div class="flex items-end px-5">
				<button
					@click="$emit('refresh')"
					style="background-color: black"
					class="rounded-md px-4 py-2 text-white hover:bg-gray-900"
				>
					Refresh
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
defineProps({
	fromDate: { type: String, default: "" },
	toDate: { type: String, default: "" },
});

defineEmits(["update:fromDate", "update:toDate", "refresh"]);
</script>
