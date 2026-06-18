<template>
	<div class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
		<table class="min-w-full divide-y divide-gray-200">
			<thead class="bg-gray-100">
				<tr>
					<th class="px-3 py-2 text-left text-3xl font-bold tracking-wider text-gray-900">
						Branch
					</th>
					<th class="px-3 py-2 text-right text-xs font-bold tracking-wider text-gray-900">
						Feedback
					</th>
					<th class="px-3 py-2 text-right text-xs font-bold tracking-wider text-gray-900">
						Customer Responded
					</th>
					<th class="px-3 py-2 text-right text-xs font-bold tracking-wider text-gray-900">
						Response Rate (%)
					</th>
					<th class="px-3 py-2 text-right text-xs font-bold tracking-wider text-gray-900">
						CSI (%)
					</th>
					<th class="px-3 py-2 text-right text-xs font-bold tracking-wider text-gray-900">
						Satisfied
					</th>
					<th class="px-3 py-2 text-right text-xs font-bold tracking-wider text-gray-900">
						Neutral
					</th>
					<th class="px-3 py-2 text-right text-xs font-bold tracking-wider text-gray-900">
						Dissatisfied
					</th>
				</tr>
			</thead>

			<tbody class="divide-y divide-gray-100 bg-white">
				<tr
					v-for="(data, branch) in items"
					:key="branch"
					class="cursor-pointer transition-colors hover:bg-gray-50"
				>
					<td class="px-3 py-3 text-sm font-medium text-gray-900">
						{{ branch }}
					</td>
					<td class="px-3 py-3 text-right text-sm text-gray-600">
						<span
							class="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800"
						>
							{{ data.feedback_count }}
						</span>
					</td>
					<td class="px-3 py-3 text-right text-sm text-gray-600">
						<span
							class="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800"
						>
							{{ data.customer_respond_count }}
						</span>
					</td>
					<td class="px-3 py-3 text-right text-sm text-gray-600">
						<span
							class="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800"
						>
							{{ Math.floor((data.customer_respond_count / data.feedback_count) * 100) }}
						</span>
					</td>
					<td class="px-3 py-3 text-right text-sm text-gray-600">
						<span
							class="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800"
						>
							{{ data.customer_satisfaction_index }}
						</span>
					</td>
					<td class="px-3 py-3 text-right text-sm text-gray-600">
						<span
							class="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800"
						>
							{{ data.satisfied_count }}
						</span>
					</td>
					<td class="px-3 py-3 text-right text-sm text-gray-600">
						<span
							class="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800"
						>
							{{ data.neutral_count }}
						</span>
					</td>
					<td class="px-3 py-3 text-right text-sm text-gray-600">
						<span
							class="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800"
						>
							{{ data.dissatisfied_count }}
						</span>
					</td>
				</tr>

				<tr v-if="Object.keys(items).length === 0">
					<td colspan="2" class="px-4 py-8 text-center text-sm text-gray-500">
						No feedback data found
					</td>
				</tr>
			</tbody>
		</table>
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
