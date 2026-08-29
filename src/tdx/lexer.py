"""Tokenizer for the tdx command language.

The language is free-format.  A physical line is one of four things:

===========  =========================================================
``BLANK``    empty or whitespace only
``COMMENT``  starts with ``!``, ``#`` or ``;``
``DATA``     nothing but numbers -- a row for the current data buffer
``COMMAND``  a verb followed by qualifiers, numbers and quoted strings
===========  =========================================================

Distinguishing a data line from a command line is the one genuinely odd job
in this grammar, and it is done here so that no other module has to care:
a line whose tokens are *all* numbers is data, anything else is a command.

Deliberately gone from the original: fixed columns, an 80-character limit,
uppercase-only input, and the six-character identifier truncation.  Commands
are case-insensitive; strings keep their case and their Unicode.
"""

from __future__ import annotations

import re
from functools import lru_cache
from dataclasses import dataclass
from enum import Enum

from .errors import LexError

COMMENT_PREFIXES = ("!", "#", ";")
QUOTES = ("'", '"')

# Accepts 1, 1., .5, -1.5e-3 and the Fortran-style 1.5D+03 found in old files.
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eEdD][+-]?\d+)?$")


class TokKind(Enum):
    WORD = "word"
    NUMBER = "number"
    STRING = "string"


@dataclass(frozen=True)
class Token:
    kind: TokKind
    text: str
    value: float | None = None

    @property
    def is_number(self) -> bool:
        return self.kind is TokKind.NUMBER

    @property
    def is_word(self) -> bool:
        return self.kind is TokKind.WORD

    @property
    def is_string(self) -> bool:
        return self.kind is TokKind.STRING

    @property
    def upper(self) -> str:
        return self.text.upper()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"{self.kind.value}({self.text!r})"


class LineKind(Enum):
    BLANK = "blank"
    COMMENT = "comment"
    DATA = "data"
    COMMAND = "command"


@dataclass
class Line:
    kind: LineKind
    raw: str
    tokens: list[Token]
    lineno: int | None = None

    @property
    def numbers(self) -> list[float]:
        return [t.value for t in self.tokens if t.value is not None]


def parse_number(text: str) -> float | None:
    """Return the float value of *text*, or ``None`` if it is not a number."""
    if not _NUMBER_RE.match(text):
        return None
    return float(text.replace("d", "e").replace("D", "e"))


def tokenize(text: str, lineno: int | None = None) -> list[Token]:
    """Split one line into tokens.  Commas count as whitespace."""
    tokens: list[Token] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace() or ch == ",":
            i += 1
            continue
        if ch in QUOTES:
            quote = ch
            i += 1
            buf: list[str] = []
            while True:
                if i >= n:
                    raise LexError(f"unterminated string: {text.strip()!r}", lineno)
                if text[i] == quote:
                    # A doubled quote is a literal quote, as in the original.
                    if i + 1 < n and text[i + 1] == quote:
                        buf.append(quote)
                        i += 2
                        continue
                    i += 1
                    break
                buf.append(text[i])
                i += 1
            tokens.append(Token(TokKind.STRING, "".join(buf)))
            continue
        start = i
        while i < n and not text[i].isspace() and text[i] != "," and text[i] not in QUOTES:
            i += 1
        word = text[start:i]
        # Old files write SIZE=0.1 and ANGLE=90; '=' is just a separator, so
        # split it here and no command has to think about it.
        if "=" in word and not word.startswith("="):
            for part in word.split("="):
                if part:
                    tokens.append(_word_or_number(part))
            continue
        tokens.append(_word_or_number(word))
    return tokens


def _word_or_number(word: str) -> Token:
    value = parse_number(word)
    if value is None:
        return Token(TokKind.WORD, word)
    return Token(TokKind.NUMBER, word, value)


@lru_cache(maxsize=1 << 16)
def classify(raw: str) -> tuple[LineKind, tuple[Token, ...]]:
    """Tokenize and classify, cached.

    Every replay re-reads the same lines, so the same strings are scanned over
    and over.  Tokens are frozen, so sharing them between replays is safe, and
    caching turns tokenizing into a dictionary lookup for the second and every
    later replay of a data file.
    """
    stripped = raw.strip()
    if not stripped:
        return LineKind.BLANK, ()
    if stripped[0] in COMMENT_PREFIXES:
        return LineKind.COMMENT, ()
    tokens = tuple(tokenize(raw))
    if tokens and all(t.is_number for t in tokens):
        return LineKind.DATA, tokens
    return LineKind.COMMAND, tokens


def scan_line(raw: str, lineno: int | None = None) -> Line:
    """Classify and tokenize a single line."""
    try:
        kind, tokens = classify(raw)
    except LexError as exc:
        raise LexError(exc.message, lineno) from None
    return Line(kind, raw, list(tokens), lineno)


def scan(text: str) -> list[Line]:
    """Classify and tokenize a whole script."""
    return [scan_line(raw, i) for i, raw in enumerate(text.splitlines(), start=1)]
