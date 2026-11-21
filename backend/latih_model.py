"""
Melatih model final (XGBoost dan Random Forest manual) pada data bawaan, lalu menyimpannya ke folder models/.

Jalankan sekali (atau dari notebook):
    python latih_model.py

Hasil:
    models/model_xgboost.pkl         model XGBoost manual + encoder
    models/model_random_forest.pkl   model Random Forest manual + encoder
    models/evaluasi.json             metrik, confusion matrix, SHAP global, baseline (untuk menu Evaluasi)
"""
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from ml import config                                                     # noqa: E402
from ml.algoritma import (Binner, DecisionTreeGini, RandomForestManual,    # noqa: E402
                          XGBoostManual, hitung_metrik, shap_permutasi, stratified_split)
from ml.preprocessing import FITUR, LABEL, Encoder, clean_raw              # noqa: E402

MODELS = BASE / 'models'


def main():
    MODELS.mkdir(exist_ok=True)
    data, _, info = clean_raw(pd.read_csv(BASE / 'data' / 'hotel_bookings.csv'))
    y = data[LABEL].to_numpy()
    idx_latih, idx_uji = stratified_split(y, test_size=0.2, seed=config.SEED)
    latih = data.iloc[idx_latih]
    enc = Encoder().fit(latih)
    X_latih, X_uji = enc.transform(latih), enc.transform(data.iloc[idx_uji])
    y_latih, y_uji = y[idx_latih], y[idx_uji]

    # nilai bawaan untuk isian yang tidak diisi pengguna (nilai paling umum di data latih)
    bawaan = {}
    for f in FITUR:
        v = latih[f].mode()[0]
        bawaan[f] = v.item() if hasattr(v, 'item') else v

    rng = np.random.default_rng(0)
    latar = X_latih[rng.choice(len(X_latih), 1000, replace=False)]
    hasil = dict(data=dict(nama='Hotel Booking Demand', jumlah=info['baris_bersih'],
                           latih=int(len(idx_latih)), uji=int(len(idx_uji)), persen_batal=info['persen_batal']),
                 model={})

    for kode, nama, kelas, param in [('xgboost', 'XGBoost', XGBoostManual, config.PARAM_XGB),
                                     ('random_forest', 'Random Forest', RandomForestManual, config.PARAM_RF)]:
        t = time.time()
        model = kelas(**param, seed=config.SEED).fit(X_latih, y_latih)
        durasi = time.time() - t
        m = hitung_metrik(y_uji, model.predict_proba(X_uji) >= 0.5)
        phi = shap_permutasi(model.output, X_uji[:200], latar, enc.groups, n_perm=10)
        besar = np.abs(phi).mean(axis=0)
        shap = sorted([dict(fitur=g[0], persen=round(float(v / besar.sum() * 100), 2))
                       for g, v in zip(enc.groups, besar)], key=lambda x: -x['persen'])
        hasil['model'][kode] = dict(nama=nama, **{k: (round(v, 2) if isinstance(v, float) else v) for k, v in m.items()},
                                    shap=shap[:10], parameter=param, durasi_latih=round(durasi, 1))
        with open(MODELS / f'model_{kode}.pkl', 'wb') as f:
            pickle.dump(dict(model=model, encoder=enc, latar=latar, bawaan=bawaan), f)
        print(f'{nama}: F1 {m["f1"]:.2f}%, disimpan ke models/model_{kode}.pkl ({durasi:.1f} detik)')

    # baseline sederhana sebagai pembanding
    b = Binner().fit(X_latih)
    pohon = DecisionTreeGini(max_depth=3, min_samples_leaf=1).fit_binned(
        b.transform(X_latih), y_latih.astype(float), np.ones(len(y_latih)), np.arange(len(y_latih)))
    mb = hitung_metrik(y_uji, pohon.predict_proba_binned(b.transform(X_uji)) >= 0.5)
    hasil['baseline'] = dict(nama='Pohon keputusan kedalaman 3', f1=round(mb['f1'], 2), accuracy=round(mb['accuracy'], 2))
    hasil['terbaik'] = max(hasil['model'], key=lambda k: hasil['model'][k]['f1'])

    (MODELS / 'evaluasi.json').write_text(json.dumps(hasil, indent=2, default=float))
    print('Model terbaik:', hasil['model'][hasil['terbaik']]['nama'])


if __name__ == '__main__':
    main()
