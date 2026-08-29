"""JSON backend -- the test oracle.

Golden-file tests compare display lists, not images: stable across matplotlib
versions, readable in a diff, and they fail with a message you can act on.
"""

from __future__ import annotations

import json

from ..display import Frame


def to_dict(frames: list[Frame]) -> dict:
    return {"frames": [f.to_dict() for f in frames]}


def dumps(frames: list[Frame], indent: int = 2) -> str:
    return json.dumps(to_dict(frames), indent=indent, sort_keys=True, ensure_ascii=False)
