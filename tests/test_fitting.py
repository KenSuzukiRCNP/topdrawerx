"""FIT and SPLINE — the maths, the commands, and the fallback without scipy."""

import math
import sys

import numpy as np
import pytest

from topdrawerx import Session
from topdrawerx import fitting
from topdrawerx.display import Polyline
from topdrawerx.errors import ArgumentError


def run(script: str) -> Session:
    session = Session()
    session.run(script)
    return session


LINE_DATA = "SET ORDER X Y DY\n1 2 0.1\n2 4 0.1\n3 6 0.1\n4 8 0.1\n5 10 0.1\n"


# -- the maths ----------------------------------------------------------
def test_a_straight_line_is_recovered_exactly():
    result = fitting.fit("LINE", [1, 2, 3, 4], [3, 5, 7, 9])
    intercept, slope = (value for _, value, _ in result.parameters)
    assert intercept == pytest.approx(1.0)
    assert slope == pytest.approx(2.0)
    assert result.ndf == 2


def test_polynomial_of_any_degree():
    xs = [0, 1, 2, 3, 4, 5]
    ys = [1 + 2 * x + 3 * x**2 for x in xs]
    result = fitting.fit("POLY", xs, ys, degree=2)
    values = [value for _, value, _ in result.parameters]
    assert values == pytest.approx([1, 2, 3])


def test_weights_come_from_dy():
    """The point with the small error should pull the line towards itself."""
    xs, ys = [0, 1, 2], [0.0, 5.0, 2.0]
    loose = fitting.fit("LINE", xs, ys, [1.0, 1.0, 1.0])
    tight = fitting.fit("LINE", xs, ys, [1.0, 0.01, 1.0])
    at_one = lambda r: float(r.function(np.array([1.0]))[0])  # noqa: E731
    assert abs(at_one(tight) - 5.0) < abs(at_one(loose) - 5.0)
    assert tight.weighted is True
    assert loose.weighted is True


def test_chi2_is_reported_and_scales_with_the_errors():
    xs, ys = [1, 2, 3, 4], [1.1, 1.9, 3.2, 3.9]
    small = fitting.fit("LINE", xs, ys, [0.1] * 4)
    big = fitting.fit("LINE", xs, ys, [1.0] * 4)
    assert small.chi2 > big.chi2
    assert small.ndf == 2
    assert small.chi2_per_ndf == pytest.approx(small.chi2 / 2)


def test_gaussian_recovers_its_parameters():
    xs = np.linspace(-3, 4, 40)
    ys = 7.0 * np.exp(-0.5 * ((xs - 0.5) / 1.3) ** 2)
    result = fitting.fit("GAUSSIAN", xs, ys)
    amplitude, mean, sigma = (value for _, value, _ in result.parameters)
    assert amplitude == pytest.approx(7.0, rel=1e-3)
    assert mean == pytest.approx(0.5, rel=1e-3)
    assert abs(sigma) == pytest.approx(1.3, rel=1e-3)


def test_exponential_recovers_its_parameters():
    xs = np.linspace(0, 3, 20)
    ys = 2.5 * np.exp(-1.4 * xs)
    result = fitting.fit("EXPONENTIAL", xs, ys)
    amplitude, rate = (value for _, value, _ in result.parameters)
    assert amplitude == pytest.approx(2.5, rel=1e-3)
    assert rate == pytest.approx(-1.4, rel=1e-3)


def test_the_fallback_works_when_scipy_is_missing(monkeypatch):
    """Not everyone has scipy; the log-linear fit must still be sane."""
    monkeypatch.setitem(sys.modules, "scipy", None)
    monkeypatch.setitem(sys.modules, "scipy.optimize", None)
    xs = np.linspace(-3, 4, 40)
    ys = 7.0 * np.exp(-0.5 * ((xs - 0.5) / 1.3) ** 2)
    result = fitting.fit("GAUSSIAN", xs, ys)
    amplitude, mean, sigma = (value for _, value, _ in result.parameters)
    assert amplitude == pytest.approx(7.0, rel=1e-6)
    assert mean == pytest.approx(0.5, rel=1e-6)
    assert result.method == "log-linearised"
    assert result.note and "scipy" in result.note
    assert all(math.isnan(error) for _, _, error in result.parameters)


def test_too_few_points():
    with pytest.raises(fitting.FitError):
        fitting.fit("LINE", [1], [1])


def test_gaussian_on_data_curving_the_wrong_way_is_refused():
    """log(y) curving upward cannot be a gaussian, and is caught before fitting.

    (A monotonic ramp is not refused: a very broad gaussian really is the best
    least-squares fit to one, however useless that is.)
    """
    xs = np.array([0.0, 1.0, 2.0, 3.0, 4.0])
    with pytest.raises(fitting.FitError):
        fitting.fit("GAUSSIAN", xs, np.exp(xs**2))


def test_zero_error_bars_are_refused():
    with pytest.raises(fitting.FitError):
        fitting.fit("LINE", [1, 2, 3], [1, 2, 3], [0.1, 0.0, 0.1])


# -- the spline ---------------------------------------------------------
def test_a_spline_passes_through_every_point():
    xs, ys = [0, 1, 2, 3, 4], [0, 1, 0, 1, 0]
    function = fitting.natural_cubic_spline(xs, ys)
    assert list(function(np.array(xs, dtype=float))) == pytest.approx(ys)


def test_a_spline_is_smooth_between_points():
    function = fitting.natural_cubic_spline([0, 1, 2, 3], [0, 1, 0, 1])
    dense = function(np.linspace(0, 3, 200))
    assert np.all(np.isfinite(dense))
    assert np.max(np.abs(np.diff(dense, 2))) < 0.05  # no kinks


def test_a_spline_needs_distinct_x():
    with pytest.raises(fitting.FitError):
        fitting.natural_cubic_spline([1, 1, 2], [1, 2, 3])


# -- the commands -------------------------------------------------------
def test_fit_draws_a_curve_and_reports():
    session = Session()
    messages = session.run(LINE_DATA + "PLOT\nFIT LINE\n")
    assert isinstance(session.frame.items[-1], Polyline)
    assert len(session.frame.items[-1].x) == 200
    assert any("slope" in m for m in messages)
    assert session.fits[0].model == "LINE"


def test_fit_nodraw_only_reports():
    session = Session()
    session.run(LINE_DATA + "FIT LINE NODRAW\n")
    assert session.frame.items == []
    assert session.fits


def test_fit_points_sets_the_resolution():
    session = run(LINE_DATA + "FIT LINE POINTS 20\n")
    assert len(session.frame.items[-1].x) == 20


def test_fit_range_restricts_both_the_fit_and_the_curve():
    session = run(LINE_DATA + "FIT LINE FROM 2 TO 4\n")
    curve = session.frame.items[-1]
    assert min(curve.x) == pytest.approx(2.0)
    assert max(curve.x) == pytest.approx(4.0)
    assert session.fits[0].ndf == 1  # three points, two parameters


def test_fit_poly_takes_its_degree():
    session = run("SET ORDER X Y\n0 1\n1 2\n2 5\n3 10\n4 17\nFIT POLY 2 NODRAW\n")
    assert [round(v, 6) for _, v, _ in session.fits[0].parameters] == [1, 0, 1]


def test_fit_uses_the_palette_like_any_other_verb():
    session = run("SET PALETTE OKABE\n" + LINE_DATA + "PLOT\nFIT LINE\n")
    assert session.frame.items[-1].color == session.frame.items[-2].color


def test_spline_draws_through_the_points():
    session = run("SET ORDER X Y\n0 0\n1 1\n2 0\n3 1\nPLOT\nSPLINE\n")
    curve = session.frame.items[-1]
    assert isinstance(curve, Polyline)
    assert min(curve.x) == pytest.approx(0.0)
    assert max(curve.x) == pytest.approx(3.0)


def test_fit_without_a_model_is_an_error():
    with pytest.raises(ArgumentError):
        Session().run(LINE_DATA + "FIT\n")


def test_fit_with_an_unknown_model_names_the_choices():
    with pytest.raises(ArgumentError) as excinfo:
        Session().run(LINE_DATA + "FIT PARABOLOID\n")
    assert "gaussian" in str(excinfo.value)


def test_a_stray_number_is_explained():
    with pytest.raises(ArgumentError) as excinfo:
        Session().run(LINE_DATA + "FIT LINE 3\n")
    assert "FROM" in str(excinfo.value)


def test_an_empty_range_is_an_error():
    with pytest.raises(ArgumentError):
        Session().run(LINE_DATA + "FIT LINE FROM 90 TO 99\n")


def test_fit_results_survive_replay():
    session = run(LINE_DATA + "FIT LINE\n")
    again = Session()
    again.run(session.script())
    assert again.messages == session.messages
    assert again.frame.to_dict() == session.frame.to_dict()


def test_messages_do_not_accumulate_across_replays():
    """Replay regenerates every message; the count must not grow each time."""
    session = run(LINE_DATA + "FIT LINE\n")
    before = len(session.messages)
    session.execute("SET LIMITS X 0 6")
    assert len(session.messages) == before
