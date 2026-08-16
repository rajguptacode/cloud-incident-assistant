"""Command-line interface for the Cloud Incident Assistant."""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from .models import Incident
from .storage import Storage

DEFAULT_DB = Path(os.environ.get("CIA_DB", Path.home() / ".cia" / "incidents.json"))


def _db(args: argparse.Namespace) -> Storage:
    return Storage(Path(args.db) if args.db else DEFAULT_DB)


def cmd_create(args: argparse.Namespace) -> int:
    incident = Incident(
        title=args.title,
        severity=args.severity,
        service=args.service,
        description=args.description,
    )
    db = _db(args)
    incidents = [Incident.from_dict(d) for d in db.read()]
    incidents.append(incident)
    db.write([i.to_dict() for i in incidents])
    print(f"Created incident {incident.id}: {incident.title}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    incidents = [Incident.from_dict(d) for d in _db(args).read()]
    if args.status:
        incidents = [i for i in incidents if i.status == args.status]
    if not incidents:
        print("No incidents found.")
        return 0
    for i in incidents:
        print(f"{i.id}  [{i.severity:>8}] [{i.status:<12}] {i.title}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    db = _db(args)
    incidents = [Incident.from_dict(d) for d in db.read()]
    for i in incidents:
        if i.id == args.id:
            i.status = args.status
            i.updated_at = datetime.now(timezone.utc).isoformat()
            db.write([x.to_dict() for x in incidents])
            print(f"Incident {i.id} status -> {args.status}")
            return 0
    print(f"Incident {args.id} not found.", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cia",
        description="Cloud Incident Assistant - manage cloud incidents from the terminal.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--db", help="path to storage file (default: ~/.cia/incidents.json)")

    sub = parser.add_subparsers(dest="command", required=True)

    p_create = sub.add_parser("create", help="report a new incident")
    p_create.add_argument("title")
    p_create.add_argument("--severity", choices=("low", "medium", "high", "critical"), default="medium")
    p_create.add_argument("--service", default="")
    p_create.add_argument("--description", default="")

    p_list = sub.add_parser("list", help="list incidents")
    p_list.add_argument("--status", choices=("open", "investigating", "resolved"))

    p_status = sub.add_parser("status", help="update incident status")
    p_status.add_argument("id")
    p_status.add_argument("status", choices=("open", "investigating", "resolved"))

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {"create": cmd_create, "list": cmd_list, "status": cmd_status}
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())