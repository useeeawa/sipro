# Kredensial Uji SIPRO (demo seed)

Sandi SEMUA akun demo: `Sipro#2026`

| Peran | Email | Catatan |
|---|---|---|
| Super Admin | superadmin@sipro.co.id | akses penuh + admin sistem |
| Owner/Direksi | owner@sipro.co.id | dashboard direksi, laporan |
| Manajer Sales | manager@sipro.co.id | approve diskon, pipeline |
| Marketing Admin | marketing@sipro.co.id | leads, kampanye |
| Sales | sales@sipro.co.id | leads/deal miliknya (uji RBAC 403 konstruksi) |
| Sales 2 | sales2@sipro.co.id | uji isolasi antar sales |
| Finance | finance@sipro.co.id | pembayaran, kas, GL |
| Manajer Proyek | pm@sipro.co.id | konstruksi, kalender, kalibrasi |
| Pelaksana Lapangan | site@sipro.co.id | Papan Mandor, progres (tanpa tombol kalibrasi) |
| Manajer Keuangan | finlead@sipro.co.id | approve fee/komisi/kas bon, tutup periode GL |
| Supervisor Digital Marketing | dmlead@sipro.co.id | otomasi, template WA, broadcast, showroom |
| Staf Digital Marketing | dm@sipro.co.id | inbox WA, broadcast (tanpa approve) |

## Pemisahan tugas yang DIUJI (jangan dianggap bug)
- **Fee mitra**: sales/marketing/manajer **MENGAJUKAN** (`marketing_fee:create`), finance
  **MENYETUJUI + MEMBAYAR** (`approve`/`update`). Karena itu tombol **"Ajukan Fee"
  SENGAJA nonaktif untuk finance** dan `POST /api/partners/rules/issue` menjawab **403**
  untuk finance — itu perilaku benar, bukan cacat.
- **Pemeliharaan jam tahap** (`POST /api/aging/reconcile`): hanya owner/super_admin
  (`aging:manage`). Semua peran boleh MELIHAT laporan umur tahap.
- **Mitra**: sales hanya boleh MELIHAT; finance boleh mengubah **aturan fee**
  (`partners:update`) tetapi TIDAK boleh mendaftarkan mitra baru (`partners:create`).

## Memulihkan lingkungan dari repo (WAJIB dibaca agen lanjutan)
Berkas `.env` TIDAK ada di git. Setelah `git clone`, backend akan **gagal login** sampai
variabel ini ada di `backend/.env` (selain `MONGO_URL` dan `DB_NAME` milik container):

```
JWT_SECRET="<acak, mis. python3 -c 'import secrets;print(secrets.token_urlsafe(48))'>"
```

`security.py` membacanya dengan `os.environ["JWT_SECRET"]` (tanpa nilai bawaan), jadi tanpa
baris itu setiap `POST /api/auth/login` mati 500. Variabel lain (WhatsApp, e-sign, storage)
opsional: bila kosong, modulnya jalan dalam **mode simulasi** dan aplikasi tetap utuh.

Dependensi yang biasanya belum ada di image dasar: `APScheduler`, `reportlab`, `tzlocal`
(`pip install -r backend/requirements.txt` bisa bentrok antara `emergentintegrations` dan
wheel `litellm`; pasang tiga paket itu saja bila paket lain sudah ada).

## Portal Pelanggan
- Login OTP; **OTP master pengujian = `000000`** (env `PORTAL_MASTER_OTP`).
- Nomor/nama pelanggan demo dapat dilihat di halaman Customer (hasil seed `customers`).

## Catatan pengujian
- Tidak ada backdoor auth. Halaman login punya tombol **"Masuk cepat"** yang hanya memanggil
  `POST /api/auth/login` biasa dengan akun demo di atas (boleh dihapus sebelum go-live).
- Bersihkan `localStorage` saat berganti peran agar sesi lama tidak terbawa.
- Login endpoint: `POST {REACT_APP_BACKEND_URL}/api/auth/login` body `{"email": "...", "password": "Sipro#2026"}`.

## Analitik & BI (Fase 44) — yang DIUJI, jangan dianggap bug
- **Metrik yang mengaku "belum ada data" itu BENAR.** 6 dari 47 metrik memang belum punya
  sumber data di sistem (demografi lead, alasan reschedule survei, pendapatan add-on tanpa
  `price_breakdown`, margin proyek tanpa budget operasional, waktu jual dari riwayat status
  bentukan migrasi, alasan lost yang belum diisi). Aturan repo: **jangan pernah menampilkan 0
  untuk data yang tidak ada** — kartunya menulis "belum ada data" + menyebut apa yang kurang.
- **Lencana "Dihitung dari sebagian data (40/47)"** juga benar: angkanya sah tetapi cakupannya
  belum penuh (mis. hanya 40 dari 47 lead punya `stage_history`).
- **Row-scope**: `sales@sipro.co.id` HANYA melihat metrik miliknya (server memaksa lewat
  `owner_email`); tombol "Hitung ulang snapshot" sengaja TIDAK muncul untuknya
  (butuh `analytics:manage`). Peran ber-`manage`: owner, super_admin, manajer sales, manajer
  keuangan, manajer proyek, supervisor DM.
- **Snapshot bukan kebenaran**: `POST /api/analytics/snapshots/rebuild` selalu menghitung ulang
  dan MEMPERBAIKI baris lama; gate membuktikannya dengan sengaja merusak satu nilai snapshot.
