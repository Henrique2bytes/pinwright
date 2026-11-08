"""Closed marker grammar. Markers are parsed, never evaluated as Python."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

_TOKEN = re.compile(
    r"\s+"
    r"|(?P<and>\band\b)"
    r"|(?P<op>==|>=|<=|!=|>|<)"
    r"|(?P<ident>[A-Za-z_][A-Za-z0-9_]*)"
    r"|(?P<lp>\()"
    r"|(?P<rp>\))"
    r"|(?P<string>\"[^\"\\]*\"|'[^'\\]*')"
)

_PLATFORM = {
    "sys_platform": frozenset({"darwin", "linux", "win32"}),
    "os_name": frozenset({"posix", "nt"}),
}
_VERSION_OPS = frozenset({"==", "!=", ">=", "<=", ">", "<"})
_VERSION = re.compile(r"^\d+\.\d+$")


class MarkerError(ValueError):
    pass


@dataclass(frozen=True)
class _Cmp:
    ident: str
    op: str
    value: str


@dataclass(frozen=True)
class _And:
    terms: tuple[object, ...]


@dataclass(frozen=True)
class _Group:
    inner: object


def normalize_marker(text: str) -> str:
    return _render(_parse(text))


def marker_holds(text: str | None, env: Mapping[str, str]) -> bool:
    if text is None:
        return True
    return _eval(_parse(text), env)


def _parse(text: str):
    tokens = list(_tokenize(text))
    if not tokens:
        raise MarkerError("empty marker")
    parser = _Parser(tokens)
    node = parser.expression()
    if parser.remaining():
        raise MarkerError("trailing marker syntax")
    return node


def _tokenize(text: str):
    index = 0
    while index < len(text):
        match = _TOKEN.match(text, index)
        if match is None:
            raise MarkerError("invalid marker syntax")
        index = match.end()
        if match.group(0).isspace():
            continue
        kind = next(name for name, value in match.groupdict().items() if value is not None)
        yield kind, match.group(kind)


class _Parser:
    def __init__(self, tokens: list[tuple[str, str]]) -> None:
        self.tokens = tokens
        self.index = 0

    def remaining(self) -> bool:
        return self.index < len(self.tokens)

    def _peek(self) -> tuple[str, str] | None:
        if self.index >= len(self.tokens):
            return None
        return self.tokens[self.index]

    def _take(self, kind: str) -> str | None:
        current = self._peek()
        if current is None or current[0] != kind:
            return None
        self.index += 1
        return current[1]

    def expression(self):
        terms = [self._term()]
        while self._take("and") is not None:
            terms.append(self._term())
        if len(terms) == 1:
            return terms[0]
        return _And(tuple(terms))

    def _term(self):
        if self._take("lp") is not None:
            inner = self.expression()
            if self._take("rp") is None:
                raise MarkerError("unclosed marker group")
            return _Group(inner)
        return self._comparison()

    def _comparison(self) -> _Cmp:
        ident = self._take("ident")
        op = self._take("op")
        raw = self._take("string")
        if ident is None or op is None or raw is None:
            raise MarkerError("marker clause must be ident, operator, string")
        value = raw[1:-1]
        if ident in _PLATFORM:
            if op != "==":
                raise MarkerError(f"{ident} only allows ==")
            if value not in _PLATFORM[ident]:
                raise MarkerError(f"unsupported value for {ident}")
        elif ident == "python_version":
            if op not in _VERSION_OPS:
                raise MarkerError("unsupported python_version operator")
            if _VERSION.fullmatch(value) is None:
                raise MarkerError("python_version must be major.minor")
        else:
            raise MarkerError(f"unsupported marker name {ident}")
        return _Cmp(ident, op, value)


def _render(node) -> str:
    if isinstance(node, _Cmp):
        return f'{node.ident} {node.op} "{node.value}"'
    if isinstance(node, _Group):
        return "(" + _render(node.inner) + ")"
    if isinstance(node, _And):
        return " and ".join(_render(term) for term in node.terms)
    raise MarkerError("unknown marker node")


def _eval(node, env: Mapping[str, str]) -> bool:
    if isinstance(node, _And):
        return all(_eval(term, env) for term in node.terms)
    if isinstance(node, _Group):
        return _eval(node.inner, env)
    if isinstance(node, _Cmp):
        actual = env.get(node.ident, "")
        if node.ident == "python_version":
            return _version_cmp(actual, node.op, node.value)
        return node.op == "==" and actual == node.value
    raise MarkerError("unknown marker node")


def _version_cmp(actual: str, op: str, expected: str) -> bool:
    if _VERSION.fullmatch(actual) is None:
        return False
    left = tuple(int(part) for part in actual.split("."))
    right = tuple(int(part) for part in expected.split("."))
    return {
        "==": left == right,
        "!=": left != right,
        ">=": left >= right,
        "<=": left <= right,
        ">": left > right,
        "<": left < right,
    }[op]
