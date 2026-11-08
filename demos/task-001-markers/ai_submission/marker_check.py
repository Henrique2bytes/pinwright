"""Candidate checker for extras, markers, and git pins.

This is the submission under review. It is not the reference implementation.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def audit(text: str) -> dict:
    findings = []
    pins = []
    for number, line in enumerate(text.splitlines(), start=1):
        raw = line.strip()
        if not raw or raw.startswith("#"):
            continue
        body, _, marker = raw.partition(";")
        body = body.strip()
        marker = marker.strip()
        if "==" not in body and "@" not in body:
            findings.append({"line": number, "code": "unpinned", "message": "missing pin"})
            continue
        if "@" in body:
            name, _, url = body.partition("@")
            pins.append({"name": name.strip(), "pin": url.strip(), "marker": marker})
            continue
        name, _, version = body.partition("==")
        pins.append({"name": name.strip(), "pin": version.strip(), "marker": marker})
    return {
        "ok": not findings,
        "findings": findings,
        "pins": pins,
        "digest": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def write_report(path: Path, payload: str) -> None:
    path.write_text(payload, encoding="utf-8")
