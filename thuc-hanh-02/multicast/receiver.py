from __future__ import annotations

import argparse
import json
import socket
import struct
import time
from pathlib import Path

try:
    from .common import DEFAULT_GROUP, DEFAULT_PORT, append_jsonl, now_iso
except ImportError:
    from common import DEFAULT_GROUP, DEFAULT_PORT, append_jsonl, now_iso  # type: ignore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UDP multicast receiver")
    parser.add_argument("--name", default="receiver-1")
    parser.add_argument("--group", default=DEFAULT_GROUP)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--interface",
        default="0.0.0.0",
        help="IPv4 cua card mang; mac dinh de he dieu hanh tu chon",
    )
    parser.add_argument("--count", type=int, default=0, help="0 nghia la nhan lien tuc")
    parser.add_argument("--timeout", type=float, default=0.0, help="0 nghia la khong timeout")
    parser.add_argument("--log-file", default=None)
    return parser.parse_args()


def create_socket(group: str, port: int, interface: str, timeout: float) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if hasattr(socket, "SO_REUSEPORT"):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            pass
    sock.bind(("", port))
    membership = struct.pack(
        "=4s4s", socket.inet_aton(group), socket.inet_aton(interface)
    )
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
    if timeout > 0:
        sock.settimeout(timeout)
    return sock


def main() -> None:
    args = parse_args()
    if args.count < 0 or args.timeout < 0:
        raise SystemExit("--count va --timeout khong duoc am")
    log_file = args.log_file or str(
        Path(__file__).resolve().parents[1] / "logs" / f"{args.name}.jsonl"
    )
    sock = create_socket(args.group, args.port, args.interface, args.timeout)
    received_count = 0
    print(
        f"[{args.name}] Da join {args.group}:{args.port}. Nhan Ctrl+C de dung.",
        flush=True,
    )

    try:
        while args.count == 0 or received_count < args.count:
            try:
                payload, sender_address = sock.recvfrom(65535)
            except socket.timeout:
                print(f"[{args.name}] Het thoi gian cho ({args.timeout}s).")
                break

            received_epoch = time.time()
            try:
                message = json.loads(payload.decode("utf-8"))
                latency_ms = (received_epoch - float(message["sentEpoch"])) * 1000
            except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                print(f"[{args.name}] Bo qua goi khong hop le tu {sender_address}: {exc}")
                continue

            received_count += 1
            received_at = now_iso()
            event = {
                "event": "received",
                "receiver": args.name,
                "sender": f"{sender_address[0]}:{sender_address[1]}",
                "receivedAt": received_at,
                "latencyMs": round(latency_ms, 3),
                **message,
            }
            append_jsonl(log_file, event)
            print(
                f"[{args.name}] seq={message['seq']} | gui={message['sentAt']} | "
                f"nhan={received_at} | do_tre={latency_ms:.2f}ms",
                flush=True,
            )
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
        print(f"[{args.name}] Tong da nhan: {received_count} ban tin.")


if __name__ == "__main__":
    main()

