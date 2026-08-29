"""tdx -- a TopDrawer-flavoured plotting language for modern Python.

Quick use::

    import topdrawerx

    session = tdx.Session()
    session.run('''
        SET ORDER X Y DY
        1.0  2.0  0.1
        2.0  3.9  0.2
        PLOT
        JOIN
        TITLE LEFT '$d\\sigma/d\\Omega$  (μb/sr)'
    ''')
    tdx.save(session.frames, "figure.pdf")

The command language, the display list and the backends are separate on
purpose: see :mod:`tdx.session` for why the whole log is replayed on every
command, and :mod:`tdx.display` for the boundary the backends sit behind.
"""

from __future__ import annotations

from .errors import (
    AmbiguousCommand,
    ArgumentError,
    DataError,
    LexError,
    TdxError,
    UnknownCommand,
)
from .session import Context, Session, render_script, replay
from . import commands  # noqa: F401  (importing this fills the registries)

__version__ = "0.5.0"

__all__ = [
    "Session",
    "Context",
    "render_script",
    "replay",
    "save",
    "figure",
    "TdxError",
    "LexError",
    "UnknownCommand",
    "AmbiguousCommand",
    "ArgumentError",
    "DataError",
    "__version__",
]


def save(frames, path: str) -> list[str]:
    """Write display-list frames to a file (format from the suffix)."""
    from .backends import matplotlib_backend

    return matplotlib_backend.save(frames, path)


def figure(frame):
    """Render one frame into a matplotlib ``Figure`` you can keep working on."""
    from .backends import matplotlib_backend

    return matplotlib_backend.make_figure(frame)
