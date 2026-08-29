"""The display list -- the boundary between language and graphics.

The interpreter never imports matplotlib.  It produces frames made of a small
set of primitives in data coordinates, and a backend turns those into pictures.
Two things fall out of that:

* a second backend (native SVG, an interactive canvas) can be added without
  touching a single command;
* tests compare a JSON dump of the display list, which is stable and readable,
  instead of comparing PNGs pixel by pixel.

Keep this vocabulary small.  If a new command needs a new primitive, that is a
design decision worth making explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .state import TITLE_SLOTS, State


@dataclass
class Polyline:
    x: list[float]
    y: list[float]
    color: str = "black"
    width: float = 1.2
    dash: str = "solid"
    kind: str = field(default="polyline", init=False)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "x": list(self.x),
            "y": list(self.y),
            "color": self.color,
            "width": self.width,
            "dash": self.dash,
        }


@dataclass
class Markers:
    x: list[float]
    y: list[float]
    symbol: str = "circle"
    size: float = 5.0
    color: str = "black"
    fill: bool = False
    kind: str = field(default="markers", init=False)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "x": list(self.x),
            "y": list(self.y),
            "symbol": self.symbol,
            "size": self.size,
            "color": self.color,
            "fill": self.fill,
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


Item = Polyline | Markers | ErrorBars


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

    # -- limits ---------------------------------------------------------
    def data_bounds(self) -> tuple[float, float, float, float] | None:
        xs: list[float] = []
        ys: list[float] = []
        for item in self.items:
            dx = getattr(item, "dx", None)
            dy = getattr(item, "dy", None)
            for i, (px, py) in enumerate(zip(item.x, item.y)):
                ex = dx[i] if dx else 0.0
                ey = dy[i] if dy else 0.0
                xs.extend([px - ex, px + ex])
                ys.extend([py - ey, py + ey])
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
