from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pika

try:
    from .common import (
        QUEUE_NAME,
        append_jsonl,
        build_order,
        mode_is_durable,
        now_iso,
        open_connection,
    )
except ImportError:
    from common import (  # type: ignore
        QUEUE_NAME,
        append_jsonl,
        build_order,
        mode_is_durable,
        now_iso,
        open_connection,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Producer dat hang cho RabbitMQ")
    parser.add_argument("--count", type=int, default=1, help="So thong diep can gui")
    parser.add_argument(
        "--mode", choices=("persistent", "transient"), default="persistent"
    )
    parser.add_argument("--interval", type=float, default=0.0, help="Do tre giua hai lan gui")
    parser.add_argument("--prefix", default="DH", help="Tien to ma don hang")
    parser.add_argument("--queue", default=QUEUE_NAME)
    parser.add_argument("--log-file", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.count < 1:
        raise SystemExit("--count phai lon hon 0")
    if args.interval < 0:
        raise SystemExit("--interval khong duoc am")

    durable = mode_is_durable(args.mode)
    log_file = args.log_file or str(
        Path(__file__).resolve().parents[1] / "logs" / f"producer-{args.mode}.jsonl"
    )
    connection = open_connection()
    channel = connection.channel()

    try:
        channel.queue_declare(queue=args.queue, durable=durable)
        channel.confirm_delivery()
        started = time.perf_counter()

        for index in range(1, args.count + 1):
            order = build_order(index, args.prefix)
            body = json.dumps(order, ensure_ascii=False).encode("utf-8")
            channel.basic_publish(
                exchange="",
                routing_key=args.queue,
                body=body,
                mandatory=True,
                properties=pika.BasicProperties(
                    content_type="application/json",
                    content_encoding="utf-8",
                    delivery_mode=2 if durable else 1,
                    message_id=order["maDonHang"],
                    timestamp=int(order["thoiGianGuiEpoch"]),
                ),
            )
            event = {
                "event": "sent",
                "mode": args.mode,
                "queue": args.queue,
                "confirmed": True,
                "loggedAt": now_iso(),
                **order,
            }
            append_jsonl(log_file, event)
            print(
                f"[GUI] {order['maDonHang']} | {order['thoiGianGui']} | "
                f"mode={args.mode} | confirmed=True",
                flush=True,
            )
            if args.interval:
                time.sleep(args.interval)

        elapsed = time.perf_counter() - started
        summary = {
            "event": "producer_summary",
            "mode": args.mode,
            "count": args.count,
            "elapsedSeconds": round(elapsed, 6),
            "loggedAt": now_iso(),
        }
        append_jsonl(log_file, summary)
        print(f"[XONG] Da gui {args.count} thong diep trong {elapsed:.3f} giay.")
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()

