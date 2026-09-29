from __future__ import annotations

import argparse
import json
import socket
import time
from pathlib import Path

try:
    from .common import DEFAULT_GROUP, DEFAULT_PORT, append_jsonl, now_iso
except ImportError:
    from common import DEFAULT_GROUP, DEFAULT_PORT, append_jsonl, now_iso  # type: ignore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UDP multicast sender")
    parser.add_argument("--group", default=DEFAULT_GROUP)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--count", type=int, default=0, help="0 nghia la gui lien tuc")
    parser.add_argument("--ttl", type=int, default=2)
    parser.add_argument("--log-file", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.interval < 0 or args.count < 0:
        raise SystemExit("--interval va --count khong duoc am")
    if not 1 <= args.ttl <= 255:
        raise SystemExit("--ttl phai nam trong 1..255")

    log_file = args.log_file or str(
        Path(__file__).resolve().parents[1] / "logs" / "multicast-sender.jsonl"
    )
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, args.ttl)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

    sequence = 0
    try:
        while args.count == 0 or sequence < args.count:
            sent_epoch = time.time()
            message = {
                "seq": sequence,
                "sentAt": now_iso(),
                "sentEpoch": sent_epoch,
            }
            payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
            sock.sendto(payload, (args.group, args.port))
            append_jsonl(
                log_file,
                {
                    "event": "sent",
                    "group": args.group,
                    "port": args.port,
                    **message,
                },
            )
            print(
                f"[SENDER] seq={sequence} | {message['sentAt']} | "
                f"{args.group}:{args.port}",
                flush=True,
            )
            sequence += 1
            if args.count == 0 or sequence < args.count:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
        print(f"[SENDER] Da gui tong cong {sequence} ban tin.")


if __name__ == "__main__":
    main()

