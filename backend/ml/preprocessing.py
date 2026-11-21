"""
Preprocessing data Hotel Booking Demand (tanpa scikit-learn).

Dua tahap:
1. clean_raw()  : membersihkan data mentah (32 kolom) menjadi data bersih yang
                  masih mudah dibaca (21 fitur + tahun kedatangan + label).
2. Encoder      : mengubah data bersih menjadi matriks angka (68 kolom) untuk model.
                  Encoder di-fit HANYA pada data latih agar tidak terjadi kebocoran data.
"""
import numpy as np
import pandas as pd

BULAN = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
         'August', 'September', 'October', 'November', 'December']

# Kolom yang wajib ada pada data mentah
RAW_REQUIRED = [
    'hotel', 'is_canceled', 'lead_time', 'arrival_date_year', 'arrival_date_month',
    'stays_in_weekend_nights', 'stays_in_week_nights', 'adults', 'children', 'babies',
    'meal', 'country', 'market_segment', 'distribution_channel', 'is_repeated_guest',
    'previous_cancellations', 'previous_bookings_not_canceled', 'reserved_room_type',
    'deposit_type', 'agent', 'company', 'days_in_waiting_list', 'customer_type', 'adr',
    'required_car_parking_spaces', 'total_of_special_requests',
]

# Kolom kebocoran data (baru diketahui setelah status reservasi terjadi)
LEAKAGE = ['reservation_status', 'reservation_status_date', 'assigned_room_type', 'booking_changes']

FITUR_NUMERIK = ['lead_time', 'adr', 'total_malam', 'total_tamu', 'previous_cancellations',
                 'previous_bookings_not_canceled', 'days_in_waiting_list',
                 'required_car_parking_spaces', 'total_of_special_requests']
FITUR_BINER = ['is_repeated_guest', 'punya_company']
FITUR_ORDINAL = ['arrival_date_month']
FITUR_NOMINAL = ['hotel', 'meal', 'country', 'market_segment', 'distribution_channel',
                 'reserved_room_type', 'deposit_type', 'customer_type', 'agent']
FITUR = FITUR_NUMERIK + FITUR_BINER + FITUR_ORDINAL + FITUR_NOMINAL          # 21 fitur
LABEL = 'is_canceled'
CLEAN_COLS = ['arrival_date_year'] + FITUR + [LABEL]                         # 23 kolom


def is_clean(df: pd.DataFrame) -> bool:
    """Data dianggap sudah bersih jika kolomnya persis format data bersih."""
    return set(df.columns) == set(CLEAN_COLS)


def is_raw(df: pd.DataFrame) -> bool:
    return all(c in df.columns for c in RAW_REQUIRED)


def clean_raw(df: pd.DataFrame):
    """Membersihkan data mentah. Mengembalikan (data_bersih, laporan_langkah)."""
    d = df.copy()
    laporan = []
    n0, k0 = d.shape

    # 1. Hapus kolom kebocoran data
    bocor = [c for c in LEAKAGE if c in d.columns]
    d = d.drop(columns=bocor)
    laporan.append(dict(judul='Hapus kolom kebocoran data',
                        detail=', '.join(bocor) if bocor else 'tidak ada kolom kebocoran',
                        hasil=f'{len(bocor)} kolom'))

    # 2. Isi missing value
    n_missing = int(d[['company', 'agent', 'country', 'children']].isna().sum().sum())
    d['punya_company'] = d['company'].notna().astype(int)
    d = d.drop(columns=['company'])
    d['agent'] = d['agent'].fillna(0).astype(int)
    d['country'] = d['country'].fillna('Unknown')
    d['children'] = d['children'].fillna(0).astype(int)
    laporan.append(dict(judul='Isi missing value',
                        detail='company jadi flag punya_company, agent jadi 0, country jadi Unknown, children jadi 0',
                        hasil=f'{n_missing:,} sel'.replace(',', '.')))

    # 3. Hapus data tidak wajar
    tamu = d['adults'] + d['children'] + d['babies']
    buang = (tamu <= 0) | (d['adr'] < 0) | (d['adr'] > 1000)
    d = d[~buang]
    laporan.append(dict(judul='Hapus data tidak wajar',
                        detail='Reservasi tanpa tamu dan ADR di luar 0 sampai 1.000',
                        hasil=f'{int(buang.sum()):,} baris'.replace(',', '.')))

    # 4. Rapikan kategori
    d['meal'] = d['meal'].replace('Undefined', 'SC')
    undef = (d['market_segment'] == 'Undefined') | (d['distribution_channel'] == 'Undefined')
    d = d[~undef]
    laporan.append(dict(judul='Rapikan kategori',
                        detail='meal Undefined jadi SC, segmen/channel Undefined dihapus',
                        hasil=f'{int(undef.sum())} baris'))

    # 5. Gabungkan tipe kamar langka
    vc = d['reserved_room_type'].value_counts()
    langka = list(vc[vc < 100].index)
    d['reserved_room_type'] = d['reserved_room_type'].where(~d['reserved_room_type'].isin(langka), 'Lainnya')
    laporan.append(dict(judul='Gabungkan tipe kamar langka',
                        detail='Tipe kamar dengan kurang dari 100 data jadi Lainnya',
                        hasil=f'{len(langka)} kategori'))

    # 6. Hapus duplikat
    n_sebelum = len(d)
    d = d.drop_duplicates(keep='first')
    laporan.append(dict(judul='Hapus data duplikat', detail='Baris yang identik di semua kolom',
                        hasil=f'{n_sebelum - len(d):,} baris'.replace(',', '.')))

    # 7. Feature engineering
    d['total_malam'] = d['stays_in_weekend_nights'] + d['stays_in_week_nights']
    d['total_tamu'] = d['adults'] + d['children'] + d['babies']
    d['arrival_date_month'] = d['arrival_date_month'].map({b: i for i, b in enumerate(BULAN, 1)})
    d['agent'] = d['agent'].astype(str).replace({'0': 'Tanpa agen'})
    laporan.append(dict(judul='Feature engineering',
                        detail='total_malam, total_tamu, bulan diubah jadi angka 1 sampai 12',
                        hasil='2 fitur baru'))

    d = d[CLEAN_COLS].reset_index(drop=True)

    # 8. Encoding (dilakukan saat training, dicatat agar pengguna tahu bentuk akhirnya)
    enc = Encoder().fit(d)
    laporan.append(dict(judul='Encoding',
                        detail='One-Hot Encoding 9 fitur kategori (country dan agent: 15 teratas + Lainnya)',
                        hasil=f'{len(enc.columns)} fitur'))

    info = dict(baris_awal=int(n0), kolom_awal=int(k0), baris_bersih=int(len(d)),
                kolom_bersih=int(d.shape[1]), kolom_model=int(len(enc.columns) + 1),
                persen_batal=round(float(d[LABEL].mean() * 100), 2))
    return d, laporan, info


class Encoder:
    """One-Hot Encoding manual (drop_first) + pengelompokan 15 kategori teratas."""

    def __init__(self, top_n=15):
        self.top_n = top_n

    def fit(self, d: pd.DataFrame):
        self.kategori = {}
        self.top = {}
        for c in FITUR_NOMINAL:
            s = d[c].astype(str)
            if c in ('country', 'agent'):
                top = list(s.value_counts().head(self.top_n).index)
                s = s.where(s.isin(top), 'Lainnya')
                self.top[c] = top
            cats = sorted(s.unique())
            self.kategori[c] = cats[1:]          # drop_first: kategori pertama jadi acuan
        self.columns = (FITUR_NUMERIK + FITUR_BINER + FITUR_ORDINAL +
                        [f'{c}_{k}' for c in FITUR_NOMINAL for k in self.kategori[c]])
        # kelompok kolom per fitur asal (untuk SHAP)
        self.groups = []
        for f in FITUR:
            idx = [i for i, col in enumerate(self.columns) if col == f or col.startswith(f + '_') and f in FITUR_NOMINAL]
            self.groups.append((f, np.array(idx)))
        return self

    def transform(self, d: pd.DataFrame) -> np.ndarray:
        n = len(d)
        X = np.zeros((n, len(self.columns)), dtype=np.float32)
        j = 0
        for c in FITUR_NUMERIK + FITUR_BINER + FITUR_ORDINAL:
            X[:, j] = d[c].to_numpy(dtype=np.float32)
            j += 1
        for c in FITUR_NOMINAL:
            s = d[c].astype(str)
            if c in self.top:
                s = s.where(s.isin(self.top[c]), 'Lainnya')
            v = s.to_numpy()
            for k in self.kategori[c]:
                X[:, j] = (v == k)
                j += 1
        return X
