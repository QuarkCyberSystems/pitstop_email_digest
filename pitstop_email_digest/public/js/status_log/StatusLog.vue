<template>
	<!-- tw-scope: the Tailwind utilities are scoped to it -->
	<div class="tw-scope">
		<div class="border-0 border-t border-solid border-gray-200 px-4 py-5">
			<h4 class="m-0 mb-3 text-base font-semibold text-gray-900">{{ __("Status Log") }}</h4>

			<div v-if="loading && !stops.length" class="py-4 text-center text-xs text-gray-500">
				{{ __("Loading...") }}
			</div>

			<template v-else-if="stops.length">
				<div class="flex overflow-x-auto px-1 pb-1 pt-2">
					<div
						v-for="(stop, i) in stops"
						:key="stop.status"
						class="relative min-w-[110px] flex-1 px-1.5 text-center"
					>
						<!-- track from the previous stop -->
						<div
							v-if="i > 0"
							class="absolute left-[-50%] top-[9px] h-1 w-full rounded-full bg-sky-300"
						></div>

						<div
							class="relative mx-auto mb-1.5 h-[22px] w-[22px] rounded-full border-[3px]"
							:class="
								isDone(i)
									? 'border-sky-300 bg-sky-300'
									: 'border-sky-500 bg-sky-50 ring-4 ring-sky-100'
							"
						></div>

						<div class="text-xs font-semibold text-gray-800">{{ __(stop.status) }}</div>

						<template v-if="isLast(i) && isFinal">
							<div
								class="mt-1 inline-block rounded-full bg-sky-100 px-2 py-px text-[11px] text-sky-800"
							>
								{{ frappe.datetime.str_to_user(stop.start) }}
							</div>
						</template>
						<template v-else>
							<div
								class="mt-1 inline-block rounded-full bg-sky-100 px-2 py-px text-[11px] text-sky-800"
							>
								{{ formatDays(stop.seconds) }}
							</div>
							<div class="mt-0.5 text-[10px] text-gray-500">
								{{ formatDuration(stop.seconds) }}
							</div>
						</template>

						<div v-if="stop.visits > 1" class="mt-0.5 text-[10px] text-gray-500">
							{{ __("{0} times", [stop.visits]) }}
						</div>
					</div>
				</div>

				<div class="mt-1 text-right text-xs text-gray-500">
					{{ isFinal ? __("Total turnaround") : __("Open for") }}:
					<b class="text-gray-800">{{ formatDays(totalSeconds) }}</b>
					({{ formatDuration(totalSeconds) }})
				</div>
			</template>

			<div v-else class="py-4 text-center text-xs text-gray-500">
				{{ __("No status changes yet") }}
			</div>
		</div>
	</div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";

const props = defineProps({
	project: { type: String, required: true },
});

const API = "pitstop_email_digest.overrides.project.project_status_train.get_status_train";

const stops = ref([]);
const isFinal = ref(false);
const totalSeconds = ref(0);
const loading = ref(false);

const isLast = (i) => i === stops.value.length - 1;
const isDone = (i) => !isLast(i) || isFinal.value;

function formatDuration(seconds) {
	const minutes = Math.floor(seconds / 60);
	const hours = Math.floor(minutes / 60);
	const days = Math.floor(hours / 24);

	if (days) return `${days}d ${hours % 24}h`;
	if (hours) return `${hours}h ${minutes % 60}m`;
	return `${minutes}m`;
}

function formatDays(seconds) {
	const days = seconds / 86400;
	return `${days.toFixed(days < 10 ? 1 : 0)} ${days.toFixed(1) === "1.0" ? __("day") : __("days")}`;
}

async function load() {
	const project = props.project;
	loading.value = true;
	try {
		const { message } = await frappe.call({ method: API, args: { project } });
		// ignore a late response after switching to another Repair Order
		if (!message || project !== props.project) return;

		stops.value = message.stops || [];
		isFinal.value = message.is_final;
		totalSeconds.value = message.total_seconds;
	} finally {
		loading.value = false;
	}
}

defineExpose({ load });
onMounted(load);
watch(() => props.project, load);
</script>
