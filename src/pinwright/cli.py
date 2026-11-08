"""Command line. Reads a local pinfile and writes JSON. It does not resolve packages."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pinwright.audit import audit_json, audit_path, publish_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pinwright")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="audit a pinfile")
    check.add_argument("pinfile", type=Path)
    check.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.command != "check":
        parser.error("unknown command")
    audit = audit_path(args.pinfile)
    payload = audit_json(audit)
    sys.stdout.write(payload)
    if args.out is not None:
        try:
            publish_report(args.out, payload)
        except OSError as exc:
            sys.stderr.write(f"pinwright: report was not published: {exc}\n")
            return 1
    if any(finding.code == "io-error" for finding in audit.findings):
        return 1
    return 0 if audit.ok else 2
