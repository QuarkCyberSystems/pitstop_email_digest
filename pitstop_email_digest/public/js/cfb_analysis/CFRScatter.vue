<template>
	<div
		class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
		:style="{ width: '100%', height: height + 'px' }"
	>
		<h4 class="mb-3 text-lg font-semibold">Customer Feedback Response Scatter Points</h4>
		<div ref="chartRef" :style="{ width: '100%', height: props.height + 'px' }"></div>
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
	height: { type: Number, default: 400 },
});

const chartRef = ref(null);
let chart = null;
let resizeObserver = null;

function buildChartData(items) {
	// Group branches by identical [x, y] coordinates
	const groups = {};

	Object.entries(items).forEach(([location, val]) => {
		const key = `${val.customer_respond_count}_${val.customer_satisfaction_index}`;
		if (!groups[key]) {
			groups[key] = {
				x: val.customer_respond_count,
				y: val.customer_satisfaction_index,
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
		grid: {
			top: 20,
			right: 20,
			bottom: 50,
			left: 60,
		},
		tooltip: {
			trigger: "item",
			formatter: (params) => {
				const { name, data } = params;
				const [x, y] = data.originalValue;
				// If multiple branches share this point, list them all
				const others = data.allBranches.filter((b) => b !== name);
				let tip = `<strong>${name}</strong><br/>
                   Response Count: ${x}<br/>
                   CSI: ${y}%`;
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
			name: "Customer Response",
			nameLocation: "middle",
			nameGap: 30,
		},
		yAxis: {
			type: "value",
			scale: true,
			name: "CSI (%)",
			nameLocation: "middle",
			nameGap: 40,
			min: 70,
			max: 105,
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

watch(
	() => props.height,
	async (newHeight) => {
		await nextTick(); // wait for :style binding to apply new height
		chart?.resize({
			width: chartRef.value?.offsetWidth,
			height: newHeight - 100,
		});
	}
);

watch(() => props.items, updateChart, { deep: true });
</script>
