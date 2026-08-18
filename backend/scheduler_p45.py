"""scheduler_p45.py — job berkala Fase 45 (target dinamis & peringatan anggaran).

Dipisah dari `engine.py` karena berkas itu sudah menyentuh batas NFR 800 baris (gate
`validate_compliance`). Keduanya dibungkus di sini sebagai fungsi kecil yang MENGIMPOR
modulnya secara lokal, supaya scheduler tidak menarik seluruh lapisan anggaran/target saat
`engine` dimuat (menghindari impor melingkar: `budget_reports` → `engine`).
"""
import logging

logger = logging.getLogger("sipro.scheduler.p45")


async def targets_recalc_tick() -> int:
    """Penyesuaian target bulanan (`docs/v2/32` §2.1).

    Idempoten per bulan (`recalc_period`): menjalankan tick berulang TIDAK menumpuk jejak
    palsu di `history[]`. Periode lampau dikunci, jadi laporan historis tidak berubah.
    """
    import target_store as tstore
    return await tstore.recalc_tick()


async def budget_alert_tick() -> int:
    """Peringatan anggaran (≥ `budget.alert_pct`) → notifikasi in-app + tugas FN-11.

    Hanya mengirim saat TINGKAT status naik (aman → waspada → overbudget), supaya pemakai
    tidak menerima pesan yang sama tiap hari lalu mematikan notifikasi.
    """
    import budget_reports as br
    return await br.alert_tick()
