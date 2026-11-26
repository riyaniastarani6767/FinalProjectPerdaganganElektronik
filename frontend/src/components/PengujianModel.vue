<script setup>
// Bagian "Pengujian model" di halaman Prediksi: kartu XGBoost dan Random Forest, perbandingan metrik, dan SHAP global
import { computed } from 'vue'
import { desimal, LABEL_FITUR, ribuan } from '../api'

const props = defineProps({
  ev: { type: Object, required: true },
  pilih: { type: String, default: 'keduanya' }   // 'xgboost' | 'random_forest' | 'keduanya'
})
const dua = computed(() => props.pilih === 'keduanya')
const METRIK = [['accuracy', 'Accuracy'], ['precision', 'Precision'], ['recall', 'Recall'], ['f1', 'F1-score']]
const ARTI = {
  accuracy: 'Persentase semua tebakan yang benar. Bisa menyesatkan karena data tidak seimbang.',
  precision: 'Dari yang ditebak batal, berapa persen yang benar batal.',
  recall: 'Dari yang benar batal, berapa persen yang tertangkap model.',
  f1: 'Rata-rata harmonis precision dan recall. Dasar pemilihan model terbaik.'
}
const WARNA = { xgboost: '#5C47A3', random_forest: '#C25680' }
const xgb = computed(() => props.ev.model.xgboost)
const rf = computed(() => props.ev.model.random_forest)
const baselineTerbaik = computed(() => props.ev.baseline.reduce((a, b) => (b.f1 > a.f1 ? b : a)))

const kartu = computed(() => (dua.value ? ['xgboost', 'random_forest'] : [props.pilih]).map((kode) => {
  const m = props.ev.model[kode]
  const lawan = props.ev.model[kode === 'xgboost' ? 'random_forest' : 'xgboost']
  const terbaik = kode === props.ev.terbaik
  const unggul = METRIK.filter(([k]) => m[k] > lawan[k]).map(([k, l]) => `${l.toLowerCase()} ${desimal(m[k])}%`)
  return {
    kode, m, terbaik,
    selisih: desimal(Math.abs(m.f1 - lawan.f1)),
    keBaseline: desimal(m.f1 - baselineTerbaik.value.f1),
    lawan: lawan.nama,
    unggul: unggul.join(' dan ')
  }
}))

// grafik batang berkelompok
const W = 520, H = 240, L = 34, B = 30, T = 24, lebar = (W - L - 10) / 4
const y = (v) => H - B - ((H - B - T) * v) / 100

// SHAP kupu-kupu: gabungan fitur teratas kedua model
const shap = computed(() => {
  const a = Object.fromEntries(xgb.value.shap.map((s) => [s.fitur, s.persen]))
  const b = Object.fromEntries(rf.value.shap.map((s) => [s.fitur, s.persen]))
  const fitur = [...new Set([...xgb.value.shap.slice(0, 8), ...rf.value.shap.slice(0, 8)].map((s) => s.fitur))].slice(0, 8)
  const max = Math.max(...fitur.flatMap((f) => [a[f] || 0, b[f] || 0]), 1)
  return fitur.map((f) => ({ f, label: LABEL_FITUR[f] || f, x: a[f] || 0, r: b[f] || 0, wx: ((a[f] || 0) / max) * 100, wr: ((b[f] || 0) / max) * 100 }))
})
// SHAP satu model
const shapSatu = computed(() => {
  if (dua.value) return []
  const m = props.ev.model[props.pilih], top = m.shap.slice(0, 6), max = Math.max(...top.map((s) => s.persen), 1)
  return top.map((s) => ({ f: s.fitur, label: LABEL_FITUR[s.fitur] || s.fitur, v: s.persen, w: (s.persen / max) * 100 }))
})
const kalimatShapSatu = computed(() => {
  if (dua.value) return ''
  const t = shapSatu.value.slice(0, 3).map((s) => s.label.toLowerCase())
  return `Fitur yang paling memengaruhi prediksi ${props.ev.model[props.pilih].nama} adalah ${t.join(', ')}.`
})
const kalimatShap = computed(() => {
  const top = (m) => m.shap.slice(0, 3).map((s) => (LABEL_FITUR[s.fitur] || s.fitur).toLowerCase())
  const tx = top(xgb.value), tr = top(rf.value)
  const sama = tx.filter((f) => tr.includes(f))
  return `Pada XGBoost, fitur paling berpengaruh adalah ${tx.join(', ')}. Pada Random Forest: ${tr.join(', ')}.` +
    (sama.length ? ` Kedua model sama-sama menempatkan ${sama.join(' dan ')} di tiga teratas.` : '')
})
</script>

<template>
  <div class="px-1 mt-3">
    <h2 class="text-lg font-bold">Pengujian model</h2>
    <p class="sub mt-1 leading-relaxed">Hasil pengujian {{ dua ? 'XGBoost dan Random Forest' : ev.model[pilih].nama }} pada {{ ribuan(ev.data.uji) }} data uji (20% data) · arahkan kursor ke angka atau grafik untuk penjelasannya</p>
  </div>

  <section class="grid grid-cols-1 xl:grid-cols-2 gap-4">
    <div v-for="k in kartu" :key="k.kode" class="rounded-[14px] p-[22px] text-white flex flex-col gap-4" :style="{ background: WARNA[k.kode] }">
      <div class="flex justify-between items-start gap-3">
        <div><small class="block text-xs opacity-75">{{ k.terbaik ? 'Model terbaik' : 'Pembanding' }}</small><div class="text-[26px] font-extrabold mt-0.5">{{ k.m.nama }}</div></div>
        <div class="text-right"><b class="block text-[38px] font-extrabold leading-none tabular-nums">{{ desimal(k.m.f1) }}%</b><span class="block text-xs opacity-75 mt-1">F1-score data uji</span></div>
      </div>
      <p v-if="!dua" class="text-[13px] leading-relaxed opacity-95">
        <template v-if="k.terbaik">Model terbaik berdasarkan F1-score, <b>{{ k.keBaseline }} poin</b> di atas baseline terbaik (pohon keputusan sederhana).</template>
        <template v-else>F1-score <b>{{ k.keBaseline }} poin</b> di atas baseline terbaik (pohon keputusan sederhana)<template v-if="k.unggul">, dengan {{ k.unggul }} sehingga banyak pembatalan yang tertangkap</template>.</template>
      </p>
      <p v-else-if="k.terbaik" class="text-[13px] leading-relaxed opacity-95">F1-score paling tinggi, <b>{{ k.selisih }} poin</b> di atas {{ k.lawan }} dan <b>{{ k.keBaseline }} poin</b> di atas baseline terbaik.</p>
      <p v-else class="text-[13px] leading-relaxed opacity-95">F1-score <b>{{ k.selisih }} poin</b> di bawah {{ k.lawan }}<template v-if="k.unggul">, tetapi unggul di {{ k.unggul }}, artinya lebih banyak pembatalan yang tertangkap</template>.</p>
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-auto">
        <div v-for="[key, label] in METRIK" :key="key" v-tip="[`${label} ${k.m.nama}`, `${desimal(k.m[key])}%`, ARTI[key]]" class="bg-white/15 rounded-[10px] px-3 py-2.5">
          <span class="block text-[11px] opacity-75">{{ label }}</span><b class="text-[17px] tabular-nums">{{ desimal(k.m[key]) }}%</b>
        </div>
      </div>
    </div>
      <div v-if="!dua" class="kartu flex flex-col gap-2">
      <div class="flex flex-wrap justify-between items-baseline gap-2"><h3 class="judul-kartu">Fitur paling berpengaruh (SHAP)</h3><span class="sub">% dari total pengaruh · 200 data uji</span></div>
      <div class="grid grid-cols-[120px_1fr_48px] gap-x-3 gap-y-2 items-center text-[12.5px] mt-1">
        <div v-for="s in shapSatu" :key="s.f" class="contents" v-tip="[s.label, `${desimal(s.v, 1)}% dari total pengaruh pada prediksi`, 'Rata-rata nilai SHAP mutlak pada 200 data uji']">
          <span class="truncate">{{ s.label }}</span>
          <div class="h-3 bg-ungu-pucat rounded"><div class="h-3 rounded" :style="{ width: s.w + '%', background: WARNA[pilih] }"></div></div>
          <span class="text-right tabular-nums font-semibold">{{ desimal(s.v, 1) }}%</span>
        </div>
      </div>
      <p class="sub mt-2 leading-relaxed">{{ kalimatShapSatu }}</p>
    </div>
  </section>

  <section v-if="dua" class="grid grid-cols-1 xl:grid-cols-2 gap-4">
    <div class="kartu flex flex-col gap-2">
      <div class="flex flex-wrap justify-between items-baseline gap-2">
        <h3 class="judul-kartu">Perbandingan metrik</h3>
        <div class="legenda"><span><i class="bg-[#5C47A3]"></i>XGBoost</span><span><i class="bg-[#C25680]"></i>Random Forest</span></div>
      </div>
      <svg :viewBox="`0 0 ${W} ${H}`" class="w-full h-auto" role="img" aria-label="Perbandingan metrik XGBoost dan Random Forest">
        <g v-for="(v, i) in [0, 25, 50, 75, 100]" :key="v">
          <line :x1="L" :x2="W - 10" :y1="y(v)" :y2="y(v)" stroke="#EFEDF2" :stroke-dasharray="i ? '3 4' : null" />
          <text :x="L - 6" :y="y(v) + 4" text-anchor="end" font-size="10.5" fill="#6B6873">{{ v }}</text>
        </g>
        <g v-for="([key, label], i) in METRIK" :key="key">
          <g v-for="(m, j) in [xgb, rf]" :key="m.nama" v-tip="[`${label} ${m.nama}`, `${desimal(m[key])}%`, ARTI[key]]">
            <rect :x="L + i * lebar + lebar * 0.18 + j * (lebar * 0.3 + 4)" :y="y(m[key])" :width="lebar * 0.3" :height="H - B - y(m[key])" rx="5" :fill="j ? '#C25680' : '#5C47A3'" />
            <text :x="L + i * lebar + lebar * 0.18 + j * (lebar * 0.3 + 4) + lebar * 0.15" :y="y(m[key]) - 6" text-anchor="middle" font-size="10.5" font-weight="700" fill="#1E1B24">{{ desimal(m[key], 1) }}</text>
          </g>
          <text :x="L + i * lebar + lebar * 0.48 + 2" :y="H - 9" text-anchor="middle" font-size="12" font-weight="500" fill="#4A4752">{{ label }}</text>
        </g>
      </svg>
      <p class="sub">F1-score dipakai sebagai dasar pemilihan karena data tidak seimbang ({{ desimal(ev.data.persen_batal, 1) }}% batal), sehingga accuracy saja bisa menyesatkan.</p>
    </div>

    <div class="kartu flex flex-col gap-2">
      <div class="flex flex-wrap justify-between items-baseline gap-2"><h3 class="judul-kartu">Fitur paling berpengaruh (SHAP)</h3><span class="sub">% dari total pengaruh · 200 data uji</span></div>
      <div class="grid grid-cols-[1fr_118px_1fr] gap-y-2 items-center text-[12.5px] mt-1">
        <span class="text-right text-xs font-semibold text-[#5C47A3]">XGBoost</span><span></span><span class="text-xs font-semibold text-[#C25680]">Random Forest</span>
        <div v-for="s in shap" :key="s.f" class="contents"
          v-tip="[s.label, `XGBoost: ${desimal(s.x, 1)}% dari total pengaruh`, `Random Forest: ${desimal(s.r, 1)}% dari total pengaruh`]">
          <div class="flex items-center justify-end gap-2"><span class="tabular-nums text-xs">{{ desimal(s.x, 1) }}%</span><div class="h-3.5 rounded bg-[#5C47A3]" :style="{ width: s.wx * 0.75 + '%' }"></div></div>
          <span class="text-center font-medium">{{ s.label }}</span>
          <div class="flex items-center gap-2"><div class="h-3.5 rounded bg-[#C25680]" :style="{ width: s.wr * 0.75 + '%' }"></div><span class="tabular-nums text-xs">{{ desimal(s.r, 1) }}%</span></div>
        </div>
      </div>
      <p class="sub mt-2 leading-relaxed">{{ kalimatShap }}</p>
    </div>
  </section>
</template>
