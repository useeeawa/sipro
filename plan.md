# Rencana Development SIPRO — Fase 45 (Target Proyek & Budget/RAB)

Problem statement (verbatim):
> "saya ingin anda lanutkan development dari repo ini https://github.com/waabaksada/sipro lanjutkan fase 45"

Konteks status saat ini:
- Repo sudah pulih, backend+frontend hidup, seed OK, dan `bash scripts/run_all_gates.sh` → **OVERALL PASS (28 gates)**.
- Fase 43 (Ads) & Fase 44 (Analitik & BI `/bi`) sudah selesai dan digembok gate.
- **Fase 45** = `docs/v2/32_TARGET_BUDGET_SPEC.md` (Target + Budget/RAB + realisasi 3 lapis + margin + alert 90%).
- Keputusan: **tidak ada pintu sidebar baru** → fitur masuk sebagai **tab di `/boq`**.

---

## 1) Objectives
1. Implement **Target Proyek** (5 metode) dengan re-baseline bulanan, `lock_past`, `carry_over`, dan jejak `history[]`.
2. Implement **Master Budget (`budget_items`)** yang bisa ditambah user + link ke RAB/BoQ tanpa dua kebenaran (kategori konstruksi = Σ `boq_items`).
3. Implement **Realisasi 3 lapis** (general → kategori → dokumen sumber) dengan rumus exposure/variance, dan **honest state** (0 ≠ belum ada data).
4. Buka metrik yang tertunda: **PRJ-07 (Margin proyek)** jadi bernilai bila data cukup (tanpa mengarang 0).
5. Alert anggaran: **≥ `budget.alert_pct`** kirim **notifikasi in-app + tugas** ke `owner_role`.
6. Tutup fase dengan **gate baru** `verify_budget_target.py` + **uji-mutasi** `mutasi_45.py` dan baseline tetap hijau.

---

## 2) Implementation Steps

### FASE 1 — POC Core (isolasi, WAJIB sebelum UI)
**Output:** `poc/poc_45.py` hijau (exit 0) membuktikan core yang paling rawan gagal.

User stories (POC):
1. Sebagai owner, saya bisa menghitung target bulanan 5 metode dan hasilnya selalu Σ=total target.
2. Sebagai owner, saat bulan berganti, periode lampau tetap dan kekurangan tampil sebagai `carry_over` (bukan target naik misterius).
3. Sebagai finance, exposure (komitmen+realisasi) tidak double-count dan bisa ditelusuri ke sumber.
4. Sebagai PM, angka konstruksi tie-out dengan `opname.cost_control()` (tidak ada dua kebenaran RAB).
5. Sebagai auditor, bila data belum ada maka `value=null` + `missing[]` (bukan Rp 0).

Langkah:
- P1. Buat `poc/poc_45.py` (satu file) yang:
  - menjalankan kalkulasi 5 metode target + recalc bulanan (`keep_total`, `lock_past`, `carry_over`, `history`).
  - membangun ringkasan budget vs actual untuk 1 proyek seed dan **tie-out** bagian konstruksi ke `opname.cost_control()`.
  - memverifikasi drill lapis 3: Σ dokumen sumber == angka lapis 2.
  - memverifikasi aturan jujur: tanpa `budget_items`/target → `value` null dan ada `missing`.
- P2. (Websearch singkat) best-practice re-baseline target bulanan + S-curve weighting, hanya untuk mengunci edge-case.
- P3. Jika POC gagal: perbaiki engine sampai POC stabil, **jangan lanjut**.


### FASE 2 — V1 App Development (backend + frontend end-to-end)
**Output:** tab baru di `/boq` hidup, API lengkap, dan UX jujur.

User stories (V1):
1. Sebagai owner/direksi, saya bisa membuat target proyek (5 metode) dan melihat **pratinjau dampak** sebelum simpan.
2. Sebagai owner, saya bisa aktivasi/menutup target, serta melihat progress target vs realisasi per bulan.
3. Sebagai finance manager, saya bisa membuat `budget_items` (non-konstruksi) dan melihat rencana vs exposure vs variance.
4. Sebagai PM, saya bisa melihat realisasi RAB konstruksi dari data yang sudah ada (BoQ/SPK/claim/AP/material/jurnal) dengan drill sampai dokumen sumber.
5. Sebagai super admin, saya bisa mengubah setting `budget.enforce_cost_ref` (default OFF) dan melihat laporan “biaya belum terpetakan”.

Backend (minimal tetapi lengkap):
- B1. Tambah `backend/reference_p45.py` (SSOT): `target_method`, `target_status`, `budget_match_rule`, `budget_period`, `budget_health`, `cost_source`, dan `budget_category` (admin-extendable).
- B2. Tambah `backend/models_p45.py`: payload target, periods, budget_items, revise, realization drill.
- B3. Implement `backend/target_engine.py` (fungsi murni): 5 metode + recalc tick + validasi `child ≤ parent`.
- B4. Implement `backend/budget_engine.py`: 
  - summary general & by-category & item→dokumen sumber,
  - konstruksi planned = Σ `boq_items` terkait (read-only),
  - exposure/variance/margin/margin_pro sesuai spec.
- B5. Routers:
  - `backend/routers/targets_router.py` sesuai spec (§2.2).
  - `backend/routers/budget_router.py` sesuai spec (§4 endpoint) + laporan `unmapped`.
- B6. Settings: ubah default `budget.enforce_cost_ref` menjadi **False** (tetap bisa dinyalakan via Config Center).
- B7. Scheduler:
  - `targets_recalc_tick` bulanan (simulasi via endpoint manual juga).
  - `budget_alert_tick` harian: jika exposure/rencana ≥ alert_pct → `engine.create_notification` + `workhub.spawn` ke `owner_role`.
  - Tambah jobdesk code baru untuk tindak lanjut anggaran.
- B8. Indexes unik natural key: `project_targets` (org_id+project_id+name?) dan `budget_items` (org_id+project_id+code) agar idempotent.
- B9. Seed: `seed_phase45.py` menambah 1 target aktif + beberapa budget_items non-konstruksi + contoh mapping minimal untuk demo drill.
- B10. Metrics:
  - buka PRJ-07 agar memakai `budget_items` (opex) dan mengaku incomplete bila masih ada missing.
  - tambah 1–2 metrik target (mis. gap target vs actual) masuk dashboard proyek (`/bi`).

Frontend:
- F1. Update `frontend/src/pages/BoQPage.js`: tambah tab **Target & Budget** + **Realisasi RAB** (pakai `TabPage`, sinkron URL).
- F2. Tambah `frontend/src/components/budget/*`:
  - TargetPanel + TargetDialog (preview before save), PeriodTable.
  - BudgetItemsPanel + BudgetItemDialog + Revise dialog.
  - Realization view 3 lapis + drawer/Modal detail dokumen sumber.
  - UnmappedCostPanel (biaya belum terpetakan).
  - Margin panel.
- F3. Ringkasan: kartu target di `ProjectDetailPage` dan kartu/matriks ringkas di tab proyek `/bi` (persona proyek), tanpa hardcode label enum.
- F4. Tambah testIds di `frontend/src/constants/testIds/*` untuk tab baru & komponen inti.

Akhir fase:
- F5. 1 putaran E2E multi-peran (owner, finance_manager/finance, project_manager, sales_manager, super_admin) untuk alur:
  target create→preview→activate→recalc; budget item create→summary→drill dokumen; alert trigger; config enforce toggle.


### FASE 3 — Gate + Uji-mutasi + Governance
**Output:** guardrail bergigi + dokumen diperbarui, baseline tetap PASS.

User stories (QA/Governance):
1. Sebagai maintainer, gate menangkap bila UI menampilkan 0 saat data kosong.
2. Sebagai maintainer, gate gagal bila konstruksi planned tidak tie-out dengan `boq_items`/`cost_control`.
3. Sebagai maintainer, gate gagal bila drill lapis 3 tidak menjumlah ke lapis 2.
4. Sebagai maintainer, gate gagal bila alert tidak membuat notifikasi+tugas saat melewati ambang.
5. Sebagai auditor, perubahan setting enforce tercatat dan perilaku ON/OFF bisa diuji negatif.

Langkah:
- G1. Buat `scripts/verify_budget_target.py` dan daftarkan ke `scripts/run_all_gates.sh` sebagai **gate ke-29**.
  - cek route/tab `/boq` berubah tanpa pintu sidebar baru,
  - cek POC 45 hijau,
  - cek 5 metode target + recalc + history + lock_past,
  - cek realisasi 3 lapis + tie-out konstruksi + kejujuran `value=null` saat missing,
  - cek `budget.enforce_cost_ref` default OFF tapi bila ON menolak dokumen tanpa ref,
  - cek alert menghasilkan notifikasi + task.
- G2. Buat `scripts/mutasi_45.py` (8–12 mutasi) merusak: Σ target, lock_past, carry_over, tie-out, drill sum, honesty, alert, enforce toggle; pastikan gate memerah.
- G3. Update `docs/v2/32_TARGET_BUDGET_SPEC.md` bila ada kontrak yang disesuaikan implementasi.
- G4. Update `docs/v2/40_PETA_NAV_V2.md` (hanya catatan tab baru di `/boq`, tanpa menambah door).
- G5. Update `test_result.md`, `plan.md`, `CODEBASE_MAP.md`, dan `memory/test_credentials.md` (apa yang DIUJI & bukan bug).

---

## 3) Next Actions
1. Implement `poc/poc_45.py` sampai hijau (tie-out + drill + honesty + target math).
2. Tambah backend core: `reference_p45.py`, `models_p45.py`, `target_engine.py`, `budget_engine.py`.
3. Tambah routers `/api/targets/*` dan `/api/budget/*` + seed_phase45.
4. Update default setting: `budget.enforce_cost_ref = False` + UI Config Center tetap bisa menyalakan.
5. Implement UI tab baru di `/boq` + komponen budget/target + kartu ringkasan.
6. Tambah scheduler ticks + jobdesk code + notifikasi+tugas.
7. Buat gate `verify_budget_target.py` + `mutasi_45.py`, jalankan `run_all_gates.sh`.
8. Jalankan E2E multi-peran 1 putaran, lalu update docs/plan/test_result.

---

## 4) Success Criteria
- `python3 poc/poc_45.py` → PASS (tidak ada angka tanpa asal; target math stabil; tie-out konstruksi valid).
- UI `/boq` punya 4 tab: Items, Kendali Biaya, **Target & Budget**, **Realisasi RAB**; tidak ada pintu sidebar baru.
- Alert ≥ `budget.alert_pct` menghasilkan notifikasi in-app + task ke `owner_role`.
- PRJ-07 tidak lagi “belum ada data” bila budget operasional tersedia; tetap jujur bila sebagian.
- `bash scripts/run_all_gates.sh` → **OVERALL PASS** dengan gate baru (29 gates).
- `python3 scripts/mutasi_45.py` → semua mutasi tertangkap, baseline pulih hijau.
