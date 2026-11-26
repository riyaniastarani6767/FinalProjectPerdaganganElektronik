<script setup>
// Grafik garis halus (SVG manual). Hover/ketuk satu bulan untuk melihat semua nilainya.
import { computed, ref } from 'vue'
const props = defineProps({
  labels: { type: Array, required: true },
  series: { type: Array, required: true },   // [{ name, color, values, tag }] tag = teks penanda nilai tertinggi
  format: { type: Function, default: (v) => Math.round(v).toLocaleString('id-ID') },
  satuan: { type: String, default: '' },
  aria: { type: String, default: 'Grafik garis' }
})
const W = 640, H = 240, L = 46, R = 10, T = 34, B = 26
const uid = Math.random().toString(36).slice(2, 8)
const aktif = ref(null)

const hi = computed(() => {
  const m = Math.max(...props.series.flatMap((s) => s.values), 1)
  const p = Math.pow(10, Math.floor(Math.log10(m)))
  return Math.ceil((m / p) * 2) / 2 * p
})
const n = computed(() => props.labels.length)
const x = (i) => L + (n.value < 2 ? 0 : (i * (W - L - R)) / (n.value - 1))
const y = (v) => H - B - ((H - B - T) * v) / hi.value
const ticks = computed(() => [0, 1, 2, 3, 4].map((k) => (hi.value * k) / 4))
const halus = (vals) => vals.map((v, i) => {
  if (!i) return `M${x(0)},${y(v)}`
  const cx = (x(i - 1) + x(i)) / 2
  return `C${cx},${y(vals[i - 1])} ${cx},${y(v)} ${x(i)},${y(v)}`
}).join(' ')
const area = (vals) => `${halus(vals)} L${x(vals.length - 1)},${H - B} L${x(0)},${H - B} Z`
const tampilLabel = computed(() => props.labels.map((l, i) => (i === n.value - 1 || (i % 4 === 0 && n.value - 1 - i >= 3) ? l : null)))
const penanda = computed(() => props.series.filter((s) => s.tag).map((s) => {
  const i = s.values.indexOf(Math.max(...s.values))
  const teks = `${s.tag} ${props.format(s.values[i])}`
  const lebar = teks.length * 6 + 16
  return { i, v: s.values[i], color: s.color, teks, lebar, kx: Math.min(Math.max(x(i) - lebar / 2, L), W - R - lebar) }
}))
const lebarKolom = computed(() => (W - L - R) / Math.max(n.value - 1, 1))
const isiTip = (i) => [props.labels[i], ...props.series.map((s) => `${s.name}: ${props.format(s.values[i])}${props.satuan}`)]
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${H}`" class="w-full h-auto" role="img" :aria-label="aria" @mouseleave="aktif = null">
    <defs>
      <linearGradient v-for="(s, k) in series" :id="`g${uid}${k}`" :key="k" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" :stop-color="s.color" stop-opacity="0.18" /><stop offset="1" :stop-color="s.color" stop-opacity="0" />
      </linearGradient>
    </defs>
    <g v-for="(t, k) in ticks" :key="k">
      <line :x1="L" :x2="W - R" :y1="y(t)" :y2="y(t)" stroke="#EFEDF2" :stroke-dasharray="k ? '3 4' : null" />
      <text :x="L - 8" :y="y(t) + 4" text-anchor="end" font-size="10.5" fill="#6B6873">{{ format(t) }}</text>
    </g>
    <template v-for="(s, k) in series" :key="s.name">
      <path :d="area(s.values)" :fill="`url(#g${uid}${k})`" />
      <path :d="halus(s.values)" fill="none" :stroke="s.color" stroke-width="2.2" />
    </template>
    <template v-for="p in penanda" :key="p.teks">
      <line :x1="x(p.i)" :x2="x(p.i)" :y1="y(p.v)" :y2="H - B" :stroke="p.color" stroke-dasharray="2 3" opacity="0.5" />
      <circle :cx="x(p.i)" :cy="y(p.v)" r="4" fill="#fff" :stroke="p.color" stroke-width="2" />
      <rect :x="p.kx" :y="y(p.v) - 26" :width="p.lebar" height="18" rx="5" :fill="p.color" />
      <text :x="p.kx + p.lebar / 2" :y="y(p.v) - 13" text-anchor="middle" font-size="10.5" font-weight="600" fill="#fff">{{ p.teks }}</text>
    </template>
    <!-- garis bantu bulan yang sedang di-hover -->
    <template v-if="aktif !== null">
      <line :x1="x(aktif)" :x2="x(aktif)" :y1="T - 6" :y2="H - B" stroke="#A99CCB" />
      <circle v-for="s in series" :key="s.name" :cx="x(aktif)" :cy="y(s.values[aktif])" r="4" :fill="s.color" stroke="#fff" stroke-width="1.5" />
    </template>
    <text v-for="(l, i) in tampilLabel" v-show="l" :key="'l' + i" :x="x(i)" :y="H - 6" :text-anchor="i === n - 1 ? 'end' : 'middle'" font-size="10.5" fill="#6B6873">{{ l }}</text>
    <rect v-for="(l, i) in labels" :key="'h' + i" v-tip="isiTip(i)" :x="x(i) - lebarKolom / 2" :y="T - 6" :width="lebarKolom" :height="H - B - T + 6"
      fill="transparent" @mouseenter="aktif = i" @touchstart.passive="aktif = i" />
  </svg>
</template>
