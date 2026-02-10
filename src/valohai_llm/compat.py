import secrets
import time
import uuid


def _uuid7() -> uuid.UUID:
    """
    Generate a UUIDv7 (RFC 9562) with millisecond precision timestamp.
    """
    timestamp_ms = int(time.time() * 1000)
    rand_bytes = secrets.token_bytes(10)
    rand_a = int.from_bytes(rand_bytes[0:2], "big") & 0x0FFF
    high = (timestamp_ms << 16) | (0x7 << 12) | rand_a
    rand_b = int.from_bytes(rand_bytes[2:10], "big") & 0x3FFFFFFFFFFFFFFF
    low = (0b10 << 62) | rand_b
    return uuid.UUID(int=(high << 64) | low)


uuid7 = getattr(uuid, "uuid7", _uuid7)
