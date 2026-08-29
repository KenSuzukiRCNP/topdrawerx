"""The graphics state: everything ``SET`` can change.

The state is a plain dataclass that drawing verbs read and ``SET`` writes.  It
is rebuilt from scratch on every replay (see :mod:`tdx.session`), which is what
makes ``SET LIMITS`` typed *after* ``PLOT`` take effect retroactively -- an
improvement the original could not offer on a storage-tube terminal.

Two groups of fields behave differently at ``NEW FRAME``:

* *per-frame* -- limits, log scaling and titles reset, because they describe
  one picture;
* *persistent* -- symbol, colour, line style and data order carry over, because
  they describe how you like to draw.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

DEFAULT_ORDER = ("X", "Y")
TITLE_SLOTS = ("TOP", "BOTTOM", "LEFT", "RIGHT")


@dataclass
class Axis:
    lo: float | None = None
    hi: float | None = None
    log: bool = False

    @property
    def auto(self) -> bool:
        return self.lo is None or self.hi is None

    def limits(self) -> tuple[float, float] | None:
        if self.auto:
            return None
        return (float(self.lo), float(self.hi))


@dataclass
class Style:
    """How the next drawing verb will look."""

    color: str = "black"
    width: float = 1.2
    dash: str = "solid"  # solid | dashes | dots | dotdash
    symbol: str = "circle"
    size: float = 5.0
    fill: bool = False
    #: Font family for every piece of text on the frame (SET FONT).
    font: str = "serif"
    #: Base text size in points; None follows the backend default.
    font_size: float | None = None
    #: Hatch pattern for filled areas (SET HATCH); "none" for a plain fill.
    hatch: str = "none"


SIDES = ("TOP", "BOTTOM", "LEFT", "RIGHT")


@dataclass
class Ticks:
    """Axis tick marks — ``SET TICKS``.

    ``size`` is the length of the *short* (minor) ticks in inches, as in the
    original, and ``long`` the ratio of major to minor. ``direction`` is tdx's
    own: the plotter always drew them inward, but outward ticks are a
    legitimate house style.
    """

    size: float = 0.1
    long: float = 3.0
    direction: str = "in"
    on: dict[str, bool] = field(
        default_factory=lambda: {"TOP": True, "BOTTOM": True, "LEFT": True, "RIGHT": True}
    )
    permanent: bool = False

    def copy(self) -> "Ticks":
        return Ticks(self.size, self.long, self.direction, dict(self.on), self.permanent)

    def to_dict(self) -> dict:
        return {
            "size": self.size,
            "long": self.long,
            "direction": self.direction,
            "on": dict(self.on),
        }


@dataclass
class Labels:
    """Numeric axis labels — ``SET LABELS``.  ``size`` is in points."""

    size: float | None = None
    on: dict[str, bool] = field(
        default_factory=lambda: {"TOP": False, "BOTTOM": True, "LEFT": True, "RIGHT": False}
    )
    permanent: bool = False

    def copy(self) -> "Labels":
        return Labels(self.size, dict(self.on), self.permanent)

    def to_dict(self) -> dict:
        return {"size": self.size, "on": dict(self.on)}


@dataclass
class Page:
    """The physical page, in inches — ``SET PAGE``.

    Frames are placed on it: ``ZONE`` divides it into equal cells, ``SET
    WINDOW`` puts a frame at an exact position.  Dividing a page does not
    enlarge it, exactly as on a plotter, so a 2x2 zone gives four quarter-size
    panels; make the page bigger if you want bigger panels.
    """

    width: float = 6.4
    height: float = 5.0

    def copy(self) -> "Page":
        return Page(self.width, self.height)

    def to_dict(self) -> dict:
        return {"width": self.width, "height": self.height}


@dataclass
class Legend:
    """Where the key goes — ``LEGEND AT``, ``LEGEND TOP RIGHT``, ``LEGEND OFF``."""

    on: bool = True
    position: str = "best"
    at: tuple[float, float] | None = None
    box: bool = False

    def copy(self) -> "Legend":
        return Legend(self.on, self.position, self.at, self.box)

    def to_dict(self) -> dict:
        return {
            "on": self.on,
            "position": self.position,
            "at": list(self.at) if self.at else None,
            "box": self.box,
        }


@dataclass
class State:
    x: Axis = field(default_factory=Axis)
    y: Axis = field(default_factory=Axis)
    titles: dict[str, str] = field(default_factory=dict)
    style: Style = field(default_factory=Style)
    ticks: Ticks = field(default_factory=Ticks)
    labels: Labels = field(default_factory=Labels)
    legend: Legend = field(default_factory=Legend)
    order: tuple[str, ...] = DEFAULT_ORDER
    #: Page layout.  ``zone`` is (columns, rows) or None; ``window`` is an
    #: explicit (x0, y0, x1, y1) in inches and wins over the zone.  Both live
    #: on the page, so they survive NEW FRAME.
    page: Page = field(default_factory=Page)
    zone: tuple[int, int] | None = None
    window: tuple[float, float, float, float] | None = None
    #: Colour cycling: the palette name, and how far through it we are.
    #: "none" means every dataset is drawn in the current SET COLOR, which is
    #: the original's behaviour and stays the default.
    palette: str = "none"
    palette_index: int = -1
    #: Settings accepted for compatibility and deliberately not acted on
    #: (SET DEVICE, SET INTENSITY on a device with no pens, ...).
    ignored: dict[str, str] = field(default_factory=dict)

    def copy(self) -> "State":
        return State(
            x=replace(self.x),
            y=replace(self.y),
            titles=dict(self.titles),
            style=replace(self.style),
            ticks=self.ticks.copy(),
            labels=self.labels.copy(),
            legend=self.legend.copy(),
            order=tuple(self.order),
            page=self.page.copy(),
            zone=self.zone,
            window=self.window,
            palette=self.palette,
            palette_index=self.palette_index,
            ignored=dict(self.ignored),
        )

    def next_frame(self) -> "State":
        """State for the frame that follows ``NEW FRAME``.

        Axis furniture goes back to the default unless it was set
        ``PERMANENT``, which is how the original distinguished "this plot" from
        "every plot".
        """
        carried = self.copy()
        carried.x = Axis(log=self.x.log)
        carried.y = Axis(log=self.y.log)
        carried.titles = {}
        if not self.ticks.permanent:
            carried.ticks = Ticks()
        if not self.labels.permanent:
            carried.labels = Labels()
        carried.palette_index = -1  # each frame starts at the top of the palette
        return carried
