<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, LABEL_FITUR, persen, ribuan } from '../api'
import ConfusionMatrix from '../components/ConfusionMatrix.vue'

const ev = ref(null)
const error = ref('')
onMounted(async () => {
  try { ev.value = await api.evaluasi() } catch (e) { error.value = e.message }
})

const xgb = computed(() => ev.value?.model.xgboost)
const rf = computed(() => ev.value?.model.random_forest)
const terbaik = computed(() => ev.value?.model[ev.value.terbaik])
const lain = computed(() => (ev.value?.terbaik === 'xgboost' ? rf.value : xgb.value))
const baselineTerbaik = computed(() => ev.value ? ev.value.baseline.reduce((a, b) => (b.f1 > a.f1 ? b : a)) : null)
const METRIK = [['accuracy', 'Accuracy'], ['precision', 'Precision'], ['recall', 'Recall'], ['f1', 'F1-score']]

// gabungan fitur SHAP kedua model, urut dari model terbaik
const shap = computed(() => {
  if (!ev.value) return []
  const a = Object.fromEntries(xgb.value.shap.map((s) => [s.fitur, s.persen]))
  const b = Object.fromEntries(rf.value.shap.map((s) => [s.fitur, s.persen]))
  const urut = [...new Set([...terbaik.value.shap.map((s) => s.fitur), ...lain.value.shap.map((s) => s.fitur)])].slice(0, 8)
  return urut.map((f) => ({ fitur: f, xgb: a[f] ?? 0, rf: b[f] ?? 0 }))
})
const maxShap = computed(() => Math.max(...shap.value.flatMap((s) => [s.xgb, s.rf]), 1))
</script>

<template>
  <div class="flex flex-col gap-1.5 pb-4 border-b border-[#E1DCF5]">
    <h1 class="text-[32px] font-normal">Evaluasi</h1>
    <span class="text-[13px] text-teks-redup">Hasil pengujian XGBoost dan Random Forest pada {{ ribuan(ev?.data.uji) }} data uji (20% data)</span>
  </div>

  <p v-if="error" class="kartu text-pink-tua">{{ error }}</p>
  <p v-else-if="!ev" class="kartu text-teks-redup">Memuat hasil evaluasi...</p>

  <template v-else>
    <section class="grid grid-cols-[repeat(auto-fit,minmax(340px,1fr))] gap-4">
      <div v-for="(m, i) in [xgb, rf]" :key="i" class="rounded-lg px-6 py-5 flex flex-col gap-3.5"
        :class="i === 0 ? 'bg-ungu text-white' : 'bg-pink-muda text-pink-gelap'">
        <div class="flex justify-between items-center gap-2">
          <strong class="text-[22px]">{{ m.nama }}</strong>
          <span class="px-2.5 py-1 rounded bg-white text-xs font-bold" :class="i === 0 ? 'text-ungu' : 'text-pink-tua'">
            {{ m === terbaik ? 'MODEL TERBAIK' : 'PEMBANDING' }}
          </span>
        </div>
        <div class="grid grid-cols-4 gap-2">
          <div v-for="[k, label] in METRIK" :key="k" class="flex flex-col">
            <span class="text-xs opacity-85">{{ label }}</span><strong class="text-[22px]">{{ persen(m[k]) }}</strong>
          </div>
        </div>
      </div>
    </section>

    <section class="kartu text-sm leading-relaxed">
      <strong>Kesimpulan:</strong> {{ terbaik.nama }} dipilih sebagai model terbaik karena F1-score-nya paling tinggi
      ({{ persen(terbaik.f1) }} vs {{ persen(lain.f1) }}). F1-score dipakai karena data tidak seimbang
      ({{ persen(ev.data.persen_batal, 1) }} batal), sehingga accuracy saja bisa menyesatkan. Kedua model jauh lebih baik
      dari baseline terbaik, {{ baselineTerbaik.nama.toLowerCase() }} (F1 {{ persen(baselineTerbaik.f1) }}).
    </section>

    <section class="kartu flex flex-col gap-3">
      <div>
        <h2 class="judul-kartu">Perbandingan dengan model pembanding (baseline)</h2>
        <span class="sub">Hasil pada {{ ribuan(ev.data.uji) }} data uji yang sama. Model yang baik harus mengalahkan pembanding sederhana.</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[620px] text-sm tabular-nums">
          <thead><tr class="text-left text-xs text-teks-redup">
            <th class="px-2 py-2.5 font-medium border-b border-garis">Model</th>
            <th v-for="[k, label] in METRIK" :key="k" class="px-2 py-2.5 font-medium border-b border-garis text-right">{{ label }}</th>
          </tr></thead>
          <tbody>
            <tr v-for="b in ev.baseline" :key="b.nama" class="text-teks-redup">
              <td class="px-2 py-2.5 border-b border-[#F3F2F7]">{{ b.nama }}</td>
              <td v-for="[k] in METRIK" :key="k" class="px-2 py-2.5 border-b border-[#F3F2F7] text-right">{{ k === 'precision' && b.recall === 0 ? 'Tidak ada' : persen(b[k]) }}</td>
            </tr>
            <tr v-for="m in [rf, xgb]" :key="m.nama" :class="m === terbaik ? 'bg-ungu-pucat font-semibold' : ''">
              <td class="px-2 py-2.5 border-b border-[#F3F2F7]">{{ m.nama }}{{ m === terbaik ? ' (terbaik)' : '' }}</td>
              <td v-for="[k] in METRIK" :key="k" class="px-2 py-2.5 border-b border-[#F3F2F7] text-right">{{ persen(m[k]) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <div v-for="m in [xgb, rf]" :key="m.nama" class="kartu flex flex-col gap-3.5 min-w-0">
        <h2 class="judul-kartu">Confusion matrix {{ m.nama }}</h2>
        <ConfusionMatrix :tn="m.tn" :fp="m.fp" :fn="m.fn" :tp="m.tp" />
      </div>
    </section>

    <section class="kartu flex flex-col gap-3">
      <div class="flex flex-wrap justify-between gap-2">
        <div><h2 class="judul-kartu">Fitur paling berpengaruh (SHAP)</h2><span class="sub">Persen dari total pengaruh pada prediksi</span></div>
        <div class="flex gap-4 text-xs text-teks-sedang">
          <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 bg-ungu"></span>XGBoost</span>
          <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 bg-pink"></span>Random Forest</span>
        </div>
      </div>
      <div class="grid grid-cols-[150px_1fr_50px] gap-x-3 gap-y-1 items-center text-[13px]">
        <template v-for="s in shap" :key="s.fitur">
          <span class="pt-1.5">{{ LABEL_FITUR[s.fitur] || s.fitur }}</span>
          <div class="h-2 bg-latar mt-1.5"><div class="h-2 bg-ungu" :style="{ width: (s.xgb / maxShap) * 100 + '%' }"></div></div>
          <strong class="text-right pt-1.5">{{ persen(s.xgb, 1) }}</strong>
          <span></span>
          <div class="h-2 bg-latar"><div class="h-2 bg-pink" :style="{ width: (s.rf / maxShap) * 100 + '%' }"></div></div>
          <span class="text-right">{{ persen(s.rf, 1) }}</span>
        </template>
      </div>
    </section>
  </template>
</template>
