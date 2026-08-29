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
class State:
    x: Axis = field(default_factory=Axis)
    y: Axis = field(default_factory=Axis)
    titles: dict[str, str] = field(default_factory=dict)
    style: Style = field(default_factory=Style)
    ticks: Ticks = field(default_factory=Ticks)
    labels: Labels = field(default_factory=Labels)
    order: tuple[str, ...] = DEFAULT_ORDER
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
            order=tuple(self.order),
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
        return carried
