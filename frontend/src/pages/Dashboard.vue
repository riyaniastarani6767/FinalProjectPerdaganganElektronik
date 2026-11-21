<script setup>
import { computed, onMounted, ref } from 'vue'
import { api, store, desimal, euro, persen, ribuan } from '../api'
import LineChart from '../components/LineChart.vue'
import BarChart from '../components/BarChart.vue'
import DonutChart from '../components/DonutChart.vue'

const d = ref(null)
const error = ref('')
const WARNA_CHANNEL = ['#6C4CF1', '#A48DF8', '#E85D9A', '#F2B935', '#1F1D2B']
const SKALA = ['#EEEAFE', '#CFC3FB', '#A48DF8', '#7B5CF3', '#4A2DC4']

onMounted(async () => {
  try {
    d.value = await api.dashboard()
    store.dataset = d.value.dataset
  } catch (e) { error.value = e.message }
})

const kpi = computed(() => d.value?.kpi)
const hotelText = computed(() => (kpi.value?.hotel || []).map((h) => `${h.nama.replace(' Hotel', '')} ${desimal(h.persen, 0)}%`).join(' · '))
const maxSeg = computed(() => Math.max(...(d.value?.segmen || []).map((s) => s.persen_batal), 1))
const maxLead = computed(() => Math.max(...(d.value?.lead || []).map((s) => s.persen_batal), 1))
const maxNeg = computed(() => Math.max(...(d.value?.negara || []).map((s) => s.jumlah), 1))
const semuaHeat = computed(() => (d.value?.heatmap.baris || []).flatMap((b) => b.nilai).filter((v) => v != null))
function warnaHeat(v) {
  if (v == null) return { background: '#F7F7F9' }
  const lo = Math.min(...semuaHeat.value), hi = Math.max(...semuaHeat.value)
  const i = Math.min(4, Math.floor(((v - lo) / Math.max(hi - lo, 1)) * 5))
  return { background: SKALA[i], color: i >= 3 ? '#fff' : '#1F1D2B', fontWeight: i >= 4 ? 600 : 400 }
}
const ribuK = (v) => ribuan(v)
const cetak = () => window.print()
const xgb = computed(() => d.value?.model.find((m) => m.kode === 'xgboost'))
const rf = computed(() => d.value?.model.find((m) => m.kode === 'random_forest'))
</script>

<template>
  <div class="flex flex-wrap justify-between items-end gap-3 pb-4 border-b border-[#E1DCF5]">
    <div class="flex flex-col gap-1.5">
      <h1 class="text-[32px] font-normal">Dashboard Pembatalan Reservasi</h1>
      <span class="text-[13px] text-teks-redup">Data aktif: <strong class="text-teks">{{ d?.dataset.nama_file }}</strong> · {{ ribuan(kpi?.total) }} reservasi setelah pembersihan data</span>
    </div>
    <button class="btn-ungu print:hidden" @click="cetak">Ekspor laporan</button>
  </div>

  <p v-if="error" class="kartu text-pink-tua">{{ error }}</p>
  <p v-else-if="!d" class="kartu text-teks-redup">Memuat dashboard...</p>

  <template v-else>
    <!-- KPI -->
    <section class="grid grid-cols-[repeat(auto-fit,minmax(190px,1fr))] gap-4">
      <div class="kartu border-t-4 border-ungu flex flex-col gap-1">
        <span class="text-xs text-teks-sedang">Total reservasi</span><strong class="text-[26px]">{{ ribuan(kpi.total) }}</strong>
        <span class="sub">{{ hotelText }}</span>
      </div>
      <div class="kartu border-t-4 border-ungu flex flex-col gap-1">
        <span class="text-xs text-teks-sedang">Reservasi batal</span><strong class="text-[26px]">{{ ribuan(kpi.batal) }}</strong>
        <span class="text-xs font-semibold text-pink-tua">{{ persen(kpi.persen_batal, 1) }} dari total</span>
      </div>
      <div class="kartu border-t-4 border-ungu flex flex-col gap-1">
        <span class="text-xs text-teks-sedang">Rata-rata ADR</span><strong class="text-[26px]">{{ euro(kpi.adr) }}</strong>
        <span class="sub">per kamar per malam</span>
      </div>
      <div class="kartu border-t-4 border-ungu flex flex-col gap-1">
        <span class="text-xs text-teks-sedang">Pendapatan hilang</span><strong class="text-[26px]">{{ euro(kpi.hilang) }}</strong>
        <span class="text-xs font-semibold text-pink-tua">{{ persen(kpi.persen_hilang, 1) }} dari potensi</span>
      </div>
      <div class="kartu border-t-4 border-ungu flex flex-col gap-1">
        <span class="text-xs text-teks-sedang">Rata-rata lead time</span><strong class="text-[26px]">{{ desimal(kpi.lead, 1) }} hari</strong>
        <span class="sub">pesan sebelum datang</span>
      </div>
    </section>

    <!-- Hasil model -->
    <section class="kartu flex flex-col gap-3.5">
      <div class="flex flex-wrap justify-between items-center gap-2">
        <div>
          <h2 class="judul-kartu">Hasil model: XGBoost vs Random Forest</h2>
          <span class="sub">Diuji pada {{ ribuan(d.data_uji) }} data uji · model terbaik dipilih dari F1-score tertinggi</span>
        </div>
        <RouterLink to="/evaluasi" class="text-[13px] font-semibold text-ungu">Lihat evaluasi lengkap</RouterLink>
      </div>
      <div class="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
        <div v-for="(m, i) in [xgb, rf]" :key="i" class="rounded-lg p-5 flex flex-col gap-3"
          :class="i === 0 ? 'bg-ungu text-white' : 'bg-pink-muda text-pink-gelap'">
          <div class="flex justify-between items-center gap-2">
            <strong class="text-xl">{{ m.nama }}</strong>
            <span class="px-2.5 py-1 rounded bg-white text-xs font-bold" :class="i === 0 ? 'text-ungu' : 'text-pink-tua'">
              {{ m.terbaik ? 'MODEL TERBAIK' : 'PEMBANDING' }}
            </span>
          </div>
          <div class="grid grid-cols-4 gap-2">
            <div v-for="[k, label] in [['accuracy', 'Accuracy'], ['precision', 'Precision'], ['recall', 'Recall'], ['f1', 'F1-score']]" :key="k" class="flex flex-col">
              <span class="text-[11px] opacity-80">{{ label }}</span>
              <strong class="text-lg">{{ persen(m[k]) }}</strong>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Tren + status -->
    <section class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <div class="kartu xl:col-span-2 min-w-0 flex flex-col gap-2">
        <div class="flex flex-wrap justify-between gap-2">
          <div><h2 class="judul-kartu">Tren reservasi dan pembatalan per bulan</h2><span class="sub">Arahkan kursor ke titik untuk melihat angkanya</span></div>
          <div class="flex gap-4 text-xs text-teks-sedang">
            <span class="flex items-center gap-1.5"><span class="w-3.5 h-[3px] bg-ungu"></span>Total reservasi</span>
            <span class="flex items-center gap-1.5"><span class="w-3.5 h-[3px] bg-pink"></span>Batal</span>
          </div>
        </div>
        <LineChart :labels="d.tren.label" :series="[{ name: 'Total', color: '#6C4CF1', values: d.tren.total, area: true }, { name: 'Batal', color: '#E85D9A', values: d.tren.batal, area: true }]" aria="Tren reservasi dan pembatalan" />
      </div>
      <div class="kartu flex flex-col gap-3">
        <h2 class="judul-kartu">Status reservasi</h2>
        <div class="flex justify-center">
          <DonutChart :segments="[{ label: 'Batal', value: kpi.batal, color: '#E85D9A' }, { label: 'Tidak batal', value: kpi.total - kpi.batal, color: '#6C4CF1' }]" :center="persen(kpi.persen_batal, 1)" sub="batal" />
        </div>
        <div class="flex justify-between text-[13px]"><span class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-sm bg-pink"></span>Batal</span><strong>{{ ribuan(kpi.batal) }}</strong></div>
        <div class="flex justify-between text-[13px]"><span class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-sm bg-ungu"></span>Tidak batal</span><strong>{{ ribuan(kpi.total - kpi.batal) }}</strong></div>
      </div>
    </section>

    <!-- Pendapatan + channel -->
    <section class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <div class="kartu xl:col-span-2 min-w-0 flex flex-col gap-2">
        <div class="flex flex-wrap justify-between gap-2">
          <h2 class="judul-kartu">Pendapatan terealisasi vs hilang per bulan (ribu €)</h2>
          <div class="flex gap-4 text-xs text-teks-sedang">
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 bg-ungu"></span>Terealisasi</span>
            <span class="flex items-center gap-1.5"><span class="w-2.5 h-2.5 bg-[#F4A6C6]"></span>Hilang karena batal</span>
          </div>
        </div>
        <BarChart :labels="d.tren.label" :series="[{ name: 'Terealisasi', color: '#6C4CF1', values: d.tren.realisasi }, { name: 'Hilang', color: '#F4A6C6', values: d.tren.hilang }]" :format="ribuK" aria="Pendapatan terealisasi dan hilang per bulan" />
      </div>
      <div class="kartu flex flex-col gap-3">
        <h2 class="judul-kartu">Channel distribusi</h2>
        <div class="flex justify-center">
          <DonutChart :segments="d.channel.map((c, i) => ({ label: c.nama, value: c.porsi, color: WARNA_CHANNEL[i % 5] }))" :center="persen(d.channel[0].porsi, 1)" :sub="'lewat ' + d.channel[0].nama" />
        </div>
        <div class="grid grid-cols-[1fr_auto_auto] gap-x-3 gap-y-2 text-[13px]">
          <span class="text-[11px] text-teks-redup">Channel</span><span class="text-[11px] text-teks-redup">Porsi</span><span class="text-[11px] text-teks-redup">Batal</span>
          <template v-for="(c, i) in d.channel" :key="c.nama">
            <span class="flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-sm" :style="{ background: WARNA_CHANNEL[i % 5] }"></span>{{ c.nama }}</span>
            <span>{{ persen(c.porsi, 1) }}</span><strong>{{ persen(c.persen_batal, 1) }}</strong>
          </template>
        </div>
      </div>
    </section>

    <!-- Heatmap -->
    <section class="kartu flex flex-col gap-3.5">
      <div class="flex flex-wrap justify-between items-center gap-2">
        <div><h2 class="judul-kartu">Pola musiman: tingkat pembatalan per bulan kedatangan (%)</h2><span class="sub">Warna semakin gelap berarti pembatalan semakin tinggi</span></div>
        <div class="flex items-center gap-1 text-xs text-teks-redup">Rendah <span v-for="c in SKALA" :key="c" class="w-5 h-3" :style="{ background: c }"></span> Tinggi</div>
      </div>
      <div class="overflow-x-auto">
        <div class="min-w-[760px] grid grid-cols-[110px_repeat(12,minmax(0,1fr))] gap-1 text-[13px] text-center">
          <span></span><span v-for="b in d.heatmap.bulan" :key="b" class="text-xs text-teks-redup">{{ b }}</span>
          <template v-for="row in d.heatmap.baris" :key="row.hotel">
            <span class="text-left font-semibold self-center">{{ row.hotel }}</span>
            <span v-for="(v, i) in row.nilai" :key="i" class="py-3 rounded" :style="warnaHeat(v)">{{ v == null ? '-' : desimal(v, 0) }}</span>
          </template>
        </div>
      </div>
    </section>

    <!-- Negara, segmen, lead time -->
    <section class="grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
      <div class="kartu flex flex-col gap-3">
        <h2 class="judul-kartu">Top 5 negara asal tamu</h2>
        <div v-for="n in d.negara" :key="n.kode" class="flex flex-col gap-1 text-[13px]">
          <div class="flex justify-between gap-2"><span><span class="text-[11px] text-teks-redup w-9 inline-block">{{ n.kode }}</span>{{ n.nama }}</span><strong>{{ ribuan(n.jumlah) }}</strong></div>
          <div class="flex items-center gap-2 pl-9">
            <div class="flex-1 h-1.5 bg-ungu-muda rounded"><div class="h-1.5 bg-ungu rounded" :style="{ width: (n.jumlah / maxNeg) * 100 + '%' }"></div></div>
            <span class="text-[11px] w-20 text-right" :class="n.persen_batal >= kpi.persen_batal ? 'text-pink-tua' : 'text-teks-redup'">{{ persen(n.persen_batal, 1) }} batal</span>
          </div>
        </div>
      </div>
      <div class="kartu flex flex-col gap-3">
        <h2 class="judul-kartu">Pembatalan per segmen pasar</h2>
        <div class="grid grid-cols-[100px_1fr_48px] gap-3 items-center text-[13px]">
          <template v-for="(s, i) in d.segmen" :key="s.nama">
            <span>{{ s.nama }}</span>
            <div class="h-3.5 bg-latar rounded-sm"><div class="h-3.5 rounded-sm" :style="{ width: (s.persen_batal / maxSeg) * 100 + '%', background: i < 2 ? (i === 0 ? '#E85D9A' : '#F08BB6') : '#A48DF8' }"></div></div>
            <strong class="text-right">{{ persen(s.persen_batal, 1) }}</strong>
          </template>
        </div>
      </div>
      <div class="kartu flex flex-col gap-3">
        <h2 class="judul-kartu">Pembatalan per lead time</h2>
        <div class="grid grid-cols-5 gap-2 items-end h-[150px]">
          <div v-for="(l, i) in d.lead" :key="l.kelompok" class="flex flex-col items-center gap-1">
            <span class="text-[11px] font-semibold">{{ desimal(l.persen_batal, 1) }}</span>
            <div class="w-full rounded-t-sm" :style="{ height: (l.persen_batal / maxLead) * 120 + 'px', background: SKALA[Math.min(i, 4)] === '#EEEAFE' ? '#CFC3FB' : SKALA[Math.min(i, 4)] }"></div>
          </div>
        </div>
        <div class="grid grid-cols-5 gap-2 text-center text-[11px] text-teks-redup"><span v-for="l in d.lead" :key="l.kelompok">{{ l.kelompok }}</span></div>
        <span class="sub">Hari antara pemesanan dan kedatangan · angka = % batal</span>
      </div>
    </section>

    <!-- Insight -->
    <section class="bg-ungu text-white rounded-lg px-6 py-5 grid grid-cols-[repeat(auto-fit,minmax(240px,1fr))] gap-5">
      <div v-for="(t, i) in d.insight" :key="i" class="flex flex-col gap-1.5">
        <span class="text-xs font-semibold text-ungu-terang">INSIGHT {{ i + 1 }}</span>
        <span class="text-sm leading-relaxed">{{ t }}</span>
      </div>
    </section>
  </template>
</template>
