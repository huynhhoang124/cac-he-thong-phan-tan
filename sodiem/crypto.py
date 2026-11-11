"""Khóa Ed25519 của mỗi node + tiện ích băm/ký dùng chung."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def fingerprint(public_key: str) -> str:
    return sha256(base64.b64decode(public_key))[:16]


def verify(public_key: str, payload: dict, signature: str) -> bool:
    try:
        key = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key, validate=True))
        key.verify(base64.b64decode(signature, validate=True), canonical(payload))
        return True
    except (ValueError, TypeError, InvalidSignature):
        return False


class Identity:
    """Khóa riêng của node. Lưu ở data_dir để restart container vẫn giữ danh tính."""

    def __init__(self, node_id: str, data_dir: str | None = None) -> None:
        self.node_id = node_id
        self._key = self._load(Path(data_dir) / f"{node_id}.pem") if data_dir else Ed25519PrivateKey.generate()
        raw = self._key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.public_key = base64.b64encode(raw).decode()
        self.fingerprint = fingerprint(self.public_key)

    @staticmethod
    def _load(path: Path) -> Ed25519PrivateKey:
        try:
            if path.exists():
                return serialization.load_pem_private_key(path.read_bytes(), password=None)
            path.parent.mkdir(parents=True, exist_ok=True)
            key = Ed25519PrivateKey.generate()
            path.write_bytes(key.private_bytes(
                serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
            os.chmod(path, 0o600)
            return key
        except OSError:
            return Ed25519PrivateKey.generate()

    def sign(self, payload: dict) -> str:
        return base64.b64encode(self._key.sign(canonical(payload))).decode()

    def signed(self, payload: dict) -> dict:
        return {"payload": payload, "signature": self.sign(payload)}
