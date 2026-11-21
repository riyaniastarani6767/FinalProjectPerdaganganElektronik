"""
Pohon keputusan (Decision Tree) manual dengan Gini impurity, dasar dari Random Forest.

- Binner          : mengelompokkan nilai tiap fitur ke maksimal 32 bin (histogram) agar pencarian split cepat
- prediksi_pohon  : menelusuri pohon untuk banyak baris sekaligus (dipakai Random Forest dan XGBoost)
- DecisionTreeGini:
    Fungsi di awal : Gini impurity = 1 - p_batal^2 - p_tidak^2, split dipilih yang paling menurunkan Gini
    Fungsi di akhir: probabilitas batal = proporsi batal di daun
    Pre-pruning    : max_depth, min_samples_split, min_samples_leaf, max_features, min_impurity_decrease
    Post-pruning   : ccp_alpha (cost complexity pruning) setelah pohon selesai dibangun
"""
import numpy as np


# Binning (histogram) agar pencarian split cepat
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


def prediksi_pohon(Xb, feat, binv, left, right, value):
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


# Decision Tree (Gini) untuk Random Forest
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
        return prediksi_pohon(Xb, self.feat, self.binv, self.left, self.right, self.value)

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
