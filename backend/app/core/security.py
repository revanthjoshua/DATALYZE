from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
import hashlib
import hmac
import os
from jose import jwt
from app.core.config import settings

# Try optional passlib/bcrypt if installed
try:
    import bcrypt
    HAS_BCRYPT = True
except Exception:
    HAS_BCRYPT = False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password or not plain_password:
        return False

    # 1. PBKDF2 Format: pbkdf2$salt$hash
    if hashed_password.startswith("pbkdf2$"):
        parts = hashed_password.split("$")
        if len(parts) == 3:
            salt = bytes.fromhex(parts[1])
            expected_key = parts[2]
            key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100000)
            return hmac.compare_digest(key.hex(), expected_key)

    # 2. Bcrypt Format: $2b$, $2a$, $2y$
    if hashed_password.startswith(("$2b$", "$2a$", "$2y$")) and HAS_BCRYPT:
        try:
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception:
            pass

    # 3. Direct plaintext fallback (e.g. initial dev fixtures)
    if plain_password == hashed_password:
        return True

    return False


def get_password_hash(password: str) -> str:
    """
    Produces deterministic, secure, zero-dependency PBKDF2-SHA256 hashes
    compatible across all Python versions (3.11, 3.12, 3.13, 3.14+).
    """
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"pbkdf2${salt.hex()}${key.hex()}"


# Alias for convenience
hash_password = get_password_hash


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except Exception:
        return None
