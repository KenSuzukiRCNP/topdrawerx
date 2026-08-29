"""Backends turn a display list into something you can look at.

``matplotlib`` is the default; ``json`` is used by the tests.  Nothing above
this package knows which one is in use.
"""

from . import json_backend, matplotlib_backend  # noqa: F401

__all__ = ["json_backend", "matplotlib_backend"]
