from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path
from typing import Any

import pika

try:
    from .common import QUEUE_NAME, append_jsonl, mode_is_durable, now_iso, open_connection
except ImportError:
    from common import (  # type: ignore
        QUEUE_NAME,
        append_jsonl,
        mode_is_durable,
        now_iso,
        open_connection,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Consumer xu ly don hang")
    parser.add_argument("--name", default="consumer-1")
    parser.add_argument(
        "--mode", choices=("persistent", "transient"), default="persistent"
    )
    parser.add_argument("--queue", default=QUEUE_NAME)
    parser.add_argument("--sleep-min", type=float, default=1.0)
    parser.add_argument("--sleep-max", type=float, default=3.0)
    parser.add_argument(
        "--max-messages", type=int, default=0, help="0 nghia la chay lien tuc"
    )
    parser.add_argument("--log-file", default=None)
    return parser.parse_args()


def decode_order(body: bytes) -> dict[str, Any]:
    order = json.loads(body.decode("utf-8"))
    required = {
        "maDonHang",
        "danhSachSanPham",
        "tongTien",
        "thoiGianGui",
        "thoiGianGuiEpoch",
    }
    missing = required.difference(order)
    if missing:
        raise ValueError(f"Thieu truong bat buoc: {', '.join(sorted(missing))}")
    return order


def main() -> None:
    args = parse_args()
    if args.sleep_min < 0 or args.sleep_max < args.sleep_min:
        raise SystemExit("Khoang sleep khong hop le")
    if args.max_messages < 0:
        raise SystemExit("--max-messages khong duoc am")

    durable = mode_is_durable(args.mode)
    log_file = args.log_file or str(
        Path(__file__).resolve().parents[1] / "logs" / f"{args.name}.jsonl"
    )
    connection = open_connection()
    channel = connection.channel()
    channel.queue_declare(queue=args.queue, durable=durable)
    channel.basic_qos(prefetch_count=1)
    processed_count = 0

    def on_message(
        ch: pika.adapters.blocking_connection.BlockingChannel,
        method: pika.spec.Basic.Deliver,
        properties: pika.BasicProperties,
        body: bytes,
    ) -> None:
        nonlocal processed_count
        received_epoch = time.time()
        received_at = now_iso()
        try:
            order = decode_order(body)
            latency_ms = (received_epoch - float(order["thoiGianGuiEpoch"])) * 1000
            print(
                f"[{args.name}] NHAN {order['maDonHang']} | {received_at} | "
                f"do_tre={latency_ms:.2f}ms",
                flush=True,
            )
            append_jsonl(
                log_file,
                {
                    "event": "received",
                    "consumer": args.name,
                    "receivedAt": received_at,
                    "latencyMs": round(latency_ms, 3),
                    **order,
                },
            )

            processing_seconds = random.uniform(args.sleep_min, args.sleep_max)
            time.sleep(processing_seconds)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            processed_count += 1
            finished_at = now_iso()
            append_jsonl(
                log_file,
                {
                    "event": "processed",
                    "consumer": args.name,
                    "maDonHang": order["maDonHang"],
                    "processingSeconds": round(processing_seconds, 3),
                    "finishedAt": finished_at,
                },
            )
            print(
                f"[{args.name}] XONG {order['maDonHang']} | {finished_at} | "
                f"xu_ly={processing_seconds:.2f}s | da_ack",
                flush=True,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
            print(f"[{args.name}] LOI thong diep: {exc}; loai bo thong diep.", flush=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        if args.max_messages and processed_count >= args.max_messages:
            ch.stop_consuming()

    channel.basic_consume(queue=args.queue, on_message_callback=on_message, auto_ack=False)
    print(
        f"[{args.name}] Dang nghe queue={args.queue}, mode={args.mode}. "
        "Nhan Ctrl+C de dung.",
        flush=True,
    )
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        print(f"[{args.name}] Tong da xu ly: {processed_count} thong diep.")
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()

