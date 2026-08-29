"""LEGEND, and the renamed commands."""

import pytest

from topdrawerx import Session
from topdrawerx.errors import ArgumentError

DATA = "SET ORDER X Y\n1 2\n2 3\n"


def run(script: str) -> Session:
    session = Session()
    session.run(script)
    return session


# -- legend -------------------------------------------------------------
def test_legend_labels_the_thing_just_drawn():
    session = run(DATA + "PLOT\nLEGEND 'K beam'\n")
    assert session.frame.items[-1].label == "K beam"


def test_each_verb_can_be_named_separately():
    session = run(DATA + "PLOT\nLEGEND 'points'\nJOIN\nLEGEND 'model'\n")
    assert [i.label for i in session.frame.items] == ["points", "model"]


def test_legend_text_before_anything_is_an_error():
    with pytest.raises(ArgumentError):
        Session().execute("LEGEND 'nothing yet'")


def test_legend_placement():
    assert run("LEGEND TOP RIGHT\n").frame.legend.position == "upper right"
    assert run("LEGEND BOTTOM LEFT\n").frame.legend.position == "lower left"
    assert run("LEGEND RIGHT TOP\n").frame.legend.position == "upper right"


def test_legend_at_coordinates():
    legend = run("LEGEND AT 0.6 0.9\n").frame.legend
    assert legend.at == (0.6, 0.9)


def test_legend_off_and_box():
    assert run("LEGEND OFF\n").frame.legend.on is False
    assert run("LEGEND BOX\n").frame.legend.box is True


def test_legend_at_needs_two_numbers():
    with pytest.raises(ArgumentError):
        Session().execute("LEGEND AT 0.6")


def test_labels_survive_replay():
    session = run(DATA + "PLOT\nLEGEND 'a'\n")
    again = Session()
    again.run(session.script())
    assert again.frame.to_dict() == session.frame.to_dict()


# -- the renamed commands ----------------------------------------------
def test_list_shows_the_data():
    messages = Session().run(DATA + "LIST\n")
    assert any("1" in m for m in messages)
    assert any("X" in m and "Y" in m for m in messages)


def test_history_shows_the_log():
    session = Session()
    messages = session.run(DATA + "HISTORY\n")
    assert any("SET ORDER X Y" in m for m in messages)


def test_hist_still_abbreviates_histogram():
    session = run(DATA + "HIST\n")
    assert session.frame.items


def test_flush_drops_the_buffer():
    with pytest.raises(Exception):
        Session().run(DATA + "FLUSH\nPLOT\n")


def test_clear_keeps_the_settings():
    session = run("TITLE TOP 'kept'\nSET LIMITS X 0 5\n" + DATA + "PLOT\nCLEAR\n")
    assert len(session.frames) == 2
    assert session.state.titles["TOP"] == "kept"
    assert session.state.x.limits() == (0.0, 5.0)


def test_new_frame_still_resets():
    session = run("TITLE TOP 'gone'\nSET LIMITS X 0 5\nNEW FRAME\n")
    assert session.state.titles == {}
    assert session.state.x.limits() is None


def test_stop_leaves():
    session = Session()
    session.execute("STOP")
    assert session.running is False
