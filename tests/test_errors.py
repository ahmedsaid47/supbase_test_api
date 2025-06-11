# tests/test_errors.py
from utils_supabase import *
from utils_supabase import _r


def test_404_not_found(token):
    r = _r("GET", f"{REST}/nonexistent_table", hdr={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404

def test_400_bad_json(token):
    r = _r("POST", f"{REST}/test_api",
           hdr={"Authorization": f"Bearer {token}"},
           data="not-json")                   # bilinçli bozuk
    assert r.status_code == 400

def test_500_simulation(token):
    # 500 alabilmek için Postgres function'ı bilerek yanlış param yolluyoruz
    r = _r("GET",
           f"{REST}/rpc/doesnt_exist",        # olmayan RPC
           hdr={"Authorization": f"Bearer {token}"})
    assert r.status_code == 500
