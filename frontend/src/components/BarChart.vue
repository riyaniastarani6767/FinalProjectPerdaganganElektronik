<script setup>
// Grafik batang bertumpuk (SVG manual). Hover/ketuk satu batang untuk melihat rinciannya.
import { computed, ref } from 'vue'
const props = defineProps({
  labels: { type: Array, required: true },
  series: { type: Array, required: true },   // [{ name, color, values }] dari bawah ke atas
  format: { type: Function, default: (v) => Math.round(v).toLocaleString('id-ID') },
  satuan: { type: String, default: '' },
  aria: { type: String, default: 'Grafik batang bertumpuk' }
})
const W = 640, H = 220, L = 46, R = 8, T = 10, B = 26
const aktif = ref(null)
const totals = computed(() => props.labels.map((_, i) => props.series.reduce((a, s) => a + (s.values[i] || 0), 0)))
const hi = computed(() => {
  const m = Math.max(...totals.value, 1)
  const p = Math.pow(10, Math.floor(Math.log10(m)))
  return Math.ceil((m / p) * 2) / 2 * p
})
const n = computed(() => props.labels.length)
const lebar = computed(() => (W - L - R) / n.value)
const tinggi = (v) => ((H - B - T) * v) / hi.value
const ticks = computed(() => [0, 1, 2, 3, 4].map((k) => (hi.value * k) / 4))
const batang = computed(() => props.labels.map((_, i) => {
  let dasar = 0
  return props.series.map((s) => {
    const h = tinggi(s.values[i] || 0)
    const r = { x: L + i * lebar.value + lebar.value * 0.2, w: lebar.value * 0.6, y: H - B - dasar - h, h, color: s.color }
    dasar += h
    return r
  })
}))
const tampilLabel = computed(() => props.labels.map((l, i) => (i === n.value - 1 || (i % 4 === 0 && n.value - 1 - i >= 3) ? l : null)))
const isiTip = (i) => {
  const baris = props.series.map((s) => `${s.name}: ${props.format(s.values[i])}${props.satuan}`)
  if (props.series.length > 1) {
    const pertama = props.series[props.series.length - 1].values[i]
    baris.push(`Total: ${props.format(totals.value[i])}${props.satuan} (${props.series[props.series.length - 1].name.toLowerCase()} ${Math.round((pertama / (totals.value[i] || 1)) * 100)}%)`)
  }
  return [props.labels[i], ...baris]
}
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${H}`" class="w-full h-auto" role="img" :aria-label="aria" @mouseleave="aktif = null">
    <g v-for="(t, k) in ticks" :key="k">
      <line :x1="L" :x2="W - R" :y1="H - B - tinggi(t)" :y2="H - B - tinggi(t)" stroke="#EFEDF2" :stroke-dasharray="k ? '3 4' : null" />
      <text :x="L - 8" :y="H - B - tinggi(t) + 4" text-anchor="end" font-size="10.5" fill="#6B6873">{{ format(t) }}</text>
    </g>
    <g v-for="(kol, i) in batang" :key="i" v-tip="isiTip(i)" :opacity="aktif === null || aktif === i ? 1 : 0.45"
      @mouseenter="aktif = i" @touchstart.passive="aktif = i">
      <rect :x="L + i * lebar" :y="T" :width="lebar" :height="H - B - T" fill="transparent" />
      <rect v-for="(b, j) in kol" :key="j" :x="b.x" :y="b.y" :width="b.w" :height="Math.max(b.h, 0)" :fill="b.color" rx="2" />
    </g>
    <text v-for="(l, i) in tampilLabel" v-show="l" :key="'l' + i" :x="i === n - 1 ? L + (i + 0.8) * lebar : L + (i + 0.5) * lebar" :y="H - 6"
      :text-anchor="i === n - 1 ? 'end' : 'middle'" font-size="10.5" fill="#6B6873">{{ l }}</text>
  </svg>
</template>
