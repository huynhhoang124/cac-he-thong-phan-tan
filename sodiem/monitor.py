"""9.6 Monitoring: application-level firewall, SIDS/AIDS sensor, collaborative IDS."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from .crypto import Identity, verify
from .trust import Keyring


class Firewall:
    """Application gateway: chặn payload quá lớn và vượt tần suất theo IP nguồn.

    ponytail: bộ đếm nằm riêng trong từng node, rải request lên nhiều node là lọt;
    muốn chặn toàn cluster phải chia sẻ bộ đếm (đúng điểm demo muốn chỉ ra).
    """

    def __init__(self, limit: int = 60, window: float = 10, max_body: int = 64_000) -> None:
        self.limit, self.window, self.max_body = limit, window, max_body
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def admit(self, source: str, size: int) -> tuple[int, str] | None:
        if size > self.max_body:
            return 413, f"payload {size} byte > {self.max_body}"
        now = time.time()
        hits = self._hits[source]
        while hits and hits[0] < now - self.window:
            hits.popleft()
        if len(hits) >= self.limit:
            return 429, f"{source} vượt {self.limit} request / {self.window:g} giây"
        hits.append(now)
        return None

    def reset(self) -> None:
        self._hits.clear()


# SIDS: mẫu tấn công đã biết.
SIGNATURES = {"../": "path traversal", "' or 1=1": "SQL injection", "<script": "XSS"}


class Detector:
    """Sensor cục bộ (SIDS + AIDS) và bộ ghép cảnh báo theo quorum.

    Không có đồng hồ chung: báo cáo được ghép theo thời điểm *node này nhận*,
    trong cửa sổ `correlate` giây, không dựa vào timestamp của node gửi.
    """

    def __init__(self, identity: Identity, keyring: Keyring, quorum: int = 2,
                 threshold: int = 3, window: float = 30, correlate: float = 600) -> None:
        self.identity, self.keyring = identity, keyring
        self.quorum, self.threshold, self.window, self.correlate = quorum, threshold, window, correlate
        self._lock = Lock()
        self.reset()

    def reset(self) -> None:
        self._denied: dict[str, deque[float]] = defaultdict(deque)
        self._raised: set[tuple[str, str]] = set()
        self._reports: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
        self.incidents: dict[str, dict] = {}
        self.alerts: list[dict] = []

    def observe(self, event: dict) -> list[dict]:
        """Trả về các cảnh báo cục bộ (đã ký) sinh ra từ một sự kiện truy cập."""
        now, source, found = time.time(), event["source"], []
        path = event.get("path", "").lower()
        for pattern, name in SIGNATURES.items():
            if pattern in path:
                found.append(("SIDS", f"{name}: {event['path']}"))
        if event.get("decision") == "denied":
            hits = self._denied[source]
            hits.append(now)
            while hits and hits[0] < now - self.window:
                hits.popleft()
            if len(hits) >= self.threshold:
                found.append(("AIDS", f"{len(hits)} lần bị từ chối / {self.window:g}s (ngưỡng {self.threshold})"))
        alerts = []
        for kind, evidence in found:
            if (kind, source) in self._raised:
                continue
            self._raised.add((kind, source))
            alerts.append(self.identity.signed({"kind": kind, "source": source, "evidence": evidence,
                                                "actor": event.get("actor"), "reporter": self.identity.node_id}))
        for alert in alerts:
            self.accept(alert)
        return alerts

    def accept(self, signed: dict) -> dict:
        """Nhận cảnh báo (của mình hoặc peer). Sensor nói dối/mạo danh bị loại ở đây."""
        p = signed["payload"]
        key = self.keyring.key_of(p["reporter"])
        if key is None:
            raise ValueError(f"reporter '{p['reporter']}' không thuộc cluster")
        if not verify(key, p, signed["signature"]):
            raise ValueError(f"chữ ký không khớp khóa đã ghim của {p['reporter']}")
        now = time.time()
        with self._lock:
            reports = self._reports[(p["kind"], p["source"])]
            reports[p["reporter"]] = now
            for reporter, seen in list(reports.items()):
                if seen < now - self.correlate:
                    del reports[reporter]
            reporters = sorted(reports)
            confirmed = len(reporters) >= self.quorum
            self.alerts.append({**p, "received": now})
            self.alerts = self.alerts[-40:]
            if confirmed:
                self.incidents[f"{p['kind']}|{p['source']}"] = {
                    "kind": p["kind"], "source": p["source"], "evidence": p["evidence"], "reporters": reporters}
        return {"source": p["source"], "kind": p["kind"], "reporters": reporters, "confirmed": confirmed}
