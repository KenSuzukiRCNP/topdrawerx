"""Things drawn on the frame rather than from a column of numbers: BOX, ARROW.

Both come in two forms — one that takes coordinates, and one that works from
the data buffer like any other drawing verb::

    BOX 2.0 1.0 4.0 3.0            a rectangle, corner to corner
    BOX                            a rectangle per data point, DX/DY as the
                                   half-widths — systematic error boxes

    ARROW 1.0 8.0 3.0 6.5          an arrow from here to there
    ARROW DOWN LENGTH 1.5          an arrow down from each data point —
                                   upper limits

The per-point forms are the reason these commands are worth having: error
boxes and upper limits are otherwise tedious to draw, and both are ordinary
requests in a physics figure.
"""

from __future__ import annotations

from ..display import Arrow, Box
from ..errors import ArgumentError
from ..lexer import Token
from ..registry import COMMANDS
from ..session import Context

DIRECTIONS = {
    "UP": (0.0, 1.0),
    "DOWN": (0.0, -1.0),
    "LEFT": (-1.0, 0.0),
    "RIGHT": (1.0, 0.0),
}


def _numbers(args: list[Token]) -> list[float]:
    return [t.value for t in args if t.is_number]


def _face(ctx: Context, filled: bool) -> str | None:
    """The fill colour for a filled shape, or None for an open one."""
    if not filled:
        return None
    return ctx.state.style.color if ctx.state.style.hatch == "none" else "none"


@COMMANDS.define("BOX", min_abbrev=3, usage="BOX [<x0> <y0> <x1> <y1>] [FILL]")
def cmd_box(ctx: Context, args: list[Token]) -> None:
    """Draw a rectangle, or one per data point from the DX/DY columns."""
    style = ctx.state.style
    filled = style.fill
    for tok in args:
        if tok.is_word:
            word = tok.upper
            if word == "FILL":
                filled = True
            elif word in ("OPEN", "NOFILL"):
                filled = False
            else:
                ctx.warn(f"BOX: ignoring {tok.text!r}")

    values = _numbers(args)
    if values:
        if len(values) != 4:
            raise ArgumentError("BOX needs four numbers: BOX x0 y0 x1 y1")
        x0, y0, x1, y1 = values
        ctx.frame.add(
            Box(
                x0=min(x0, x1),
                y0=min(y0, y1),
                x1=max(x0, x1),
                y1=max(y0, y1),
                color=style.color,
                width=style.width,
                dash=style.dash,
                facecolor=_face(ctx, filled),
                hatch=style.hatch,
            )
        )
        return

    data = ctx.buffer.snapshot()
    dx, dy = data.dx, data.dy
    if dx is None and dy is None:
        raise ArgumentError("BOX over data needs DX and/or DY columns, or four numbers")
    for i, (px, py) in enumerate(zip(data.x, data.y)):
        ex = dx[i] if dx else 0.0
        ey = dy[i] if dy else 0.0
        ctx.frame.add(
            Box(
                x0=px - ex,
                y0=py - ey,
                x1=px + ex,
                y1=py + ey,
                color=style.color,
                width=style.width,
                dash=style.dash,
                facecolor=_face(ctx, filled),
                hatch=style.hatch,
            )
        )
    ctx.buffer.seal()


@COMMANDS.define(
    "ARROW",
    min_abbrev=3,
    usage="ARROW <x0> <y0> <x1> <y1> | ARROW UP|DOWN|LEFT|RIGHT [LENGTH <n>]",
)
def cmd_arrow(ctx: Context, args: list[Token]) -> None:
    """Draw an arrow, or one from each data point (upper limits)."""
    style = ctx.state.style
    head = True
    direction: tuple[float, float] | None = None
    length: float | None = None
    expect_length = False

    for tok in args:
        if tok.is_number:
            if expect_length:
                length = tok.value
                expect_length = False
            continue
        word = tok.upper
        if word == "NOHEAD":
            head = False
        elif word == "LENGTH":
            expect_length = True
        elif word in DIRECTIONS:
            direction = DIRECTIONS[word]
        else:
            ctx.warn(f"ARROW: ignoring {tok.text!r}")

    values = _numbers(args)
    if direction is None:
        if len(values) != 4:
            raise ArgumentError(
                "ARROW needs four numbers, or a direction: ARROW DOWN LENGTH 1.5"
            )
        x0, y0, x1, y1 = values
        ctx.frame.add(
            Arrow(x0=x0, y0=y0, x1=x1, y1=y1, color=style.color, width=style.width, head=head)
        )
        return

    data = ctx.buffer.snapshot()
    ux, uy = direction
    if length is None:
        # No LENGTH given: a tenth of the span of the axis the arrow runs
        # along, which is about what an upper-limit arrow wants to be.
        along = data.y if uy else data.x
        span = max(along) - min(along)
        length = (span or abs(max(along)) or 1.0) * 0.1
    for px, py in zip(data.x, data.y):
        ctx.frame.add(
            Arrow(
                x0=px,
                y0=py,
                x1=px + ux * length,
                y1=py + uy * length,
                color=style.color,
                width=style.width,
                head=head,
            )
        )
    ctx.buffer.seal()
