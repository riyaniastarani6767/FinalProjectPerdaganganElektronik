# HotelGuard Frontend

Tampilan aplikasi HotelGuard dengan Vue 3 + Tailwind CSS. Grafik digambar manual dengan SVG (tanpa library grafik).

Dikerjakan oleh: Riyana (frontend dan deploy)

## Menjalankan

```bash
npm install
npm run dev        # buka http://localhost:5173
```

Backend Flask harus berjalan di http://localhost:5000. Jika backend memakai port lain, buat file `.env` berisi `VITE_API_URL=http://localhost:5001`.

## Struktur

| File | Fungsi |
|---|---|
| `src/main.js` | Start aplikasi dan daftar halaman (router) |
| `src/App.vue` | Header, sidebar 4 menu, layout |
| `src/api.js` | Koneksi ke backend Flask, data bersama, format angka, nama fitur |
| `src/style.css` | Gaya dasar Tailwind dan kelas bersama (kartu, tombol) |
| `src/pages/Dashboard.vue` | Dashboard BI: KPI, tren, pendapatan hilang, channel, negara, segmen |
| `src/pages/UnggahData.vue` | Unggah CSV, preview 10 data, preprocessing, unduh data bersih |
| `src/pages/Prediksi.vue` | Form 10 isian, pilih model, hasil prediksi dan 3 alasan SHAP |
| `src/pages/Evaluasi.vue` | Metrik kedua model, baseline, confusion matrix, SHAP |
| `src/components/` | LineChart, BarChart, DonutChart, ConfusionMatrix |

## Deploy ke Vercel

Root Directory = `frontend`, framework Vite, Environment Variable `VITE_API_URL` = alamat backend di Vercel.
