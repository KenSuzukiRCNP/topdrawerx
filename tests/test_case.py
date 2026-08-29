"""Legacy CASE lines, and what they convert into."""

import pytest

from topdrawerx import Session
from topdrawerx.charsets import resolve_symbol
from topdrawerx.text import apply_case


def run(script: str) -> Session:
    session = Session()
    session.run(script)
    return session


# -- apply_case ---------------------------------------------------------
def test_greek_lower_and_upper():
    assert apply_case("S", "G") == "σ"
    assert apply_case("S", "F") == "Σ"
    assert apply_case("ABG", "GGG") == "αβγ"


def test_roman_stays_roman():
    assert apply_case("dN/dx", "") == "dN/dx"
    assert apply_case("dN/dx", "     ") == "dN/dx"


def test_lower_case_shift():
    assert apply_case("ABC", "LLL") == "abc"


def test_subscript_and_superscript():
    # P, enter subscript, T, leave subscript
    assert apply_case("P0T1", " X X") == "P$_{T}$"
    assert apply_case("X2n3", " X X") == "X$^{n}$"


def test_shift_runs_to_the_end_without_a_closing_control():
    assert apply_case("P0T", " X") == "P$_{T}$"


def test_greek_inside_a_subscript_uses_tex():
    # 'S' in Greek inside a subscript must not be a bare Unicode σ, which
    # mathtext would have to render itself.
    assert apply_case("A0S1", " XGX") == "A$_{\\sigma}$"


def test_maths_and_arrows():
    assert apply_case("+", "M") == "±"
    assert apply_case("R", "W") == "→"
    assert apply_case("H", "K") == "ħ"


def test_case_shorter_than_the_title():
    assert apply_case("SIGMA", "G") == "σIGMA"


def test_unknown_case_letter_warns_and_keeps_the_character():
    said: list[str] = []
    assert apply_case("AB", "Z ", said.append) == "AB"
    assert said and "Z" in said[0]


def test_unimplemented_set_complains_once():
    said: list[str] = []
    apply_case("ABC", "PPP", said.append)
    assert len(said) == 1


# -- the CASE command ---------------------------------------------------
def test_case_command_rewrites_the_previous_title():
    session = run("TITLE LEFT 'DS/DW'\nCASE 'LG LG'\n")
    assert session.frames[0].titles["LEFT"] == "dσ/dω"


def test_blank_case_keeps_the_character_as_typed():
    """Blank is Roman, not lower case: 'DS' + ' G' is Dσ, exactly as it was."""
    assert apply_case("DS", " G") == "Dσ"


def test_case_applies_to_the_slot_it_followed():
    session = run("TITLE TOP 'S'\nTITLE BOTTOM 'S'\nCASE 'G'\n")
    titles = session.frames[0].titles
    assert titles["TOP"] == "S"
    assert titles["BOTTOM"] == "σ"


def test_more_appends_and_case_applies_to_the_added_part_only():
    session = run("TITLE TOP 'mass of '\nMORE 'L'\nCASE 'G'\n")
    assert session.frames[0].titles["TOP"] == "mass of λ"


def test_case_without_a_title_warns():
    session = run("CASE 'GG'\n")
    assert any("no title" in w for w in session.warnings)


def test_case_survives_replay():
    session = run("TITLE LEFT 'S'\nCASE 'G'\n")
    again = Session()
    again.run(session.script())
    assert again.frames[0].titles == session.frames[0].titles


# -- legacy symbol codes ------------------------------------------------
@pytest.mark.parametrize(
    "code,name",
    [("0O", "cross"), ("1O", "diagcross"), ("3O", "square"), ("5O", "fancysquare"), ("9O", "octagon")],
)
def test_legacy_symbol_codes(code, name):
    assert resolve_symbol(code) == name


def test_set_symbol_accepts_legacy_codes_and_names():
    session = run("SET SYMBOL 5O\nSET ORDER X Y\n1 2\n2 3\nPLOT\n")
    assert session.frame.items[0].symbol == "fancysquare"
    session = run("SET SYMBOL TRI\nSET ORDER X Y\n1 2\n2 3\nPLOT\n")
    assert session.frame.items[0].symbol == "triangle"


def test_plot_takes_a_symbol_qualifier():
    session = run("SET ORDER X Y\n1 2\n2 3\nPLOT 8O\n")
    assert session.frame.items[0].symbol == "star"


# -- fonts --------------------------------------------------------------
def test_set_font_maps_plotter_names():
    assert run("SET FONT DUPLEX\n").state.style.font == "serif"
    assert run("SET FONT SIMPLEX\n").state.style.font == "sans-serif"
    assert run("SET FONT Helvetica\n").state.style.font == "Helvetica"


def test_font_reaches_the_frame():
    session = run("SET FONT SIMPLEX\nTITLE TOP 'x'\n")
    assert session.frame.font == "sans-serif"
