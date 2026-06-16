<template>
	<aside class="md:w-1/3 bg-white border border-gray-200 rounded-lg shadow-sm p-4">
		<h3 class="text-base font-semibold text-gray-800 border-b border-gray-200 pb-2 mb-3">
			{{ __("Items") }}
		</h3>
		<input v-model="query" type="text" class="form-control mb-3" :placeholder="__('Search...')" />
		<ul class="space-y-1">
			<li
				v-for="item in filteredItems"
				:key="item.id"
				@click="$emit('select', item.id)"
				:class="[
					'px-3 py-2 rounded cursor-pointer text-sm',
					selectedId === item.id
						? 'bg-blue-100 text-blue-800 font-semibold'
						: 'hover:bg-gray-100 text-gray-700',
				]"
			>
				{{ item.name }}
			</li>
			<li v-if="!filteredItems.length" class="px-3 py-2 text-sm text-gray-400">
				{{ __("No results") }}
			</li>
		</ul>
	</aside>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
	items: { type: Array, required: true },
	selectedId: { type: [Number, String, null], default: null },
});
defineEmits(["select"]);

const query = ref("");
const filteredItems = computed(() => {
	const q = query.value.trim().toLowerCase();
	if (!q) return props.items;
	return props.items.filter((it) => it.name.toLowerCase().includes(q));
});

const __ = window.__ || ((s) => s);
</script>
