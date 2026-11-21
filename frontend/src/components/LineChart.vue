<script setup>
import { computed } from 'vue'
const props = defineProps({
  labels: { type: Array, required: true },
  series: { type: Array, required: true },   // [{ name, color, values, area }]
  min: { type: Number, default: null },       // batas bawah sumbu (default 0)
  format: { type: Function, default: (v) => v.toLocaleString('id-ID') },
  aria: { type: String, default: 'Grafik garis' }
})
const W = 770, H = 250, L = 52, R = 22, T = 16, Bm = 34
const semua = computed(() => props.series.flatMap((s) => s.values))
const skala = computed(() => {
  const lo = props.min ?? 0
  const hiRaw = Math.max(...semua.value, lo + 1)
  const step = Math.pow(10, Math.floor(Math.log10(hiRaw - lo))) / 2
  const hi = Math.ceil(hiRaw / step) * step
  return { lo, hi }
})
const x = (i) => L + (props.labels.length < 2 ? 0 : (i * (W - L - R)) / (props.labels.length - 1))
const y = (v) => T + (H - T - Bm) * (1 - (v - skala.value.lo) / (skala.value.hi - skala.value.lo))
const ticks = computed(() => [0, 1, 2, 3, 4].map((k) => skala.value.lo + ((skala.value.hi - skala.value.lo) * k) / 4))
const tampilLabel = computed(() => {
  const n = props.labels.length
  const lompat = Math.max(1, Math.ceil(n / 7))
  return props.labels.map((l, i) => (i === n - 1 || (i % lompat === 0 && n - 1 - i >= lompat / 2) ? l : null))
})
const titik = (s) => s.values.map((v, i) => `${x(i)},${y(v)}`).join(' ')
const area = (s) => `${x(0)},${y(skala.value.lo)} ${titik(s)} ${x(s.values.length - 1)},${y(skala.value.lo)}`
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${H}`" class="w-full h-auto" role="img" :aria-label="aria">
    <g v-for="t in ticks" :key="t">
      <line :x1="L" :x2="W - R" :y1="y(t)" :y2="y(t)" stroke="#F0EDF8" />
      <text :x="L - 8" :y="y(t) + 4" text-anchor="end" font-size="11" fill="#6B6880">{{ format(t) }}</text>
    </g>
    <template v-for="s in series" :key="s.name">
      <polygon v-if="s.area" :points="area(s)" :fill="s.color" fill-opacity="0.12" />
      <polyline :points="titik(s)" fill="none" :stroke="s.color" stroke-width="2.5" stroke-linejoin="round" />
      <circle v-for="(v, i) in s.values" :key="i" :cx="x(i)" :cy="y(v)" r="3" :fill="s.color">
        <title>{{ labels[i] }} · {{ s.name }}: {{ format(v) }}</title>
      </circle>
    </template>
    <text v-for="(l, i) in tampilLabel" :key="'l' + i" v-show="l" :x="x(i)" :y="H - 12" text-anchor="middle" font-size="11" fill="#6B6880">{{ l }}</text>
  </svg>
</template>
