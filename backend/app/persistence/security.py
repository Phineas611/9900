# backend/app/persistence/security.py
import secrets
import hashlib
import time
from itsdangerous import URLSafeSerializer, BadSignature

def _gen_salt(n_bytes: int = 16) -> str:
    return secrets.token_hex(n_bytes)

def _pbkdf2(password: str, salt_hex: str, iterations: int = 100_000) -> str:
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
    return dk.hex()

def hash_password(password: str) -> str:
    salt = _gen_salt()
    h = _pbkdf2(password, salt)
    return f"{salt}${h}"

def verify_password(password: str, stored: str) -> bool:
    try:
        salt, correct = stored.split("$", 1)
    except ValueError:
        return False
    calc = _pbkdf2(password, salt)
    return secrets.compare_digest(calc, correct)

SECRET_KEY = "123456"
SIGNER = URLSafeSerializer(SECRET_KEY, salt="session")

def sign_session(user_id: int, expire_seconds: int = 86400) -> str:
    payload = {"uid": user_id, "exp": int(time.time()) + expire_seconds}
    return SIGNER.dumps(payload)

def verify_session(token: str) -> int | None:
    try:
        data = SIGNER.loads(token)
    except BadSignature:
        return None
    if data.get("exp", 0) < int(time.time()):
        return None
    return data.get("uid")
