from __future__ import annotations

import copy
import time
from threading import Lock
from typing import Any

from .security import canonical_json, sha256_hex


class AuditChain:
    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self._records: list[dict[str, Any]] = []
        self._lock = Lock()

    def append(self, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            previous_hash = self._records[-1]["hash"] if self._records else "0" * 64
            body = {
                "index": len(self._records),
                "node_id": self.node_id,
                "timestamp": round(time.time(), 6),
                "event_type": event_type,
                "data": copy.deepcopy(data),
                "previous_hash": previous_hash,
            }
            record = {**body, "hash": sha256_hex(previous_hash.encode("ascii") + canonical_json(body))}
            self._records.append(record)
            return copy.deepcopy(record)

    def verify(self) -> dict[str, Any]:
        previous_hash = "0" * 64
        for index, record in enumerate(self._records):
            body = {key: value for key, value in record.items() if key != "hash"}
            expected = sha256_hex(previous_hash.encode("ascii") + canonical_json(body))
            if record.get("previous_hash") != previous_hash or record.get("hash") != expected:
                return {"valid": False, "broken_at": index, "records": len(self._records)}
            previous_hash = record["hash"]
        return {"valid": True, "broken_at": None, "records": len(self._records)}

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        return copy.deepcopy(self._records[-limit:])

    def tamper_for_demo(self) -> bool:
        with self._lock:
            if not self._records:
                return False
            self._records[0]["data"]["tampered"] = True
            return True

    def clear(self) -> None:
        with self._lock:
            self._records.clear()
