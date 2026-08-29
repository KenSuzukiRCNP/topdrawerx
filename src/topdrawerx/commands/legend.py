"""LEGEND -- the key TopDrawer never had.

It follows the same rule as ``CASE``: it attaches to the thing just drawn.

    PLOT
    LEGEND 'K⁻ beam'
    JOIN DASHES
    LEGEND 'model'
    LEGEND TOP RIGHT BOX

Entries are drawn with the real symbol, colour and line style of the item they
name, so a legend cannot drift out of step with the plot.
"""

from __future__ import annotations

from ..display import Markers, Polygon, Polyline
from ..errors import ArgumentError
from ..lexer import Token
from ..registry import COMMANDS
from ..session import Context

LABELLABLE = (Markers, Polyline, Polygon)

#: word pairs → matplotlib's corner names
CORNERS = {
    ("TOP", "RIGHT"): "upper right",
    ("TOP", "LEFT"): "upper left",
    ("BOTTOM", "RIGHT"): "lower right",
    ("BOTTOM", "LEFT"): "lower left",
    ("TOP",): "upper center",
    ("BOTTOM",): "lower center",
    ("LEFT",): "center left",
    ("RIGHT",): "center right",
    ("BEST",): "best",
    ("CENTER",): "center",
}


@COMMANDS.define(
    "LEGEND",
    min_abbrev=3,
    usage="LEGEND '<text>' | LEGEND [TOP|BOTTOM] [LEFT|RIGHT] | LEGEND AT <x> <y> | LEGEND OFF | LEGEND BOX",
)
def cmd_legend(ctx: Context, args: list[Token]) -> None:
    """Name the thing just drawn, or place the key."""
    text = next((tok.text for tok in args if tok.is_string), None)
    if text is not None:
        item = next(
            (i for i in reversed(ctx.frame.items) if isinstance(i, LABELLABLE)), None
        )
        if item is None:
            raise ArgumentError("LEGEND '<text>' must follow something drawn")
        item.label = text
        return

    legend = ctx.state.legend
    words: list[str] = []
    coords: list[float] = []
    for tok in args:
        if tok.is_number:
            coords.append(tok.value)
        else:
            words.append(tok.upper)

    if "AT" in words:
        if len(coords) != 2:
            raise ArgumentError("LEGEND AT needs an x and a y (0-1 across the frame)")
        legend.at = (coords[0], coords[1])
        legend.on = True
        words = [w for w in words if w != "AT"]
    for word in words:
        if word == "OFF":
            legend.on = False
        elif word == "ON":
            legend.on = True
        elif word == "BOX":
            legend.box = True
        elif word in ("NOBOX", "OPEN"):
            legend.box = False
        elif word in ("TOP", "BOTTOM", "LEFT", "RIGHT", "BEST", "CENTER"):
            continue
        else:
            ctx.warn(f"LEGEND: ignoring {word!r}")

    corner = tuple(w for w in words if w in ("TOP", "BOTTOM", "LEFT", "RIGHT", "BEST", "CENTER"))
    if corner:
        position = CORNERS.get(corner) or CORNERS.get(tuple(reversed(corner)))
        if position is None:
            raise ArgumentError(f"LEGEND: {' '.join(corner)} is not a corner")
        legend.position = position
        legend.at = None
        legend.on = True
