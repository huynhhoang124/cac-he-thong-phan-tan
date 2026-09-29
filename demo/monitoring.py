from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from .models import SecurityEvent
from .security import NodeIdentity, sha256_hex


class CollaborativeDetector:
    def __init__(self, node_id: str, identity: NodeIdentity, quorum: int = 2) -> None:
        self.node_id = node_id
        self.identity = identity
        self.quorum = quorum
        self.denied: dict[str, deque[float]] = defaultdict(deque)
        self.actors: dict[str, deque[tuple[float, str]]] = defaultdict(deque)
        self.alerts: dict[str, dict] = {}
        self.reports: dict[str, set[str]] = defaultdict(set)
        self.incidents: dict[str, dict] = {}
        self.outcomes: list[tuple[bool, bool]] = []
        self._lock = Lock()

    @staticmethod
    def fingerprint(kind: str, source: str, timestamp: float) -> str:
        bucket = int(timestamp // 60)
        return sha256_hex(f"{kind}|{source}|{bucket}".encode("utf-8"))[:24]

    def observe(self, event: SecurityEvent) -> list[dict]:
        now = time.time()
        detected_kinds: list[str] = []
        with self._lock:
            if event.decision == "denied":
                history = self.denied[event.source]
                history.append(now)
                while history and history[0] < now - 30:
                    history.popleft()
                if len(history) >= 3:
                    detected_kinds.append("denied_access_burst")

            actor_history = self.actors[event.source]
            actor_history.append((now, event.actor))
            while actor_history and actor_history[0][0] < now - 30:
                actor_history.popleft()
            sybil_names = {actor for _, actor in actor_history if actor.startswith("sybil-")}
            if len(sybil_names) >= 4:
                detected_kinds.append("sybil_identity_burst")

            detected = bool(detected_kinds)
            self.outcomes.append((event.ground_truth == "malicious", detected))

        return [self._make_alert(kind, event, now) for kind in sorted(set(detected_kinds))]

    def _make_alert(self, kind: str, event: SecurityEvent, now: float) -> dict:
        fp = self.fingerprint(kind, event.source, now)
        payload = {
            "fingerprint": fp,
            "kind": kind,
            "source": event.source,
            "reporter": self.node_id,
            "timestamp": now,
            "evidence": {"event_id": event.event_id, "actor": event.actor, "action": event.action},
        }
        signed = {"payload": payload, "signature": self.identity.sign(payload), "public_key": self.identity.public_key_b64}
        self.accept_verified_alert(signed)
        return signed

    def accept_verified_alert(self, signed: dict) -> dict:
        payload = signed["payload"]
        fp = payload["fingerprint"]
        reporter = payload["reporter"]
        with self._lock:
            self.alerts[f"{fp}:{reporter}"] = signed
            self.reports[fp].add(reporter)
            confirmed = len(self.reports[fp]) >= self.quorum
            if confirmed:
                self.incidents[fp] = {
                    "fingerprint": fp,
                    "kind": payload["kind"],
                    "source": payload["source"],
                    "reporters": sorted(self.reports[fp]),
                    "confirmed": True,
                }
        return {"fingerprint": fp, "reporters": sorted(self.reports[fp]), "confirmed": confirmed}

    def metrics(self) -> dict:
        tp = sum(1 for malicious, detected in self.outcomes if malicious and detected)
        tn = sum(1 for malicious, detected in self.outcomes if not malicious and not detected)
        fp = sum(1 for malicious, detected in self.outcomes if not malicious and detected)
        fn = sum(1 for malicious, detected in self.outcomes if malicious and not detected)
        total = tp + tn + fp + fn
        return {
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "accuracy": round((tp + tn) / total, 3) if total else None,
            "precision": round(tp / (tp + fp), 3) if tp + fp else None,
        }

    def snapshot(self) -> dict:
        return {
            "alerts": list(self.alerts.values())[-30:],
            "incidents": list(self.incidents.values())[-20:],
            "metrics": self.metrics(),
        }
