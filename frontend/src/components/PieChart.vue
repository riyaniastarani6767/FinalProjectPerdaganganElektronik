<script setup>
// Diagram pie 2 warna (SVG manual). Hover/ketuk irisan untuk melihat jumlah dan persentasenya.
import { computed, ref } from 'vue'
const props = defineProps({
  segments: { type: Array, required: true },  // [{ label, value, color, teks }] teks = warna angka di dalam irisan
  satuan: { type: String, default: 'reservasi' }
})
const r = 58, c = 66
const aktif = ref(null)
const total = computed(() => props.segments.reduce((a, s) => a + s.value, 0) || 1)
const titik = (sudut, rr) => [c + rr * Math.sin(sudut), c - rr * Math.cos(sudut)]
const irisan = computed(() => {
  let mulai = 0
  return props.segments.map((s) => {
    const p = s.value / total.value, akhir = mulai + p * 2 * Math.PI
    const [x0, y0] = titik(mulai, r), [x1, y1] = titik(akhir, r), [lx, ly] = titik((mulai + akhir) / 2, r * 0.58)
    const d = p >= 0.999 ? '' : `M${c},${c} L${x0},${y0} A${r},${r} 0 ${p > 0.5 ? 1 : 0} 1 ${x1},${y1} Z`
    mulai = akhir
    return { ...s, p, d, lx, ly }
  })
})
</script>

<template>
  <svg viewBox="0 0 132 132" class="w-[132px] h-[132px] shrink-0" role="img" :aria-label="segments.map((s) => s.label).join(', ')" @mouseleave="aktif = null">
    <g v-for="(s, i) in irisan" :key="s.label" v-tip="[s.label, `${Math.round(s.value).toLocaleString('id-ID')} ${satuan}`, `${(s.p * 100).toFixed(1).replace('.', ',')}% dari total`]"
      :transform="aktif === i ? `translate(${(s.lx - c) * 0.12} ${(s.ly - c) * 0.12})` : null" style="transition: transform .15s"
      @mouseenter="aktif = i" @touchstart.passive="aktif = i">
      <circle v-if="!s.d" :cx="c" :cy="c" :r="r" :fill="s.color" />
      <path v-else :d="s.d" :fill="s.color" />
      <text :x="s.lx" :y="s.ly + 4" text-anchor="middle" font-size="12" font-weight="700" :fill="s.teks || '#fff'">{{ Math.round(s.p * 100) }}%</text>
    </g>
  </svg>
</template>
