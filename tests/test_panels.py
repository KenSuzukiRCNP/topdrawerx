"""Several frames on one page: ZONE, SET WINDOW, SET PAGE, NEW PAGE."""

import pytest

from topdrawerx import Session
from topdrawerx.display import layout
from topdrawerx.errors import ArgumentError

DATA = "SET ORDER X Y\n1 1\n2 2\n"


def run(script: str) -> Session:
    session = Session()
    session.run(script)
    return session


def frames_of(session: Session):
    return layout(session.frames)


# -- zones --------------------------------------------------------------
def test_zone_puts_frames_in_cells_of_one_page():
    session = run("ZONE 2 2\n" + (DATA + "PLOT\nNEW FRAME\n") * 3 + DATA + "PLOT\n")
    pages = frames_of(session)
    assert len(pages) == 1
    assert len(pages[0].frames) == 4


def test_cells_fill_left_to_right_then_down():
    session = run("ZONE 2 2\n" + (DATA + "PLOT\nNEW FRAME\n") * 3 + DATA + "PLOT\n")
    rects = [f.rect for f in session.frames]
    assert rects[0][0] < rects[1][0]  # second is to the right of the first
    assert rects[0][1] > rects[2][1]  # third is below the first
    assert rects[2][0] < rects[3][0]


def test_a_full_zone_starts_another_page():
    session = run("ZONE 2 2\n" + (DATA + "PLOT\nNEW FRAME\n") * 4 + DATA + "PLOT\n")
    pages = frames_of(session)
    assert [len(p.frames) for p in pages] == [4, 1]


def test_zone_off_goes_back_to_one_frame_per_page():
    session = run(
        "ZONE 2 2\n" + DATA + "PLOT\nNEW FRAME\nZONE OFF\n" + DATA + "PLOT\n"
    )
    pages = frames_of(session)
    assert [len(p.frames) for p in pages] == [1, 1]


def test_zone_needs_two_numbers():
    with pytest.raises(ArgumentError):
        Session().execute("ZONE 2")


def test_zone_rejects_nonsense_grids():
    with pytest.raises(ArgumentError):
        Session().execute("ZONE 0 3")


# -- windows ------------------------------------------------------------
def test_window_is_taken_as_inches_on_the_page():
    session = run("SET PAGE 10 8\nSET WINDOW X 1 TO 6 Y 2 TO 6\n" + DATA + "PLOT\n")
    x0, y0, x1, y1 = session.frame.rect
    assert (x0, x1) == pytest.approx((0.1, 0.6))
    assert (y0, y1) == pytest.approx((0.25, 0.75))


def test_stacked_windows_touch():
    """The ratio-panel case: adjacent windows leave no gap."""
    session = run(
        "SET PAGE 6 6\nSET WINDOW X 1 TO 5 Y 3 TO 5.5\n" + DATA + "PLOT\n"
        "NEW FRAME\nSET WINDOW X 1 TO 5 Y 1 TO 3\n" + DATA + "PLOT\n"
    )
    upper, lower = session.frames
    assert upper.rect[1] == pytest.approx(lower.rect[3])
    assert len(frames_of(session)) == 1


def test_window_wins_over_zone():
    session = run("ZONE 2 2\nSET WINDOW X 0 TO 6.4 Y 0 TO 5\n" + DATA + "PLOT\n")
    assert session.frame.rect == pytest.approx((0.0, 0.0, 1.0, 1.0))


def test_window_off_returns_to_the_zone():
    session = run(
        "ZONE 2 1\nSET WINDOW X 0 TO 3 Y 0 TO 3\n" + DATA + "PLOT\n"
        "NEW FRAME\nSET WINDOW OFF\n" + DATA + "PLOT\n"
    )
    assert session.frames[1].window is None
    assert session.frames[1].zone == (2, 1)


def test_window_off_the_page_warns_but_still_draws():
    session = run("SET WINDOW X 1 TO 20 Y 1 TO 4\n" + DATA + "PLOT\n")
    assert any("page" in w for w in session.warnings)
    assert session.frame.rect[2] > 1.0


def test_window_needs_both_axes():
    with pytest.raises(ArgumentError):
        Session().execute("SET WINDOW X 1 TO 5")


# -- pages --------------------------------------------------------------
def test_set_page_changes_the_page_size():
    session = run("SET PAGE 9 7\n" + DATA + "PLOT\n")
    assert frames_of(session)[0].size == (9.0, 7.0)


def test_new_page_leaves_the_rest_of_the_zone_empty():
    session = run(
        "ZONE 2 2\n" + DATA + "PLOT\nNEW PAGE\n" + DATA + "PLOT\n"
    )
    pages = frames_of(session)
    assert [len(p.frames) for p in pages] == [1, 1]


def test_page_settings_survive_new_frame():
    session = run("SET PAGE 9 7\nZONE 2 1\n" + DATA + "PLOT\nNEW FRAME\n")
    assert session.state.page.width == pytest.approx(9)
    assert session.state.zone == (2, 1)


def test_a_zone_typed_later_lays_out_the_frames_after_it():
    session = run(DATA + "PLOT\nNEW FRAME\nZONE 2 1\n" + DATA + "PLOT\n")
    pages = frames_of(session)
    assert [len(p.frames) for p in pages] == [1, 1]
    assert session.frames[1].zone == (2, 1)


def test_layout_survives_replay():
    session = run("ZONE 2 2\n" + DATA + "PLOT\nNEW FRAME\n" + DATA + "PLOT\n")
    again = Session()
    again.run(session.script())
    assert [f.rect for f in again.frames] == [f.rect for f in session.frames]


def test_panels_render_to_one_file_per_page(tmp_path):
    import matplotlib

    matplotlib.use("Agg")
    from topdrawerx import save

    session = run("ZONE 1 2\n" + DATA + "PLOT\nNEW PAGE\n" + DATA + "PLOT\n")
    written = save(session.frames, str(tmp_path / "p.png"))
    assert [p.split("/")[-1] for p in written] == ["p-1.png", "p-2.png"]
