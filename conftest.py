# conftest.py
import os, uuid, pytest
from faker import Faker
from utils_supabase import *

fake = Faker()

@pytest.fixture(scope="session")
def email_domain():
    return os.getenv("TEST_EMAIL_DOMAIN", "@example.test")

@pytest.fixture
def fresh_user(email_domain):
    mail = f"u{uuid.uuid4().hex[:8]}{email_domain}"
    pw   = "ValidPassw0rd*"
    r, _ = register(mail, pw); assert r.status_code == 200
    yield {"email": mail, "pw": pw}
    # İstersen temizlik için admin delete_user kullan
    # delete_user(uid)

@pytest.fixture
def token(fresh_user):
    r, j = login(fresh_user["email"], fresh_user["pw"])
    assert r.status_code == 200
    return j["access_token"]
