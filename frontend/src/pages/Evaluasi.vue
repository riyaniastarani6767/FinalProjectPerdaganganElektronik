<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, desimal, LABEL_FITUR, persen, ribuan } from '../api'
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
const PENJELASAN = {
  accuracy: 'Persentase semua tebakan yang benar. Bisa menyesatkan karena data tidak seimbang.',
  precision: 'Dari yang ditebak batal, berapa persen yang benar-benar batal.',
  recall: 'Dari yang benar-benar batal, berapa persen yang tertangkap model.',
  f1: 'Rata-rata harmonis precision dan recall. Dasar pemilihan model terbaik.'
}

// gabungan fitur SHAP kedua model, urut dari model terbaik
const shap = computed(() => {
  if (!ev.value) return []
  const a = Object.fromEntries(xgb.value.shap.map((s) => [s.fitur, s.persen]))
  const b = Object.fromEntries(rf.value.shap.map((s) => [s.fitur, s.persen]))
  const urut = [...new Set([...terbaik.value.shap.map((s) => s.fitur), ...lain.value.shap.map((s) => s.fitur)])].slice(0, 8)
  return urut.map((f) => ({ fitur: f, xgb: a[f] ?? 0, rf: b[f] ?? 0 }))
})
const maxShap = computed(() => Math.max(...shap.value.flatMap((s) => [s.xgb, s.rf]), 1))

// selisih data latih dan data uji untuk cek overfitting / underfitting
const fit = computed(() => (ev.value ? [xgb.value, rf.value].map((m) => ({
  nama: m.nama, latih: m.latih, uji: m,
  selisih: m.latih ? m.latih.f1 - m.f1 : null
})) : []))
const statusFit = (s) => (s == null ? '-' : s <= 5 ? 'Good fit' : 'Cenderung overfitting')

// parameter model, dikelompokkan menjadi pre-pruning, post-pruning, dan lainnya
const PRUNING = {
  xgboost: { pre: ['max_depth', 'min_child_weight'], post: ['gamma'] },
  random_forest: { pre: ['max_depth', 'min_samples_split', 'min_samples_leaf', 'max_features'], post: ['ccp_alpha'] }
}
const parameter = computed(() => (ev.value ? ['xgboost', 'random_forest'].map((k) => {
  const p = ev.value.model[k].parameter
  const { pre, post } = PRUNING[k]
  const ambil = (daftar) => daftar.filter((n) => n in p).map((n) => `${n} = ${p[n]}`)
  return {
    nama: ev.value.model[k].nama, pre: ambil(pre), post: ambil(post),
    lain: ambil(Object.keys(p).filter((n) => !pre.includes(n) && !post.includes(n)))
  }
}) : []))

// perbandingan pembagian data (split)
const splitBaris = computed(() => {
  if (!ev.value?.split) return []
  const urut = [...new Set(ev.value.split.map((s) => s.split))]
  return urut.map((s) => ({
    split: s,
    xgb: ev.value.split.find((r) => r.split === s && r.model === 'XGBoost'),
    rf: ev.value.split.find((r) => r.split === s && r.model === 'Random Forest')
  }))
})
</script>

<template>
  <div class="px-1">
    <h2 class="judul-halaman">Evaluasi Model</h2>
    <p class="sub mt-1 leading-relaxed">Hasil pengujian XGBoost dan Random Forest pada {{ ribuan(ev?.data.uji) }} data uji (20% data) · arahkan kursor ke angka atau grafik untuk penjelasannya</p>
  </div>

  <p v-if="error" class="kartu text-pink-tua">{{ error }}</p>
  <p v-else-if="!ev" class="kartu text-teks-redup">Memuat hasil evaluasi...</p>

  <template v-else>
    <section class="grid grid-cols-[repeat(auto-fit,minmax(340px,1fr))] gap-4">
      <div v-for="(m, i) in [xgb, rf]" :key="i" class="kartu flex flex-col gap-3.5 border-l-4" :class="i === 0 ? 'border-ungu' : 'border-pink'">
        <div class="flex justify-between items-center gap-2">
          <strong class="text-lg">{{ m.nama }}</strong>
          <span class="px-2.5 py-1 rounded-md text-xs font-semibold" :class="m === terbaik ? 'bg-ungu-muda text-ungu' : 'bg-pink-muda text-pink-tua'">
            {{ m === terbaik ? 'Model terbaik' : 'Pembanding' }}
          </span>
        </div>
        <div class="grid grid-cols-4 gap-2">
          <div v-for="[k, label] in METRIK" :key="k" v-tip="[label + ' ' + m.nama, persen(m[k]), PENJELASAN[k]]" class="flex flex-col rounded-lg bg-ungu-pucat px-3 py-2.5">
            <span class="text-xs text-teks-redup">{{ label }}</span><strong class="text-xl tabular-nums" :class="i === 0 ? 'text-ungu-gelap' : 'text-pink-gelap'">{{ persen(m[k]) }}</strong>
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

    <section class="kartu flex flex-col gap-3">
      <div>
        <h2 class="judul-kartu">Data latih vs data uji (cek overfitting dan underfitting)</h2>
        <span class="sub">Selisih kecil berarti model tidak menghafal data latih. Nilai yang tetap jauh di atas baseline berarti model tidak underfitting.</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[620px] text-sm tabular-nums">
          <thead><tr class="text-left text-xs text-teks-redup">
            <th class="px-2 py-2.5 font-medium border-b border-garis">Model</th>
            <th class="px-2 py-2.5 font-medium border-b border-garis text-right">Accuracy latih</th>
            <th class="px-2 py-2.5 font-medium border-b border-garis text-right">Accuracy uji</th>
            <th class="px-2 py-2.5 font-medium border-b border-garis text-right">F1 latih</th>
            <th class="px-2 py-2.5 font-medium border-b border-garis text-right">F1 uji</th>
            <th class="px-2 py-2.5 font-medium border-b border-garis text-right">Selisih F1</th>
            <th class="px-2 py-2.5 font-medium border-b border-garis">Kesimpulan</th>
          </tr></thead>
          <tbody>
            <tr v-for="f in fit" :key="f.nama">
              <td class="px-2 py-2.5 border-b border-[#F3F2F7]">{{ f.nama }}</td>
              <td class="px-2 py-2.5 border-b border-[#F3F2F7] text-right">{{ persen(f.latih?.accuracy) }}</td>
              <td class="px-2 py-2.5 border-b border-[#F3F2F7] text-right">{{ persen(f.uji.accuracy) }}</td>
              <td class="px-2 py-2.5 border-b border-[#F3F2F7] text-right">{{ persen(f.latih?.f1) }}</td>
              <td class="px-2 py-2.5 border-b border-[#F3F2F7] text-right">{{ persen(f.uji.f1) }}</td>
              <td class="px-2 py-2.5 border-b border-[#F3F2F7] text-right">{{ f.selisih == null ? '-' : desimal(f.selisih) + ' poin' }}</td>
              <td class="px-2 py-2.5 border-b border-[#F3F2F7] font-semibold text-ungu-tua"><span v-tip="[statusFit(f.selisih), `Selisih F1 latih dan uji ${desimal(f.selisih)} poin`, 'Batas good fit: selisih paling besar 5 poin']">{{ statusFit(f.selisih) }}</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <div v-for="p in parameter" :key="p.nama" class="kartu flex flex-col gap-3 min-w-0 text-sm">
        <h2 class="judul-kartu">Parameter dan pruning {{ p.nama }}</h2>
        <div class="flex flex-col gap-1"><span class="sub">Pre-pruning (membatasi saat pohon dibangun)</span><span class="tabular-nums">{{ p.pre.join(' · ') }}</span></div>
        <div class="flex flex-col gap-1"><span class="sub">Post-pruning (memangkas setelah pohon jadi)</span><span class="tabular-nums">{{ p.post.join(' · ') }}</span></div>
        <div class="flex flex-col gap-1"><span class="sub">Parameter lain</span><span class="tabular-nums">{{ p.lain.join(' · ') }}</span></div>
      </div>
    </section>

    <section class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <div v-for="m in [xgb, rf]" :key="m.nama" class="kartu flex flex-col gap-3.5 min-w-0">
        <h2 class="judul-kartu">Confusion matrix {{ m.nama }}</h2>
        <ConfusionMatrix :tn="m.tn" :fp="m.fp" :fn="m.fn" :tp="m.tp" />
      </div>
    </section>

    <section v-if="splitBaris.length" class="kartu flex flex-col gap-3">
      <div>
        <h2 class="judul-kartu">Pengaruh pembagian data latih dan uji</h2>
        <span class="sub">Kedua model dilatih ulang dengan parameter yang sama. F1 yang stabil berarti hasil tidak bergantung pada satu cara pembagian data.</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full min-w-[620px] text-sm tabular-nums">
          <thead><tr class="text-left text-xs text-teks-redup">
            <th class="px-2 py-2.5 font-medium border-b border-garis">Latih : uji</th>
            <th class="px-2 py-2.5 font-medium border-b border-garis text-right">Jumlah data uji</th>
            <th class="px-2 py-2.5 font-medium border-b border-garis text-right">Accuracy XGBoost</th>
            <th class="px-2 py-2.5 font-medium border-b border-garis text-right">F1 XGBoost</th>
            <th class="px-2 py-2.5 font-medium border-b border-garis text-right">Accuracy Random Forest</th>
            <th class="px-2 py-2.5 font-medium border-b border-garis text-right">F1 Random Forest</th>
          </tr></thead>
          <tbody>
            <tr v-for="s in splitBaris" :key="s.split" :class="s.split === '80:20' ? 'bg-ungu-pucat font-semibold' : ''">
              <td class="px-2 py-2.5 border-b border-[#F3F2F7]">{{ s.split }}{{ s.split === '80:20' ? ' (dipakai)' : '' }}</td>
              <td class="px-2 py-2.5 border-b border-[#F3F2F7] text-right">{{ ribuan(s.xgb?.data_uji) }}</td>
              <td class="px-2 py-2.5 border-b border-[#F3F2F7] text-right">{{ persen(s.xgb?.accuracy) }}</td>
              <td class="px-2 py-2.5 border-b border-[#F3F2F7] text-right">{{ persen(s.xgb?.f1) }}</td>
              <td class="px-2 py-2.5 border-b border-[#F3F2F7] text-right">{{ persen(s.rf?.accuracy) }}</td>
              <td class="px-2 py-2.5 border-b border-[#F3F2F7] text-right">{{ persen(s.rf?.f1) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="kartu flex flex-col gap-3">
      <div class="flex flex-wrap justify-between gap-2">
        <div><h2 class="judul-kartu">Fitur paling berpengaruh (SHAP)</h2><span class="sub">Persen dari total pengaruh pada prediksi</span></div>
        <div class="flex gap-4 text-xs text-teks-sedang">
          <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-sm bg-ungu"></span>XGBoost</span>
          <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 rounded-sm bg-pink"></span>Random Forest</span>
        </div>
      </div>
      <div class="grid grid-cols-[150px_1fr_50px] gap-x-3 gap-y-1 items-center text-[13px]">
        <template v-for="s in shap" :key="s.fitur">
          <div class="contents" v-tip="[LABEL_FITUR[s.fitur] || s.fitur, `XGBoost: ${persen(s.xgb, 1)} dari total pengaruh`, `Random Forest: ${persen(s.rf, 1)} dari total pengaruh`, 'Dihitung dari rata-rata nilai SHAP mutlak pada 200 data uji']">
            <span class="pt-1.5">{{ LABEL_FITUR[s.fitur] || s.fitur }}</span>
            <div class="h-2 bg-ungu-pucat rounded mt-1.5"><div class="h-2 bg-ungu rounded" :style="{ width: (s.xgb / maxShap) * 100 + '%' }"></div></div>
            <strong class="text-right pt-1.5">{{ persen(s.xgb, 1) }}</strong>
            <span></span>
            <div class="h-2 bg-ungu-pucat rounded"><div class="h-2 bg-pink rounded" :style="{ width: (s.rf / maxShap) * 100 + '%' }"></div></div>
            <span class="text-right">{{ persen(s.rf, 1) }}</span>
          </div>
        </template>
      </div>
    </section>
  </template>
</template>
