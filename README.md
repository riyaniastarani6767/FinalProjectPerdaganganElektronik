# HotelGuard

Aplikasi Business Intelligence untuk memprediksi pembatalan reservasi hotel memakai **Random Forest** dan **XGBoost** yang ditulis manual (tanpa scikit-learn), dilengkapi **SHAP** untuk menjelaskan alasan prediksi.

Kelompok 3 · Perdagangan Elektronik dan Intelligent Bisnis · Informatika Universitas Udayana

## Fitur

| Menu | Fungsi |
|---|---|
| Dashboard | Visualisasi BI: KPI, tren pembatalan, pendapatan hilang, channel, negara, segmen |
| Unggah Data | Unggah CSV, preview, preprocessing, unduh data bersih |
| Prediksi | Isi data satu reservasi, pilih model, lihat hasil prediksi dan alasannya |
| Evaluasi | Perbandingan kedua model: accuracy, precision, recall, F1, confusion matrix |

## Teknologi

Vue 3 + Tailwind CSS · Flask · numpy + pandas · Supabase · Vercel

## Menjalankan di laptop

```bash
# Terminal 1: backend
conda create -n hotelguard python=3.11 -y
conda activate hotelguard
cd backend
pip install -r requirements.txt
python app.py

# Terminal 2: frontend
cd frontend
npm install
npm run dev
```

Buka http://localhost:5173

## Hasil model (data uji 20%)

| Model | Accuracy | Precision | Recall | F1-score |
|---|---|---|---|---|
| Random Forest | 80,23% | 60,34% | 83,35% | 70,00% |
| **XGBoost** | **81,96%** | **63,75%** | **80,76%** | **71,26%** |

Kedua model memakai pre-pruning dan post-pruning (`gamma` = 5 pada XGBoost, `ccp_alpha` = 0,00005 pada Random Forest). Selisih F1 data latih dan data uji 1,52 poin (XGBoost) dan 3,21 poin (Random Forest), sehingga model good fit.

