"""Text handling: Unicode first, maths where you want it, CASE for legacy.

Everything that can end up on the page as characters goes through here and
comes out as a list of :class:`Run` objects.  Backends only ever see runs, so
adding the legacy ``CASE`` line later (milestone 2) does not touch any backend.

Three front ends, checked in this order so that an old file never changes
meaning:

1. a ``CASE`` line attached to the title -- per-character shifts, as in the
   original (not implemented yet; :func:`apply_case` is the seam);
2. ``$...$`` -- handed to the maths renderer, e.g. ``'$\\sigma_{tot}$'``;
3. anything else -- literal Unicode, so ``'dσ/dΩ (μb/sr)'`` simply works.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Run:
    """A stretch of text with one style."""

    text: str
    math: bool = False

    def to_dict(self) -> dict:
        return {"text": self.text, "math": self.math}


def _split(text: str) -> list[Run] | None:
    """Split on unescaped ``$``; return ``None`` if the delimiters don't pair."""
    runs: list[Run] = []
    buf: list[str] = []
    math = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text) and text[i + 1] == "$":
            buf.append("$")
            i += 2
            continue
        if ch == "$":
            if buf:
                runs.append(Run("".join(buf), math))
                buf = []
            math = not math
            i += 1
            continue
        buf.append(ch)
        i += 1
    if math:
        return None
    if buf:
        runs.append(Run("".join(buf), False))
    return runs


def parse(text: str) -> list[Run]:
    """Split *text* into literal and ``$maths$`` runs.

    An odd number of ``$`` means the user meant a literal dollar sign rather
    than maths, so the whole string is taken literally.
    """
    runs = _split(text)
    if runs is None:
        return [Run(text.replace("\\$", "$"), False)]
    return runs


def to_matplotlib(text: str) -> str:
    """Render runs into a single matplotlib-safe string.

    matplotlib parses ``$...$`` itself, so the job here is only to protect the
    literal parts: a stray ``$`` and, outside maths, ``_`` and ``^`` which
    would otherwise be silently swallowed.
    """
    out: list[str] = []
    for run in parse(text):
        if run.math:
            out.append(f"${run.text}$")
        else:
            out.append(run.text.replace("$", r"\$"))
    return "".join(out)


def apply_case(title: str, case_line: str) -> str:  # pragma: no cover - M2 seam
    """Apply a legacy ``CASE`` line to *title*.

    Not implemented yet.  When it lands it will return runs, not a string, and
    non-ASCII characters in *title* will pass through untouched: ``CASE`` only
    ever modifies the characters it lines up with.
    """
    raise NotImplementedError("CASE lines are milestone 2")
