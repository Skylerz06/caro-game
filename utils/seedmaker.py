"""Quản lý seed ngẫu nhiên theo phiên và theo từng luồng sử dụng."""

from __future__ import annotations

import hashlib
import secrets


def new_global_seed() -> int:
    """Sinh seed 64-bit mới từ entropy của hệ điều hành."""
    return secrets.randbits(64)


def derive_seed(global_seed: int, stream: str) -> int:
    """Tách seed độc lập cho opening, X và O từ cùng global seed."""
    payload = f"{global_seed}:{stream}".encode("utf-8")
    digest = hashlib.blake2b(payload, digest_size=8).digest()
    return int.from_bytes(digest, byteorder="big", signed=False)
