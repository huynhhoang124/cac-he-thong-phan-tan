"""9.4 Trust: trust anchor của cluster, audit hash chain."""
from __future__ import annotations

import copy
import time
from threading import Lock
from typing import Any

from .crypto import canonical, sha256

GENESIS = "0" * 64


class Keyring:
    """Trust anchor: chỉ khóa của node trong cấu hình cluster mới được tin.

    Khóa peer học lần đầu qua /identity rồi ghim lại (trust on first use);
    về sau peer đổi khóa cũng không được chấp nhận.
    """

    def __init__(self, node_id: str, public_key: str) -> None:
        self._keys = {node_id: public_key}

    def learn(self, node_id: str, public_key: str) -> bool:
        pinned = self._keys.setdefault(node_id, public_key)
        return pinned == public_key

    def key_of(self, node_id: str) -> str | None:
        return self._keys.get(node_id)

    def members(self) -> list[str]:
        return sorted(self._keys)


class AuditChain:
    """Nhật ký append-only: hash mỗi bản ghi phủ cả hash bản ghi trước."""

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self._records: list[dict[str, Any]] = []
        self._lock = Lock()

    @staticmethod
    def _hash(body: dict) -> str:
        return sha256(canonical(body))

    def append(self, event: str, data: dict[str, Any]) -> dict:
        with self._lock:
            body = {
                "index": len(self._records),
                "node": self.node_id,
                "time": round(time.time(), 3),
                "event": event,
                "data": copy.deepcopy(data),
                "prev": self._records[-1]["hash"] if self._records else GENESIS,
            }
            self._records.append({**body, "hash": self._hash(body)})
            return copy.deepcopy(self._records[-1])

    def verify(self) -> dict:
        prev = GENESIS
        for record in self._records:
            body = {k: v for k, v in record.items() if k != "hash"}
            if record["prev"] != prev or record["hash"] != self._hash(body):
                return {"valid": False, "broken_at": record["index"], "length": len(self._records)}
            prev = record["hash"]
        return {"valid": True, "broken_at": None, "length": len(self._records), "head": prev}

    def tail(self, limit: int = 12) -> list[dict]:
        return copy.deepcopy(self._records[-limit:])

    def tamper(self, index: int) -> dict | None:
        """Kẻ tấn công sửa nội dung bản ghi cũ nhưng không tính lại hash."""
        with self._lock:
            if not 0 <= index < len(self._records):
                return None
            self._records[index]["data"] = {**self._records[index]["data"], "allowed": True, "tampered": True}
            return copy.deepcopy(self._records[index])

    def clear(self) -> None:
        with self._lock:
            self._records.clear()

