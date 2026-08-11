
import os
import hashlib
import hmac
import base64
from datetime import datetime, timedelta, timezone
from jose import jwt

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 310000

    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations
    )

    return (
        "pbkdf2_sha256$"
        + str(iterations)
        + "$"
        + base64.b64encode(salt).decode()
        + "$"
        + base64.b64encode(dk).decode()
    )

def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt_b64, hash_b64 = stored.split("$")
        if algorithm != "pbkdf2_sha256":
            return False

        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations)
        )

        return hmac.compare_digest(actual, expected)

    except Exception:
        return False

SECRET_KEY = "my-super-secret-key-change-this-later"
ALGORITHM = "HS256"

def create_token(salesman_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=12)
    return jwt.encode({"sub": str(salesman_id), "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

def salesman_id_from_token(token: str) -> int:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return int(payload["sub"])
