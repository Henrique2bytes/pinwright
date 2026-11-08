"""Pinned requirements and audit findings."""

from __future__ import annotations

from dataclasses import dataclass


def canonicalize_name(name: str) -> str:
    """PEP 503 name: lowercase, and runs of separators become one hyphen."""
    cleaned: list[str] = []
    previous_hyphen = False
    for char in name.lower():
        if char in "._-":
            if cleaned and not previous_hyphen:
                cleaned.append("-")
            previous_hyphen = True
            continue
        cleaned.append(char)
        previous_hyphen = False
    return "".join(cleaned).strip("-")


@dataclass(frozen=True)
class Pin:
    name: str
    extras: tuple[str, ...]
    version: str | None
    git: str | None
    marker: str | None
    line: int

    def canonical(self) -> str:
        extras = ",".join(self.extras)
        pin = self.version if self.version is not None else self.git or ""
        marker = self.marker or ""
        return f"{self.name}|{extras}|{pin}|{marker}"


@dataclass(frozen=True)
class Finding:
    line: int
    code: str
    message: str


@dataclass(frozen=True)
class Audit:
    pins: tuple[Pin, ...]
    findings: tuple[Finding, ...]
    digest: str | None

    @property
    def ok(self) -> bool:
        return not self.findings and self.digest is not None
