"""Parameter terbaik hasil tuning manual di notebook (dipakai aplikasi)."""

PARAM_XGB = dict(n_estimators=200, learning_rate=0.1, max_depth=8, min_child_weight=3,
                 reg_lambda=1.0, gamma=0.0, subsample=0.8, colsample_bytree=0.6,
                 scale_pos_weight=2.0)

PARAM_RF = dict(n_estimators=50, max_depth=25, min_samples_split=5, min_samples_leaf=1,
                max_features='sqrt', max_samples=0.6, class_weight='balanced', ccp_alpha=0.0)

SPLIT_PILIHAN = {'90:10': 0.1, '80:20': 0.2, '70:30': 0.3, '60:40': 0.4}
SEED = 42
SHAP_N_BARIS = 200      # jumlah data uji yang dijelaskan SHAP
SHAP_N_PERMUTASI = 10
