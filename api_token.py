import binascii

import jwt
from Crypto.Random import get_random_bytes

JWT_OPTIONS = {"verify_signature": False}


def generate(user_id: int, key: str | None = None) -> str:
    """Generate a token."""
    payload = {"id": user_id}
    use_key = key or (binascii.hexlify(get_random_bytes(64))).decode("utf-8")
    return jwt.encode(payload, use_key, algorithm="HS512")  # type: ignore # upstream


def get_user_id(token: str) -> int | None:
    """Get user ID from a token."""
    payload = jwt.decode(token, algorithms=["HS512"], options=JWT_OPTIONS)  # type: ignore # upstream
    return payload["id"]
