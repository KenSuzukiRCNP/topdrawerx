"""Axis furniture: ``SET TICKS`` and ``SET LABELS``.

Both follow the original's shape — a list of qualifiers, no punctuation::

    SET TICKS SIZE 0.08 LONG 3 ALL ON
    SET TICKS TOP OFF RIGHT OFF
    SET LABELS SIZE 11 LEFT ON BOTTOM ON PERMANENT

``X`` means top and bottom, ``Y`` means left and right, ``ALL`` means all four.
Sizes are the original's units: tick length in inches, label size in points.
``PERMANENT`` keeps the setting across ``NEW FRAME``; without it the setting
applies to this frame only, as in the original.

``IN`` and ``OUT`` are tdx's own — the plotter only ever drew ticks inward.
"""

from __future__ import annotations

from ..errors import ArgumentError
from ..lexer import Token
from ..registry import SETTERS
from ..session import Context
from ..state import SIDES

#: qualifier → the sides it selects
SIDE_GROUPS = {
    "ALL": SIDES,
    "X": ("TOP", "BOTTOM"),
    "Y": ("LEFT", "RIGHT"),
    "TOP": ("TOP",),
    "BOTTOM": ("BOTTOM",),
    "LEFT": ("LEFT",),
    "RIGHT": ("RIGHT",),
}


def _parse_sides(
    ctx: Context,
    args: list[Token],
    target,
    *,
    what: str,
    numbers: dict[str, str],
    extra: dict[str, tuple[str, str]] | None = None,
) -> bool:
    """Shared parser for SET TICKS / SET LABELS.

    *numbers* maps a qualifier that takes a number (``SIZE``) to the attribute
    it sets; *extra* maps a bare qualifier (``IN``) to (attribute, value).
    Returns whether PERMANENT was given.
    """
    pending: list[str] = []
    pending_number: str | None = None
    permanent = False

    def apply(switch: bool) -> None:
        for side in pending or SIDES:
            target.on[side] = switch
        pending.clear()

    for tok in args:
        if tok.is_number:
            if pending_number is None:
                raise ArgumentError(f"SET {what}: {tok.text} follows nothing that takes a number")
            setattr(target, pending_number, tok.value)
            pending_number = None
            continue
        word = tok.upper
        if word in numbers:
            pending_number = numbers[word]
            continue
        if word in SIDE_GROUPS:
            pending.extend(SIDE_GROUPS[word])
            continue
        if word in ("ON", "OFF"):
            # Each ON/OFF applies to the sides named since the last one, so
            # "ALL OFF BOTTOM ON LEFT ON" means what it reads as.
            apply(word == "ON")
            continue
        if word == "PERMANENT":
            permanent = True
            continue
        if extra and word in extra:
            attribute, value = extra[word]
            setattr(target, attribute, value)
            continue
        raise ArgumentError(f"SET {what}: don't understand {tok.text!r}")

    if pending_number is not None:
        raise ArgumentError(f"SET {what} {pending_number.upper()} needs a number")
    if pending:
        # "SET TICKS TOP" with no ON/OFF reads as turning it on.
        apply(True)
    return permanent


@SETTERS.define(
    "TICKS",
    min_abbrev=3,
    usage="SET TICKS [SIZE <inches>] [LONG <ratio>] [IN|OUT] [ALL|X|Y|TOP|...] [ON|OFF] [PERMANENT]",
)
def set_ticks(ctx: Context, args: list[Token]) -> None:
    """Size, direction and per-side switching of the tick marks."""
    if not args:
        raise ArgumentError("SET TICKS needs something to set, e.g. SET TICKS SIZE 0.08")
    permanent = _parse_sides(
        ctx,
        args,
        ctx.state.ticks,
        what="TICKS",
        numbers={"SIZE": "size", "LONG": "long"},
        extra={"IN": ("direction", "in"), "OUT": ("direction", "out")},
    )
    if permanent:
        ctx.state.ticks_base = ctx.state.ticks.copy()


@SETTERS.define(
    "LABELS",
    min_abbrev=3,
    usage="SET LABELS [SIZE <points>] [ALL|X|Y|TOP|...] [ON|OFF] [PERMANENT]",
)
def set_labels(ctx: Context, args: list[Token]) -> None:
    """Size and per-side switching of the numeric axis labels."""
    if not args:
        raise ArgumentError("SET LABELS needs something to set, e.g. SET LABELS SIZE 11")
    permanent = _parse_sides(
        ctx,
        args,
        ctx.state.labels,
        what="LABELS",
        numbers={"SIZE": "size"},
    )
    if permanent:
        ctx.state.labels_base = ctx.state.labels.copy()
