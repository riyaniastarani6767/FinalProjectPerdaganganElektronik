"""
Lapisan penyimpanan.

- Jika SUPABASE_URL dan SUPABASE_SERVICE_KEY diisi: memakai Supabase
  (PostgreSQL lewat REST API + Supabase Storage untuk file CSV).
- Jika tidak diisi: memakai SQLite dan folder lokal (cocok untuk menjalankan di laptop).

Hanya memakai library bawaan Python (sqlite3, urllib, json).
"""
import json
import os
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SUPABASE_URL = os.environ.get('SUPABASE_URL', '').rstrip('/')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')
BUCKET = os.environ.get('SUPABASE_BUCKET', 'datasets')
LOCAL_DIR = Path(os.environ.get('LOCAL_DATA_DIR', Path(__file__).parent / 'instance'))

KOLOM_JSON = {'laporan'}


def sekarang():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------
class SupabaseStore:
    mode = 'supabase'

    def _req(self, method, url, body=None, headers=None, raw=False):
        h = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
        if headers:
            h.update(headers)
        data = None
        if body is not None:
            if isinstance(body, (bytes, bytearray)):
                data = bytes(body)
            else:
                data = json.dumps(body).encode()
                h.setdefault('Content-Type', 'application/json')
        req = urllib.request.Request(url, data=data, headers=h, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                isi = r.read()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f'Supabase {e.code}: {e.read().decode(errors="ignore")}')
        if raw:
            return isi
        return json.loads(isi) if isi else None

    # --- tabel ---
    def _rest(self, table, query=''):
        return f'{SUPABASE_URL}/rest/v1/{table}{query}'

    def insert(self, table, row):
        out = self._req('POST', self._rest(table), row, {'Prefer': 'return=representation'})
        return out[0]

    def update(self, table, row_id, fields):
        self._req('PATCH', self._rest(table, f'?id=eq.{row_id}'), fields)

    def get(self, table, row_id):
        out = self._req('GET', self._rest(table, f'?id=eq.{row_id}&select=*'))
        return out[0] if out else None

    def list(self, table, desc=True):
        order = 'id.desc' if desc else 'id.asc'
        return self._req('GET', self._rest(table, f'?select=*&order={order}')) or []

    def active_dataset(self):
        out = self._req('GET', self._rest('dataset', '?aktif=eq.true&select=*&limit=1'))
        return out[0] if out else None

    def set_active(self, row_id):
        self._req('PATCH', self._rest('dataset', '?aktif=eq.true'), {'aktif': False})
        if row_id is not None:
            self.update('dataset', row_id, {'aktif': True})

    def delete_all(self, table):
        self._req('DELETE', self._rest(table, '?id=gt.0'))

    # --- file ---
    def save_file(self, path, content: bytes):
        url = f'{SUPABASE_URL}/storage/v1/object/{BUCKET}/{urllib.parse.quote(path)}'
        self._req('POST', url, content, {'Content-Type': 'text/csv', 'x-upsert': 'true'})

    def read_file(self, path) -> bytes:
        url = f'{SUPABASE_URL}/storage/v1/object/{BUCKET}/{urllib.parse.quote(path)}'
        return self._req('GET', url, raw=True)

    def upload_target(self, path):
        """URL bertanda tangan agar browser mengunggah file langsung ke Supabase Storage."""
        url = f'{SUPABASE_URL}/storage/v1/object/upload/sign/{BUCKET}/{urllib.parse.quote(path)}'
        out = self._req('POST', url, {}, {'x-upsert': 'true'})
        return {'url': f'{SUPABASE_URL}/storage/v1{out["url"]}', 'method': 'PUT', 'form': True}

    def download_url(self, path, filename):
        url = f'{SUPABASE_URL}/storage/v1/object/sign/{BUCKET}/{urllib.parse.quote(path)}'
        out = self._req('POST', url, {'expiresIn': 3600})
        return f'{SUPABASE_URL}/storage/v1{out["signedURL"]}&download={urllib.parse.quote(filename)}'


# ---------------------------------------------------------------------------
# Lokal (SQLite + folder)
# ---------------------------------------------------------------------------
SKEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS dataset (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_file TEXT NOT NULL,
    path_mentah TEXT,
    path_bersih TEXT,
    sudah_bersih INTEGER DEFAULT 0,
    baris_awal INTEGER, kolom_awal INTEGER,
    baris_bersih INTEGER, kolom_bersih INTEGER,
    persen_batal REAL,
    laporan TEXT,
    aktif INTEGER DEFAULT 0,
    dibuat_pada TEXT
);
"""


class LocalStore:
    mode = 'lokal'

    def __init__(self):
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)
        (LOCAL_DIR / 'files').mkdir(exist_ok=True)
        self.db = LOCAL_DIR / 'hotelguard.db'
        with self._con() as c:
            c.executescript(SKEMA_SQLITE)

    def _con(self):
        c = sqlite3.connect(self.db)
        c.row_factory = sqlite3.Row
        return c

    @staticmethod
    def _decode(row):
        if row is None:
            return None
        d = dict(row)
        for k in KOLOM_JSON:
            if k in d and isinstance(d[k], str):
                try:
                    d[k] = json.loads(d[k])
                except ValueError:
                    pass
        if 'aktif' in d:
            d['aktif'] = bool(d['aktif'])
        if 'sudah_bersih' in d:
            d['sudah_bersih'] = bool(d['sudah_bersih'])
        return d

    @staticmethod
    def _encode(row):
        return {k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in row.items()}

    def insert(self, table, row):
        row = self._encode(row)
        cols = ', '.join(row)
        with self._con() as c:
            cur = c.execute(f'INSERT INTO {table} ({cols}) VALUES ({", ".join("?" * len(row))})', list(row.values()))
            new_id = cur.lastrowid
        return self.get(table, new_id)

    def update(self, table, row_id, fields):
        fields = self._encode(fields)
        sets = ', '.join(f'{k} = ?' for k in fields)
        with self._con() as c:
            c.execute(f'UPDATE {table} SET {sets} WHERE id = ?', [*fields.values(), row_id])

    def get(self, table, row_id):
        with self._con() as c:
            return self._decode(c.execute(f'SELECT * FROM {table} WHERE id = ?', [row_id]).fetchone())

    def list(self, table, desc=True):
        with self._con() as c:
            rows = c.execute(f'SELECT * FROM {table} ORDER BY id {"DESC" if desc else "ASC"}').fetchall()
            return [self._decode(r) for r in rows]

    def active_dataset(self):
        with self._con() as c:
            return self._decode(c.execute('SELECT * FROM dataset WHERE aktif = 1 LIMIT 1').fetchone())

    def set_active(self, row_id):
        with self._con() as c:
            c.execute('UPDATE dataset SET aktif = 0')
            if row_id is not None:
                c.execute('UPDATE dataset SET aktif = 1 WHERE id = ?', [row_id])

    def delete_all(self, table):
        with self._con() as c:
            c.execute(f'DELETE FROM {table}')

    def _file(self, path):
        p = LOCAL_DIR / 'files' / path
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def save_file(self, path, content: bytes):
        self._file(path).write_bytes(content)

    def read_file(self, path) -> bytes:
        return self._file(path).read_bytes()

    def upload_target(self, path):
        return {'url': f'/api/upload/local/{path}', 'method': 'PUT', 'form': True, 'relative': True}

    def download_url(self, path, filename):
        return None          # diunduh langsung lewat Flask


def buat_store():
    return SupabaseStore() if SUPABASE_URL and SUPABASE_KEY else LocalStore()
