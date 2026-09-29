from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pika


QUEUE_NAME = "don_hang"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="milliseconds")


def mode_is_durable(mode: str) -> bool:
    if mode not in {"persistent", "transient"}:
        raise ValueError("mode phai la 'persistent' hoac 'transient'")
    return mode == "persistent"


def build_order(index: int, prefix: str = "DH") -> dict[str, Any]:
    sent_epoch = time.time()
    return {
        "maDonHang": f"{prefix}{index:03d}",
        "danhSachSanPham": [f"SP{index:03d}", f"SP{index + 1:03d}"],
        "tongTien": float(100_000 + index * 25_000),
        "thoiGianGui": datetime.fromtimestamp(sent_epoch).astimezone().isoformat(
            timespec="milliseconds"
        ),
        "thoiGianGuiEpoch": sent_epoch,
    }


def append_jsonl(path: str | Path, event: dict[str, Any]) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def connection_parameters() -> pika.ConnectionParameters:
    credentials = pika.PlainCredentials(
        os.getenv("RABBITMQ_USER", "guest"),
        os.getenv("RABBITMQ_PASSWORD", "guest"),
    )
    return pika.ConnectionParameters(
        # 127.0.0.1 tranh do tre IPv6 fallback cua localhost tren Docker Desktop/Windows.
        host=os.getenv("RABBITMQ_HOST", "127.0.0.1"),
        port=int(os.getenv("RABBITMQ_PORT", "5672")),
        virtual_host=os.getenv("RABBITMQ_VHOST", "/"),
        credentials=credentials,
        heartbeat=30,
        blocked_connection_timeout=30,
        connection_attempts=8,
        retry_delay=2,
    )


def open_connection() -> pika.BlockingConnection:
    return pika.BlockingConnection(connection_parameters())

