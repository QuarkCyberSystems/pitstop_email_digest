<template>
	<div class="p-4">
		<div class="flex flex-col md:flex-row gap-4">
			<LeftTable :items="items" :selected-id="selectedId" @select="selectedId = $event" />
		</div>
	</div>
</template>

<script setup>
import { ref, computed } from "vue";
import LeftTable from "./LeftTable.vue";

const items = ref([
	{ id: 1, name: "Alpha", description: "First sample item." },
	{ id: 2, name: "Bravo", description: "Second sample item." },
	{ id: 3, name: "Charlie", description: "Third sample item." },
	{ id: 4, name: "Delta", description: "Fourth sample item." },
]);

const selectedId = ref(null);
const selected = computed(() => items.value.find((it) => it.id === selectedId.value) || null);
</script>
