# HotelGuard: Prediksi Pembatalan Reservasi Hotel

Kelompok 3 · Perdagangan Elektronik dan Intelligent Bisnis · Informatika Universitas Udayana

Aplikasi Business Intelligence dan prediksi pembatalan reservasi hotel dengan **Random Forest** dan **XGBoost yang ditulis manual** (tanpa scikit-learn dan tanpa library xgboost), dilengkapi **SHAP manual**.

- Frontend: Vue 3 + Tailwind CSS (grafik digambar manual dengan SVG)
- Backend: Flask (Python), algoritma hanya memakai numpy dan pandas
- Database dan penyimpanan file: Supabase (atau SQLite + folder lokal saat dijalankan di laptop)
- Hosting: Vercel

## Struktur folder

```
FinalProjectPerdaganganElektronik/
├── backend/                     # Flask API (Riyani)
│   ├── app.py                   # semua endpoint: dashboard, unggah data, prediksi, evaluasi
│   ├── database.py              # Supabase (online) atau SQLite (lokal)
│   ├── dashboard.py             # hitung angka dan grafik Dashboard BI
│   ├── ml/
│   │   ├── preprocessing.py     # pembersihan data dan encoding manual
│   │   ├── algoritma.py         # Random Forest, XGBoost, metrik, SHAP (manual, hanya numpy)
│   │   └── latih_model.py       # parameter terbaik + latih dan simpan model
│   ├── models/                  # model_xgboost.pkl, model_random_forest.pkl, evaluasi.json
│   ├── data/hotel_bookings.csv  # data bawaan
│   ├── api/index.py             # titik masuk Vercel
│   ├── requirements.txt
│   ├── schema.sql               # tabel dan bucket Supabase
│   ├── Procfile                 # perintah start untuk Railway
│   ├── vercel.json
│   └── .env.example
├── frontend/                    # Vue 3 + Tailwind (Riyana)
│   └── src/
│       ├── main.js              # start aplikasi + daftar halaman
│       ├── App.vue              # header, sidebar 4 menu, layout
│       ├── api.js               # koneksi ke Flask + format angka
│       ├── style.css
│       ├── pages/               # Dashboard, UnggahData, Prediksi, Evaluasi (1 menu = 1 file)
│       └── components/          # LineChart, BarChart, DonutChart, ConfusionMatrix
├── notebook/                    # notebook modeling manual (.ipynb + .html) dan hasil/
├── README.md
└── .gitignore
```

## Menjalankan di laptop (tanpa Supabase)

Butuh Python 3.10+ (disarankan lewat conda) dan Node.js 18+.

```bash
# Terminal 1: backend
conda create -n hotelguard python=3.11 -y
conda activate hotelguard
cd backend
pip install -r requirements.txt
python app.py                 # berjalan di http://localhost:5000

# Terminal 2: frontend
cd frontend
npm install
npm run dev                   # buka http://localhost:5173
```

Tanpa variabel Supabase, backend otomatis memakai SQLite (`backend/instance/hotelguard.db`) dan menyimpan file CSV di `backend/instance/files/`.

## Menyiapkan Supabase

1. Buat project baru di supabase.com.
2. Buka **SQL Editor**, tempel isi `backend/schema.sql`, lalu klik **Run**. Perintah ini membuat tabel `dataset` dan bucket Storage `datasets`.
3. Buka **Project Settings > API**, salin:
   - Project URL ke `SUPABASE_URL`
   - kunci `service_role` ke `SUPABASE_SERVICE_KEY` (hanya untuk backend, jangan dimasukkan ke frontend)
4. Untuk mencoba di laptop dengan Supabase: buat file `backend/.env` dari `.env.example`, lalu jalankan backend dengan variabel tersebut (misalnya `export $(cat .env | xargs) && python app.py`).

## Deploy ke Vercel (backend dan frontend)

Buat **2 project Vercel** dari repo GitHub yang sama. Pastikan folder `backend` dan `frontend` sudah ter-push ke GitHub.

### 1. Backend
1. vercel.com, **Add New > Project**, pilih repo ini, lalu **Import**.
2. **Project Name**: misalnya `hotelguard-api`.
3. **Framework Preset**: `Other`. **Root Directory**: klik Edit, pilih `backend`.
4. **Environment Variables**: isi `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, dan `SUPABASE_BUCKET` = `datasets`.
5. Klik **Deploy**. Setelah selesai, buka `https://hotelguard-api.vercel.app/api/status` dan pastikan muncul `"mode": "supabase"`.

### 2. Frontend
1. **Add New > Project** lagi, pilih repo yang sama.
2. **Project Name**: misalnya `hotelguard`.
3. **Framework Preset**: `Vite`. **Root Directory**: `frontend`.
4. **Environment Variables**: `VITE_API_URL` = alamat backend, misalnya `https://hotelguard-api.vercel.app` (tanpa garis miring di akhir).
5. Klik **Deploy**, lalu buka alamat frontend.

Catatan:
- Di Vercel, Supabase **wajib** diisi karena penyimpanan file di server Vercel bersifat sementara.
- File CSV diunggah langsung dari browser ke Supabase Storage, sehingga tidak terkena batas ukuran request Vercel.
- Setiap `git push` ke GitHub otomatis membuat Vercel deploy ulang.
- Alternatif backend: Railway (sudah ada `Procfile`), tetapi Railway tidak gratis selamanya.

## Catatan Mac
Jika muncul `Port 5000 is in use`, matikan **System Settings > General > AirDrop & Continuity > AirPlay Receiver**, atau jalankan backend dengan `PORT=5001 python app.py` dan isi `frontend/.env` dengan `VITE_API_URL=http://localhost:5001`.

## Alur aplikasi

```
Unggah Data (CSV) -> preview 10 data -> preprocessing -> data bersih
        |
        v
Dashboard BI berubah sesuai data yang diunggah (sebelum ada unggahan: data bawaan)

Prediksi : isi 10 data reservasi + pilih model -> BATAL / TIDAK BATAL, peluang, 3 alasan SHAP
           (hanya untuk mencoba, tidak mengubah Dashboard)
Evaluasi : metrik XGBoost vs Random Forest, confusion matrix, SHAP (halaman pengujian model)
```

| Menu | Fungsi | Mengubah Dashboard? |
|---|---|---|
| Dashboard | Visualisasi BI: KPI, tren, pendapatan hilang, channel, pola musiman, negara, segmen, lead time, insight, ringkasan hasil model | - |
| Unggah Data | Unggah CSV, preview, preprocessing, unduh data bersih. File yang sudah bersih langsung siap dipakai | Ya |
| Prediksi | Input 10 isian (isian lain memakai nilai paling umum), output prediksi, peluang, risiko, 3 alasan SHAP | Tidak |
| Evaluasi | Hasil pengujian kedua model pada data uji 20% dan alasan pemilihan model terbaik | Tidak |

## Melatih ulang model

Model sudah dilatih dan disimpan di `backend/models/`. Jika parameter di `ml/latih_model.py` diubah, latih ulang dengan:

```bash
cd backend
python ml/latih_model.py
```

## Hasil notebook (data uji 80:20, 17.032 reservasi)

| Model | Accuracy | Precision | Recall | F1-score |
|---|---|---|---|---|
| Baseline: selalu menebak tidak batal | 72,32 | 0,00 | 0,00 | 0,00 |
| Baseline: pohon kedalaman 3 | 74,56 | 56,83 | 33,70 | 42,31 |
| Random Forest manual | 80,63 | 61,27 | 81,61 | 70,00 |
| **XGBoost manual** | **82,10** | **64,12** | **80,21** | **71,27** |

## Peta arahan dosen

| Arahan dosen | Ada di |
|---|---|
| Dilihat dari karakteristik datanya | Notebook bagian 1 (tabel karakteristik data dan alasan memilih metode) |
| Fungsi apa yang dipakai di awal dan di akhir | Notebook bagian 3 (Gini, gradien/hessian log-loss, voting, sigmoid); komentar di `ml/algoritma.py` |
| Mengubah data menjadi angka dengan cara apa | Notebook bagian 2 (One-Hot Encoding manual, ordinal, biner, 15 teratas + Lainnya) |
| Pre-pruning dan post-pruning | Notebook bagian 3 dan 3.5 (max_depth, min_samples_leaf, min_child_weight; ccp_alpha, gamma) beserta percobaannya |
| Model terbaik dibandingkan dari metode evaluasi | Notebook bagian 3.4, 3.6, 4; menu Evaluasi |
| Hasil setiap model berapa | Tabel hasil notebook; menu Evaluasi dan Dashboard |
| Kenapa memakai confusion matrix dan metrik lain | Notebook bagian 4 (tabel alasan tiap metode) |
| Tahap-tahap deployment | Notebook bagian 6; README ini |
| Halaman pengujian | Menu Evaluasi |
| Visualisasi BI berdasarkan data yang ada | Menu Unggah Data + Dashboard |
| Halaman predict model dan inputannya | Menu Prediksi (input 10 data reservasi + pilihan model) |
