"""TITLE, MORE and CASE.

``TITLE`` does double duty, as it did in the original: with a side it labels
the frame, with a pair of coordinates it puts text on the plot::

    TITLE LEFT 'dσ/dΩ  (μb/sr)'
    TITLE BOTTOM '$p_{K^-}$  (GeV/c)'
    TITLE 8.0 4.5 'preliminary' ANGLE 30 SIZE 14
    TITLE FRAME 0.05 0.92 'this run'        (0-1 across the frame)

The manual puts the leftmost character at the coordinates given; ``CENTER``
centres it there instead.

A legacy file writes accented and Greek text with a ``CASE`` line under it::

    TITLE LEFT 'DS/DW'
    CASE     'LG LG'

``CASE`` modifies the string immediately before it — a ``TITLE`` or a ``MORE``,
placed or not — exactly as the original required.  See :mod:`tdx.charsets` for
what each case letter means.
"""

from __future__ import annotations

from ..display import Text
from ..errors import ArgumentError
from ..lexer import Token
from ..registry import COMMANDS
from ..session import Context
from ..state import TITLE_SLOTS
from ..text import apply_case
from ._util import choice


def _set_title(ctx: Context, target, text: str) -> None:
    """Write *text* to a frame side or to a placed text item."""
    if isinstance(target, Text):
        target.text = text
    else:
        ctx.state.titles[target] = text


def _get_title(ctx: Context, target) -> str:
    if isinstance(target, Text):
        return target.text
    return ctx.state.titles.get(target, "")


@COMMANDS.define(
    "TITLE",
    min_abbrev=3,
    usage="TITLE [TOP|BOTTOM|LEFT|RIGHT] '<text>' | TITLE [FRAME] <x> <y> '<text>' [ANGLE n] [SIZE n] [CENTER]",
)
def cmd_title(ctx: Context, args: list[Token]) -> None:
    """Label a side of the frame, or put text at a point on it."""
    slot = "TOP"
    text: str | None = None
    coords: list[float] = []
    angle = 0.0
    size: float | None = None
    align = "left"
    frame_coords = False
    expect: str | None = None

    for tok in args:
        if tok.is_string:
            text = tok.text
            continue
        if tok.is_number:
            if expect == "angle":
                angle = tok.value
            elif expect == "size":
                size = tok.value
            else:
                coords.append(tok.value)
            expect = None
            continue
        word = tok.upper
        if word == "ANGLE":
            expect = "angle"
        elif word == "SIZE":
            expect = "size"
        elif word in ("CENTER", "CENTRE", "CENTERED"):
            align = "center"
        elif word == "FRAME":
            frame_coords = True
        else:
            slot = choice(tok.text, TITLE_SLOTS, "title position").upper()

    if text is None:
        raise ArgumentError("TITLE needs quoted text, e.g. TITLE TOP 'Missing mass'")

    if not coords:
        ctx.state.titles[slot] = text
        ctx.last_title = (slot, "", text)
        return

    if len(coords) != 2:
        raise ArgumentError(f"TITLE needs an x and a y to place text, got {len(coords)} numbers")
    item = Text(
        x=coords[0],
        y=coords[1],
        text=text,
        size=size,
        angle=angle,
        color=ctx.state.style.color,
        align=align,
        frame_coords=frame_coords,
    )
    ctx.frame.add(item)
    ctx.last_title = (item, "", text)


@COMMANDS.define("MORE", min_abbrev=3, usage="MORE '<text>'")
def cmd_more(ctx: Context, args: list[Token]) -> None:
    """Add more text to the title just given."""
    text = next((tok.text for tok in args if tok.is_string), None)
    if text is None:
        raise ArgumentError("MORE needs quoted text")
    if ctx.last_title is None:
        raise ArgumentError("MORE must follow a TITLE")
    target, _prefix, _raw = ctx.last_title
    prefix = _get_title(ctx, target)
    _set_title(ctx, target, prefix + text)
    ctx.last_title = (target, prefix, text)


@COMMANDS.define("CASE", min_abbrev=4, usage="CASE '<case letters>'")
def cmd_case(ctx: Context, args: list[Token]) -> None:
    """Apply legacy per-character character sets to the title just given."""
    case = next((tok.text for tok in args if tok.is_string), None)
    if case is None:
        raise ArgumentError("CASE needs a quoted case string")
    if ctx.last_title is None:
        ctx.warn("CASE with no title before it, ignored")
        return
    target, prefix, raw = ctx.last_title
    _set_title(ctx, target, prefix + apply_case(raw, case, ctx.warn))
