"""Drawing verbs: PLOT, JOIN, HISTOGRAM.

Each one takes what is in the data buffer, emits display-list primitives, and
seals the buffer so that the next data line starts a new dataset.  Two verbs
in a row therefore draw the same points -- the ``PLOT`` then ``JOIN`` idiom.
"""

from __future__ import annotations

from ..display import ErrorBars, Markers, Polygon, Polyline
from ..lexer import Token
from ..registry import COMMANDS
from ..session import Context
from ._util import choice
from .setcmd import DASH_NAMES, symbol_from


def _errorbars(ctx: Context, data, color: str) -> None:
    dx, dy = data.dx, data.dy
    if dx is None and dy is None:
        return
    style = ctx.state.style
    ctx.frame.add(
        ErrorBars(
            x=data.x,
            y=data.y,
            dx=dx,
            dy=dy,
            color=color,
            width=max(style.width * 0.8, 0.6),
        )
    )


@COMMANDS.define("PLOT", min_abbrev=2, usage="PLOT [<symbol>]")
def cmd_plot(ctx: Context, args: list[Token]) -> None:
    """Draw the data as symbols, with error bars if DX/DY were given."""
    data = ctx.buffer.snapshot()
    style = ctx.state.style
    color = ctx.pen()
    symbol = style.symbol
    for tok in args:
        if tok.is_word or tok.is_number:
            symbol = symbol_from(tok.text)
    _errorbars(ctx, data, color)
    ctx.frame.add(
        Markers(
            x=data.x,
            y=data.y,
            symbol=symbol,
            size=style.size,
            color=color,
            fill=style.fill,
        )
    )
    ctx.buffer.seal()


@COMMANDS.define("JOIN", min_abbrev=3, usage="JOIN [SOLID|DASHES|DOTS|DOTDASH]")
def cmd_join(ctx: Context, args: list[Token]) -> None:
    """Connect the data points with a line."""
    data = ctx.buffer.snapshot()
    style = ctx.state.style
    color = ctx.pen()
    dash = style.dash
    for tok in args:
        if tok.is_word:
            dash = choice(tok.text, DASH_NAMES, "pattern")
    ctx.frame.add(
        Polyline(x=data.x, y=data.y, color=color, width=style.width, dash=dash)
    )
    ctx.buffer.seal()


def _bin_edges(centres: list[float]) -> list[float]:
    """Bin edges implied by bin centres (uniform or not)."""
    if len(centres) == 1:
        return [centres[0] - 0.5, centres[0] + 0.5]
    mids = [(a + b) / 2.0 for a, b in zip(centres, centres[1:])]
    first = centres[0] - (mids[0] - centres[0])
    last = centres[-1] + (centres[-1] - mids[-1])
    return [first, *mids, last]


@COMMANDS.define("HISTOGRAM", min_abbrev=4, usage="HISTOGRAM [FILL]")
def cmd_histogram(ctx: Context, args: list[Token]) -> None:
    """Draw the data as a step histogram; X values are bin centres."""
    data = ctx.buffer.snapshot()
    style = ctx.state.style
    color = ctx.pen()
    filled = style.fill
    for tok in args:
        if tok.is_word:
            if tok.upper == "FILL":
                filled = True
            elif tok.upper in ("OPEN", "NOFILL"):
                filled = False
            else:
                ctx.warn(f"HISTOGRAM: ignoring {tok.text!r}")
    edges = _bin_edges(data.x)
    xs: list[float] = []
    ys: list[float] = []
    for i, y in enumerate(data.y):
        xs.extend([edges[i], edges[i + 1]])
        ys.extend([y, y])
    if filled or style.hatch != "none":
        # Close the outline down to the baseline so it can be shaded.
        ctx.frame.add(
            Polygon(
                x=[xs[0], *xs, xs[-1]],
                y=[0.0, *ys, 0.0],
                color=color,
                width=style.width,
                dash=style.dash,
                facecolor=color if (filled and style.hatch == "none") else "none",
                hatch=style.hatch,
            )
        )
    else:
        ctx.frame.add(
            Polyline(x=xs, y=ys, color=color, width=style.width, dash=style.dash)
        )
    if data.dy is not None:
        _errorbars(ctx, data, color)
    ctx.buffer.seal()
