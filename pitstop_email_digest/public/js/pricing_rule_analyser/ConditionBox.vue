<template>
	<div class="rounded-md bg-yellow-50 p-2 text-sm text-yellow-900">
		<div class="font-semibold">{{ __("Condition") }}</div>
		<div v-if="smcPackage">
			{{ __("Only when SMC package is") }} <b>{{ smcPackage }}</b>
		</div>
		<div v-else>{{ __("Only when the custom condition below is true") }}</div>
		<details class="mt-1">
			<summary class="cursor-pointer text-xs text-yellow-800">{{ __("View code") }}</summary>
			<pre class="mt-1 whitespace-pre-wrap break-words rounded bg-white p-2 text-xs text-gray-800">{{
				condition
			}}</pre>
		</details>
	</div>
</template>

<script setup>
defineProps({
	condition: { type: String, required: true },
	smcPackage: { type: String, default: null },
});
</script>
