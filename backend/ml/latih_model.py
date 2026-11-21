"""
Melatih model final (XGBoost dan Random Forest manual) pada data bawaan, lalu menyimpannya ke folder models/.

Jalankan dari folder backend:
    python ml/latih_model.py

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

BASE = Path(__file__).resolve().parent.parent          # folder backend
sys.path.insert(0, str(BASE))
from ml.evaluasi import hitung_metrik, stratified_split                   # noqa: E402
from ml.pohon_keputusan import Binner, DecisionTreeGini                  # noqa: E402
from ml.random_forest import RandomForestManual                          # noqa: E402
from ml.shap_manual import shap_permutasi                                # noqa: E402
from ml.xgboost_manual import XGBoostManual                              # noqa: E402
from ml.preprocessing import FITUR, LABEL, Encoder, clean_raw              # noqa: E402

MODELS = BASE / 'models'
SEED = 42

# Parameter terbaik hasil tuning manual di notebook
PARAM_XGB = dict(n_estimators=200, learning_rate=0.1, max_depth=8, min_child_weight=3,
                 reg_lambda=1.0, gamma=0.0, subsample=0.8, colsample_bytree=0.6,
                 scale_pos_weight=2.0)
PARAM_RF = dict(n_estimators=50, max_depth=25, min_samples_split=5, min_samples_leaf=1,
                max_features='sqrt', max_samples=0.6, class_weight='balanced', ccp_alpha=0.0)


def main():
    MODELS.mkdir(exist_ok=True)
    data, _, info = clean_raw(pd.read_csv(BASE / 'data' / 'hotel_bookings.csv'))
    y = data[LABEL].to_numpy()
    idx_latih, idx_uji = stratified_split(y, test_size=0.2, seed=SEED)
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

    for kode, nama, kelas, param in [('xgboost', 'XGBoost', XGBoostManual, PARAM_XGB),
                                     ('random_forest', 'Random Forest', RandomForestManual, PARAM_RF)]:
        t = time.time()
        model = kelas(**param, seed=SEED).fit(X_latih, y_latih)
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

    # baseline sederhana sebagai pembanding (model yang baik harus mengalahkan ini)
    def ringkas(nama, m):
        return dict(nama=nama, **{k: round(m[k], 2) for k in ['accuracy', 'precision', 'recall', 'f1']})

    b = Binner().fit(X_latih)
    pohon = DecisionTreeGini(max_depth=3, min_samples_leaf=1).fit_binned(
        b.transform(X_latih), y_latih.astype(float), np.ones(len(y_latih)), np.arange(len(y_latih)))
    non_refund = X_uji[:, enc.columns.index('deposit_type_Non Refund')] == 1
    hasil['baseline'] = [
        ringkas('Selalu menebak tidak batal', hitung_metrik(y_uji, np.zeros_like(y_uji))),
        ringkas('Aturan: deposit Non Refund berarti batal', hitung_metrik(y_uji, non_refund)),
        ringkas('Pohon keputusan kedalaman 3', hitung_metrik(y_uji, pohon.predict_proba_binned(b.transform(X_uji)) >= 0.5)),
    ]
    hasil['terbaik'] = max(hasil['model'], key=lambda k: hasil['model'][k]['f1'])

    (MODELS / 'evaluasi.json').write_text(json.dumps(hasil, indent=2, default=float))
    print('Model terbaik:', hasil['model'][hasil['terbaik']]['nama'])


if __name__ == '__main__':
    main()
