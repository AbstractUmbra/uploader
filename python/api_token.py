import binascii
from typing import Optional

import jwt
from Crypto.Random import get_random_bytes


def generate(user_id: int, key=None) -> str:
    """Generate a token."""
    payload = {"id": user_id}
    key = key or binascii.hexlify(get_random_bytes(20))
    return jwt.encode(payload, key, algorithm='HS512').decode()


def get_user_id(token: str) -> Optional[int]:
    """Get user ID from a token."""
    try:
        payload = jwt.decode(token, verify=False, algorithms=['HS512'])
        return payload['id']
    except jwt.DecodeError:
        return None
