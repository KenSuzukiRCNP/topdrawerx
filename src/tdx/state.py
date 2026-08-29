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


@dataclass
class State:
    x: Axis = field(default_factory=Axis)
    y: Axis = field(default_factory=Axis)
    titles: dict[str, str] = field(default_factory=dict)
    style: Style = field(default_factory=Style)
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
            order=tuple(self.order),
            ignored=dict(self.ignored),
        )

    def next_frame(self) -> "State":
        """State for the frame that follows ``NEW FRAME``."""
        carried = self.copy()
        carried.x = Axis(log=self.x.log)
        carried.y = Axis(log=self.y.log)
        carried.titles = {}
        return carried
