"""Several frames on one page: ZONE, SET WINDOW, SET PAGE, NEW PAGE.

    ZONE 2 2                     divide the page into four; each NEW FRAME
                                 takes the next cell, filling left to right
    ZONE OFF                     back to one frame per page

    SET PAGE 9 7                 the page itself, in inches
    SET WINDOW X 1 TO 5 Y 4 TO 7 put this frame exactly there, in inches
    SET WINDOW OFF               back to the zone (or the whole page)

    NEW PAGE                     start a page, leaving the rest of the zone
                                 empty

``ZONE`` gives equal cells, which is what most multi-panel figures want.  For
unequal ones — a tall plot over a short ratio panel, sharing an axis — use
``SET WINDOW`` on each frame; adjacent windows leave no gap, which is the point.

Dividing a page does not enlarge it: four panels on a 6.4 x 5 inch page are
quarter-size.  ``SET PAGE`` is how you get room.
"""

from __future__ import annotations

from ..errors import ArgumentError
from ..lexer import Token
from ..registry import COMMANDS, SETTERS
from ..session import Context
from ._util import strip_noise

AXES = {"X": 0, "Y": 1}


@COMMANDS.define("ZONE", min_abbrev=3, usage="ZONE <columns> <rows> | ZONE OFF")
def cmd_zone(ctx: Context, args: list[Token]) -> None:
    """Divide the page into equal cells, one frame per cell."""
    if any(tok.is_word and tok.upper in ("OFF", "NONE") for tok in args):
        ctx.state.zone = None
        return
    numbers = [tok.value for tok in args if tok.is_number]
    if len(numbers) != 2:
        raise ArgumentError("ZONE needs columns and rows, e.g. ZONE 2 2")
    cols, rows = (int(n) for n in numbers)
    if cols < 1 or rows < 1:
        raise ArgumentError("ZONE needs positive numbers of columns and rows")
    ctx.state.zone = (cols, rows)


@SETTERS.define("PAGE", min_abbrev=3, usage="SET PAGE <width> <height>   (inches)")
def set_page(ctx: Context, args: list[Token]) -> None:
    """Set the page size in inches."""
    numbers = [tok.value for tok in strip_noise(args) if tok.is_number]
    if len(numbers) != 2:
        raise ArgumentError("SET PAGE needs a width and a height in inches")
    width, height = numbers
    if width <= 0 or height <= 0:
        raise ArgumentError("SET PAGE needs positive sizes")
    ctx.state.page.width = width
    ctx.state.page.height = height


@SETTERS.define(
    "WINDOW",
    min_abbrev=3,
    usage="SET WINDOW X <x0> TO <x1> Y <y0> TO <y1>   (inches) | SET WINDOW OFF",
)
def set_window(ctx: Context, args: list[Token]) -> None:
    """Place this frame exactly, in inches on the page."""
    args = strip_noise(args)
    if any(tok.is_word and tok.upper in ("OFF", "NONE", "AUTO") for tok in args):
        ctx.state.window = None
        return

    values: dict[str, list[float]] = {"X": [], "Y": []}
    axis: str | None = None
    for tok in args:
        if tok.is_word:
            if tok.upper not in AXES:
                raise ArgumentError(f"SET WINDOW: unexpected {tok.text!r}")
            axis = tok.upper
            continue
        if axis is None:
            raise ArgumentError("SET WINDOW: say which axis first, e.g. X 1 TO 5")
        values[axis].append(tok.value)

    if len(values["X"]) != 2 or len(values["Y"]) != 2:
        raise ArgumentError("SET WINDOW needs X <x0> TO <x1> Y <y0> TO <y1>, in inches")
    page = ctx.state.page
    x0, x1 = values["X"]
    y0, y1 = values["Y"]
    for name, hi, extent in (("X", max(x0, x1), page.width), ("Y", max(y0, y1), page.height)):
        if hi > extent + 1e-9:
            ctx.warn(
                f"SET WINDOW {name} reaches {hi:g}in on a {extent:g}in page; "
                "SET PAGE first if that was not deliberate"
            )
    ctx.state.window = (x0, y0, x1, y1)
