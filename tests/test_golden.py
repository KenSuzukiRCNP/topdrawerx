"""Golden-file test over the display list.

Comparing display lists rather than images means the test is stable across
matplotlib versions and a failure is readable in a diff.  Regenerate after an
intentional change with::

    TDX_UPDATE_GOLDEN=1 python -m pytest tests/test_golden.py
"""

import json
import os
import pathlib

from topdrawerx import Session
from topdrawerx.backends import json_backend

ROOT = pathlib.Path(__file__).resolve().parents[1]
GOLDEN = pathlib.Path(__file__).parent / "golden" / "demo.json"


def test_demo_display_list_matches_golden():
    session = Session()
    session.run((ROOT / "examples" / "demo.tdx").read_text(encoding="utf-8"))
    produced = json_backend.dumps(session.frames)

    if os.environ.get("TDX_UPDATE_GOLDEN"):
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(produced + "\n", encoding="utf-8")

    assert json.loads(produced) == json.loads(GOLDEN.read_text(encoding="utf-8"))
