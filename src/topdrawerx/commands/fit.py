"""FIT and SPLINE — curves from the data in the buffer.

    FIT LINE                       a straight line
    FIT POLY 3                     a cubic
    FIT GAUSSIAN                   a peak
    FIT EXPONENTIAL                a decay
    FIT GAUSSIAN FROM 1.8 TO 2.1   fit only that range, and draw only there
    FIT LINE NODRAW                report the numbers, draw nothing
    SPLINE                         a smooth curve *through* every point

Both behave like any other drawing verb: they take what is in the buffer, add a
curve to the frame, and seal the buffer — so the familiar idiom works::

    SET ORDER X Y DY
    ... data ...
    PLOT
    FIT GAUSSIAN

A ``DY`` column makes the fit weighted and χ²/ndf meaningful. The parameters
are printed, and are also on the session as :attr:`Session.fits` for anyone
driving topdrawerx from Python.

The difference between the two commands is worth stating: ``FIT`` draws the
best curve *near* the points, ``SPLINE`` draws a smooth curve *through* them.
A spline is a drawing aid, not a model — do not read parameters into it.
"""

from __future__ import annotations

from .. import fitting
from ..display import Polyline
from ..errors import ArgumentError
from ..lexer import Token
from ..registry import COMMANDS
from ..session import Context

DEFAULT_POINTS = 200


def _draw(ctx: Context, function, lo: float, hi: float, points: int) -> None:
    style = ctx.state.style
    xs, ys = fitting.curve_points(function, lo, hi, points)
    ctx.frame.add(
        Polyline(x=xs, y=ys, color=ctx.pen(), width=style.width, dash=style.dash)
    )


def _restrict(data, lo: float | None, hi: float | None):
    """The points inside the requested range, as three plain lists."""
    xs, ys = data.x, data.y
    dy = data.dy
    keep = [
        i
        for i, value in enumerate(xs)
        if (lo is None or value >= lo) and (hi is None or value <= hi)
    ]
    if not keep:
        raise ArgumentError("no data points in that range")
    return (
        [xs[i] for i in keep],
        [ys[i] for i in keep],
        [dy[i] for i in keep] if dy else None,
    )


@COMMANDS.define(
    "FIT",
    min_abbrev=3,
    usage="FIT LINE|POLY <n>|GAUSSIAN|EXPONENTIAL [FROM <x> TO <x>] [POINTS <n>] [NODRAW]",
)
def cmd_fit(ctx: Context, args: list[Token]) -> None:
    """Fit a curve to the data, draw it, and report the parameters."""
    model: str | None = None
    degree = 1
    lo = hi = None
    points = DEFAULT_POINTS
    draw = True
    expect: str | None = None

    for tok in args:
        if tok.is_number:
            if expect == "degree":
                degree = int(tok.value)
            elif expect == "from":
                lo = tok.value
            elif expect == "to":
                hi = tok.value
            elif expect == "points":
                points = int(tok.value)
            else:
                raise ArgumentError(
                    f"FIT: {tok.text} follows nothing — say FROM/TO for a range, "
                    "POINTS for the curve resolution"
                )
            expect = None
            continue
        word = tok.upper
        if word in fitting.MODELS:
            model = word
            expect = "degree" if word == "POLY" else None
        elif word in ("FROM", "TO", "POINTS"):
            expect = word.lower()
        elif word in ("NODRAW", "NOPLOT"):
            draw = False
        else:
            raise ArgumentError(
                f"FIT: don't understand {tok.text!r}; models are "
                + ", ".join(m.lower() for m in fitting.MODELS)
            )

    if model is None:
        raise ArgumentError(
            "FIT needs a model: " + ", ".join(m.lower() for m in fitting.MODELS)
        )
    if model == "POLY" and degree < 1:
        raise ArgumentError("FIT POLY needs a degree of at least 1")

    data = ctx.buffer.snapshot()
    xs, ys, dy = _restrict(data, lo, hi)
    try:
        result = fitting.fit(model, xs, ys, dy, degree=degree)
    except fitting.FitError as exc:
        raise ArgumentError(str(exc)) from None

    ctx.fits.append(result)
    for line in result.summary():
        ctx.say(line)
    if result.note:
        ctx.warn(result.note)

    if draw:
        _draw(ctx, result.function, min(xs), max(xs), points)
    ctx.buffer.seal()


@COMMANDS.define("SPLINE", min_abbrev=3, usage="SPLINE [POINTS <n>]")
def cmd_spline(ctx: Context, args: list[Token]) -> None:
    """Draw a smooth curve through the data points."""
    points = DEFAULT_POINTS
    expect = False
    for tok in args:
        if tok.is_number:
            if not expect:
                raise ArgumentError("SPLINE: say POINTS before the number")
            points = int(tok.value)
            expect = False
        elif tok.upper == "POINTS":
            expect = True
        else:
            raise ArgumentError(f"SPLINE: don't understand {tok.text!r}")

    data = ctx.buffer.snapshot()
    try:
        function = fitting.natural_cubic_spline(data.x, data.y)
    except fitting.FitError as exc:
        raise ArgumentError(str(exc)) from None
    _draw(ctx, function, min(data.x), max(data.x), points)
    ctx.buffer.seal()
