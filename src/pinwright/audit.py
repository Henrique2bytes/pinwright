"""Audit a pinfile and publish the JSON report by replace."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from pinwright.model import Audit, Finding, Pin
from pinwright.parse import parse_document


def audit_text(text: str) -> Audit:
    pins, findings = parse_document(text)
    seen: dict[str, int] = {}
    for pin in pins:
        if pin.name in seen:
            findings.append(
                Finding(pin.line, "duplicate-name", f"{pin.name} repeats the pin from line {seen[pin.name]}")
            )
        else:
            seen[pin.name] = pin.line
    ordered = tuple(sorted(findings, key=lambda item: (item.line, item.code, item.message)))
    digest = _digest(pins) if not ordered else None
    return Audit(pins=tuple(pins), findings=ordered, digest=digest)


def audit_path(path: Path) -> Audit:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Audit((), (Finding(0, "invalid-encoding", "pinfile is not UTF-8"),), None)
    except OSError as exc:
        return Audit((), (Finding(0, "io-error", str(exc)),), None)
    return audit_text(text)


def audit_json(audit: Audit) -> str:
    payload = {
        "ok": audit.ok,
        "digest": audit.digest,
        "pins": [_pin_json(pin) for pin in audit.pins],
        "findings": [
            {"line": finding.line, "code": finding.code, "message": finding.message}
            for finding in audit.findings
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def publish_report(path: Path, payload: str) -> None:
    """Write a complete report, then replace the destination. A failed replace keeps the old bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".pinwright-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _digest(pins: list[Pin] | tuple[Pin, ...]) -> str:
    rows = [pin.canonical() for pin in sorted(pins, key=lambda pin: (pin.name, pin.line))]
    blob = ("\n".join(rows) + "\n").encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _pin_json(pin: Pin) -> dict[str, object]:
    return {
        "name": pin.name,
        "extras": list(pin.extras),
        "version": pin.version,
        "git": pin.git,
        "marker": pin.marker,
        "line": pin.line,
    }
