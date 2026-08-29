"""The display list -- the boundary between language and graphics.

The interpreter never imports matplotlib.  It produces frames made of a small
set of primitives in data coordinates, and a backend turns those into pictures.
Two things fall out of that:

* a second backend (native SVG, an interactive canvas) can be added without
  touching a single command;
* tests compare a JSON dump of the display list, which is stable and readable,
  instead of comparing PNGs pixel by pixel.

Keep this vocabulary small.  If a new command needs a new primitive, that is a
design decision worth making explicitly.  Every primitive answers
:meth:`points`, which is all the automatic-limit code needs to know about it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .state import Labels, Legend, State, TITLE_SLOTS, Ticks


@dataclass
class Polyline:
    x: list[float]
    y: list[float]
    color: str = "black"
    width: float = 1.2
    dash: str = "solid"
    label: str | None = None
    kind: str = field(default="polyline", init=False)

    def points(self) -> tuple[list[float], list[float]]:
        return list(self.x), list(self.y)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "x": list(self.x),
            "y": list(self.y),
            "color": self.color,
            "width": self.width,
            "dash": self.dash,
            "label": self.label,
        }


@dataclass
class Markers:
    x: list[float]
    y: list[float]
    symbol: str = "circle"
    size: float = 5.0
    color: str = "black"
    fill: bool = False
    label: str | None = None
    kind: str = field(default="markers", init=False)

    def points(self) -> tuple[list[float], list[float]]:
        return list(self.x), list(self.y)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "x": list(self.x),
            "y": list(self.y),
            "symbol": self.symbol,
            "size": self.size,
            "color": self.color,
            "fill": self.fill,
            "label": self.label,
        }


@dataclass
class ErrorBars:
    x: list[float]
    y: list[float]
    dx: list[float] | None = None
    dy: list[float] | None = None
    color: str = "black"
    width: float = 1.0
    kind: str = field(default="errorbars", init=False)

    def points(self) -> tuple[list[float], list[float]]:
        xs: list[float] = []
        ys: list[float] = []
        for i, (px, py) in enumerate(zip(self.x, self.y)):
            ex = self.dx[i] if self.dx else 0.0
            ey = self.dy[i] if self.dy else 0.0
            xs.extend([px - ex, px + ex])
            ys.extend([py - ey, py + ey])
        return xs, ys

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "x": list(self.x),
            "y": list(self.y),
            "dx": list(self.dx) if self.dx else None,
            "dy": list(self.dy) if self.dy else None,
            "color": self.color,
            "width": self.width,
        }


@dataclass
class Polygon:
    """A closed, optionally filled area — a filled histogram, a band."""

    x: list[float]
    y: list[float]
    color: str = "black"
    width: float = 1.2
    dash: str = "solid"
    facecolor: str | None = None
    hatch: str = "none"
    label: str | None = None
    kind: str = field(default="polygon", init=False)

    def points(self) -> tuple[list[float], list[float]]:
        return list(self.x), list(self.y)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "x": list(self.x),
            "y": list(self.y),
            "color": self.color,
            "width": self.width,
            "dash": self.dash,
            "facecolor": self.facecolor,
            "hatch": self.hatch,
            "label": self.label,
        }


@dataclass
class Box:
    """A rectangle in data coordinates."""

    x0: float
    y0: float
    x1: float
    y1: float
    color: str = "black"
    width: float = 1.2
    dash: str = "solid"
    facecolor: str | None = None
    hatch: str = "none"
    kind: str = field(default="box", init=False)

    def points(self) -> tuple[list[float], list[float]]:
        return [self.x0, self.x1], [self.y0, self.y1]

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "x0": self.x0,
            "y0": self.y0,
            "x1": self.x1,
            "y1": self.y1,
            "color": self.color,
            "width": self.width,
            "dash": self.dash,
            "facecolor": self.facecolor,
            "hatch": self.hatch,
        }


@dataclass
class Arrow:
    """An arrow from (x0, y0) to (x1, y1) in data coordinates."""

    x0: float
    y0: float
    x1: float
    y1: float
    color: str = "black"
    width: float = 1.2
    head: bool = True
    kind: str = field(default="arrow", init=False)

    def points(self) -> tuple[list[float], list[float]]:
        return [self.x0, self.x1], [self.y0, self.y1]

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "x0": self.x0,
            "y0": self.y0,
            "x1": self.x1,
            "y1": self.y1,
            "color": self.color,
            "width": self.width,
            "head": self.head,
        }


@dataclass
class Text:
    """Text at a point, in data coordinates unless *frame* coordinates are asked
    for (0-1 across the frame), which is how a legend line gets placed."""

    x: float
    y: float
    text: str
    size: float | None = None
    angle: float = 0.0
    color: str = "black"
    align: str = "left"
    frame_coords: bool = False
    kind: str = field(default="text", init=False)

    def points(self) -> tuple[list[float], list[float]]:
        if self.frame_coords:
            return [], []
        return [self.x], [self.y]

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "x": self.x,
            "y": self.y,
            "text": self.text,
            "size": self.size,
            "angle": self.angle,
            "color": self.color,
            "align": self.align,
            "frame_coords": self.frame_coords,
        }


Item = Polyline | Markers | ErrorBars | Polygon | Box | Arrow | Text


@dataclass
class Frame:
    """One picture: axes settings, titles and the things drawn on them."""

    items: list[Item] = field(default_factory=list)
    xlim: tuple[float, float] | None = None
    ylim: tuple[float, float] | None = None
    xlog: bool = False
    ylog: bool = False
    titles: dict[str, str] = field(default_factory=dict)
    font: str = "serif"
    font_size: float | None = None
    ticks: Ticks = field(default_factory=Ticks)
    labels: Labels = field(default_factory=Labels)
    legend: Legend = field(default_factory=Legend)

    def add(self, item: Item) -> None:
        self.items.append(item)

    @property
    def empty(self) -> bool:
        return not self.items and not self.titles

    def apply_state(self, state: State) -> None:
        """Copy the final graphics state onto the frame.

        Called when the frame closes, which is why ``SET LIMITS`` typed after a
        ``PLOT`` still applies to it.
        """
        self.xlim = state.x.limits()
        self.ylim = state.y.limits()
        self.xlog = state.x.log
        self.ylog = state.y.log
        self.titles = {k: v for k, v in state.titles.items() if k in TITLE_SLOTS}
        self.font = state.style.font
        self.font_size = state.style.font_size
        self.ticks = state.ticks.copy()
        self.labels = state.labels.copy()
        self.legend = state.legend.copy()

    # -- limits ---------------------------------------------------------
    def data_bounds(self) -> tuple[float, float, float, float] | None:
        xs: list[float] = []
        ys: list[float] = []
        for item in self.items:
            ix, iy = item.points()
            xs.extend(ix)
            ys.extend(iy)
        if not xs or not ys:
            return None
        return min(xs), max(xs), min(ys), max(ys)

    def resolved_limits(self) -> tuple[tuple[float, float], tuple[float, float]]:
        """Limits actually used for drawing, filling in whatever is automatic."""
        bounds = self.data_bounds()
        xlim = self.xlim or (_pad(bounds[0], bounds[1], self.xlog) if bounds else (0.0, 1.0))
        ylim = self.ylim or (_pad(bounds[2], bounds[3], self.ylog) if bounds else (0.0, 1.0))
        return xlim, ylim

    def to_dict(self) -> dict:
        xlim, ylim = self.resolved_limits()
        return {
            "xlim": list(xlim),
            "ylim": list(ylim),
            "xlog": self.xlog,
            "ylog": self.ylog,
            "auto_xlim": self.xlim is None,
            "auto_ylim": self.ylim is None,
            "titles": dict(self.titles),
            "font": self.font,
            "font_size": self.font_size,
            "ticks": self.ticks.to_dict(),
            "labels": self.labels.to_dict(),
            "legend": self.legend.to_dict(),
            "items": [item.to_dict() for item in self.items],
        }


def _pad(lo: float, hi: float, log: bool, frac: float = 0.05) -> tuple[float, float]:
    """Round data bounds outward a little so points do not sit on the frame."""
    if log:
        # Snap automatic log limits to whole decades: a half-labelled decade is
        # the classic ugly default, and it is what people fix by hand.
        import math

        lo = max(lo, 1e-300)
        hi = max(hi, lo * 1.0000001)
        return 10 ** math.floor(math.log10(lo)), 10 ** math.ceil(math.log10(hi))
    if hi == lo:
        pad = abs(hi) * frac or 0.5
        return lo - pad, hi + pad
    pad = (hi - lo) * frac
    return lo - pad, hi + pad
