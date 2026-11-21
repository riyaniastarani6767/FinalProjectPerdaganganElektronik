import { reactive } from 'vue'

// ===== Koneksi ke backend Flask =====
export const API = (import.meta.env.VITE_API_URL || 'http://localhost:5000').replace(/\/$/, '')

async function panggil(method, path, body) {
  const res = await fetch(API + path, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.error || `Terjadi kesalahan (${res.status})`)
  return data
}

export const api = {
  status: () => panggil('GET', '/api/status'),
  dashboard: () => panggil('GET', '/api/dashboard'),
  pakaiBawaan: () => panggil('POST', '/api/dataset/bawaan'),
  preprocess: (id) => panggil('POST', '/api/preprocess', { dataset_id: id }),
  evaluasi: () => panggil('GET', '/api/evaluasi'),
  prediksi: (model, data) => panggil('POST', '/api/predict', { model, data }),
  downloadUrl: (id) => `${API}/api/download/${id}`,

  // Unggah file: minta alamat unggah, kirim file, lalu minta backend memeriksa isinya
  async unggah(file) {
    const awal = await panggil('POST', '/api/upload/start', { nama_file: file.name })
    const t = awal.target
    const form = new FormData()
    form.append('cacheControl', '3600')
    form.append('', file)
    const res = await fetch(t.relative ? API + t.url : t.url, { method: t.method, body: form })
    if (!res.ok) throw new Error('Gagal mengunggah file')
    return panggil('POST', '/api/upload/inspect', { path: awal.path, nama_file: file.name })
  }
}

// ===== Data bersama antarhalaman =====
export const store = reactive({
  dataset: null, // dataset aktif (data bawaan atau hasil unggahan)
  async muatStatus() {
    try { this.dataset = (await api.status()).dataset } catch { this.dataset = null }
  }
})

// ===== Format angka dan label =====
export const ribuan = (n) => (n == null ? '-' : Math.round(n).toLocaleString('id-ID'))
export const desimal = (x, d = 2) => (x == null ? '-' : Number(x).toFixed(d).replace('.', ','))
export const persen = (x, d = 2) => (x == null ? '-' : desimal(x, d) + '%')
export const euro = (x) => {
  if (x == null) return '-'
  if (x >= 1e6) return '€' + desimal(x / 1e6, 2) + ' jt'
  return '€' + desimal(x, 2)
}

export const LABEL_FITUR = {
  country: 'Negara asal', agent: 'Agen', required_car_parking_spaces: 'Tempat parkir',
  total_of_special_requests: 'Special request', market_segment: 'Segmen pasar', lead_time: 'Lead time',
  adr: 'ADR', customer_type: 'Tipe pelanggan', arrival_date_month: 'Bulan kedatangan',
  distribution_channel: 'Channel distribusi', previous_cancellations: 'Riwayat batal',
  previous_bookings_not_canceled: 'Riwayat tidak batal', total_malam: 'Total malam', total_tamu: 'Total tamu',
  deposit_type: 'Tipe deposit', hotel: 'Hotel', meal: 'Paket makan', reserved_room_type: 'Tipe kamar',
  is_repeated_guest: 'Tamu berulang', punya_company: 'Pemesan perusahaan', days_in_waiting_list: 'Hari daftar tunggu'
}
