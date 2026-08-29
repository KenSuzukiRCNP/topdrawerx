"""Text handling: Unicode first, maths where you want it, CASE for legacy.

Everything that can end up on the page as characters goes through here.  Three
front ends, and they all end in the same place — an ordinary modern tdx title
string, Unicode with ``$maths$`` where a shift or a symbol needs it:

1. a legacy ``CASE`` line — per-character character sets, §12 of the manual;
2. ``$...$`` — handed to the maths renderer, e.g. ``'$\\sigma_{tot}$'``;
3. anything else — literal Unicode, so ``'dσ/dΩ (μb/sr)'`` simply works.

That CASE lands *in* the modern syntax rather than beside it is the point: the
conversion happens once, in :func:`apply_case`, and nothing downstream — not
``SHOW``, not the backends — needs to know a title came from a 1980s file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .charsets import CASE_SETS, SHIFTS, UNIMPLEMENTED_CASES

#: Characters mathtext treats as markup and must be escaped in a literal run.
_TEX_SPECIAL = "\\#$%&_^{}~"


@dataclass
class Run:
    """A stretch of text with one style."""

    text: str
    math: bool = False

    def to_dict(self) -> dict:
        return {"text": self.text, "math": self.math}


@dataclass
class Piece:
    """One converted character: how to print it, and how to spell it in TeX."""

    display: str
    tex: str
    shift: int = 0  # 0 baseline, -1 subscript, +1 superscript


def _tex_escape(text: str) -> str:
    out = []
    for ch in text:
        if ch in _TEX_SPECIAL:
            out.append("\\" + ch)
        elif ch == " ":
            out.append("\\ ")
        else:
            out.append(ch)
    return "".join(out)


def apply_case(title: str, case: str, warn: Callable[[str], None] | None = None) -> str:
    """Convert a legacy title plus its ``CASE`` line into a modern tdx title.

    The case string is lined up character by character with the title; it may
    be shorter (the rest is Roman) or longer (the excess is ignored).  Anything
    tdx cannot do is reported through *warn* and left as the original
    character, so a title never disappears because of one exotic case letter.
    """
    say = warn or (lambda message: None)
    padded = case.ljust(len(title))
    pieces: list[Piece] = []
    shift = 0
    complained: set[str] = set()

    for ch, code in zip(title, padded):
        upper = code.upper()
        if code == " ":
            pieces.append(Piece(ch, ch, shift))
            continue
        if upper == "L":
            pieces.append(Piece(ch.lower(), ch.lower(), shift))
            continue
        if upper == "X":
            if ch not in SHIFTS:
                say(f"CASE X: {ch!r} is not a shift control (0-3), ignored")
                continue
            if ch == "0":
                shift = -1
            elif ch == "2":
                shift = 1
            else:
                shift = 0
            continue
        table = CASE_SETS.get(upper)
        if table is not None:
            entry = table.get(ch.upper())
            if entry is None:
                say(f"CASE {upper}: no character {ch!r} in that set, left as typed")
                pieces.append(Piece(ch, ch, shift))
                continue
            pieces.append(Piece(entry[0], entry[1], shift))
            continue
        if upper in UNIMPLEMENTED_CASES and upper not in complained:
            complained.add(upper)
            say(f"CASE {upper} ({UNIMPLEMENTED_CASES[upper]}) is not implemented yet")
        elif upper not in UNIMPLEMENTED_CASES and upper not in complained:
            complained.add(upper)
            say(f"CASE {upper}: unknown character set, left as typed")
        pieces.append(Piece(ch, ch, shift))

    return _assemble(pieces)


def _assemble(pieces: list[Piece]) -> str:
    """Join converted characters, wrapping shifted stretches in maths."""
    out: list[str] = []
    i = 0
    while i < len(pieces):
        shift = pieces[i].shift
        run = []
        while i < len(pieces) and pieces[i].shift == shift:
            run.append(pieces[i])
            i += 1
        if shift == 0:
            out.append("".join(p.display for p in run))
            continue
        body = "".join(p.tex if p.tex != p.display else _tex_escape(p.display) for p in run)
        out.append(("$_{%s}$" if shift < 0 else "$^{%s}$") % body)
    return "".join(out)


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
    literal parts: a stray ``$`` would otherwise open a maths group.
    """
    out: list[str] = []
    for run in parse(text):
        if run.math:
            out.append(f"${run.text}$")
        else:
            out.append(run.text.replace("$", r"\$"))
    return "".join(out)
