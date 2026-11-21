-- Jalankan di Supabase: menu SQL Editor -> New query -> Run

create table if not exists dataset (
    id bigint generated always as identity primary key,
    nama_file text not null,
    path_mentah text,
    path_bersih text,
    sudah_bersih boolean default false,
    baris_awal integer,
    kolom_awal integer,
    baris_bersih integer,
    kolom_bersih integer,
    persen_batal real,
    laporan jsonb,
    aktif boolean default false,
    dibuat_pada timestamptz default now()
);


-- Bucket penyimpanan file CSV (privat, diakses lewat backend dengan service key)
insert into storage.buckets (id, name, public)
values ('datasets', 'datasets', false)
on conflict (id) do nothing;
