<script setup>
import { reactive, ref } from 'vue'
import { api, desimal } from '../api'

const BULAN = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
const SEGMEN = ['Online TA', 'Offline TA/TO', 'Direct', 'Groups', 'Corporate', 'Complementary', 'Aviation']
const DEPOSIT = ['No Deposit', 'Non Refund', 'Refundable']

const model = ref('xgboost')
const form = reactive({
  hotel: 'City Hotel', arrival_date_month: 3, lead_time: 238, total_malam: 4, total_tamu: 2, adr: 91.2,
  market_segment: 'Online TA', deposit_type: 'No Deposit', total_of_special_requests: 1, required_car_parking_spaces: 0
})
const hasil = ref(null)
const sibuk = ref(false)
const error = ref('')

async function prediksi() {
  sibuk.value = true; error.value = ''
  try { hasil.value = await api.prediksi(model.value, { ...form }) } catch (e) { error.value = e.message } finally { sibuk.value = false }
}
function gantiModel(m) {
  model.value = m
  if (hasil.value) prediksi()
}

const kotak = () => (model.value === 'xgboost' ? 'bg-ungu text-white' : 'bg-pink-muda text-pink-gelap')
const isian = 'min-h-[44px] border border-[#E4E2EC] rounded px-2.5 text-sm text-teks bg-white focus:outline-none focus:border-ungu'
</script>

<template>
  <div class="flex flex-col gap-1.5 pb-4 border-b border-[#E1DCF5]">
    <h1 class="text-[32px] font-normal">Prediksi</h1>
    <span class="text-[13px] text-teks-redup">Isi data satu reservasi, lalu lihat apakah reservasi itu berisiko batal</span>
  </div>

  <div class="flex flex-wrap gap-5 items-start">
    <form class="kartu flex-[1_1_560px] min-w-0 p-7 flex flex-col gap-5" @submit.prevent="prediksi">
      <div class="flex flex-wrap justify-between items-center gap-3">
        <h2 class="text-[17px] font-semibold">Data reservasi</h2>
        <div role="group" aria-label="Pilih model" class="flex bg-ungu-pucat rounded-md p-1 gap-1">
          <button v-for="[k, n] in [['xgboost', 'XGBoost'], ['random_forest', 'Random Forest']]" :key="k" type="button"
            class="min-h-[40px] px-4 rounded text-sm font-semibold" :class="model === k ? 'bg-ungu text-white' : 'text-teks'"
            :aria-pressed="model === k" @click="gantiModel(k)">{{ n }}</button>
        </div>
      </div>

      <div class="grid grid-cols-[repeat(auto-fit,minmax(170px,1fr))] gap-4">
        <label class="flex flex-col gap-1.5 text-[13px] font-medium text-teks-sedang">Hotel
          <select v-model="form.hotel" :class="isian"><option>City Hotel</option><option>Resort Hotel</option></select></label>
        <label class="flex flex-col gap-1.5 text-[13px] font-medium text-teks-sedang">Bulan kedatangan
          <select v-model.number="form.arrival_date_month" :class="isian"><option v-for="(b, i) in BULAN" :key="b" :value="i + 1">{{ b }}</option></select></label>
        <label class="flex flex-col gap-1.5 text-[13px] font-medium text-teks-sedang">Lead time (hari)
          <input v-model.number="form.lead_time" type="number" min="0" required :class="isian" /></label>
        <label class="flex flex-col gap-1.5 text-[13px] font-medium text-teks-sedang">Jumlah malam
          <input v-model.number="form.total_malam" type="number" min="0" required :class="isian" /></label>
        <label class="flex flex-col gap-1.5 text-[13px] font-medium text-teks-sedang">Jumlah tamu
          <input v-model.number="form.total_tamu" type="number" min="1" required :class="isian" /></label>
        <label class="flex flex-col gap-1.5 text-[13px] font-medium text-teks-sedang">Harga kamar per malam (€)
          <input v-model.number="form.adr" type="number" min="0" step="0.01" required :class="isian" /></label>
        <label class="flex flex-col gap-1.5 text-[13px] font-medium text-teks-sedang">Segmen pasar
          <select v-model="form.market_segment" :class="isian"><option v-for="s in SEGMEN" :key="s">{{ s }}</option></select></label>
        <label class="flex flex-col gap-1.5 text-[13px] font-medium text-teks-sedang">Tipe deposit
          <select v-model="form.deposit_type" :class="isian"><option v-for="d in DEPOSIT" :key="d">{{ d }}</option></select></label>
        <label class="flex flex-col gap-1.5 text-[13px] font-medium text-teks-sedang">Special request
          <input v-model.number="form.total_of_special_requests" type="number" min="0" max="5" required :class="isian" /></label>
        <label class="flex flex-col gap-1.5 text-[13px] font-medium text-teks-sedang">Tempat parkir
          <input v-model.number="form.required_car_parking_spaces" type="number" min="0" max="3" required :class="isian" /></label>
      </div>

      <button type="submit" class="btn-ungu self-start min-h-[50px] px-10 text-base disabled:opacity-60" :disabled="sibuk">
        {{ sibuk ? 'Memprediksi...' : 'Prediksi' }}
      </button>
      <p v-if="error" class="text-sm text-pink-tua">{{ error }}</p>
    </form>

    <section aria-label="Hasil prediksi" class="kartu flex-[1_1_340px] min-w-0 p-6 flex flex-col gap-4 border-t-4 border-ungu">
      <h2 class="text-[17px] font-semibold">Hasil prediksi</h2>
      <div v-if="!hasil" class="min-h-[240px] border-2 border-dashed border-ungu-garis rounded-lg flex items-center justify-center text-center p-5 text-sm text-teks-redup">
        Isi data reservasi, lalu klik tombol Prediksi
      </div>
      <template v-else>
        <div class="rounded-lg p-5 flex flex-col gap-1.5" :class="kotak()">
          <span class="text-[13px] opacity-85">{{ hasil.model }} memprediksi</span>
          <strong class="text-[32px]">{{ hasil.batal ? 'BATAL' : 'TIDAK BATAL' }}</strong>
          <span class="text-sm">Peluang batal <strong>{{ desimal(hasil.probabilitas, 1) }}%</strong> · risiko <strong>{{ hasil.risiko }}</strong></span>
        </div>
        <div class="flex flex-col gap-1.5">
          <div class="h-2.5 bg-ungu-muda rounded-full"><div class="h-2.5 rounded-full transition-all" :class="model === 'xgboost' ? 'bg-ungu' : 'bg-pink'" :style="{ width: hasil.probabilitas + '%' }"></div></div>
          <div class="flex justify-between text-[11px] text-teks-redup"><span>0% · rendah</span><span>35%</span><span>70%</span><span>tinggi · 100%</span></div>
        </div>
        <div class="flex flex-col gap-2.5">
          <span class="text-sm font-semibold">Alasan utama (SHAP)</span>
          <div v-for="a in hasil.alasan" :key="a.fitur" class="flex justify-between gap-2.5 text-[13px] pb-2 border-b border-[#F3F2F7]">
            <span>{{ a.teks }}</span>
            <span class="font-semibold whitespace-nowrap" :class="a.arah === 'menaikkan risiko' ? 'text-[#C2185B]' : 'text-ungu-tua'">{{ a.arah }}</span>
          </div>
        </div>
      </template>
    </section>
  </div>
</template>
