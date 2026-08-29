"""Error types for tdx.

Everything the user can get wrong raises a :class:`TdxError`.  The REPL and the
CLI catch it and print a single readable line; nothing else should escape.
"""

from __future__ import annotations


class TdxError(Exception):
    """Base class for all user-facing errors."""

    def __init__(self, message: str, lineno: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.lineno = lineno

    def __str__(self) -> str:  # pragma: no cover - trivial
        if self.lineno is None:
            return self.message
        return f"line {self.lineno}: {self.message}"


class LexError(TdxError):
    """The line could not be tokenized (unterminated string, bad number)."""


class UnknownCommand(TdxError):
    """No command matches the word the user typed."""

    def __init__(self, word: str, lineno: int | None = None, label: str = "command") -> None:
        super().__init__(f"unknown {label} {word.upper()!r}", lineno)
        self.word = word


class AmbiguousCommand(TdxError):
    """An abbreviation matches more than one command."""

    def __init__(
        self,
        word: str,
        candidates: list[str],
        lineno: int | None = None,
        label: str = "command",
    ) -> None:
        joined = ", ".join(sorted(candidates))
        super().__init__(f"{word.upper()!r} is an ambiguous {label}: {joined}", lineno)
        self.word = word
        self.candidates = candidates


class ArgumentError(TdxError):
    """A command was given arguments it cannot make sense of."""


class DataError(TdxError):
    """Something is wrong with the data buffer or a data line."""
