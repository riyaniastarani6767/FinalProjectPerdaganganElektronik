<script setup>
// Gauge setengah lingkaran untuk peluang batal (0-100%), dengan zona risiko rendah, sedang, tinggi
import { computed } from 'vue'
const props = defineProps({
  nilai: { type: Number, required: true },   // peluang batal dalam persen
  kecil: { type: Boolean, default: false }
})
const cx = 150, cy = 140, r = 110
const titik = (v, rr) => {
  const a = Math.PI * (1 - v / 100)
  return [cx + rr * Math.cos(a), cy - rr * Math.sin(a)]
}
const busur = (a, b) => {
  const [x0, y0] = titik(a, r), [x1, y1] = titik(b, r)
  return `M${x0},${y0} A${r},${r} 0 0 1 ${x1},${y1}`
}
const ZONA = [
  { a: 0, b: 35, warna: '#DCD4EC', nama: 'Risiko rendah', ket: 'Peluang batal di bawah 35%' },
  { a: 35, b: 70, warna: '#B9ACD8', nama: 'Risiko sedang', ket: 'Peluang batal 35% sampai 70%' },
  { a: 70, b: 100, warna: '#E7A9C0', nama: 'Risiko tinggi', ket: 'Peluang batal di atas 70%' }
]
const warna = computed(() => (props.nilai >= 50 ? '#C4547B' : '#4E3A86'))
const ujung = computed(() => titik(Math.min(Math.max(props.nilai, 0.5), 99.5), r))
const label = [0, 35, 50, 70, 100].map((v) => ({ v, p: titik(v, r + 22) }))
</script>

<template>
  <div class="relative flex flex-col items-center">
    <svg viewBox="0 -8 300 170" :class="kecil ? 'w-[210px]' : 'w-[300px] max-w-full'" role="img" :aria-label="`Peluang batal ${nilai}%`">
      <path v-for="z in ZONA" :key="z.nama" v-tip="[z.nama, z.ket]" :d="busur(z.a + 0.6, z.b - 0.6)" :stroke="z.warna" stroke-width="22" fill="none" />
      <path :d="busur(0.3, Math.max(nilai, 0.6))" :stroke="warna" stroke-width="8" fill="none" />
      <circle :cx="ujung[0]" :cy="ujung[1]" r="8" fill="#fff" :stroke="warna" stroke-width="3.5" />
      <text v-for="l in label" :key="l.v" :x="l.p[0]" :y="l.p[1] + 4" text-anchor="middle" font-size="10.5" fill="#6B6873">{{ l.v }}%</text>
    </svg>
    <div class="absolute text-center" :class="kecil ? 'top-[60px]' : 'top-[90px]'">
      <div class="font-extrabold leading-tight tabular-nums" :class="kecil ? 'text-2xl' : 'text-[34px]'">{{ nilai.toFixed(1).replace('.', ',') }}%</div>
      <div class="sub" :class="kecil ? 'text-[11px]' : ''">peluang batal</div>
    </div>
  </div>
</template>
