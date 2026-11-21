<script setup>
import { computed } from 'vue'
const props = defineProps({
  labels: { type: Array, required: true },
  series: { type: Array, required: true },   // [{ name, color, values }] dari bawah ke atas
  format: { type: Function, default: (v) => v.toLocaleString('id-ID') },
  aria: { type: String, default: 'Grafik batang bertumpuk' }
})
const W = 770, H = 250, L = 52, R = 12, T = 16, Bm = 34
const totals = computed(() => props.labels.map((_, i) => props.series.reduce((a, s) => a + (s.values[i] || 0), 0)))
const hi = computed(() => {
  const m = Math.max(...totals.value, 1)
  const step = Math.pow(10, Math.floor(Math.log10(m))) / 2
  return Math.ceil(m / step) * step
})
const lebar = computed(() => (W - L - R) / props.labels.length)
const y = (v) => T + (H - T - Bm) * (1 - v / hi.value)
const ticks = computed(() => [0, 1, 2, 3, 4].map((k) => (hi.value * k) / 4))
const batang = computed(() => props.labels.map((lab, i) => {
  let dasar = 0
  return props.series.map((s) => {
    const v = s.values[i] || 0
    const r = { x: L + i * lebar.value + lebar.value * 0.15, w: lebar.value * 0.7, y: y(dasar + v), h: y(dasar) - y(dasar + v), color: s.color, t: `${lab} · ${s.name}: ${props.format(v)}` }
    dasar += v
    return r
  })
}))
const tampilLabel = computed(() => {
  const n = props.labels.length, lompat = Math.max(1, Math.ceil(n / 7))
  return props.labels.map((l, i) => (i === n - 1 || (i % lompat === 0 && n - 1 - i >= lompat / 2) ? l : null))
})
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${H}`" class="w-full h-auto" role="img" :aria-label="aria">
    <g v-for="t in ticks" :key="t">
      <line :x1="L" :x2="W - R" :y1="y(t)" :y2="y(t)" stroke="#F0EDF8" />
      <text :x="L - 8" :y="y(t) + 4" text-anchor="end" font-size="11" fill="#6B6880">{{ format(t) }}</text>
    </g>
    <g v-for="(kol, i) in batang" :key="i">
      <rect v-for="(b, j) in kol" :key="j" :x="b.x" :y="b.y" :width="b.w" :height="Math.max(b.h, 0)" :fill="b.color"><title>{{ b.t }}</title></rect>
    </g>
    <text v-for="(l, i) in tampilLabel" :key="'l' + i" v-show="l" :x="L + i * lebar + lebar / 2" :y="H - 12" text-anchor="middle" font-size="11" fill="#6B6880">{{ l }}</text>
  </svg>
</template>
