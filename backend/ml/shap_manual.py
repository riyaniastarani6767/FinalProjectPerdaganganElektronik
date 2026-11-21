"""
SHAP manual (metode permutasi Shapley) untuk menjelaskan prediksi model.

Untuk tiap baris dan tiap urutan acak fitur: mulai dari baris latar (background), lalu fitur diganti
satu per satu dengan nilai baris yang dijelaskan. Selisih keluaran model saat sebuah fitur masuk
adalah kontribusi fitur itu. Hasil dirata-ratakan atas beberapa permutasi.
Kolom hasil One-Hot Encoding digabung kembali ke fitur asalnya (21 fitur).

Dipakai di:
- ml/latih_model.py : SHAP global (fitur paling berpengaruh) untuk menu Evaluasi
- app.py /api/predict: SHAP lokal (3 alasan utama) untuk menu Prediksi
"""
import numpy as np


# SHAP manual (permutation Shapley)
def shap_permutasi(output_fn, X_jelas, X_latar, groups, n_perm=10, seed=42):
    """
    Menghitung nilai Shapley tiap fitur asal (kolom One-Hot digabung per fitur).
    Untuk tiap baris dan tiap permutasi urutan fitur: mulai dari baris latar (background),
    lalu fitur diganti satu per satu dengan nilai baris yang dijelaskan. Selisih keluaran
    model saat sebuah fitur masuk = kontribusi fitur itu. Dirata-ratakan atas permutasi.
    """
    rng = np.random.default_rng(seed)
    n, F = X_jelas.shape
    G = len(groups)
    col_group = np.zeros(F, dtype=np.int64)
    for gi, (_, cols) in enumerate(groups):
        col_group[cols] = gi
    NM = n * n_perm
    X_rep = np.repeat(X_jelas, n_perm, axis=0)                          # (NM, F)
    Z = X_latar[rng.integers(0, len(X_latar), NM)]                      # baris latar acak
    order = np.argsort(rng.random((NM, G)), axis=1)                     # permutasi urutan fitur
    rank = np.argsort(order, axis=1)                                    # posisi tiap fitur dalam urutan
    langkah = np.arange(G + 1)
    masuk = rank[:, col_group][:, None, :] < langkah[None, :, None]     # (NM, G+1, F)
    data = np.where(masuk, X_rep[:, None, :], Z[:, None, :]).reshape(-1, F)
    out = output_fn(data).reshape(NM, G + 1)
    selisih = out[:, 1:] - out[:, :-1]                                  # kontribusi fitur ke-j dalam urutan
    phi = np.zeros((NM, G))
    phi[np.arange(NM)[:, None], order] = selisih
    phi = phi.reshape(n, n_perm, G).mean(axis=1)                        # (n, G)
    return phi
