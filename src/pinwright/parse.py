"""Parse a pinfile. One requirement per line. No network and no Python eval."""

from __future__ import annotations

import re

from pinwright.markers import MarkerError, normalize_marker
from pinwright.model import Finding, Pin, canonicalize_name

_NAME = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
_VERSION_REQ = re.compile(rf"^(?P<name>{_NAME})(?:\[(?P<extras>[^\]]*)\])?==(?P<version>\S+)$")
_GIT_REQ = re.compile(rf"^(?P<name>{_NAME})(?:\[(?P<extras>[^\]]*)\])? @ (?P<url>\S+)$")
_VERSION = re.compile(
    r"^(?:[0-9]+!)?"
    r"[0-9]+(?:\.[0-9]+)*"
    r"(?:(?:a|b|rc)[0-9]+)?"
    r"(?:\.post[0-9]+)?"
    r"(?:\.dev[0-9]+)?$"
)
_GIT = re.compile(
    r"^git\+https://(?P<host>[A-Za-z0-9.-]+)"
    r"(?P<path>(?:/[A-Za-z0-9._~-]+)+)"
    r"\.git@(?P<sha>[0-9a-f]{40})$"
)
_EXTRA = re.compile(rf"^{_NAME}$")


def parse_document(text: str) -> tuple[list[Pin], list[Finding]]:
    if text.startswith("\ufeff"):
        text = text[1:]
    pins: list[Pin] = []
    findings: list[Finding] = []
    for number, raw_line in enumerate(text.splitlines(), start=1):
        stripped = _strip_comment(raw_line).strip()
        if not stripped:
            continue
        body, marker_text, split_error = _split_marker(stripped)
        if split_error is not None:
            findings.append(Finding(number, split_error.code, split_error.message))
            continue
        pin, finding = _parse_body(number, body)
        if finding is not None:
            findings.append(finding)
            continue
        assert pin is not None
        if marker_text is not None:
            try:
                marker = normalize_marker(marker_text)
            except MarkerError as exc:
                findings.append(Finding(number, "invalid-marker", str(exc)))
                continue
            pin = Pin(pin.name, pin.extras, pin.version, pin.git, marker, pin.line)
        pins.append(pin)
    return pins, findings


def _parse_body(number: int, line: str) -> tuple[Pin | None, Finding | None]:
    version_match = _VERSION_REQ.fullmatch(line)
    if version_match is not None:
        return _version_pin(number, version_match)
    git_match = _GIT_REQ.fullmatch(line)
    if git_match is not None:
        return _git_pin(number, git_match)
    if "==" in line or " @ " in line:
        return None, Finding(number, "invalid-requirement", "requirement syntax is not an exact pin")
    return None, Finding(number, "unpinned", "requirement has no exact version or git commit")


def _version_pin(number: int, match: re.Match[str]) -> tuple[Pin | None, Finding | None]:
    name = canonicalize_name(match.group("name"))
    if not name:
        return None, Finding(number, "invalid-name", "package name is empty after normalization")
    extras, extra_error = _extras(number, match.group("extras"))
    if extra_error is not None:
        return None, extra_error
    version = match.group("version")
    if _VERSION.fullmatch(version) is None:
        return None, Finding(number, "invalid-version", "version is not an exact release token")
    return Pin(name, extras, version, None, None, number), None


def _git_pin(number: int, match: re.Match[str]) -> tuple[Pin | None, Finding | None]:
    name = canonicalize_name(match.group("name"))
    if not name:
        return None, Finding(number, "invalid-name", "package name is empty after normalization")
    extras, extra_error = _extras(number, match.group("extras"))
    if extra_error is not None:
        return None, extra_error
    git_match = _GIT.fullmatch(match.group("url"))
    if git_match is None:
        return None, Finding(
            number,
            "mutable-vcs",
            "git pins require git+https without credentials and a 40-character lowercase commit",
        )
    canonical = "git+https://{host}{path}.git@{sha}".format(
        host=git_match.group("host").lower(),
        path=git_match.group("path"),
        sha=git_match.group("sha"),
    )
    return Pin(name, extras, None, canonical, None, number), None


def _extras(number: int, raw: str | None) -> tuple[tuple[str, ...], Finding | None]:
    if raw is None:
        return (), None
    if raw == "" or raw.strip() != raw:
        return (), Finding(number, "invalid-extra", "extras list is empty or padded")
    extras: list[str] = []
    for part in raw.split(","):
        if _EXTRA.fullmatch(part) is None:
            return (), Finding(number, "invalid-extra", "extra name is not an identifier")
        canonical = canonicalize_name(part)
        if canonical in extras:
            return (), Finding(number, "invalid-extra", "duplicate extra")
        extras.append(canonical)
    return tuple(sorted(extras)), None


def _split_marker(line: str) -> tuple[str, str | None, Finding | None]:
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == ";" and not in_single and not in_double:
            body = line[:index].strip()
            marker = line[index + 1 :].strip()
            if not marker:
                return body, None, Finding(0, "invalid-marker", "empty marker")
            return body, marker, None
    return line.strip(), None, None


def _strip_comment(line: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double and (index == 0 or line[index - 1].isspace()):
            return line[:index]
    return line
