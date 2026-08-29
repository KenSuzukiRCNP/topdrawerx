"""Things drawn on the frame: placed titles, boxes, arrows, fills."""

import pytest

from topdrawerx import Session
from topdrawerx.display import Arrow, Box, Polygon, Text
from topdrawerx.errors import ArgumentError

DATA = "SET ORDER X Y DX DY\n2 10 0.5 1\n4 20 0.5 2\n"


def run(script: str) -> Session:
    session = Session()
    session.run(script)
    return session


# -- placed text --------------------------------------------------------
def test_title_with_coordinates_becomes_a_text_item():
    frame = run("TITLE 3.0 4.0 'preliminary'\n").frame
    item = frame.items[0]
    assert isinstance(item, Text)
    assert (item.x, item.y, item.text) == (3.0, 4.0, "preliminary")
    assert frame.titles == {}


def test_placed_text_options():
    item = run("TITLE 1 2 'x' ANGLE 30 SIZE 14 CENTER\n").frame.items[0]
    assert item.angle == pytest.approx(30)
    assert item.size == pytest.approx(14)
    assert item.align == "center"


def test_frame_coordinates_do_not_affect_limits():
    frame = run("SET ORDER X Y\n1 1\n2 2\nPLOT\nTITLE FRAME 0.9 0.9 'note'\n").frame
    (xlo, xhi), _ = frame.resolved_limits()
    assert xhi < 3.0


def test_case_applies_to_placed_text_too():
    item = run("TITLE 1 2 'S'\nCASE 'G'\n").frame.items[0]
    assert item.text == "σ"


def test_side_titles_still_work():
    assert run("TITLE LEFT 'y axis'\n").frame.titles == {"LEFT": "y axis"}


# -- boxes --------------------------------------------------------------
def test_box_from_coordinates():
    box = run("BOX 2 1 4 3\n").frame.items[0]
    assert isinstance(box, Box)
    assert (box.x0, box.y0, box.x1, box.y1) == (2.0, 1.0, 4.0, 3.0)


def test_box_normalises_corner_order():
    box = run("BOX 4 3 2 1\n").frame.items[0]
    assert (box.x0, box.y0, box.x1, box.y1) == (2.0, 1.0, 4.0, 3.0)


def test_box_per_data_point_uses_the_error_columns():
    frame = run(DATA + "BOX\n").frame
    assert len(frame.items) == 2
    first = frame.items[0]
    assert (first.x0, first.x1) == (1.5, 2.5)
    assert (first.y0, first.y1) == (9.0, 11.0)


def test_box_over_data_without_errors_is_an_error():
    with pytest.raises(ArgumentError):
        Session().run("SET ORDER X Y\n1 2\n2 3\nBOX\n")


def test_box_fill_and_hatch():
    box = run("SET COLOR red\nBOX 0 0 1 1 FILL\n").frame.items[0]
    assert box.facecolor == "red"
    box = run("SET HATCH CROSS\nBOX 0 0 1 1 FILL\n").frame.items[0]
    assert box.hatch == "cross"
    assert box.facecolor == "none"


# -- arrows -------------------------------------------------------------
def test_arrow_from_coordinates():
    arrow = run("ARROW 1 8 3 6.5\n").frame.items[0]
    assert isinstance(arrow, Arrow)
    assert (arrow.x0, arrow.y0, arrow.x1, arrow.y1) == (1.0, 8.0, 3.0, 6.5)


def test_arrow_per_data_point_for_upper_limits():
    frame = run(DATA + "ARROW DOWN LENGTH 3\n").frame
    assert len(frame.items) == 2
    assert frame.items[0].y0 - frame.items[0].y1 == pytest.approx(3.0)
    assert frame.items[0].x0 == frame.items[0].x1


def test_arrow_length_defaults_to_a_tenth_of_the_span():
    frame = run(DATA + "ARROW DOWN\n").frame
    assert frame.items[0].y0 - frame.items[0].y1 == pytest.approx(1.0)


def test_arrow_nohead():
    assert run("ARROW 0 0 1 1 NOHEAD\n").frame.items[0].head is False


def test_arrow_needs_four_numbers_or_a_direction():
    with pytest.raises(ArgumentError):
        Session().execute("ARROW 1 2")


# -- filled histograms --------------------------------------------------
def test_histogram_fill_closes_to_the_baseline():
    frame = run("SET ORDER X Y\n1 5\n2 7\nHISTOGRAM FILL\n").frame
    poly = frame.items[0]
    assert isinstance(poly, Polygon)
    assert poly.y[0] == 0.0 and poly.y[-1] == 0.0
    assert poly.facecolor == "black"


def test_hatch_implies_a_filled_outline():
    poly = run("SET HATCH DIAGONAL\nSET ORDER X Y\n1 5\n2 7\nHISTOGRAM\n").frame.items[0]
    assert isinstance(poly, Polygon)
    assert poly.hatch == "diagonal"
    assert poly.facecolor == "none"


def test_plain_histogram_is_still_a_polyline():
    from topdrawerx.display import Polyline

    item = run("SET ORDER X Y\n1 5\n2 7\nHISTOGRAM\n").frame.items[0]
    assert isinstance(item, Polyline)
