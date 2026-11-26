<script setup>
import { computed, ref } from 'vue'
import { api, store, persen, ribuan } from '../api'

const langkah = ref(1)
const jenis = ref('')           // 'mentah' | 'bersih'
const inspeksi = ref(null)
const proses = ref(null)
const sibuk = ref('')
const error = ref('')
const seret = ref(false)
const inputFile = ref(null)

const daftar = computed(() => {
  const lewati = jenis.value === 'bersih'
  return [['Unggah file', 'Pilih CSV'], ['Preview', '10 data pertama'], ['Preprocessing', 'Bersihkan data'], ['Selesai', 'Siap dianalisis']]
    .map(([label, sub], i) => {
      const no = i + 1
      const skip = lewati && (no === 2 || no === 3)
      return { no: skip ? '–' : no, label, sub: skip ? 'Dilewati' : sub, aktif: no === langkah.value, selesai: no < langkah.value || (langkah.value === 4 && no === 4) }
    })
})
const dataset = computed(() => proses.value?.dataset || inspeksi.value?.dataset)

async function pilih(file) {
  if (!file) return
  error.value = ''
  if (!file.name.toLowerCase().endsWith('.csv')) { error.value = 'File harus berformat CSV.'; return }
  sibuk.value = 'Mengunggah dan membaca file...'
  try {
    inspeksi.value = await api.unggah(file)
    jenis.value = inspeksi.value.jenis
    if (jenis.value === 'bersih') {
      langkah.value = 4
      await store.muatStatus()
    } else {
      langkah.value = 2
    }
  } catch (e) { error.value = e.message } finally { sibuk.value = '' }
}

async function jalankanPreprocessing() {
  langkah.value = 3
  sibuk.value = 'Menjalankan preprocessing...'
  error.value = ''
  try {
    proses.value = await api.preprocess(inspeksi.value.dataset.id)
    await store.muatStatus()
  } catch (e) { error.value = e.message } finally { sibuk.value = '' }
}

function ulang() {
  langkah.value = 1; jenis.value = ''; inspeksi.value = null; proses.value = null; error.value = ''
}

async function kembaliBawaan() {
  await api.pakaiBawaan()
  await store.muatStatus()
  ulang()
}

const tampil = (v) => (v === null || v === undefined ? 'NaN' : v)
</script>

<template>
  <div class="flex flex-col gap-4">
  <div class="px-1">
    <h2 class="judul-halaman">Unggah Data</h2>
    <p class="sub mt-1 leading-relaxed">Unggah data reservasi, cek isinya, lalu bersihkan sebelum dipakai di Dashboard dan Prediksi</p>
  </div>

  <nav aria-label="Tahapan" class="kartu grid grid-cols-2 md:grid-cols-4 gap-3">
    <div v-for="s in daftar" :key="s.label" class="flex items-center gap-2.5 min-w-0">
      <span class="w-[34px] h-[34px] shrink-0 rounded-full flex items-center justify-center text-sm font-bold"
        :class="s.aktif || s.selesai ? 'bg-ungu text-white' : 'bg-ungu-muda text-teks-redup'">{{ s.no }}</span>
      <div class="flex flex-col min-w-0"><strong class="text-sm" :class="s.aktif ? 'text-ungu' : ''">{{ s.label }}</strong><span class="sub">{{ s.sub }}</span></div>
    </div>
  </nav>

  <p v-if="error" class="kartu text-pink-tua text-sm">{{ error }}</p>

  <!-- Langkah 1 -->
  <section v-if="langkah === 1" class="kartu p-7 flex flex-col gap-5">
    <h2 class="text-lg font-semibold">Langkah 1 · Unggah file</h2>
    <label class="min-h-[220px] border-2 border-dashed rounded-lg flex flex-col items-center justify-center gap-2.5 p-6 text-center cursor-pointer transition-colors"
      :class="seret ? 'border-ungu bg-ungu-muda' : 'border-ungu-garis bg-ungu-pucat'"
      @dragover.prevent="seret = true" @dragleave="seret = false" @drop.prevent="seret = false; pilih($event.dataTransfer.files[0])">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#4E3A86" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 16V4M7 9l5-5 5 5M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" /></svg>
      <strong class="text-base">{{ sibuk || 'Tarik file CSV ke sini atau klik untuk memilih file' }}</strong>
      <span class="text-[13px] text-teks-redup">Bisa data mentah (format Hotel Booking, 32 kolom) atau data yang sudah dipreprocessing</span>
      <input ref="inputFile" type="file" accept=".csv" class="sr-only" :disabled="!!sibuk" @change="pilih($event.target.files[0])" />
    </label>
    <button v-if="store.dataset?.id" class="self-start text-sm underline text-teks-sedang" @click="kembaliBawaan">Kembali ke data bawaan</button>
  </section>

  <!-- Langkah 2 -->
  <section v-if="langkah === 2 && inspeksi" class="kartu p-7 flex flex-col gap-4">
    <div class="flex flex-wrap justify-between items-end gap-3">
      <div>
        <h2 class="text-lg font-semibold">Langkah 2 · Preview 10 data pertama</h2>
        <span class="text-[13px] text-teks-redup">{{ inspeksi.dataset.nama_file }} · <strong class="text-teks">{{ ribuan(inspeksi.baris) }} baris · {{ inspeksi.kolom }} kolom</strong> · ditampilkan {{ inspeksi.preview_kolom.length }} kolom utama</span>
      </div>
      <span class="px-3 py-1.5 rounded bg-pink-muda text-pink-tua text-[13px] font-semibold">Terdeteksi data mentah: perlu preprocessing</span>
    </div>
    <div class="overflow-x-auto border border-garis rounded-md">
      <table class="w-full min-w-[1100px] text-xs tabular-nums">
        <thead><tr class="bg-ungu-pucat text-left"><th v-for="k in inspeksi.preview_kolom" :key="k" class="px-2 py-2.5 font-semibold">{{ k }}</th></tr></thead>
        <tbody>
          <tr v-for="(r, i) in inspeksi.preview" :key="i" class="border-t border-[#F3F2F7]">
            <td v-for="(v, j) in r" :key="j" class="px-2 py-2" :class="v === null ? 'bg-pink-muda' : ''">{{ tampil(v) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="grid grid-cols-[repeat(auto-fit,minmax(170px,1fr))] gap-3">
      <div v-for="(n, k) in inspeksi.ringkasan.missing" :key="k" class="bg-ungu-pucat rounded-md px-3.5 py-3 flex flex-col"><span class="text-xs text-teks-sedang">Missing {{ k }}</span><strong class="text-lg">{{ ribuan(n) }}</strong></div>
      <div class="bg-pink-muda rounded-md px-3.5 py-3 flex flex-col"><span class="text-xs text-pink-tua">Data duplikat</span><strong class="text-lg">{{ ribuan(inspeksi.ringkasan.duplikat) }}</strong></div>
    </div>
    <div class="flex justify-between gap-2.5 flex-wrap">
      <button class="btn border border-ungu-garis bg-white" @click="ulang">Kembali</button>
      <button class="btn-ungu" @click="jalankanPreprocessing">Lanjut ke preprocessing</button>
    </div>
  </section>

  <!-- Langkah 3 -->
  <section v-if="langkah === 3" class="kartu p-7 flex flex-col gap-4">
    <div class="flex flex-wrap justify-between items-end gap-3">
      <div><h2 class="text-lg font-semibold">Langkah 3 · Preprocessing</h2><span class="text-[13px] text-teks-redup">Langkah yang sama dengan notebook Data Preparation</span></div>
      <span class="text-[13px] font-semibold text-ungu">{{ proses ? `${proses.laporan.length} dari ${proses.laporan.length} langkah selesai` : sibuk }}</span>
    </div>
    <div class="h-2 bg-ungu-muda rounded"><div class="h-2 bg-ungu rounded transition-all duration-700" :style="{ width: proses ? '100%' : '35%' }"></div></div>
    <ol v-if="proses" class="flex flex-col">
      <li v-for="(p, i) in proses.laporan" :key="i" class="grid grid-cols-[30px_1fr_auto] gap-3 items-center py-3 border-b border-[#F3F2F7]">
        <span class="w-[26px] h-[26px] rounded-full bg-ungu text-white flex items-center justify-center text-xs font-bold">{{ i + 1 }}</span>
        <div class="flex flex-col min-w-0"><strong class="text-sm">{{ p.judul }}</strong><span class="sub">{{ p.detail }}</span></div>
        <span class="text-[13px] font-semibold text-ungu-tua text-right">{{ p.hasil }}</span>
      </li>
    </ol>
    <div v-if="proses" class="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-3">
      <div class="bg-ungu-pucat rounded-md p-3.5 flex flex-col"><span class="text-xs text-teks-sedang">Sebelum</span><strong class="text-xl">{{ ribuan(proses.info.baris_awal) }} × {{ proses.info.kolom_awal }}</strong></div>
      <div class="bg-ungu-muda rounded-md p-3.5 flex flex-col"><span class="text-xs text-ungu">Sesudah (siap model)</span><strong class="text-xl">{{ ribuan(proses.info.baris_bersih) }} × {{ proses.info.kolom_model }}</strong></div>
      <div class="bg-pink-muda rounded-md p-3.5 flex flex-col"><span class="text-xs text-pink-tua">Proporsi batal</span><strong class="text-xl">{{ persen(proses.info.persen_batal, 1) }}</strong></div>
    </div>
    <div class="flex justify-between gap-2.5 flex-wrap">
      <button class="btn border border-ungu-garis bg-white" :disabled="!!sibuk" @click="langkah = 2">Kembali</button>
      <button class="btn-ungu disabled:opacity-50" :disabled="!proses" @click="langkah = 4">Selesai</button>
    </div>
  </section>

  <!-- Langkah 4 -->
  <section v-if="langkah === 4 && dataset" class="kartu p-7 flex flex-col gap-5">
    <div class="bg-ungu-muda text-ungu-gelap rounded-xl p-6 flex gap-4 items-center">
      <span class="w-[52px] h-[52px] shrink-0 rounded-full bg-ungu text-white flex items-center justify-center">
        <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5L20 7" /></svg>
      </span>
      <div class="flex flex-col gap-1">
        <strong class="text-xl">Data ini sudah bersih</strong>
        <span class="text-sm text-teks-sedang">{{ jenis === 'bersih'
          ? 'File ini terdeteksi sudah dipreprocessing, jadi langkah preview dan preprocessing dilewati. Selanjutnya data siap masuk ke analisis.'
          : 'Preprocessing selesai. Selanjutnya data siap masuk ke analisis di Dashboard dan Prediksi.' }}</span>
      </div>
    </div>
    <div class="grid grid-cols-[repeat(auto-fit,minmax(180px,1fr))] gap-3">
      <div class="bg-ungu-pucat rounded-md p-3.5 flex flex-col"><span class="text-xs text-teks-sedang">Nama file</span><strong class="text-base break-all">{{ dataset.nama_file }}</strong></div>
      <div class="bg-ungu-pucat rounded-md p-3.5 flex flex-col"><span class="text-xs text-teks-sedang">Jumlah data</span><strong class="text-base">{{ ribuan(dataset.baris_bersih) }} reservasi</strong></div>
      <div class="bg-ungu-pucat rounded-md p-3.5 flex flex-col"><span class="text-xs text-teks-sedang">Kolom data bersih</span><strong class="text-base">21 fitur + tahun + label</strong></div>
      <div class="bg-pink-muda rounded-md p-3.5 flex flex-col"><span class="text-xs text-pink-tua">Proporsi batal</span><strong class="text-base">{{ persen(dataset.persen_batal, 1) }}</strong></div>
    </div>
    <div class="flex gap-2.5 flex-wrap">
      <a :href="api.downloadUrl(dataset.id)" class="btn-garis">Unduh data bersih (CSV)</a>
      <RouterLink to="/" class="btn-ungu">Lihat di Dashboard</RouterLink>
      <RouterLink to="/prediksi" class="btn-pink">Lanjut ke Prediksi</RouterLink>
      <button class="btn text-teks-sedang underline font-medium" @click="ulang">Unggah file lain</button>
    </div>
  </section>
  </div>
</template>
