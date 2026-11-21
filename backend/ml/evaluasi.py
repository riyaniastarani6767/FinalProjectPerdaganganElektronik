"""
Pembagian data dan metrik evaluasi (manual).

- stratified_split : membagi data latih/uji dengan proporsi kelas batal yang sama
- hitung_metrik    : confusion matrix (TN, FP, FN, TP), accuracy, precision, recall, F1-score
"""
import numpy as np


# Pembagian data
def stratified_split(y, test_size=0.2, seed=42):
    rng = np.random.default_rng(seed)
    idx_latih, idx_uji = [], []
    for kelas in np.unique(y):
        idx = np.where(y == kelas)[0]
        rng.shuffle(idx)
        n_uji = int(round(len(idx) * test_size))
        idx_uji.append(idx[:n_uji])
        idx_latih.append(idx[n_uji:])
    latih = np.concatenate(idx_latih)
    uji = np.concatenate(idx_uji)
    rng.shuffle(latih)
    rng.shuffle(uji)
    return latih, uji


# Metrik evaluasi
def hitung_metrik(y_true, y_pred):
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    acc = (tp + tn) / len(y_true)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return dict(accuracy=acc * 100, precision=prec * 100, recall=rec * 100, f1=f1 * 100,
                tn=tn, fp=fp, fn=fn, tp=tp)
