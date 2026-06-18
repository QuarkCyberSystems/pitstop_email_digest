<template>
	<div class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
		<h4 class="mb-3 text-lg font-semibold">Customer Feedback Complains Scatter Points</h4>
		<div ref="chartRef" style="width: 100%; height: 400px"></div>
	</div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from "vue";
import * as echarts from "echarts";

const props = defineProps({
	items: {
		type: Object,
		default: () => ({}),
	},
});

const chartRef = ref(null);
let chart = null;
let resizeObserver = null;

function buildChartData(items) {
	// Group branches by identical [x, y] coordinates
	const groups = {};

	Object.entries(items).forEach(([location, val]) => {
		const key = `${val.feedback_count}_${val.complain_count}`;
		if (!groups[key]) {
			groups[key] = {
				x: val.feedback_count,
				y: val.complain_count,
				branches: [],
			};
		}
		groups[key].branches.push(location);
	});

	// Apply jitter only when multiple branches share the same point
	const jitter = (val, index, total) => {
		if (total === 1) return val;
		const spread = 1.5;
		const offset = (index - (total - 1) / 2) * spread;
		return val + offset;
	};

	const data = [];
	Object.values(groups).forEach(({ x, y, branches }) => {
		branches.forEach((name, i) => {
			data.push({
				name,
				value: [jitter(x, i, branches.length), jitter(y, i, branches.length)],
				originalValue: [x, y],
				allBranches: branches,
			});
		});
	});

	return data;
}

function updateChart() {
	if (!chart) return;

	const data = buildChartData(props.items);

	chart.setOption({
		tooltip: {
			trigger: "item",
			formatter: (params) => {
				const { name, data } = params;
				const [x, y] = data.originalValue;
				// If multiple branches share this point, list them all
				const others = data.allBranches.filter((b) => b !== name);
				let tip = `<strong>${name}</strong><br/>
                   Feedback Count: ${x}<br/>
                   Complains Count: ${y}`;
				if (others.length) {
					tip += `<br/><span style="color:#9ca3af;font-size:11px">Same point: ${others.join(
						", "
					)}</span>`;
				}
				return tip;
			},
		},
		xAxis: {
			type: "value",
			scale: true,
			name: "Feedback Count",
			nameLocation: "middle",
			nameGap: 30,
		},
		yAxis: {
			type: "value",
			scale: true,
			name: "Complains Count",
			nameLocation: "middle",
			nameGap: 40,
			min: "dataMin",
			max: "dataMax",
		},
		series: [
			{
				type: "scatter",
				symbolSize: 14,
				data,
				label: {
					show: true,
					formatter: (params) => params.name,
					position: "top",
					fontSize: 11,
					color: "#374151",
				},
				itemStyle: {
					color: "#f87171", // blue
				},
			},
		],
	});
}

onMounted(async () => {
	await nextTick();
	chart = echarts.init(chartRef.value);
	updateChart();

	// Force correct size after init
	chart.resize();

	// Keep chart responsive when parent container resizes
	resizeObserver = new ResizeObserver(() => chart?.resize());
	resizeObserver.observe(chartRef.value.parentElement);
});

onBeforeUnmount(() => {
	resizeObserver?.disconnect();
	chart?.dispose();
});

watch(() => props.items, updateChart, { deep: true });
</script>
