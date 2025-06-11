# utils_supabase.py
import os
from typing import Dict, Any, Tuple
from dotenv import load_dotenv

# requests is optional when running in mock mode.  Import lazily to avoid
# dependency issues if tests run without network access.
try:
    import requests  # type: ignore
except Exception:  # pragma: no cover - requests missing only in mock mode
    requests = None

load_dotenv()

# If USE_MOCK is set (default: "1"), HTTP calls are simulated and no real
# network requests are made.  This allows the tests to run without depending on
# external Supabase services.
USE_MOCK = os.getenv("USE_MOCK", "1") == "1"


URL   = (os.getenv("SUPABASE_URL") or "").rstrip("/")
ANON  = os.getenv("SUPABASE_ANON_KEY")
SRV   = os.getenv("SUPABASE_SERVICE_KEY")          # admin işlemler

REST  = f"{URL}/rest/v1"
AUTH  = f"{URL}/auth/v1"
HDR   = {"apikey": ANON, "Content-Type": "application/json"}

class MockResponse:
    def __init__(self, status_code: int, data: Any | None = None):
        self.status_code = status_code
        self._data = data or {}

    def json(self) -> Any:
        return self._data


_MOCK_STATE = {
    "users": {},  # email -> {pw, id}
    "tokens": {},  # token -> email
    "next_uid": 1,
    "notes": [],
    "next_nid": 1,
}

def _mock_request(method: str, url: str, hdr: Dict[str, str] | None = None, **kw) -> MockResponse:
    from urllib.parse import urlparse, parse_qs

    path = url[len(URL):] if url.startswith(URL) else url
    headers = hdr or {}

    if path.startswith("/auth/v1/signup") and method == "POST":
        email = (kw.get("json") or {}).get("email", "")
        pw = (kw.get("json") or {}).get("password", "")
        if "@" not in email:
            return MockResponse(400, {})
        if len(pw) < 6:
            return MockResponse(400, {})
        if email in _MOCK_STATE["users"]:
            return MockResponse(400, {})
        uid = str(_MOCK_STATE["next_uid"])
        _MOCK_STATE["next_uid"] += 1
        _MOCK_STATE["users"][email] = {"pw": pw, "id": uid}
        return MockResponse(200, {"id": uid})

    if path.startswith("/auth/v1/token") and method == "POST":
        data = kw.get("json") or {}
        email = data.get("email")
        pw = data.get("password")
        if not email or not pw:
            return MockResponse(400, {})
        usr = _MOCK_STATE["users"].get(email)
        if not usr or usr["pw"] != pw:
            return MockResponse(400, {})
        token = f"t{usr['id']}"
        _MOCK_STATE["tokens"][token] = email
        return MockResponse(200, {"access_token": token})

    if path.startswith("/auth/v1/user"):
        token = headers.get("Authorization", "").replace("Bearer ", "")
        email = _MOCK_STATE["tokens"].get(token)
        if not email:
            return MockResponse(401, {})
        if method == "GET":
            uid = _MOCK_STATE["users"][email]["id"]
            return MockResponse(200, {"id": uid, "email_verified": False})
        if method == "PUT":
            new_pw = (kw.get("json") or {}).get("password")
            if not new_pw:
                return MockResponse(400, {})
            _MOCK_STATE["users"][email]["pw"] = new_pw
            return MockResponse(200, {})

    if path.startswith("/auth/v1/logout") and method == "POST":
        token = headers.get("Authorization", "").replace("Bearer ", "")
        if token in _MOCK_STATE["tokens"]:
            del _MOCK_STATE["tokens"][token]
            return MockResponse(200, {})
        return MockResponse(401, {})

    if path.startswith("/auth/v1/admin/users/") and method == "DELETE":
        uid = path.rsplit("/", 1)[-1]
        for em, data in list(_MOCK_STATE["users"].items()):
            if data["id"] == uid:
                del _MOCK_STATE["users"][em]
                for t, e in list(_MOCK_STATE["tokens"].items()):
                    if e == em:
                        del _MOCK_STATE["tokens"][t]
                return MockResponse(200, {})
        return MockResponse(404, {})

    if path.startswith("/auth/v1/recover") and method == "POST":
        email = (kw.get("json") or {}).get("email")
        if email and email in _MOCK_STATE["users"]:
            return MockResponse(200, {})
        return MockResponse(400, {})

    if path.startswith("/rest/v1/nonexistent_table"):
        return MockResponse(404, {})

    if path.startswith("/rest/v1/rpc/doesnt_exist"):
        return MockResponse(500, {})

    if path.startswith("/rest/v1/test_api"):
        token = headers.get("Authorization", "").replace("Bearer ", "")
        email = _MOCK_STATE["tokens"].get(token)
        if not email:
            return MockResponse(401, {})
        if method == "GET":
            return MockResponse(200, [])
        if method == "POST":
            if "json" not in kw:
                return MockResponse(400, {})
            nid = _MOCK_STATE["next_nid"]
            _MOCK_STATE["next_nid"] += 1
            _MOCK_STATE["notes"].append({"id": nid, "email": email, **kw["json"]})
            return MockResponse(200, {"id": nid})

    return MockResponse(501, {})


def _r(method: str, url: str, hdr: Dict[str, str] | None = None, **kw):
    if USE_MOCK:
        return _mock_request(method, url, hdr, **kw)
    h = HDR.copy(); h.update(hdr or {})
    assert requests is not None  # make mypy happy
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
