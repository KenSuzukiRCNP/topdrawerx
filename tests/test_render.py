"""The backend actually produces files.

Kept deliberately thin: the display-list tests carry the meaning, this only
checks that matplotlib is wired up and the suffix picks the format.
"""

import matplotlib

matplotlib.use("Agg")

import pathlib  # noqa: E402

import pytest  # noqa: E402

from tdx import Session, save  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _demo_session() -> Session:
    session = Session()
    session.run((ROOT / "examples" / "demo.tdx").read_text(encoding="utf-8"))
    return session


@pytest.mark.parametrize("suffix", [".png", ".pdf", ".svg"])
def test_save_writes_a_file(tmp_path, suffix):
    session = _demo_session()
    written = save(session.frames, str(tmp_path / f"fig{suffix}"))
    assert written
    for path in written:
        assert pathlib.Path(path).stat().st_size > 0


def test_multi_frame_pdf_is_one_file(tmp_path):
    session = _demo_session()
    assert len(session.frames) == 2
    written = save(session.frames, str(tmp_path / "both.pdf"))
    assert len(written) == 1


def test_multi_frame_png_is_numbered(tmp_path):
    session = _demo_session()
    written = save(session.frames, str(tmp_path / "both.png"))
    assert [pathlib.Path(p).name for p in written] == ["both-1.png", "both-2.png"]
