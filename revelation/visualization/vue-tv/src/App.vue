<script setup>
import Chart from "./components/Chart.vue";
import { ref } from "vue";

const data = ref([
  { time: 1716508800, open: 42500, high: 42800, low: 42350, close: 42710 },
  { time: 1716595200, open: 42710, high: 43020, low: 42600, close: 42950 },
  { time: 1716681600, open: 42950, high: 43300, low: 42880, close: 43250 },
  { time: 1716768000, open: 43250, high: 43540, low: 43100, close: 43480 },
]);
</script>

<template>
  <div>
    <h1>hello</h1>
    <Chart :data="data" />
  </div>
</template>

<style scoped></style>
