"""
XGBoost manual (gradient boosting orde dua).

Fungsi di awal : skor awal = log-odds proporsi batal. Tiap pohon dibangun dari gradien (g = p - y)
                 dan hessian (h = p(1 - p)) fungsi log-loss. Gain split:
                 0,5 * [GL^2/(HL+lambda) + GR^2/(HR+lambda) - G^2/(H+lambda)]
                 Bobot daun = -G / (H + lambda). Pohon dibangun berurutan, tiap pohon memperbaiki
                 kesalahan pohon sebelumnya (dikalikan learning_rate).
Fungsi di akhir: skor total (log-odds) diubah menjadi probabilitas dengan fungsi sigmoid
                 sigma(z) = 1 / (1 + e^-z), lalu diputuskan batal jika >= 0,5.
Pre-pruning    : max_depth, min_child_weight
Post-pruning   : gamma (pohon dibangun dulu, lalu split dengan gain < gamma dipangkas dari bawah ke atas)
Data tidak seimbang: scale_pos_weight (gradien kelas batal diperbesar)
"""
import numpy as np

from .pohon_keputusan import Binner, prediksi_pohon


# XGBoost manual
def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


class XGBoostManual:
    """
    Awal  : skor awal = log-odds proporsi batal. Tiap pohon dibangun dari gradien (g = p - y)
            dan hessian (h = p(1 - p)) fungsi log-loss. Gain split:
            0.5 * [GL^2/(HL+lambda) + GR^2/(HR+lambda) - G^2/(H+lambda)]
    Akhir : skor total (log-odds) diubah menjadi probabilitas dengan fungsi sigmoid.
    Pre-pruning : max_depth, min_child_weight
    Post-pruning: gamma (cabang dengan gain < gamma dipangkas dari bawah ke atas)
    """

    def __init__(self, n_estimators=150, learning_rate=0.1, max_depth=6, min_child_weight=3,
                 reg_lambda=1.0, gamma=0.0, subsample=0.8, colsample_bytree=0.6,
                 scale_pos_weight=1.0, n_bins=32, seed=42):
        self.params = dict(n_estimators=n_estimators, learning_rate=learning_rate, max_depth=max_depth,
                           min_child_weight=min_child_weight, reg_lambda=reg_lambda, gamma=gamma,
                           subsample=subsample, colsample_bytree=colsample_bytree,
                           scale_pos_weight=scale_pos_weight)
        self.n_bins = n_bins
        self.seed = seed

    def _build_tree(self, Xb, g, h, idx, feats, rng):
        p = self.params
        B = self.n_bins + 1
        lam = p['reg_lambda']
        feat, binv, left, right, G_, H_, gain_ = [], [], [], [], [], [], []

        def new_node(G, H):
            feat.append(-1); binv.append(0); left.append(-1); right.append(-1)
            G_.append(G); H_.append(H); gain_.append(0.0)
            return len(G_) - 1

        k = len(feats)

        def histogram(ix):
            flat = (Xb[ix][:, feats].astype(np.int64) + (np.arange(k) * B)).ravel()
            Gh = np.bincount(flat, weights=np.repeat(g[ix], k), minlength=k * B).reshape(-1, B)
            Hh = np.bincount(flat, weights=np.repeat(h[ix], k), minlength=k * B).reshape(-1, B)
            return Gh, Hh

        root = new_node(g[idx].sum(), h[idx].sum())
        stack = [(root, idx, 0, histogram(idx))]
        while stack:
            node, ix, depth, hist = stack.pop()
            if depth >= p['max_depth'] or len(ix) < 2:
                continue
            Gh, Hh = hist
            GL, HL = Gh.cumsum(1), Hh.cumsum(1)
            G, H = GL[:, -1:], HL[:, -1:]
            GR, HR = G - GL, H - HL
            gain = 0.5 * (GL ** 2 / (HL + lam) + GR ** 2 / (HR + lam) - G ** 2 / (H + lam))
            valid = (HL >= p['min_child_weight']) & (HR >= p['min_child_weight'])
            gain = np.where(valid, gain, -np.inf)
            best = int(np.argmax(gain))
            if not np.isfinite(gain.flat[best]) or gain.flat[best] <= 0:
                continue
            fi, b = divmod(best, B)
            f = feats[fi]
            mask = Xb[ix, f] <= b
            ixl, ixr = ix[mask], ix[~mask]
            L = new_node(g[ixl].sum(), h[ixl].sum())
            R = new_node(g[ixr].sum(), h[ixr].sum())
            feat[node], binv[node], left[node], right[node] = int(f), int(b), L, R
            gain_[node] = float(gain.flat[best])
            if depth + 1 < p['max_depth']:
                # trik pengurangan histogram: hitung anak yang lebih kecil, anak lain = induk - kecil
                if len(ixl) <= len(ixr):
                    hl = histogram(ixl); hr = (Gh - hl[0], Hh - hl[1])
                else:
                    hr = histogram(ixr); hl = (Gh - hr[0], Hh - hr[1])
            else:
                hl = hr = None
            stack.append((L, ixl, depth + 1, hl))
            stack.append((R, ixr, depth + 1, hr))

        left, right = np.array(left), np.array(right)
        gain_ = np.array(gain_)
        # Post-pruning dengan gamma: dari bawah ke atas, pangkas split yang gain-nya < gamma
        if p['gamma'] > 0:
            for t in range(len(G_) - 1, -1, -1):
                if left[t] >= 0 and left[left[t]] < 0 and left[right[t]] < 0 and gain_[t] < p['gamma']:
                    left[t] = right[t] = -1
        G_, H_ = np.array(G_), np.array(H_)
        weight = -G_ / (H_ + lam)                                   # bobot daun optimal
        return (np.array(feat, dtype=np.int32), np.array(binv, dtype=np.int32),
                left.astype(np.int32), right.astype(np.int32), weight)

    def fit(self, X, y):
        p = self.params
        self.binner = Binner(self.n_bins).fit(X)
        Xb = self.binner.transform(X)
        y = y.astype(np.float64)
        n, F = X.shape
        rng = np.random.default_rng(self.seed)
        w = np.where(y == 1, p['scale_pos_weight'], 1.0)
        rata = (w * y).sum() / w.sum()
        self.base_score = np.log(rata / (1 - rata))                 # log-odds awal
        skor = np.full(n, self.base_score)
        self.trees = []
        n_col = max(1, int(round(F * p['colsample_bytree'])))
        for t in range(p['n_estimators']):
            prob = sigmoid(skor)
            g = (prob - y) * w                                      # gradien log-loss
            h = prob * (1 - prob) * w                               # hessian log-loss
            idx = np.where(rng.random(n) < p['subsample'])[0]
            feats = np.sort(rng.choice(F, n_col, replace=False))
            tree = self._build_tree(Xb, g, h, idx, feats, rng)
            self.trees.append(tree)
            skor += p['learning_rate'] * prediksi_pohon(Xb, *tree)
        return self

    def decision_function(self, X):
        Xb = self.binner.transform(X)
        skor = np.full(len(X), self.base_score)
        for tree in self.trees:
            skor += self.params['learning_rate'] * prediksi_pohon(Xb, *tree)
        return skor

    def predict_proba(self, X):
        return sigmoid(self.decision_function(X))

    def output(self, X):
        """Keluaran yang dijelaskan SHAP: log-odds (sebelum sigmoid)."""
        return self.decision_function(X)
