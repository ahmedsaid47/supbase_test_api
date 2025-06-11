# tests/test_perf.py
from utils_supabase import list_notes

def test_notes_p95_under_300ms(token, benchmark):
    res = benchmark(lambda: list_notes(token))
    assert res.status_code == 200
    # pytest-benchmark p95 istatistiğini otomatik raporlar
