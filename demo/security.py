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


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class NodeIdentity:
    def __init__(self, node_id: str, data_dir: str = "/data") -> None:
        self.node_id = node_id
        path = Path(data_dir)
        try:
            path.mkdir(parents=True, exist_ok=True)
            key_path = path / f"{node_id}.pem"
            if key_path.exists():
                self._private_key = serialization.load_pem_private_key(key_path.read_bytes(), password=None)
            else:
                self._private_key = Ed25519PrivateKey.generate()
                key_path.write_bytes(
                    self._private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )
                os.chmod(key_path, 0o600)
        except OSError:
            self._private_key = Ed25519PrivateKey.generate()

    @property
    def public_key_b64(self) -> str:
        raw = self._private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(raw).decode("ascii")

    @property
    def fingerprint(self) -> str:
        return sha256_hex(base64.b64decode(self.public_key_b64))[:20]

    def sign(self, payload: dict) -> str:
        return base64.b64encode(self._private_key.sign(canonical_json(payload))).decode("ascii")

    @staticmethod
    def verify(public_key_b64: str, payload: dict, signature_b64: str) -> bool:
        try:
            key = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64, validate=True))
            key.verify(base64.b64decode(signature_b64, validate=True), canonical_json(payload))
            return True
        except (ValueError, InvalidSignature):
            return False
