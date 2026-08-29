"""The data buffer.

``SET ORDER`` names the columns; bare numeric lines fill them; a drawing verb
consumes what has accumulated.  The original's idiom is preserved, including
the useful part where two verbs can draw the same points::

    SET ORDER X Y DY
    1.0  2.0  0.1
    2.0  3.9  0.2
    PLOT
    JOIN

After a verb has drawn, the buffer is *sealed*: the next data line starts a
fresh dataset rather than appending to the one already drawn.

Roles understood in this milestone: ``X``, ``Y``, ``DX``, ``DY``.  Anything
else is accepted, stored and ignored, so a legacy ``SET ORDER X Y DY DX FLAG``
still plots instead of aborting.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .errors import DataError

KNOWN_ROLES = ("X", "Y", "DX", "DY")


@dataclass
class DataSet:
    order: tuple[str, ...]
    rows: list[list[float]]

    def __len__(self) -> int:
        return len(self.rows)

    def column(self, role: str) -> list[float] | None:
        role = role.upper()
        if role not in self.order:
            return None
        i = self.order.index(role)
        return [row[i] for row in self.rows]

    @property
    def x(self) -> list[float]:
        col = self.column("X")
        if col is None:
            raise DataError("no X column: check SET ORDER")
        return col

    @property
    def y(self) -> list[float]:
        col = self.column("Y")
        if col is None:
            raise DataError("no Y column: check SET ORDER")
        return col

    @property
    def dx(self) -> list[float] | None:
        return self.column("DX")

    @property
    def dy(self) -> list[float] | None:
        return self.column("DY")


@dataclass
class DataBuffer:
    order: tuple[str, ...] = ("X", "Y")
    rows: list[list[float]] = field(default_factory=list)
    sealed: bool = False

    def set_order(self, roles: tuple[str, ...]) -> None:
        self.order = tuple(r.upper() for r in roles)
        self.rows = []
        self.sealed = False

    def add_row(self, values: list[float], lineno: int | None = None) -> None:
        if self.sealed:
            self.rows = []
            self.sealed = False
        want = len(self.order)
        if len(values) < want:
            raise DataError(
                f"expected {want} numbers for order {' '.join(self.order)}, got {len(values)}",
                lineno,
            )
        self.rows.append([float(v) for v in values[:want]])

    def seal(self) -> None:
        self.sealed = True

    def clear(self) -> None:
        self.rows = []
        self.sealed = False

    def snapshot(self) -> DataSet:
        if not self.rows:
            raise DataError("no data: give some numbers before a drawing command")
        return DataSet(order=tuple(self.order), rows=[list(r) for r in self.rows])


def read_table(path: str, ncolumns: int) -> list[list[float]]:
    """Read a whitespace- or comma-separated numeric table from *path*.

    Non-numeric lines (headers, comments) are skipped, so a CSV with a header
    row just works.  This is the modern replacement for having to paste your
    numbers into the plot file.
    """
    from .lexer import parse_number

    rows: list[list[float]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line[0] in "!#;":
                continue
            fields = [f for f in line.replace(",", " ").split() if f]
            values = [parse_number(f) for f in fields]
            if any(v is None for v in values):
                continue
            if len(values) < ncolumns:
                continue
            rows.append([float(v) for v in values[:ncolumns]])
    if not rows:
        raise DataError(f"no numeric rows found in {path}")
    return rows
