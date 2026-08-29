"""Small helpers shared by command handlers."""

from __future__ import annotations

from ..errors import ArgumentError
from ..lexer import Token

#: Words that exist only to read well: SET LIMITS X FROM 0 TO 10.
NOISE = {"FROM", "TO", "AND", "THE", "IS", "OF"}


def strip_noise(args: list[Token]) -> list[Token]:
    return [t for t in args if not (t.is_word and t.upper in NOISE)]


def numbers(args: list[Token]) -> list[float]:
    return [t.value for t in args if t.is_number]


def one_word(args: list[Token], what: str) -> str:
    words = [t for t in args if t.is_word or t.is_string]
    if len(words) != 1:
        raise ArgumentError(f"expected one {what}, got {len(words)}")
    return words[0].text


def choice(value: str, options: dict | tuple | list, what: str) -> str:
    """Resolve *value* against *options* by unique prefix, case-insensitively."""
    key = value.upper()
    names = [str(o).upper() for o in options]
    if key in names:
        return key.lower()
    hits = [n for n in names if n.startswith(key)]
    if len(hits) == 1:
        return hits[0].lower()
    joined = ", ".join(sorted(names))
    if not hits:
        raise ArgumentError(f"unknown {what} {value!r}; expected one of: {joined}")
    raise ArgumentError(f"{value!r} is an ambiguous {what}: {', '.join(sorted(hits))}")
