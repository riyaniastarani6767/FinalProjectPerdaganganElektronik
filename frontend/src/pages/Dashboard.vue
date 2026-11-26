<script setup>
import { computed, onActivated, onMounted, ref } from 'vue'
import { api, store, desimal, persen, ribuan } from '../api'
import LineChart from '../components/LineChart.vue'
import BarChart from '../components/BarChart.vue'
import PieChart from '../components/PieChart.vue'

const d = ref(null)
const error = ref('')
const SKALA = ['#F3F0F8', '#DCD4EC', '#B9ACD8', '#8D79BE', '#4E3A86']
const WARNA_LEAD = ['#D9D2EA', '#B9ACD8', '#9481C2', '#6E58A6', '#4E3A86']
const BULAN = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

async function muat() {
  try {
    d.value = await api.dashboard()
    store.dataset = d.value.dataset
    error.value = ''
  } catch (e) { error.value = e.message }
}
onMounted(muat)
// saat kembali ke Dashboard, data lama tetap tampil sambil diperbarui (misalnya setelah unggah data baru)
let pertama = true
onActivated(() => { if (pertama) { pertama = false; return } muat() })

const kpi = computed(() => d.value?.kpi)
// "Jul 15" -> "Juli 2015"
const PENDEK = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
const panjang = (lbl) => { const [b, t] = lbl.split(' '); return `${BULAN[PENDEK.indexOf(b)]} 20${t}` }
const periode = computed(() => {
  const l = d.value?.tren.label || []
  return l.length ? `${panjang(l[0])} sampai ${panjang(l[l.length - 1])}` : ''
})

const ikon = {
  total: 'M3 21h18M5 21V7l7-4 7 4v14M9 21v-5h6v5',
  batal: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM15 9l-6 6M9 9l6 6',
  adr: 'M17 7.5A6 6 0 1 0 17 16.5M4 10.5h9M4 13.5h9',
  hilang: 'M3 7l6 6 4-4 8 8M21 11v6h-6',
  lead: 'M5 5h14a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2zM16 3v4M8 3v4M3 11h18'
}
const tiles = computed(() => {
  const k = kpi.value
  return [
    { i: 'total', nilai: ribuan(k.total), label: 'Total reservasi', tip: ['Total reservasi', ...k.hotel.map((h) => `${h.nama}: ${ribuan(h.jumlah)} (${desimal(h.persen, 0)}%)`), 'Setelah data dibersihkan'] },
    { i: 'batal', nilai: ribuan(k.batal), label: `Batal (${desimal(k.persen_batal, 1)}%)`, pink: true, tip: ['Reservasi batal', `${ribuan(k.batal)} dari ${ribuan(k.total)} reservasi`, ...k.hotel.map((h) => `${h.nama}: ${ribuan(h.batal)} batal (${desimal(h.persen_batal, 1)}%)`)] },
    { i: 'adr', nilai: '€' + desimal(k.adr, 2), label: 'ADR per malam', tip: ['ADR (Average Daily Rate)', 'Rata-rata harga kamar per malam', 'dari semua reservasi'] },
    { i: 'hilang', nilai: '€' + desimal(k.hilang / 1e6, 2) + ' jt', label: `Hilang (${desimal(k.persen_hilang, 1)}% potensi)`, pink: true, tip: ['Pendapatan hilang', 'ADR × jumlah malam dari reservasi yang batal', `€${ribuan(k.hilang)} dari potensi €${ribuan(k.hilang + k.realisasi)}`] },
    { i: 'lead', nilai: desimal(k.lead, 1) + ' hari', label: 'Lead time rata-rata', tip: ['Lead time', 'Jarak hari antara pemesanan dan kedatangan', `Rata-rata ${desimal(k.lead, 1)} hari`] }
  ]
})

const maxNeg = computed(() => Math.max(...(d.value?.negara || []).map((n) => n.jumlah), 1))
const maxBatal = computed(() => Math.max(...[...(d.value?.channel || []), ...(d.value?.segmen || [])].map((s) => s.persen_batal), 1))
const maxLead = computed(() => Math.max(...(d.value?.lead || []).map((l) => l.persen_batal), 1))

const semuaHeat = computed(() => (d.value?.heatmap.baris || []).flatMap((b) => b.nilai).filter((v) => v != null))
function warnaHeat(v) {
  if (v == null) return { background: '#F6F4F9' }
  const lo = Math.min(...semuaHeat.value), hi = Math.max(...semuaHeat.value)
  const i = Math.min(4, Math.floor(((v - lo) / Math.max(hi - lo, 1)) * 5))
  return { background: SKALA[i], color: i >= 3 ? '#fff' : '#1E1B24' }
}
const cetak = () => window.print()
</script>

<template>
  <div class="flex flex-col gap-4">
  <div class="flex flex-wrap justify-between items-center gap-3 px-1">
    <div>
      <h2 class="judul-halaman">Dashboard Pembatalan Reservasi</h2>
      <p class="sub mt-1 leading-relaxed">Ringkasan {{ ribuan(kpi?.total) }} reservasi City Hotel dan Resort Hotel dengan tanggal kedatangan {{ periode }}. Arahkan kursor ke grafik untuk melihat rinciannya.</p>
    </div>
    <button class="btn-garis print:hidden" @click="cetak">Ekspor laporan</button>
  </div>

  <p v-if="error" class="kartu text-pink-tua">{{ error }}</p>
  <p v-else-if="!d" class="kartu text-teks-redup">Memuat dashboard...</p>

  <template v-else>
    <!-- Ringkasan -->
    <section class="kartu">
      <div class="flex justify-between items-baseline gap-3 mb-3.5"><h3 class="judul-kartu">Ringkasan</h3><span class="sub">Dihitung dari data aktif setelah pembersihan</span></div>
      <div class="grid grid-cols-1 min-[430px]:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
        <div v-for="t in tiles" :key="t.i" v-tip="t.tip" class="border border-garis rounded-xl px-3.5 py-3 flex gap-3 items-center hover:border-ungu-garis transition-colors">
          <span class="w-10 h-10 rounded-[10px] grid place-items-center shrink-0" :class="t.pink ? 'bg-pink-muda text-pink' : 'bg-ungu-muda text-ungu'">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path :d="ikon[t.i]" /></svg>
          </span>
          <div class="min-w-0"><strong class="block text-[19px] font-bold tabular-nums">{{ t.nilai }}</strong><span class="text-xs text-teks-redup">{{ t.label }}</span></div>
        </div>
      </div>
    </section>

    <div class="grid grid-cols-1 xl:grid-cols-[1fr_1fr_1.15fr] gap-4">
      <!-- Model -->
      <section class="kartu flex flex-col gap-2.5">
        <div class="flex justify-between items-baseline gap-2"><h3 class="judul-kartu">Model prediksi</h3><span class="sub">F1-score data uji</span></div>
        <div v-for="m in d.model" :key="m.kode"
          v-tip="[m.nama + (m.terbaik ? ' (model terbaik)' : ''), `Accuracy ${persen(m.accuracy)}`, `Precision ${persen(m.precision)}`, `Recall ${persen(m.recall)}`, `F1-score ${persen(m.f1)}`, `Diuji pada ${ribuan(d.data_uji)} data uji`]"
          class="flex justify-between items-center px-3 py-2.5 rounded-[10px]" :class="m.terbaik ? 'bg-ungu-muda' : 'bg-ungu-pucat'">
          <span class="font-semibold text-[13.5px]">{{ m.nama }}<span v-if="m.terbaik" class="ml-1.5 text-[11px] text-ungu">Terbaik</span></span>
          <span class="text-lg font-bold tabular-nums"><span class="text-[11px] text-teks-redup font-medium mr-1">F1</span>{{ persen(m.f1) }}</span>
        </div>
        <p class="sub leading-relaxed">Model terbaik dipilih dari F1-score tertinggi karena data tidak seimbang.</p>
        <RouterLink to="/prediksi" class="text-[12.5px] font-semibold text-ungu">Lihat pengujian model →</RouterLink>
      </section>

      <!-- Status -->
      <section class="kartu flex flex-col gap-3">
        <h3 class="judul-kartu">Status reservasi</h3>
        <div class="flex items-center gap-5 flex-wrap">
          <PieChart :segments="[{ label: 'Batal', value: kpi.batal, color: '#E7C3D1', teks: '#7A1F45' }, { label: 'Tidak batal', value: kpi.total - kpi.batal, color: '#4E3A86' }]" />
          <div class="flex flex-col gap-2.5 text-[12.5px]">
            <div><span class="flex items-center gap-1.5 text-teks-redup"><i class="w-[9px] h-[9px] rounded-sm bg-[#E7C3D1]"></i>Batal</span><strong class="text-[15px] tabular-nums">{{ ribuan(kpi.batal) }}</strong></div>
            <div><span class="flex items-center gap-1.5 text-teks-redup"><i class="w-[9px] h-[9px] rounded-sm bg-ungu"></i>Tidak batal</span><strong class="text-[15px] tabular-nums">{{ ribuan(kpi.total - kpi.batal) }}</strong></div>
            <div v-for="h in kpi.hotel" :key="h.nama" v-tip="[h.nama, `${ribuan(h.jumlah)} reservasi`, `${ribuan(h.batal)} batal (${desimal(h.persen_batal, 1)}%)`]">
              <span class="text-teks-redup">{{ h.nama }}</span><strong class="block text-[14px]">{{ desimal(h.persen_batal, 1) }}% batal</strong>
            </div>
          </div>
        </div>
      </section>

      <!-- Daftar batang kanan -->
      <section class="kartu xl:row-span-2 flex flex-col">
        <div class="flex justify-between items-baseline gap-2 mb-3"><h3 class="judul-kartu">Negara asal tamu</h3><span class="sub">5 teratas</span></div>
        <div class="grid grid-cols-[92px_1fr_52px] gap-x-2.5 gap-y-2 items-center text-[12.5px]">
          <template v-for="n in d.negara" :key="n.kode">
            <div class="contents" v-tip="[`${n.nama} (${n.kode})`, `${ribuan(n.jumlah)} reservasi (${desimal((n.jumlah / kpi.total) * 100, 1)}% dari total)`, `Tingkat batal ${desimal(n.persen_batal, 1)}%`]">
              <span class="truncate">{{ n.nama }}</span>
              <div class="h-2 bg-ungu-pucat rounded"><div class="h-2 bg-ungu rounded" :style="{ width: (n.jumlah / maxNeg) * 100 + '%' }"></div></div>
              <span class="text-right font-semibold tabular-nums">{{ ribuan(n.jumlah) }}</span>
            </div>
          </template>
        </div>
        <p class="sub mt-5 mb-2.5 pt-3.5 border-t border-garis">Channel distribusi · tingkat batal</p>
        <div class="grid grid-cols-[92px_1fr_52px] gap-x-2.5 gap-y-2 items-center text-[12.5px]">
          <template v-for="c in d.channel" :key="c.nama">
            <div class="contents" v-tip="[`Channel ${c.nama}`, `Porsi ${desimal(c.porsi, 1)}% dari reservasi`, `Tingkat batal ${desimal(c.persen_batal, 1)}%`]">
              <span class="truncate">{{ c.nama }}</span>
              <div class="h-2 bg-ungu-pucat rounded"><div class="h-2 bg-pink rounded" :style="{ width: (c.persen_batal / maxBatal) * 100 + '%' }"></div></div>
              <span class="text-right font-semibold tabular-nums">{{ persen(c.persen_batal, 1) }}</span>
            </div>
          </template>
        </div>
        <p class="sub mt-5 mb-2.5 pt-3.5 border-t border-garis">Segmen pasar · tingkat batal</p>
        <div class="grid grid-cols-[92px_1fr_52px] gap-x-2.5 gap-y-2 items-center text-[12.5px]">
          <template v-for="s in d.segmen" :key="s.nama">
            <div class="contents" v-tip="[`Segmen ${s.nama}`, `${ribuan(s.jumlah)} reservasi (${desimal((s.jumlah / kpi.total) * 100, 1)}% dari total)`, `Tingkat batal ${desimal(s.persen_batal, 1)}%`]">
              <span class="truncate">{{ s.nama }}</span>
              <div class="h-2 bg-ungu-pucat rounded"><div class="h-2 bg-pink rounded" :style="{ width: (s.persen_batal / maxBatal) * 100 + '%' }"></div></div>
              <span class="text-right font-semibold tabular-nums">{{ persen(s.persen_batal, 1) }}</span>
            </div>
          </template>
        </div>
      </section>

      <!-- Tren -->
      <section class="kartu xl:col-span-2 flex flex-col gap-2">
        <div class="flex flex-wrap justify-between items-baseline gap-2">
          <h3 class="judul-kartu">Tren reservasi dan pembatalan per bulan</h3>
          <div class="legenda"><span><i class="bg-ungu"></i>Total reservasi</span><span><i class="bg-pink"></i>Batal</span></div>
        </div>
        <LineChart :labels="d.tren.label" satuan=" reservasi" aria="Tren reservasi dan pembatalan per bulan"
          :series="[{ name: 'Total', color: '#4E3A86', values: d.tren.total, tag: 'Tertinggi' }, { name: 'Batal', color: '#C4547B', values: d.tren.batal, tag: 'Batal' }]" />
      </section>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[2fr_1.15fr] gap-4">
      <!-- Pendapatan -->
      <section class="kartu flex flex-col gap-2">
        <div class="flex flex-wrap justify-between items-baseline gap-2">
          <h3 class="judul-kartu">Pendapatan per bulan (ribu €)</h3>
          <div class="legenda"><span><i class="bg-ungu"></i>Terealisasi</span><span><i class="bg-pink-lembut"></i>Hilang karena batal</span></div>
        </div>
        <BarChart :labels="d.tren.label" satuan=" ribu €" aria="Pendapatan terealisasi dan hilang per bulan"
          :series="[{ name: 'Terealisasi', color: '#4E3A86', values: d.tren.realisasi }, { name: 'Hilang karena batal', color: '#E7A9C0', values: d.tren.hilang }]" />
      </section>

      <!-- Lead time -->
      <section class="kartu flex flex-col">
        <div class="flex justify-between items-baseline gap-2 mb-3"><h3 class="judul-kartu">Pembatalan per lead time</h3><span class="sub">% batal</span></div>
        <div class="grid grid-cols-5 gap-3 items-end h-[170px] border-b border-garis">
          <div v-for="(l, i) in d.lead" :key="l.kelompok" class="flex flex-col items-center gap-1.5 h-full justify-end"
            v-tip="[`Lead time ${l.kelompok} hari`, `${ribuan(l.jumlah)} reservasi`, `Tingkat batal ${desimal(l.persen_batal, 1)}%`]">
            <span class="text-[11.5px] font-semibold">{{ desimal(l.persen_batal, 1) }}%</span>
            <div class="w-full rounded-t-[5px] transition-opacity hover:opacity-80" :style="{ height: (l.persen_batal / maxLead) * 130 + 'px', background: WARNA_LEAD[i] }"></div>
          </div>
        </div>
        <div class="grid grid-cols-5 gap-3 text-center text-[11px] text-teks-redup mt-1.5"><span v-for="l in d.lead" :key="l.kelompok">{{ l.kelompok }}</span></div>
        <p class="sub text-center mt-2">hari antara pemesanan dan kedatangan</p>
      </section>
    </div>

    <!-- Heatmap -->
    <section class="kartu flex flex-col gap-3.5">
      <div class="flex flex-wrap justify-between items-center gap-2">
        <h3 class="judul-kartu">Pola musiman: % batal per bulan kedatangan</h3>
        <div class="flex items-center gap-1 text-xs text-teks-redup">Rendah <span v-for="c in SKALA" :key="c" class="w-5 h-3 rounded-sm" :style="{ background: c }"></span> Tinggi</div>
      </div>
      <div class="overflow-x-auto">
        <div class="min-w-[720px] grid grid-cols-[96px_repeat(12,minmax(0,1fr))] gap-1 text-xs text-center">
          <span></span><span v-for="b in d.heatmap.bulan" :key="b" class="text-teks-redup pb-0.5">{{ b }}</span>
          <template v-for="row in d.heatmap.baris" :key="row.hotel">
            <span class="text-left font-medium self-center">{{ row.hotel }}</span>
            <span v-for="(v, i) in row.nilai" :key="i" v-tip="[`${row.hotel} · ${BULAN[i]}`, v == null ? 'Tidak ada data' : `Tingkat batal ${desimal(v, 0)}%`]"
              class="py-2.5 rounded-md tabular-nums hover:ring-2 hover:ring-ungu-garis" :style="warnaHeat(v)">{{ v == null ? '-' : desimal(v, 0) }}</span>
          </template>
        </div>
      </div>
    </section>

    <!-- Insight -->
    <section class="kartu">
      <div class="flex justify-between items-baseline gap-3 mb-3.5"><h3 class="judul-kartu">Insight</h3><span class="sub">Dibuat otomatis dari data aktif</span></div>
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div v-for="(t, i) in d.insight" :key="i" class="flex gap-3 text-[13px] leading-relaxed text-teks-sedang">
          <b class="w-6 h-6 shrink-0 rounded-full bg-ungu-muda text-ungu grid place-items-center text-xs">{{ i + 1 }}</b><p>{{ t }}</p>
        </div>
      </div>
    </section>
  </template>
  </div>
</template>
