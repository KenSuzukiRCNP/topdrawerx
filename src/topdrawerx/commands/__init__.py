"""Every command lives in one small module here.

Importing this package is what fills the registries.  Adding a command means
adding a module and one line below -- no other file changes.
"""

from . import (  # noqa: F401
    annotate,
    axes,
    draw,
    frame,
    legend,
    meta,
    page,
    read,
    setcmd,
    title,
)

__all__ = [
    "annotate",
    "axes",
    "draw",
    "frame",
    "legend",
    "meta",
    "page",
    "read",
    "setcmd",
    "title",
]
