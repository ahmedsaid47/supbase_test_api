# tests/test_auth.py
import uuid, pytest
from utils_supabase import *
import pytest_check as check

from utils_supabase import _r


# --- Login ---
def test_login_success(fresh_user):
    r, _ = login(fresh_user["email"], fresh_user["pw"])
    assert r.status_code == 200

@pytest.mark.parametrize("missing", ["email", "password"])
def test_login_missing_field(fresh_user, missing):
    data = {"email": fresh_user["email"], "password": fresh_user["pw"]}
    data.pop(missing)
    r = _r("POST", f"{AUTH}/token?grant_type=password", json=data)
    assert r.status_code == 400

def test_login_wrong_password(fresh_user):
    r, _ = login(fresh_user["email"], "Wrong123!")
    assert r.status_code == 400

def test_login_unregistered():
    r, _ = login("nouser@example.test", "Pass123!")
    assert r.status_code == 400

# --- Register ---
def test_register_duplicate(fresh_user):
    r, _ = register(fresh_user["email"], "Another1*")
    assert r.status_code == 400

def test_register_invalid_email():
    r, _ = register("not-mail", "Abcdef1*")
    assert r.status_code == 400

def test_register_short_password(email_domain):
    r, _ = register(f"x{uuid.uuid4().hex[:5]}{email_domain}", "123")
    assert r.status_code == 400

# --- Token verify & profile ---
def test_profile_valid(token):
    r = profile(token)
    assert r.status_code == 200
    check.equal(r.json().get("email_verified"), False)

def test_profile_bad_token():
    r = profile("eyJbadToken")
    assert r.status_code in (401, 403)

# --- Change password ---
def test_change_password_flow(fresh_user, token):
    new = "N3wPass*12"
    r = _r("PUT", f"{AUTH}/user",
           hdr={"Authorization": f"Bearer {token}"},
           json={"password": new})
    assert r.status_code == 200
    # eski şifre login başarısız
    r2, _ = login(fresh_user["email"], fresh_user["pw"])
    assert r2.status_code == 400
    # yeni şifre başarılı
    r3, _ = login(fresh_user["email"], new)
    assert r3.status_code == 200

# --- Forgot password (e-posta yollandı mı test) ---
def test_forgot_password_ok(fresh_user):
    r = _r("POST", f"{AUTH}/recover", json={"email": fresh_user["email"]})
    assert r.status_code == 200

@pytest.mark.parametrize("bad", ["", "badmail"])
def test_forgot_password_bad(bad):
    r = _r("POST", f"{AUTH}/recover", json={"email": bad})
    assert r.status_code == 400

# --- Logout ---
def test_logout_ok(token):
    r = logout(token)
    assert r.status_code == 200

def test_logout_missing():
    r = logout("")
    assert r.status_code in (401, 403)

# --- Delete account ---
def test_delete_account(token):
    uid = profile(token).json()["id"]
    r = delete_user(uid)
    assert r.status_code == 200
