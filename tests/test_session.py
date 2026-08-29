import pytest

from tdx import Session
from tdx.display import ErrorBars, Markers, Polyline
from tdx.errors import ArgumentError, DataError, UnknownCommand

SIMPLE = """
SET ORDER X Y
1 2
2 4
3 6
PLOT
"""


def run(script: str) -> Session:
    session = Session()
    session.run(script)
    return session


def test_plot_makes_markers():
    frame = run(SIMPLE).frame
    assert len(frame.items) == 1
    assert isinstance(frame.items[0], Markers)
    assert frame.items[0].x == [1.0, 2.0, 3.0]


def test_plot_then_join_share_the_data():
    frame = run(SIMPLE + "JOIN\n").frame
    kinds = [type(i) for i in frame.items]
    assert kinds == [Markers, Polyline]
    assert frame.items[0].x == frame.items[1].x


def test_new_data_after_a_verb_starts_a_new_dataset():
    frame = run(SIMPLE + "10 20\n11 22\nJOIN\n").frame
    assert frame.items[1].x == [10.0, 11.0]


def test_error_columns_make_error_bars():
    frame = run("SET ORDER X Y DY\n1 2 0.1\n2 4 0.2\nPLOT\n").frame
    assert isinstance(frame.items[0], ErrorBars)
    assert frame.items[0].dy == [0.1, 0.2]


def test_limits_apply_retroactively():
    """The point of replay: settings typed after the plot still take effect."""
    session = run(SIMPLE)
    assert session.frame.xlim is None
    session.execute("SET LIMITS X 0 10 Y 0 20")
    assert session.frame.xlim == (0.0, 10.0)
    assert session.frame.ylim == (0.0, 20.0)


def test_limits_accept_noise_words():
    session = run("SET LIMITS X FROM 0 TO 10\n")
    assert session.state.x.limits() == (0.0, 10.0)


def test_auto_limits_pad_the_data():
    (xlo, xhi), _ = run(SIMPLE).frame.resolved_limits()
    assert xlo < 1.0 and xhi > 3.0


def test_undo_removes_the_last_command():
    session = run(SIMPLE)
    session.execute("JOIN")
    assert len(session.frame.items) == 2
    session.execute("UNDO")
    assert len(session.frame.items) == 1


def test_a_failing_command_leaves_the_session_untouched():
    session = run(SIMPLE)
    before = session.script()
    with pytest.raises(ArgumentError):
        session.execute("SET LIMITS X 0")
    assert session.script() == before
    assert len(session.frame.items) == 1


def test_meta_commands_are_not_recorded():
    session = run(SIMPLE)
    session.execute("SHOW")
    assert "SHOW" not in session.script()


def test_new_frame_resets_titles_but_keeps_style():
    session = run(
        "SET SYMBOL SQUARE\nTITLE TOP 'one'\n" + SIMPLE + "NEW FRAME\n1 1\n2 2\nPLOT\n"
    )
    assert len(session.frames) == 2
    assert session.frames[0].titles == {"TOP": "one"}
    assert session.frames[1].titles == {}
    assert session.frames[1].items[0].symbol == "square"


def test_log_scale():
    session = run("SET SCALE Y LOG\n" + SIMPLE)
    assert session.frame.ylog is True
    assert session.frame.xlog is False


def test_unknown_command_reports_the_word():
    with pytest.raises(UnknownCommand):
        Session().execute("FLURB 1 2")


def test_drawing_without_data_is_an_error():
    with pytest.raises(DataError):
        Session().execute("PLOT")


def test_script_round_trips():
    session = run(SIMPLE)
    again = Session()
    again.run(session.script())
    assert again.frame.to_dict() == session.frame.to_dict()


LEGACY = "SET ORDER X Y\n1 2\n2 4\nZONE 2 2\nSET TICKS SIZE 0.1\nPLOT\n"


def test_lenient_run_skips_what_it_cannot_do():
    """A legacy file still plots; the omissions stay visible in the log."""
    session = Session()
    session.run(LEGACY, lenient=True)
    assert len(session.skipped) == 2
    assert "unknown command 'ZONE'" in session.skipped[0]
    assert "unknown SET property 'TICKS'" in session.skipped[1]
    assert session.script().count("! tdx skipped") == 2
    assert len(session.frame.items) == 1


def test_strict_run_stops():
    with pytest.raises(UnknownCommand):
        Session().run(LEGACY)


def test_a_skipped_script_still_round_trips():
    session = Session()
    session.run(LEGACY, lenient=True)
    again = Session()
    again.run(session.script())
    assert again.frame.to_dict() == session.frame.to_dict()


def test_read_file(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("x,y\n1,2\n2,4\n")
    session = run(f"SET ORDER X Y\nREAD '{path}'\nPLOT\n")
    assert session.frame.items[0].y == [2.0, 4.0]


def test_histogram_uses_bin_edges():
    frame = run("SET ORDER X Y\n1 5\n2 7\n3 3\nHISTOGRAM\n").frame
    poly = frame.items[0]
    assert poly.x[0] == pytest.approx(0.5)
    assert poly.x[-1] == pytest.approx(3.5)
    assert poly.y[:2] == [5.0, 5.0]
