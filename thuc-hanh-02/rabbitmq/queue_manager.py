from __future__ import annotations

import argparse

try:
    from .common import QUEUE_NAME, mode_is_durable, open_connection
except ImportError:
    from common import QUEUE_NAME, mode_is_durable, open_connection  # type: ignore


def main() -> None:
    parser = argparse.ArgumentParser(description="Xoa va tao lai queue cho tung kich ban")
    parser.add_argument(
        "--mode", choices=("persistent", "transient"), required=True
    )
    parser.add_argument("--queue", default=QUEUE_NAME)
    parser.add_argument("--delete-first", action="store_true")
    args = parser.parse_args()

    connection = open_connection()
    channel = connection.channel()
    try:
        if args.delete_first:
            channel.queue_delete(queue=args.queue)
            print(f"Da xoa queue {args.queue} (neu ton tai).")
        result = channel.queue_declare(
            queue=args.queue, durable=mode_is_durable(args.mode)
        )
        print(
            f"Queue={args.queue}, mode={args.mode}, "
            f"message_count={result.method.message_count}, "
            f"consumer_count={result.method.consumer_count}"
        )
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()

