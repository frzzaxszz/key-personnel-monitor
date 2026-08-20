<template>
  <div ref="el" class="chart" :style="{ width: '100%', height: height }"></div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: String, default: '100%' },
  onEvents: { type: Object, default: () => ({}) }
})

const el = ref(null)
let chart = null
let ro = null
const boundEvents = new Set()

function bindEvents() {
  for (const key of boundEvents) { chart.off(key) }
  boundEvents.clear()
  for (const [name, handler] of Object.entries(props.onEvents || {})) {
    if (typeof handler !== 'function') continue
    chart.on(name, handler)
    boundEvents.add(name)
  }
}

function render() {
  if (!chart && el.value) { chart = echarts.init(el.value) }
  if (chart) { chart.setOption(props.option, true); bindEvents() }
}

function resize() { chart && chart.resize() }

onMounted(() => {
  nextTick(() => {
    render()
    ro = new ResizeObserver(resize)
    ro.observe(el.value)
  })
})

watch(() => props.option, () => render(), { deep: true })
watch(() => props.onEvents, () => chart && bindEvents(), { deep: true })

onBeforeUnmount(() => {
  ro && ro.disconnect()
  chart && chart.dispose()
  chart = null
})
</script>

<style scoped>
.chart { overflow: hidden; }
</style>
