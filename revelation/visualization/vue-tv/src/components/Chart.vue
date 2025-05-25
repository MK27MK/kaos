<script setup>
import { onMounted, onUnmounted, ref, defineProps, watch } from "vue";
import { CandlestickSeries, createChart } from "lightweight-charts";

const props = defineProps({
  height: { type: Number, default: 400 },
  data: {
    type: Array,
    required: true,
  },
});
let chart;
const chartContainer = ref();

onMounted(() => {
  const chartOptions = {
    width: chartContainer.value.clientWidth,
    height: props.height,
    layout: {
      background: { type: "solid", color: "#ffffff" },
      textColor: "#333",
    },
    grid: {
      vertLines: { color: "#f0f3fa" },
      horzLines: { color: "#f0f3fa" },
    },
  };

  const chart = createChart(chartContainer.value, chartOptions);
  const series = chart.addSeries(CandlestickSeries);
  series.setData(props.data);
});
onUnmounted(() => {
  chart.remove();
  chart = null;
});

watch(
  () => props.data,
  (newData) => {
    if (!series) return;
    series.setData(newData);
  }
);
</script>

<template>
  <div class="lw-chart" ref="chartContainer"></div>
</template>

<style scoped>
.lw-chart {
  width: 100%;
  height: 100%;
}
</style>
