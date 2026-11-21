"""Perhitungan angka dan grafik Dashboard BI dari data bersih (pandas)."""
import numpy as np
import pandas as pd

BLN_PANJANG = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
BLN = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
NEGARA = {'PRT': 'Portugal', 'GBR': 'Inggris', 'FRA': 'Prancis', 'ESP': 'Spanyol', 'DEU': 'Jerman',
          'ITA': 'Italia', 'IRL': 'Irlandia', 'BEL': 'Belgia', 'BRA': 'Brasil', 'NLD': 'Belanda',
          'USA': 'Amerika Serikat', 'CHE': 'Swiss', 'CN': 'Kanada', 'AUT': 'Austria', 'CHN': 'Tiongkok',
          'SWE': 'Swedia', 'POL': 'Polandia', 'ISR': 'Israel', 'RUS': 'Rusia', 'NOR': 'Norwegia'}


def koma(x, d=1):
    return f'{x:.{d}f}'.replace('.', ',')


def r(x, d=2):
    return round(float(x), d)


def hitung(d: pd.DataFrame) -> dict:
    d = d.copy()
    d['pendapatan'] = d['adr'] * d['total_malam']
    batal = d['is_canceled'] == 1
    total = len(d)
    n_batal = int(batal.sum())
    hilang = float(d.loc[batal, 'pendapatan'].sum())
    real = float(d.loc[~batal, 'pendapatan'].sum())

    per_hotel = d.groupby('hotel')['is_canceled'].agg(['size', 'sum', 'mean'])
    kpi = dict(total=total, batal=n_batal, persen_batal=r(n_batal / total * 100, 1),
               adr=r(d['adr'].mean()), hilang=r(hilang), realisasi=r(real),
               persen_hilang=r(hilang / (hilang + real) * 100, 1) if hilang + real else 0,
               lead=r(d['lead_time'].mean(), 1),
               hotel=[dict(nama=h, jumlah=int(v['size']), persen=r(v['size'] / total * 100, 0),
                           batal=int(v['sum']), persen_batal=r(v['mean'] * 100, 1))
                      for h, v in per_hotel.iterrows()])

    d['periode'] = d['arrival_date_year'].astype(int) * 100 + d['arrival_date_month'].astype(int)
    per = d.groupby('periode').agg(total=('is_canceled', 'size'), batal=('is_canceled', 'sum'))
    rev = d.groupby(['periode', 'is_canceled'])['pendapatan'].sum().unstack(fill_value=0)
    label = [f"{BLN[p % 100 - 1]} {str(p // 100)[2:]}" for p in per.index]
    tren = dict(label=label, total=per['total'].astype(int).tolist(), batal=per['batal'].astype(int).tolist(),
                realisasi=[r(v / 1000, 1) for v in rev.get(0, pd.Series(0, index=per.index)).reindex(per.index, fill_value=0)],
                hilang=[r(v / 1000, 1) for v in rev.get(1, pd.Series(0, index=per.index)).reindex(per.index, fill_value=0)])

    ch = d.groupby('distribution_channel')['is_canceled'].agg(['size', 'mean']).sort_values('size', ascending=False)
    channel = [dict(nama=k, porsi=r(v['size'] / total * 100, 1), persen_batal=r(v['mean'] * 100, 1)) for k, v in ch.iterrows()]

    hm = d.pivot_table(index='hotel', columns='arrival_date_month', values='is_canceled', aggfunc='mean')
    heatmap = dict(bulan=BLN, baris=[dict(hotel=h, nilai=[None if pd.isna(hm.loc[h].get(m)) else r(hm.loc[h].get(m) * 100, 0)
                                                           for m in range(1, 13)]) for h in hm.index])

    ng = d.groupby('country')['is_canceled'].agg(['size', 'mean']).sort_values('size', ascending=False).head(5)
    negara = [dict(kode=k, nama=NEGARA.get(k, k), jumlah=int(v['size']), persen_batal=r(v['mean'] * 100, 1)) for k, v in ng.iterrows()]

    sg = d.groupby('market_segment')['is_canceled'].agg(['size', 'mean'])
    sg = sg[sg['size'] >= 100].sort_values('mean', ascending=False).head(5)
    segmen = [dict(nama=k, jumlah=int(v['size']), persen_batal=r(v['mean'] * 100, 1)) for k, v in sg.iterrows()]

    kel = pd.cut(d['lead_time'], [-1, 7, 30, 90, 180, np.inf], labels=['0-7', '8-30', '31-90', '91-180', '>180'])
    lt = d.groupby(kel, observed=False)['is_canceled'].agg(['size', 'mean'])
    lead = [dict(kelompok=str(k), jumlah=int(v['size']), persen_batal=r(v['mean'] * 100, 1) if v['size'] else 0) for k, v in lt.iterrows()]

    insight = []
    if lead[0]['persen_batal'] > 0:
        rasio = koma(lead[-1]['persen_batal'] / lead[0]['persen_batal'], 1)
        insight.append(f"Pemesanan lebih dari 180 hari sebelumnya batal {rasio} kali lebih sering dibanding 0-7 hari.")
    if heatmap['baris']:
        b0 = max(heatmap['baris'], key=lambda x: max(v or 0 for v in x['nilai']))
        i_max = int(np.nanargmax([v if v is not None else np.nan for v in b0['nilai']]))
        insight.append(f"Tingkat pembatalan tertinggi terjadi di {b0['hotel']} pada bulan {BLN_PANJANG[i_max]} ({b0['nilai'][i_max]:.0f}%).")
    if segmen:
        s0 = segmen[0]
        insight.append(f"Segmen {s0['nama']} menyumbang {koma(s0['jumlah'] / total * 100, 0)}% reservasi dengan tingkat batal "
                       f"{koma(s0['persen_batal'], 1)}%, tertinggi di antara segmen.")

    return dict(kpi=kpi, tren=tren, channel=channel, heatmap=heatmap, negara=negara,
                segmen=segmen, lead=lead, insight=insight)
