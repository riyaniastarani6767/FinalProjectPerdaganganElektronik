<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { api, desimal } from '../api'
import Gauge from '../components/Gauge.vue'
import PengujianModel from '../components/PengujianModel.vue'

const BULAN = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
const SEGMEN = ['Online TA', 'Offline TA/TO', 'Direct', 'Groups', 'Corporate', 'Complementary', 'Aviation']
const DEPOSIT = ['No Deposit', 'Non Refund', 'Refundable']
const PILIHAN = [['xgboost', 'XGBoost'], ['random_forest', 'Random Forest'], ['keduanya', 'Keduanya']]

// Form dimulai kosong; tombol Reset mengembalikan ke keadaan ini
const KOSONG = {
  hotel: '', arrival_date_month: '', lead_time: '', total_malam: '', total_tamu: '', adr: '',
  market_segment: '', deposit_type: '', total_of_special_requests: '', required_car_parking_spaces: '', country: ''
}

const model = ref('xgboost')
const form = reactive({ ...KOSONG })
const hasil = ref(null)          // { xgboost?: {...}, random_forest?: {...} }
const modelHasil = ref(null)     // model yang dipakai untuk hasil yang sedang tampil
const sibuk = ref(false)
const error = ref('')
const ev = ref(null)
const negara = ref([])          // pilihan negara asal dari backend (15 teratas + negara lain)

// data pengujian model; diambil saat halaman dibuka, dan dicoba lagi saat Prediksi diklik jika sebelumnya gagal
async function muatEvaluasi() {
  if (ev.value) return
  try { ev.value = await api.evaluasi() } catch { /* dicoba lagi saat Prediksi diklik */ }
}
async function muatOpsi() {
  if (negara.value.length) return
  try { negara.value = (await api.opsi()).negara } catch { /* dicoba lagi saat halaman dibuka ulang */ }
}
onMounted(() => { muatEvaluasi(); muatOpsi() })

async function prediksi() {
  sibuk.value = true; error.value = ''
  try {
    const kode = model.value === 'keduanya' ? ['xgboost', 'random_forest'] : [model.value]
    const [hasilModel] = await Promise.all([Promise.all(kode.map((k) => api.prediksi(k, { ...form }))), muatEvaluasi()])
    hasil.value = Object.fromEntries(kode.map((k, i) => [k, hasilModel[i]]))
    modelHasil.value = model.value
  } catch (e) { error.value = e.message; hasil.value = null } finally { sibuk.value = false }
}
function gantiModel(m) {
  model.value = m
  if (hasil.value) prediksi()
}
function reset() {
  Object.assign(form, KOSONG)
  hasil.value = null
  modelHasil.value = null
  error.value = ''
}

const satu = computed(() => (hasil.value && modelHasil.value !== 'keduanya' ? hasil.value[modelHasil.value] : null))
const dua = computed(() => (hasil.value && modelHasil.value === 'keduanya' ? hasil.value : null))

// gabung daftar menjadi "a, b, dan c"
const gabung = (arr) => (arr.length < 3 ? arr.join(' dan ') : `${arr.slice(0, -1).join(', ')}, dan ${arr[arr.length - 1]}`)
function kalimat(h) {
  const kecil = (t) => t.charAt(0).toLowerCase() + t.slice(1)
  const naik = h.alasan.filter((a) => a.nilai > 0).map((a) => kecil(a.teks))
  const turun = h.alasan.filter((a) => a.nilai <= 0).map((a) => kecil(a.teks))
  return { arah: h.batal ? 'cenderung batal' : 'cenderung tidak batal', naik: gabung(naik), turun: gabung(turun) }
}
const lebarShap = (h, a) => (Math.abs(a.nilai) / Math.max(...h.alasan.map((x) => Math.abs(x.nilai)))) * 55
const satuanShap = (h) => (h.model === 'XGBoost' ? 'log-odds' : 'peluang')
const tipAlasan = (h, a) => [a.teks, a.nilai > 0 ? 'Menaikkan risiko batal' : 'Menurunkan risiko batal', `Nilai SHAP ${desimal(a.nilai, 3)} (${satuanShap(h)})`]
const tipRisiko = (h) => [`Risiko ${h.risiko}`, 'Rendah: di bawah 35%', 'Sedang: 35% sampai 70%', 'Tinggi: di atas 70%']

const isian = 'min-h-[42px] border border-garis rounded-[9px] px-2.5 text-sm text-teks bg-white focus:outline-none focus:border-ungu'
const label = 'flex flex-col gap-1.5 text-[12.5px] font-medium text-teks-sedang'
const grup = 'flex flex-col gap-3 py-4 border-t border-garis first:border-t-0 first:pt-1'
</script>

<template>
  <div class="flex flex-col gap-4">
  <div class="px-1">
    <h2 class="judul-halaman">Prediksi Pembatalan</h2>
    <p class="sub mt-1 leading-relaxed">Isi data satu reservasi, pilih model, lalu klik Prediksi. Hasil prediksi dan hasil pengujian model akan tampil setelah prediksi dijalankan.</p>
  </div>

  <div class="grid grid-cols-1 xl:grid-cols-[1.05fr_1fr] gap-4">
    <!-- Form -->
    <form class="kartu flex flex-col" @submit.prevent="prediksi">
      <div class="flex flex-wrap justify-between items-center gap-3 pb-3 border-b border-garis">
        <h3 class="judul-kartu">Data reservasi</h3>
        <div role="group" aria-label="Pilih model" class="flex bg-ungu-pucat rounded-[10px] p-1 gap-1">
          <button v-for="[k, n] in PILIHAN" :key="k" type="button" class="min-h-[36px] px-3.5 rounded-[7px] text-[13px] font-semibold"
            :class="model === k ? 'bg-ungu text-white' : 'text-teks-sedang'" :aria-pressed="model === k" @click="gantiModel(k)">{{ n }}</button>
        </div>
      </div>

      <div class="flex flex-col">
        <div :class="grup">
          <span class="text-[11.5px] font-semibold text-teks-redup">Kedatangan</span>
          <div class="grid grid-cols-1 sm:grid-cols-2 2xl:grid-cols-4 gap-3">
            <label :class="label">Hotel
              <select v-model="form.hotel" required :class="isian"><option value="" disabled>Pilih hotel</option><option>City Hotel</option><option>Resort Hotel</option></select></label>
            <label :class="label">Bulan kedatangan
              <select v-model.number="form.arrival_date_month" required :class="isian"><option value="" disabled>Pilih bulan</option><option v-for="(b, i) in BULAN" :key="b" :value="i + 1">{{ b }}</option></select></label>
            <label :class="label">Lead time (hari)
              <input v-model.number="form.lead_time" type="number" min="0" required placeholder="contoh: 30" :class="isian" /></label>
            <label :class="label">Negara asal tamu
              <select v-model="form.country" required :class="isian" @focus="muatOpsi"><option value="" disabled>Pilih negara</option><option v-for="n in negara" :key="n.kode" :value="n.kode">{{ n.nama }}</option></select></label>
          </div>
        </div>
        <div :class="grup">
          <span class="text-[11.5px] font-semibold text-teks-redup">Kamar dan tamu</span>
          <div class="grid grid-cols-[repeat(auto-fit,minmax(150px,1fr))] gap-3">
            <label :class="label">Jumlah malam
              <input v-model.number="form.total_malam" type="number" min="0" required placeholder="contoh: 3" :class="isian" /></label>
            <label :class="label">Jumlah tamu
              <input v-model.number="form.total_tamu" type="number" min="1" required placeholder="contoh: 2" :class="isian" /></label>
            <label :class="label">Harga per malam (€)
              <input v-model.number="form.adr" type="number" min="0" max="1000" step="0.01" required placeholder="contoh: 100" :class="isian" /></label>
          </div>
        </div>
        <div :class="grup">
          <span class="text-[11.5px] font-semibold text-teks-redup">Pemesanan</span>
          <div class="grid grid-cols-1 sm:grid-cols-2 2xl:grid-cols-4 gap-3">
            <label :class="label">Segmen pasar
              <select v-model="form.market_segment" required :class="isian"><option value="" disabled>Pilih segmen</option><option v-for="s in SEGMEN" :key="s">{{ s }}</option></select></label>
            <label :class="label">Tipe deposit
              <select v-model="form.deposit_type" required :class="isian"><option value="" disabled>Pilih deposit</option><option v-for="d in DEPOSIT" :key="d">{{ d }}</option></select></label>
            <label :class="label">Special request
              <input v-model.number="form.total_of_special_requests" type="number" min="0" max="5" required placeholder="0 sampai 5" :class="isian" /></label>
            <label :class="label">Tempat parkir
              <input v-model.number="form.required_car_parking_spaces" type="number" min="0" max="3" required placeholder="0 sampai 3" :class="isian" /></label>
          </div>
        </div>
      </div>

      <div class="flex flex-wrap gap-2.5 pt-2">
        <button type="submit" class="btn-ungu min-h-[46px] px-9 text-sm disabled:opacity-60" :disabled="sibuk">{{ sibuk ? 'Memprediksi...' : 'Prediksi' }}</button>
        <button type="button" class="btn-garis min-h-[46px] px-6" :disabled="sibuk" @click="reset">Reset</button>
      </div>
      <p v-if="error" class="text-sm text-pink-tua mt-3">{{ error }}</p>
    </form>

    <!-- Hasil -->
    <section aria-label="Hasil prediksi" class="kartu flex flex-col">
      <div class="flex justify-between items-center gap-2 mb-1">
        <h3 class="judul-kartu">Hasil prediksi</h3>
        <span v-if="hasil" class="text-[11.5px] font-semibold px-2.5 py-1 rounded-full bg-[#F1EFF4] text-teks-sedang">{{ dua ? 'XGBoost dan Random Forest' : satu?.model }}</span>
      </div>

      <div v-if="!hasil" class="min-h-[300px] mt-3 border-2 border-dashed border-ungu-garis rounded-xl flex flex-col items-center justify-center gap-2 text-center p-6 text-sm text-teks-redup">
        <svg class="w-9 h-9 text-ungu-garis" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 3v18h18M7 15l4-5 3 3 5-7" /></svg>
        Isi data reservasi, pilih model, lalu klik Prediksi
      </div>

      <!-- Satu model -->
      <template v-else-if="satu">
        <Gauge :nilai="satu.probabilitas" class="mt-1" />
        <div class="flex items-center justify-center gap-2 flex-wrap mt-1">
          <strong class="text-[22px] font-extrabold tracking-wide" :class="satu.batal ? 'text-pink-gelap' : 'text-ungu'">{{ satu.batal ? 'BATAL' : 'TIDAK BATAL' }}</strong>
          <span v-tip="tipRisiko(satu)" class="text-[11.5px] font-semibold px-2.5 py-1 rounded-full" :class="satu.risiko === 'rendah' ? 'bg-ungu-muda text-ungu' : 'bg-pink-muda text-pink-gelap'">Risiko {{ satu.risiko }}</span>
        </div>
        <p class="sub text-center mt-1">Diputuskan batal jika peluang 50% atau lebih</p>
        <div class="bg-ungu-pucat rounded-xl px-3.5 py-3 text-[13px] leading-relaxed text-teks-sedang mt-4">
          Reservasi ini <b class="text-teks">{{ kalimat(satu).arah }}</b><template v-if="kalimat(satu).naik">, terutama karena {{ kalimat(satu).naik }}</template>.
          <template v-if="kalimat(satu).turun"> Faktor yang menurunkan risiko: {{ kalimat(satu).turun }}.</template>
        </div>
        <div class="flex flex-wrap justify-between items-baseline gap-2 mt-5 mb-1.5">
          <h3 class="judul-kartu">Alasan utama (SHAP)</h3>
          <div class="legenda"><span><i class="bg-ungu"></i>Menurunkan</span><span><i class="bg-pink"></i>Menaikkan</span></div>
        </div>
        <div v-for="a in satu.alasan" :key="a.fitur" v-tip="tipAlasan(satu, a)" class="grid grid-cols-2 items-center h-[34px] relative">
          <div class="absolute left-1/2 inset-y-0 w-px bg-[#CFC8DC]"></div>
          <div class="flex justify-end items-center">
            <span v-if="a.nilai > 0" class="text-[12.5px] px-2.5 text-right">{{ a.teks }}</span>
            <template v-else><span class="text-[12.5px] px-2.5">{{ a.teks }}</span><div class="h-3 rounded bg-ungu" :style="{ width: lebarShap(satu, a) + '%' }"></div></template>
          </div>
          <div class="flex items-center"><div v-if="a.nilai > 0" class="h-3 rounded bg-pink" :style="{ width: lebarShap(satu, a) + '%' }"></div></div>
        </div>
      </template>

      <!-- Kedua model -->
      <template v-else-if="dua">
        <div class="rounded-xl px-3.5 py-3 text-[13px] leading-relaxed mt-2 mb-3.5" :class="dua.xgboost.batal === dua.random_forest.batal ? 'bg-ungu-pucat' : 'bg-pink-muda'">
          <template v-if="dua.xgboost.batal === dua.random_forest.batal">
            Kedua model <b>sepakat</b>: reservasi ini {{ dua.xgboost.batal ? 'cenderung batal' : 'cenderung tidak batal' }}.
            Selisih peluang batal {{ desimal(Math.abs(dua.xgboost.probabilitas - dua.random_forest.probabilitas), 1) }} poin.
          </template>
          <template v-else>Kedua model <b>berbeda hasil</b>. Gunakan hasil XGBoost sebagai acuan karena F1-score-nya lebih tinggi.</template>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          <div v-for="[k, h] in [['xgboost', dua.xgboost], ['random_forest', dua.random_forest]]" :key="k" class="border border-garis rounded-xl p-3.5 flex flex-col items-center gap-1.5">
            <b class="text-[13.5px]" :class="k === 'xgboost' ? 'text-ungu' : 'text-pink-gelap'">{{ h.model }}</b>
            <Gauge :nilai="h.probabilitas" kecil />
            <div class="flex items-center gap-2 flex-wrap justify-center">
              <strong class="text-lg font-extrabold" :class="h.batal ? 'text-pink-gelap' : 'text-ungu'">{{ h.batal ? 'BATAL' : 'TIDAK BATAL' }}</strong>
              <span v-tip="tipRisiko(h)" class="text-[11px] font-semibold px-2 py-0.5 rounded-full" :class="h.risiko === 'rendah' ? 'bg-ungu-muda text-ungu' : 'bg-pink-muda text-pink-gelap'">Risiko {{ h.risiko }}</span>
            </div>
            <div class="w-full flex flex-col gap-1.5 mt-2 pt-2.5 border-t border-garis">
              <div v-for="a in h.alasan" :key="a.fitur" v-tip="tipAlasan(h, a)" class="flex gap-2 items-center text-[12.5px]">
                <i class="not-italic w-5 h-5 rounded-md grid place-items-center text-[10px] shrink-0" :class="a.nilai > 0 ? 'bg-pink-muda text-pink' : 'bg-ungu-muda text-ungu'">{{ a.nilai > 0 ? '▲' : '▼' }}</i>{{ a.teks }}
              </div>
            </div>
          </div>
        </div>
        <div class="legenda justify-center mt-3"><span>▲ menaikkan risiko</span><span>▼ menurunkan risiko</span><span>Batal jika peluang 50% atau lebih</span></div>
      </template>
    </section>
  </div>

  <PengujianModel v-if="ev && hasil" :ev="ev" :pilih="modelHasil" />
  </div>
</template>
