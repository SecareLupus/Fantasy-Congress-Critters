import argparse
import time

from . import db, download, legislators
from .billstatus import iter_zip
from .config import BILL_TYPES
from .normalize import normalize_bill


def cmd_download(args) -> None:
    download.download_billstatus(args.congress, force=args.force)
    download.download_legislators(force=args.force)


def cmd_load(args) -> None:
    with db.connect() as conn:
        db.init_schema(conn)
        print(f"critters: {legislators.load_critters(conn)}")
        print(f"committees: {legislators.load_committees(conn)}")
        for bill_type in BILL_TYPES:
            start, count, n_events = time.time(), 0, 0
            for bill in iter_zip(download.billstatus_path(args.congress, bill_type)):
                events = normalize_bill(bill)
                db.save_bill(conn, bill, events)
                count += 1
                n_events += len(events)
            conn.commit()
            print(f"{bill_type}: {count} bills, {n_events} events ({time.time() - start:.1f}s)")


def main() -> None:
    parser = argparse.ArgumentParser(prog="critters")
    sub = parser.add_subparsers(required=True)

    p = sub.add_parser("download", help="fetch raw source files")
    p.add_argument("--congress", type=int, default=118)
    p.add_argument("--force", action="store_true", help="re-download files already on disk")
    p.set_defaults(func=cmd_download)

    p = sub.add_parser("load", help="parse, normalize, and load into Postgres")
    p.add_argument("--congress", type=int, default=118)
    p.set_defaults(func=cmd_load)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
