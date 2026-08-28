from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


MIN_PASSWORD_LENGTH = 12


def validate_password_length(password: str) -> None:
    from studio_api.errors import APIError

    if len(password) < MIN_PASSWORD_LENGTH:
        raise APIError(
            "password_too_short",
            "Password must be at least 12 characters",
            422,
        )
