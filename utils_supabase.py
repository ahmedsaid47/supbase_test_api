# utils_supabase.py
import os, requests
from typing import Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()


URL   = os.getenv("SUPABASE_URL").rstrip("/")
ANON  = os.getenv("SUPABASE_ANON_KEY")
SRV   = os.getenv("SUPABASE_SERVICE_KEY")          # admin işlemler

REST  = f"{URL}/rest/v1"
AUTH  = f"{URL}/auth/v1"
HDR   = {"apikey": ANON, "Content-Type": "application/json"}

def _r(method:str, url:str, hdr:Dict[str,str]=None, **kw) -> requests.Response:
    h = HDR.copy(); h.update(hdr or {})
    return requests.request(method, url, headers=h, timeout=10, **kw)

# ---------- AUTH ----------
def register(email:str, pw:str) -> Tuple[requests.Response, Any]:
    return _x("POST", f"{AUTH}/signup", json={"email": email, "password": pw})

def login(email:str, pw:str) -> Tuple[requests.Response, Any]:
    return _x("POST", f"{AUTH}/token?grant_type=password",
              json={"email": email, "password": pw})

def profile(tok:str):   return _r("GET", f"{AUTH}/user",
                                  hdr={"Authorization": f"Bearer {tok}"})
def logout(tok:str):    return _r("POST", f"{AUTH}/logout",
                                  hdr={"Authorization": f"Bearer {tok}"})
def delete_user(uid:str): return _r("DELETE", f"{AUTH}/admin/users/{uid}",
                                    hdr={"Authorization": f"Bearer {SRV}"})

# ---------- NOTES ----------
def create_note(tok:str, title:str, body:str):
    return _r("POST", f"{REST}/test_api?return=representation",
              hdr={"Authorization": f"Bearer {tok}"},
              json={"title": title, "body": body})

def list_notes(tok:str):
    return _r("GET", f"{REST}/test_api", hdr={"Authorization": f"Bearer {tok}"})

def get_note(tok:str, nid:int):
    return _r("GET", f"{REST}/test_api?id=eq.{nid}",
              hdr={"Authorization": f"Bearer {tok}"})

def update_note(tok:str, nid:int, body:str):
    return _r("PATCH", f"{REST}/test_api?id=eq.{nid}",
              hdr={"Authorization": f"Bearer {tok}"}, json={"body": body})

def delete_note(tok:str, nid:int):
    return _r("DELETE", f"{REST}/test_api?id=eq.{nid}",
              hdr={"Authorization": f"Bearer {tok}"})

# ---------- helper ----------
def _x(method:str, url:str, **kw):
    r = _r(method, url, **kw)
    try: return r, r.json()
    except ValueError: return r, {}
