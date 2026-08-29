"""SET TICKS and SET LABELS."""

import pytest

from tdx import Session
from tdx.errors import ArgumentError


def run(script: str) -> Session:
    session = Session()
    session.run(script)
    return session


def test_tick_size_and_ratio():
    ticks = run("SET TICKS SIZE 0.08 LONG 2.5\n").state.ticks
    assert ticks.size == pytest.approx(0.08)
    assert ticks.long == pytest.approx(2.5)


def test_equals_form_from_old_files():
    """SET TICKS SIZE=0.08 — '=' is just a separator."""
    assert run("SET TICKS SIZE=0.08\n").state.ticks.size == pytest.approx(0.08)


def test_sides_off():
    ticks = run("SET TICKS TOP OFF RIGHT OFF\n").state.ticks
    assert ticks.on == {"TOP": False, "BOTTOM": True, "LEFT": True, "RIGHT": False}


def test_axis_groups():
    assert run("SET TICKS X OFF\n").state.ticks.on["BOTTOM"] is False
    assert run("SET TICKS X OFF\n").state.ticks.on["LEFT"] is True
    assert run("SET TICKS Y OFF\n").state.ticks.on["RIGHT"] is False


def test_all_off_then_one_on():
    ticks = run("SET TICKS ALL OFF\nSET TICKS BOTTOM ON\n").state.ticks
    assert ticks.on == {"TOP": False, "BOTTOM": True, "LEFT": False, "RIGHT": False}


def test_direction():
    assert run("SET TICKS OUT\n").state.ticks.direction == "out"
    assert run("SET TICKS OUT\nSET TICKS IN\n").state.ticks.direction == "in"


def test_labels_size_and_sides():
    labels = run("SET LABELS SIZE 11 RIGHT ON\n").state.labels
    assert labels.size == pytest.approx(11)
    assert labels.on["RIGHT"] is True
    assert labels.on["TOP"] is False


def test_furniture_resets_at_new_frame():
    session = run("SET TICKS SIZE 0.5\nNEW FRAME\n")
    assert session.state.ticks.size == pytest.approx(0.1)


def test_permanent_survives_new_frame():
    session = run("SET TICKS SIZE 0.5 PERMANENT\nNEW FRAME\n")
    assert session.state.ticks.size == pytest.approx(0.5)


def test_settings_reach_the_frame():
    frame = run("SET TICKS OUT ALL OFF\nSET LABELS SIZE 9\nTITLE TOP 'x'\n").frame
    assert frame.ticks.direction == "out"
    assert frame.ticks.on["BOTTOM"] is False
    assert frame.labels.size == pytest.approx(9)


def test_bad_qualifier_is_an_error():
    with pytest.raises(ArgumentError):
        Session().execute("SET TICKS SIDEWAYS")


def test_size_without_a_number_is_an_error():
    with pytest.raises(ArgumentError):
        Session().execute("SET TICKS SIZE")
