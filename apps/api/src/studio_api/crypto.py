from __future__ import annotations

import hashlib
import hmac
import secrets


def hash_secret(secret: str, pepper: str) -> str:
    return hashlib.sha256(f"{pepper}:{secret}".encode()).hexdigest()


def verify_secret(secret: str, pepper: str, stored_hash: str) -> bool:
    return hmac.compare_digest(hash_secret(secret, pepper), stored_hash)


def generate_token(length: int = 32) -> str:
    return secrets.token_urlsafe(length)


def generate_api_key() -> tuple[str, str, str]:
    """Return (full_key, prefix, secret)."""
    secret_part = secrets.token_urlsafe(24)
    full_key = f"stk_{secret_part}"
    prefix = full_key[:12]
    return full_key, prefix, secret_part
