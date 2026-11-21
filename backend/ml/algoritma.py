"""
Algoritma manual (tanpa scikit-learn / xgboost), hanya numpy.

Isi:
- stratified_split      : pembagian data latih/uji dengan proporsi kelas terjaga
- Binner                : mengelompokkan nilai fitur ke maksimal 32 bin (histogram)
- DecisionTreeGini      : pohon keputusan dengan Gini impurity, pre-pruning, post-pruning (ccp_alpha)
- RandomForestManual    : bagging banyak pohon + fitur acak, keputusan akhir dengan voting (rata-rata probabilitas)
- XGBoostManual         : gradient boosting orde dua (gradien + hessian) untuk log-loss, akhir dengan sigmoid
- hitung_metrik         : confusion matrix, accuracy, precision, recall, F1
- shap_permutasi        : nilai SHAP (Shapley) dengan metode permutasi per fitur asal
"""
import numpy as np


# ---------------------------------------------------------------------------
# Pembagian data
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Binning (histogram) agar pencarian split cepat
# ---------------------------------------------------------------------------
class Binner:
    def __init__(self, max_bins=32):
        self.max_bins = max_bins

    def fit(self, X):
        self.edges = []
        for j in range(X.shape[1]):
            u = np.unique(X[:, j])
            if len(u) <= self.max_bins:
                e = (u[:-1] + u[1:]) / 2                      # titik tengah antar nilai unik
            else:
                q = np.quantile(X[:, j], np.linspace(0, 1, self.max_bins + 1)[1:-1])
                e = np.unique(q)
            self.edges.append(e.astype(np.float64))
        return self

    def transform(self, X):
        Xb = np.empty(X.shape, dtype=np.uint8)
        for j, e in enumerate(self.edges):
            Xb[:, j] = np.searchsorted(e, X[:, j], side='right')
        return Xb


def _predict_tree(Xb, feat, binv, left, right, value):
    """Menelusuri pohon untuk semua baris sekaligus (vectorized)."""
    node = np.zeros(len(Xb), dtype=np.int32)
    rows = np.arange(len(Xb))
    while True:
        internal = left[node] >= 0
        if not internal.any():
            break
        r = rows[internal]
        n = node[internal]
        ke_kiri = Xb[r, feat[n]] <= binv[n]
        node[r] = np.where(ke_kiri, left[n], right[n])
    return value[node]


# ---------------------------------------------------------------------------
# Decision Tree (Gini) untuk Random Forest
# ---------------------------------------------------------------------------
class DecisionTreeGini:
    """
    Pre-pruning : max_depth, min_samples_split, min_samples_leaf, min_impurity_decrease
    Post-pruning: ccp_alpha (cost complexity pruning) setelah pohon selesai dibangun
    """

    def __init__(self, max_depth=12, min_samples_split=10, min_samples_leaf=5,
                 max_features=None, min_impurity_decrease=0.0, ccp_alpha=0.0, n_bins=32, seed=0):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.min_impurity_decrease = min_impurity_decrease
        self.ccp_alpha = ccp_alpha
        self.n_bins = n_bins
        self.rng = np.random.default_rng(seed)

    @staticmethod
    def gini(p):
        # Gini impurity: 1 - p_batal^2 - p_tidak^2
        return 1.0 - p ** 2 - (1.0 - p) ** 2

    def fit_binned(self, Xb, y, w, idx):
        B = self.n_bins + 1
        F = Xb.shape[1]
        k = F if self.max_features is None else min(F, self.max_features)
        W_total = w[idx].sum()
        feat, binv, left, right, value, wsum, imp = [], [], [], [], [], [], []

        def new_node(v, ws, im):
            feat.append(-1); binv.append(0); left.append(-1); right.append(-1)
            value.append(v); wsum.append(ws); imp.append(im)
            return len(value) - 1

        wi, yi = w[idx], y[idx]
        p0 = (wi * yi).sum() / wi.sum()
        root = new_node(p0, wi.sum(), self.gini(p0))
        stack = [(root, idx, 0)]
        while stack:
            node, ix, depth = stack.pop()
            p = value[node]
            if depth >= self.max_depth or len(ix) < self.min_samples_split or p <= 0 or p >= 1:
                continue
            feats = self.rng.choice(F, k, replace=False) if k < F else np.arange(F)
            sub = Xb[ix][:, feats].astype(np.int64) + (np.arange(len(feats)) * B)
            flat = sub.ravel()
            wi, yi = w[ix], y[ix]
            tot = np.bincount(flat, weights=np.repeat(wi, len(feats)), minlength=len(feats) * B).reshape(-1, B)
            pos = np.bincount(flat, weights=np.repeat(wi * yi, len(feats)), minlength=len(feats) * B).reshape(-1, B)
            cnt = np.bincount(flat, minlength=len(feats) * B).reshape(-1, B)
            nl, pl, cl = tot.cumsum(1), pos.cumsum(1), cnt.cumsum(1)
            n, ps, c = nl[:, -1:], pl[:, -1:], cl[:, -1:]
            nr, pr, cr = n - nl, ps - pl, c - cl
            with np.errstate(divide='ignore', invalid='ignore'):
                g_l = self.gini(pl / nl)
                g_r = self.gini(pr / nr)
                anak = nl * g_l + nr * g_r
            parent = n * self.gini(ps / n)
            gain = (parent - anak) / W_total
            valid = (cl >= self.min_samples_leaf) & (cr >= self.min_samples_leaf)
            gain = np.where(valid & np.isfinite(gain), gain, -np.inf)
            best = int(np.argmax(gain))
            fi, b = divmod(best, B)
            if not np.isfinite(gain.flat[best]) or gain.flat[best] <= self.min_impurity_decrease:
                continue
            f = feats[fi]
            mask = Xb[ix, f] <= b
            ixl, ixr = ix[mask], ix[~mask]
            pl_ = (w[ixl] * y[ixl]).sum() / w[ixl].sum()
            pr_ = (w[ixr] * y[ixr]).sum() / w[ixr].sum()
            L = new_node(pl_, w[ixl].sum(), self.gini(pl_))
            R = new_node(pr_, w[ixr].sum(), self.gini(pr_))
            feat[node], binv[node], left[node], right[node] = int(f), int(b), L, R
            stack.append((L, ixl, depth + 1))
            stack.append((R, ixr, depth + 1))

        self.feat = np.array(feat, dtype=np.int32)
        self.binv = np.array(binv, dtype=np.int32)
        self.left = np.array(left, dtype=np.int32)
        self.right = np.array(right, dtype=np.int32)
        self.value = np.array(value, dtype=np.float64)
        self.wsum = np.array(wsum)
        self.imp = np.array(imp)
        if self.ccp_alpha > 0:
            self._post_prune(W_total)
        return self

    def _post_prune(self, W_total):
        """Cost complexity pruning: potong cabang yang tambahan kualitasnya < ccp_alpha."""
        R_node = self.wsum / W_total * self.imp
        R_sub = R_node.copy()
        n_leaf = np.ones(len(self.value))
        for t in range(len(self.value) - 1, -1, -1):          # anak selalu dibuat setelah induk
            if self.left[t] >= 0:
                L, R = self.left[t], self.right[t]
                R_sub[t] = R_sub[L] + R_sub[R]
                n_leaf[t] = n_leaf[L] + n_leaf[R]
                g = (R_node[t] - R_sub[t]) / max(n_leaf[t] - 1, 1)
                if g <= self.ccp_alpha:
                    self.left[t] = self.right[t] = -1
                    R_sub[t], n_leaf[t] = R_node[t], 1

    def predict_proba_binned(self, Xb):
        return _predict_tree(Xb, self.feat, self.binv, self.left, self.right, self.value)

    def n_leaves(self):
        # hanya simpul yang masih terjangkau dari akar
        stack, n = [0], 0
        while stack:
            t = stack.pop()
            if self.left[t] < 0:
                n += 1
            else:
                stack += [self.left[t], self.right[t]]
        return n


# ---------------------------------------------------------------------------
# Random Forest manual
# ---------------------------------------------------------------------------
class RandomForestManual:
    """
    Awal  : setiap pohon dilatih pada sampel bootstrap dan memilih split dengan Gini impurity
            dari subset fitur acak (max_features).
    Akhir : probabilitas batal = rata-rata probabilitas semua pohon (soft voting), lalu threshold 0,5.
    """

    def __init__(self, n_estimators=60, max_depth=14, min_samples_split=10, min_samples_leaf=3,
                 max_features='sqrt', max_samples=0.6, class_weight='balanced', ccp_alpha=0.0,
                 n_bins=32, seed=42):
        self.params = dict(n_estimators=n_estimators, max_depth=max_depth,
                           min_samples_split=min_samples_split, min_samples_leaf=min_samples_leaf,
                           max_features=max_features, max_samples=max_samples,
                           class_weight=class_weight, ccp_alpha=ccp_alpha)
        self.n_bins = n_bins
        self.seed = seed

    def fit(self, X, y):
        p = self.params
        self.binner = Binner(self.n_bins).fit(X)
        Xb = self.binner.transform(X)
        y = y.astype(np.float64)
        n, F = X.shape
        if p['class_weight'] == 'balanced':
            n1 = y.sum()
            w = np.where(y == 1, n / (2 * n1), n / (2 * (n - n1)))
        else:
            w = np.ones(n)
        mf = int(np.sqrt(F)) if p['max_features'] == 'sqrt' else p['max_features']
        rng = np.random.default_rng(self.seed)
        self.trees = []
        for t in range(p['n_estimators']):
            idx = rng.integers(0, n, int(n * p['max_samples']))          # bootstrap (dengan pengembalian)
            tree = DecisionTreeGini(max_depth=p['max_depth'], min_samples_split=p['min_samples_split'],
                                    min_samples_leaf=p['min_samples_leaf'], max_features=mf,
                                    ccp_alpha=p['ccp_alpha'], n_bins=self.n_bins,
                                    seed=int(rng.integers(1e9)))
            tree.fit_binned(Xb, y, w, idx)
            self.trees.append(tree)
        return self

    def predict_proba(self, X):
        Xb = self.binner.transform(X)
        return np.mean([t.predict_proba_binned(Xb) for t in self.trees], axis=0)

    def output(self, X):
        """Keluaran yang dijelaskan SHAP: probabilitas batal."""
        return self.predict_proba(X)


# ---------------------------------------------------------------------------
# XGBoost manual
# ---------------------------------------------------------------------------
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
            skor += p['learning_rate'] * _predict_tree(Xb, *tree)
        return self

    def decision_function(self, X):
        Xb = self.binner.transform(X)
        skor = np.full(len(X), self.base_score)
        for tree in self.trees:
            skor += self.params['learning_rate'] * _predict_tree(Xb, *tree)
        return skor

    def predict_proba(self, X):
        return sigmoid(self.decision_function(X))

    def output(self, X):
        """Keluaran yang dijelaskan SHAP: log-odds (sebelum sigmoid)."""
        return self.decision_function(X)


# ---------------------------------------------------------------------------
# Metrik evaluasi
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# SHAP manual (permutation Shapley)
# ---------------------------------------------------------------------------
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
