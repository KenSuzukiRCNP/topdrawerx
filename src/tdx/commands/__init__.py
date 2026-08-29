"""Every command lives in one small module here.

Importing this package is what fills the registries.  Adding a command means
adding a module and one line below -- no other file changes.
"""

from . import draw, frame, meta, read, setcmd, title  # noqa: F401

__all__ = ["draw", "frame", "meta", "read", "setcmd", "title"]
