"""
Random Forest manual (bagging).

Fungsi di awal : setiap pohon dilatih pada sampel bootstrap (acak dengan pengembalian) dan memilih
                 split dengan Gini impurity dari subset fitur acak (max_features = akar jumlah fitur).
Fungsi di akhir: soft voting, yaitu probabilitas batal = rata-rata probabilitas semua pohon,
                 lalu diputuskan batal jika >= 0,5.
Pre-pruning    : max_depth, min_samples_split, min_samples_leaf, max_features
Post-pruning   : ccp_alpha (diteruskan ke setiap pohon)
Data tidak seimbang: class_weight='balanced' (kelas batal diberi bobot lebih besar)
"""
import numpy as np

from .pohon_keputusan import Binner, DecisionTreeGini


# Random Forest manual
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
