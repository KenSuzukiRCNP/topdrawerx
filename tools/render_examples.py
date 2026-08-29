#!/usr/bin/env python3
"""Render every example into ``docs/images`` for the README gallery.

    python tools/render_examples.py

Run it after changing an example or anything that affects how a figure looks;
the images in the gallery are checked in, so the README works on GitHub.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")

from topdrawerx import Session, save  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
IMAGES = ROOT / "docs" / "images"


def main() -> int:
    IMAGES.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for source in sorted(EXAMPLES.glob("*.tdx")) + sorted(EXAMPLES.glob("*.top")):
        session = Session()
        session.run(source.read_text(encoding="utf-8"), lenient=True)
        for warning in session.warnings:
            print(f"  {source.name}: {warning}", file=sys.stderr)
        target = IMAGES / f"{source.stem}.png"
        written.extend(save(session.frames, str(target)))
    for path in written:
        print(f"wrote {pathlib.Path(path).relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
