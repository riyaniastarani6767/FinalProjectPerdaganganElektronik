"""
Backend HotelGuard (Flask).

Endpoint utama:
  GET    /api/status                 info mode penyimpanan dan dataset aktif
  POST   /api/upload/start           minta alamat unggah file CSV
  PUT    /api/upload/local/<path>    unggah file (mode lokal)
  POST   /api/upload/inspect         baca file, deteksi mentah/bersih, preview 10 data
  POST   /api/preprocess             jalankan preprocessing data mentah
  GET    /api/download/<id>          unduh data bersih
  POST   /api/dataset/bawaan         kembali memakai data bawaan
  GET    /api/dashboard              angka dan grafik Dashboard BI
  GET    /api/evaluasi               hasil pengujian XGBoost dan Random Forest
  POST   /api/predict                prediksi satu reservasi (10 isian + pilihan model)
"""
import io
import json
import pickle
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, Response, jsonify, redirect, request

sys.path.insert(0, str(Path(__file__).parent))
from dashboard import hitung as hitung_dashboard          # noqa: E402
from ml import config                                      # noqa: E402
from ml.algoritma import shap_permutasi                     # noqa: E402
from ml.preprocessing import (CLEAN_COLS, LABEL, RAW_REQUIRED,  # noqa: E402
                              clean_raw, is_clean, is_raw)
from storage import buat_store, sekarang                   # noqa: E402

BASE = Path(__file__).parent
DATA_BAWAAN = BASE / 'data' / 'hotel_bookings.csv'
NAMA_BAWAAN = 'data_bawaan.csv'

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 60 * 1024 * 1024
store = buat_store()
_cache = {}


@app.after_request
def cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return resp


@app.route('/api/<path:_any>', methods=['OPTIONS'])
def preflight(_any):
    return Response(status=204)


@app.errorhandler(Exception)
def error(e):
    kode = getattr(e, 'code', 500)
    return jsonify(error=str(getattr(e, 'description', e))), kode if isinstance(kode, int) else 500


def gagal(pesan, kode=400):
    return jsonify(error=pesan), kode


# ---------------------------------------------------------------------------
# Data aktif
# ---------------------------------------------------------------------------
def data_bawaan():
    if 'bawaan' not in _cache:
        d, laporan, info = clean_raw(pd.read_csv(DATA_BAWAAN))
        _cache['bawaan'] = (d, laporan, info)
    return _cache['bawaan']


def dataset_aktif():
    ds = store.active_dataset()
    if ds and ds.get('path_bersih'):
        return ds
    _, laporan, info = data_bawaan()
    return dict(id=None, nama_file=NAMA_BAWAAN, sudah_bersih=False, laporan=laporan, **info)


def data_bersih(ds):
    if ds.get('id') is None:
        return data_bawaan()[0]
    key = f"ds{ds['id']}"
    if key not in _cache:
        _cache[key] = pd.read_csv(io.BytesIO(store.read_file(ds['path_bersih'])))
    return _cache[key]


def info_dataset(ds):
    kunci = ['id', 'nama_file', 'sudah_bersih', 'baris_awal', 'kolom_awal', 'baris_bersih',
             'kolom_bersih', 'persen_batal', 'dibuat_pada']
    return {k: ds.get(k) for k in kunci}


def jsonable(x):
    if isinstance(x, dict):
        return {k: jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return None if np.isnan(x) else float(x)
    if isinstance(x, float) and np.isnan(x):
        return None
    return x


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------
@app.get('/api/status')
def status():
    return jsonify(mode=store.mode, dataset=info_dataset(dataset_aktif()))


# ---------------------------------------------------------------------------
# Unggah data
# ---------------------------------------------------------------------------
@app.post('/api/upload/start')
def upload_start():
    nama = (request.get_json(silent=True) or {}).get('nama_file', 'data.csv')
    if not nama.lower().endswith('.csv'):
        return gagal('File harus berformat CSV.')
    aman = re.sub(r'[^A-Za-z0-9_.-]', '_', nama)
    path = f"raw/{int(time.time() * 1000)}_{aman}"
    return jsonify(path=path, target=store.upload_target(path))


@app.put('/api/upload/local/<path:path>')
def upload_local(path):
    if store.mode != 'lokal':
        return gagal('Hanya untuk mode lokal.', 404)
    isi = next(iter(request.files.values())).read() if request.files else request.get_data()
    store.save_file(path, isi)
    return jsonify(ok=True)


@app.post('/api/upload/inspect')
def upload_inspect():
    body = request.get_json(force=True)
    path, nama = body['path'], body.get('nama_file', 'data.csv')
    try:
        df = pd.read_csv(io.BytesIO(store.read_file(path)))
    except Exception as e:  # noqa: BLE001
        return gagal(f'File tidak bisa dibaca sebagai CSV: {e}')

    if is_clean(df):
        jenis = 'bersih'
        df = df[CLEAN_COLS]
        row = store.insert('dataset', dict(
            nama_file=nama, path_mentah=path, path_bersih=path, sudah_bersih=True,
            baris_awal=len(df), kolom_awal=df.shape[1], baris_bersih=len(df), kolom_bersih=df.shape[1],
            persen_batal=round(float(df[LABEL].mean() * 100), 2), laporan=[], aktif=False, dibuat_pada=sekarang()))
        store.set_active(row['id'])
        ringkasan = dict(missing=int(df.isna().sum().sum()), duplikat=0)
    elif is_raw(df):
        jenis = 'mentah'
        row = store.insert('dataset', dict(
            nama_file=nama, path_mentah=path, sudah_bersih=False, baris_awal=len(df), kolom_awal=df.shape[1],
            aktif=False, dibuat_pada=sekarang()))
        ringkasan = dict(missing={c: int(df[c].isna().sum()) for c in ['company', 'agent', 'country', 'children']},
                         duplikat=int(df.duplicated().sum()))
    else:
        kurang = [c for c in RAW_REQUIRED if c not in df.columns]
        return gagal('Format kolom tidak dikenali. Kolom yang belum ada: ' + ', '.join(kurang[:10]))

    kolom_preview = list(df.columns) if jenis == 'bersih' else [
        'hotel', 'is_canceled', 'lead_time', 'arrival_date_month', 'stays_in_weekend_nights',
        'stays_in_week_nights', 'adults', 'children', 'meal', 'country', 'market_segment',
        'deposit_type', 'agent', 'company', 'adr'] + (['reservation_status'] if 'reservation_status' in df else [])
    prev = df[kolom_preview].head(10).astype(object).where(df[kolom_preview].head(10).notna(), None)
    return jsonify(jsonable(dict(jenis=jenis, dataset=info_dataset(row), baris=len(df), kolom=df.shape[1],
                                 preview_kolom=kolom_preview, preview=prev.values.tolist(), ringkasan=ringkasan)))


@app.post('/api/preprocess')
def preprocess():
    ds_id = request.get_json(force=True)['dataset_id']
    ds = store.get('dataset', ds_id)
    if not ds:
        return gagal('Dataset tidak ditemukan.', 404)
    raw = pd.read_csv(io.BytesIO(store.read_file(ds['path_mentah'])))
    d, laporan, info = clean_raw(raw)
    path = f"clean/{ds_id}_data_bersih.csv"
    store.save_file(path, d.to_csv(index=False).encode())
    store.update('dataset', ds_id, dict(path_bersih=path, baris_bersih=info['baris_bersih'],
                                        kolom_bersih=info['kolom_bersih'], persen_batal=info['persen_batal'],
                                        laporan=laporan))
    store.set_active(ds_id)
    _cache[f'ds{ds_id}'] = d
    return jsonify(jsonable(dict(laporan=laporan, info=info, dataset=info_dataset(store.get('dataset', ds_id)))))


@app.get('/api/download/<int:ds_id>')
def download(ds_id):
    ds = store.get('dataset', ds_id)
    if not ds or not ds.get('path_bersih'):
        return gagal('Data bersih belum tersedia.', 404)
    nama = re.sub(r'\.csv$', '', ds['nama_file']) + '_bersih.csv'
    url = store.download_url(ds['path_bersih'], nama)
    if url:
        return redirect(url)
    return Response(store.read_file(ds['path_bersih']), mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename="{nama}"'})


@app.post('/api/dataset/bawaan')
def pakai_bawaan():
    store.set_active(None)
    return jsonify(dataset=info_dataset(dataset_aktif()))


# ---------------------------------------------------------------------------
# Model (dilatih sekali dengan latih_model.py, disimpan di models/)
# ---------------------------------------------------------------------------
MODELS = BASE / 'models'
NAMA_MODEL = {'xgboost': 'XGBoost', 'random_forest': 'Random Forest'}


def evaluasi_model():
    if 'evaluasi' not in _cache:
        _cache['evaluasi'] = json.loads((MODELS / 'evaluasi.json').read_text())
    return _cache['evaluasi']


def muat_model(kode):
    key = f'model_{kode}'
    if key not in _cache:
        with open(MODELS / f'model_{kode}.pkl', 'rb') as f:
            _cache[key] = pickle.load(f)
    return _cache[key]


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.get('/api/dashboard')
def dashboard():
    ds = dataset_aktif()
    key = f"dash{ds.get('id')}"
    if key not in _cache:
        _cache[key] = hitung_dashboard(data_bersih(ds))
    ev = evaluasi_model()
    model = [dict(kode=k, nama=v['nama'], accuracy=v['accuracy'], precision=v['precision'], recall=v['recall'],
                  f1=v['f1'], terbaik=(k == ev['terbaik'])) for k, v in ev['model'].items()]
    return jsonify(jsonable(dict(dataset=info_dataset(ds), **_cache[key], model=model, data_uji=ev['data']['uji'])))


# ---------------------------------------------------------------------------
# Evaluasi
# ---------------------------------------------------------------------------
@app.get('/api/evaluasi')
def evaluasi():
    return jsonify(evaluasi_model())


# ---------------------------------------------------------------------------
# Prediksi satu reservasi
# ---------------------------------------------------------------------------
INPUT = ['hotel', 'arrival_date_month', 'lead_time', 'total_malam', 'total_tamu', 'adr',
         'market_segment', 'deposit_type', 'total_of_special_requests', 'required_car_parking_spaces']
ANGKA = {'arrival_date_month', 'lead_time', 'total_malam', 'total_tamu', 'adr',
         'total_of_special_requests', 'required_car_parking_spaces'}
BULAN = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September',
         'Oktober', 'November', 'Desember']


def kalimat(fitur, v):
    if fitur == 'lead_time':
        return f'Lead time {v:g} hari'
    if fitur == 'required_car_parking_spaces':
        return 'Tidak meminta tempat parkir' if v == 0 else f'Meminta {v:g} tempat parkir'
    if fitur == 'total_of_special_requests':
        return 'Tidak ada special request' if v == 0 else f'Ada {v:g} special request'
    if fitur == 'arrival_date_month':
        return f'Kedatangan bulan {BULAN[int(v) - 1]}'
    if fitur == 'adr':
        return f'Harga kamar €{v:g} per malam'
    if fitur == 'total_malam':
        return f'Menginap {v:g} malam'
    if fitur == 'total_tamu':
        return f'{v:g} tamu'
    if fitur == 'market_segment':
        return f'Segmen {v}'
    if fitur == 'deposit_type':
        return f'Deposit {v}'
    return str(v)


@app.post('/api/predict')
def predict():
    body = request.get_json(force=True)
    kode = body.get('model', 'xgboost')
    if kode not in NAMA_MODEL:
        return gagal('Model tidak dikenal.')
    paket = muat_model(kode)
    model, enc = paket['model'], paket['encoder']

    baris = dict(paket['bawaan'])                      # isian lain memakai nilai paling umum
    for f in INPUT:
        if f not in body.get('data', {}):
            return gagal(f'Isian {f} belum diisi.')
        v = body['data'][f]
        try:
            baris[f] = float(v) if f in ANGKA else str(v)
        except (TypeError, ValueError):
            return gagal(f'Isian {f} harus berupa angka.')
        if f in ANGKA and baris[f] < 0:
            return gagal(f'Isian {f} tidak boleh negatif.')
    X = enc.transform(pd.DataFrame([baris]))
    prob = float(model.predict_proba(X)[0])

    # SHAP hanya untuk 10 isian pengguna: fitur lain dibuat sama dengan baris latar
    grup = [g for g in enc.groups if g[0] in INPUT]
    lain = np.concatenate([g[1] for g in enc.groups if g[0] not in INPUT])
    latar = paket['latar'].copy()
    latar[:, lain] = X[0, lain]
    phi = shap_permutasi(model.output, X, latar, grup, n_perm=30, seed=config.SEED)[0]
    urut = np.argsort(-np.abs(phi))[:3]
    alasan = [dict(fitur=grup[i][0], teks=kalimat(grup[i][0], baris[grup[i][0]]),
                   arah='menaikkan risiko' if phi[i] > 0 else 'menurunkan risiko', nilai=round(float(phi[i]), 4))
              for i in urut]
    risiko = 'rendah' if prob < 0.35 else 'sedang' if prob < 0.7 else 'tinggi'
    return jsonify(dict(model=NAMA_MODEL[kode], probabilitas=round(prob * 100, 1), batal=prob >= 0.5,
                        risiko=risiko, alasan=alasan))


@app.get('/')
def root():
    return jsonify(app='HotelGuard API', mode=store.mode)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
