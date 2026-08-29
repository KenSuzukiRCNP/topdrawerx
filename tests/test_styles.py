"""Styles and colour palettes."""

import pytest

from topdrawerx import Session
from topdrawerx.errors import ArgumentError
from topdrawerx.styles import list_styles, state_to_commands


def run(script: str) -> Session:
    session = Session()
    session.run(script)
    return session


# -- built-in styles ----------------------------------------------------
def test_the_five_built_ins_are_there():
    assert {"classic", "paper", "talk", "poster", "notebook"} <= set(list_styles())


@pytest.mark.parametrize("name", ["classic", "paper", "talk", "poster", "notebook"])
def test_every_built_in_style_loads_without_warnings(name):
    session = run(f"SET STYLE {name}\n")
    assert session.warnings == []


def test_style_changes_the_look():
    session = run("SET STYLE TALK\n")
    assert session.state.style.font == "sans-serif"
    assert session.state.style.font_size == pytest.approx(16)
    assert session.state.palette == "okabe"


def test_style_survives_new_frame():
    """Styles set their axis furniture PERMANENT, so a second frame matches."""
    session = run("SET STYLE PAPER\nNEW FRAME\n")
    assert session.state.ticks.size == pytest.approx(0.05)
    assert session.state.labels.size == pytest.approx(9)


def test_unknown_style_names_the_ones_there_are():
    with pytest.raises(ArgumentError) as excinfo:
        Session().execute("SET STYLE NONSUCH")
    assert "paper" in str(excinfo.value)


def test_user_styles_shadow_built_ins(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    styles = tmp_path / "tdx" / "styles"
    styles.mkdir(parents=True)
    (styles / "paper.tdx").write_text("SET WIDTH 9\n", encoding="utf-8")
    assert run("SET STYLE PAPER\n").state.style.width == pytest.approx(9)


def test_save_style_round_trips(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    session = run("SET WIDTH 3.5\nSET SYMBOL SQUARE\nSET TICKS SIZE 0.02 OUT\n")
    session.execute("SAVE STYLE 'mine'")
    restored = run("SET STYLE MINE\n")
    assert restored.state.style.width == pytest.approx(3.5)
    assert restored.state.style.symbol == "square"
    assert restored.state.ticks.size == pytest.approx(0.02)
    assert restored.state.ticks.direction == "out"


def test_a_style_is_only_set_commands():
    session = Session()
    session.run("SET ORDER X Y\n")
    lines = state_to_commands(session.state)
    assert all(line.startswith("SET ") for line in lines)
    assert not any("ORDER" in line or "LIMITS" in line for line in lines)


# -- palettes -----------------------------------------------------------
DATA = "SET ORDER X Y\n1 2\n2 3\n"


def test_palette_advances_once_per_dataset_not_once_per_verb():
    """PLOT then JOIN is one dataset, so it keeps one colour."""
    session = run("SET PALETTE OKABE\n" + DATA + "PLOT\nJOIN\n3 1\n4 2\nPLOT\n")
    colors = [item.color for item in session.frame.items]
    assert colors[0] == colors[1] == "#000000"
    assert colors[2] == "#E69F00"


def test_no_palette_by_default():
    session = run(DATA + "PLOT\n3 1\n4 2\nPLOT\n")
    assert {item.color for item in session.frame.items} == {"black"}


def test_explicit_colour_turns_cycling_off():
    session = run("SET PALETTE OKABE\nSET COLOR red\n" + DATA + "PLOT\n")
    assert session.state.palette == "none"
    assert session.frame.items[0].color == "red"


def test_palette_restarts_each_frame():
    session = run(
        "SET PALETTE OKABE\n" + DATA + "PLOT\nNEW FRAME\nSET ORDER X Y\n1 1\n2 2\nPLOT\n"
    )
    assert session.frames[0].items[0].color == session.frames[1].items[0].color


def test_unknown_palette_is_an_error():
    with pytest.raises(ArgumentError):
        Session().execute("SET PALETTE TARTAN")
