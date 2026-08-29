"""Curve fitting and splines — the maths, with no knowledge of the language.

numpy does the polynomial fits and the spline, so those always work: numpy
arrives with matplotlib anyway.  The non-linear fits (gaussian, exponential)
use ``scipy.optimize.curve_fit`` when scipy is installed and fall back to a
log-linearised estimate when it is not.

That fallback is a real fit, not a stub: taking the logarithm turns both models
into polynomials, which numpy can solve exactly.  It is also not the same fit —
it minimises residuals in log space, so it weights small values more heavily
than a proper least-squares fit does.  Every result says which method produced
it, and the command warns when the fallback was used.

Errors on the parameters come from the covariance matrix.  When the data has a
DY column the fit is weighted by 1/σ and χ²/ndf is meaningful; without it the
fit is unweighted and χ² is reported against unit errors, which is only useful
as a relative number.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Sequence

import numpy as np

MODELS = ("LINE", "POLY", "GAUSSIAN", "EXPONENTIAL")


@dataclass
class FitResult:
    """What a fit produced: the curve, its parameters, and how good it is."""

    model: str
    #: (name, value, error) for each parameter, in a sensible reading order.
    parameters: list[tuple[str, float, float]]
    function: Callable[[np.ndarray], np.ndarray] = field(repr=False)
    chi2: float | None = None
    ndf: int = 0
    weighted: bool = False
    method: str = "least squares"
    note: str | None = None

    @property
    def chi2_per_ndf(self) -> float | None:
        if self.chi2 is None or self.ndf <= 0:
            return None
        return self.chi2 / self.ndf

    def summary(self) -> list[str]:
        """Human-readable lines, the way the REPL should print them."""
        lines = [f"fit: {self.model.lower()} ({self.method})"]
        for name, value, error in self.parameters:
            if error and math.isfinite(error):
                lines.append(f"    {name:<12} {value:12.6g} ± {error:.3g}")
            else:
                lines.append(f"    {name:<12} {value:12.6g}")
        if self.chi2 is not None and self.ndf > 0:
            what = "chi2/ndf" if self.weighted else "chi2/ndf (unweighted)"
            lines.append(f"    {what:<12} {self.chi2:.4g} / {self.ndf} = {self.chi2_per_ndf:.4g}")
        if self.note:
            lines.append(f"    note: {self.note}")
        return lines


class FitError(Exception):
    """The fit could not be done — too few points, bad data, no convergence."""


def _arrays(
    x: Sequence[float], y: Sequence[float], dy: Sequence[float] | None
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    xs = np.asarray(x, dtype=float)
    ys = np.asarray(y, dtype=float)
    if xs.size != ys.size:
        raise FitError("x and y have different lengths")
    if dy is None:
        return xs, ys, None
    sigma = np.asarray(dy, dtype=float)
    if np.any(sigma <= 0):
        raise FitError("a DY value is zero or negative; cannot weight the fit")
    return xs, ys, sigma


def _chi2(ys: np.ndarray, model: np.ndarray, sigma: np.ndarray | None) -> float:
    residual = ys - model
    if sigma is None:
        return float(np.sum(residual**2))
    return float(np.sum((residual / sigma) ** 2))


# -- polynomials --------------------------------------------------------
def polynomial(
    x: Sequence[float],
    y: Sequence[float],
    degree: int,
    dy: Sequence[float] | None = None,
) -> FitResult:
    """Weighted least-squares polynomial fit, lowest order first."""
    xs, ys, sigma = _arrays(x, y, dy)
    if xs.size <= degree:
        raise FitError(f"a degree-{degree} fit needs more than {degree} points")

    weights = None if sigma is None else 1.0 / sigma
    coefficients, covariance = np.polyfit(xs, ys, degree, w=weights, cov="unscaled" if sigma is not None else True)
    errors = np.sqrt(np.diag(covariance))

    # numpy gives highest order first; physicists read c0 + c1 x + ...
    coefficients = coefficients[::-1]
    errors = errors[::-1]

    if degree == 1:
        names = ["intercept", "slope"]
    else:
        names = [f"c{i}" for i in range(degree + 1)]

    def function(values: np.ndarray) -> np.ndarray:
        return np.polyval(coefficients[::-1], values)

    return FitResult(
        model="LINE" if degree == 1 else f"POLY {degree}",
        parameters=[(n, float(c), float(e)) for n, c, e in zip(names, coefficients, errors)],
        function=function,
        chi2=_chi2(ys, function(xs), sigma),
        ndf=int(xs.size - (degree + 1)),
        weighted=sigma is not None,
    )


# -- gaussian and exponential ------------------------------------------
def _gaussian(values, amplitude, mean, sigma):
    return amplitude * np.exp(-0.5 * ((values - mean) / sigma) ** 2)


def _exponential(values, amplitude, rate):
    return amplitude * np.exp(rate * values)


def _log_linear_guess(model: str, xs: np.ndarray, ys: np.ndarray) -> list[float]:
    """Start values from a fit to log(y), which is exact for these two models."""
    positive = ys > 0
    if positive.sum() < 3:
        raise FitError(f"a {model.lower()} fit needs at least three positive Y values")
    lx, ly = xs[positive], np.log(ys[positive])
    if model == "EXPONENTIAL":
        rate, log_amplitude = np.polyfit(lx, ly, 1)
        return [float(np.exp(log_amplitude)), float(rate)]
    a, b, c = np.polyfit(lx, ly, 2)  # log y = a x^2 + b x + c
    if a >= 0:
        raise FitError("these points do not look like a peak; a gaussian will not fit")
    sigma = float(np.sqrt(-1.0 / (2.0 * a)))
    mean = float(-b / (2.0 * a))
    amplitude = float(np.exp(c - b**2 / (4.0 * a)))
    return [amplitude, mean, sigma]


def nonlinear(
    model: str,
    x: Sequence[float],
    y: Sequence[float],
    dy: Sequence[float] | None = None,
) -> FitResult:
    """Fit a gaussian or an exponential."""
    xs, ys, sigma = _arrays(x, y, dy)
    names = ["amplitude", "mean", "sigma"] if model == "GAUSSIAN" else ["amplitude", "rate"]
    shape = _gaussian if model == "GAUSSIAN" else _exponential
    if xs.size <= len(names):
        raise FitError(f"a {model.lower()} fit needs more than {len(names)} points")

    guess = _log_linear_guess(model, xs, ys)

    try:
        from scipy.optimize import curve_fit
    except ImportError:
        values = guess
        errors = [float("nan")] * len(values)
        method = "log-linearised"
        note = (
            "scipy is not installed, so this is a fit to log(y): it weights small "
            "values more heavily than least squares. pip install scipy for the "
            "proper fit and parameter errors."
        )
    else:
        try:
            values, covariance = curve_fit(
                shape,
                xs,
                ys,
                p0=guess,
                sigma=sigma,
                absolute_sigma=sigma is not None,
                maxfev=10000,
            )
        except (RuntimeError, ValueError) as exc:
            raise FitError(f"the {model.lower()} fit did not converge: {exc}") from None
        errors = list(np.sqrt(np.diag(covariance)))
        method = "least squares"
        note = None

    def function(points: np.ndarray) -> np.ndarray:
        return shape(points, *values)

    return FitResult(
        model=model,
        parameters=[(n, float(v), float(e)) for n, v, e in zip(names, values, errors)],
        function=function,
        chi2=_chi2(ys, function(xs), sigma),
        ndf=int(xs.size - len(names)),
        weighted=sigma is not None,
        method=method,
        note=note,
    )


def fit(
    model: str,
    x: Sequence[float],
    y: Sequence[float],
    dy: Sequence[float] | None = None,
    degree: int = 1,
) -> FitResult:
    """Fit *model* to the data.  ``model`` is one of :data:`MODELS`."""
    model = model.upper()
    if model == "LINE":
        return polynomial(x, y, 1, dy)
    if model == "POLY":
        return polynomial(x, y, degree, dy)
    if model in ("GAUSSIAN", "EXPONENTIAL"):
        return nonlinear(model, x, y, dy)
    raise FitError(f"unknown fit model {model!r}")


# -- spline -------------------------------------------------------------
def natural_cubic_spline(x: Sequence[float], y: Sequence[float]) -> Callable[[np.ndarray], np.ndarray]:
    """A natural cubic spline through the points, in pure numpy.

    "Natural" means zero curvature at the ends.  The spline passes through
    every point exactly, which is what ``SPLINE`` promises — it draws a smooth
    curve *through* the data, unlike ``FIT``, which draws the best curve *near*
    it.
    """
    xs = np.asarray(x, dtype=float)
    ys = np.asarray(y, dtype=float)
    order = np.argsort(xs)
    xs, ys = xs[order], ys[order]
    if xs.size < 3:
        raise FitError("a spline needs at least three points")
    if np.any(np.diff(xs) <= 0):
        raise FitError("two points share an X value; a spline needs distinct X")

    n = xs.size
    h = np.diff(xs)
    # Solve for the second derivatives (the classic tridiagonal system).
    matrix = np.zeros((n, n))
    rhs = np.zeros(n)
    matrix[0, 0] = matrix[-1, -1] = 1.0  # natural boundary: zero curvature
    for i in range(1, n - 1):
        matrix[i, i - 1] = h[i - 1]
        matrix[i, i] = 2.0 * (h[i - 1] + h[i])
        matrix[i, i + 1] = h[i]
        rhs[i] = 6.0 * ((ys[i + 1] - ys[i]) / h[i] - (ys[i] - ys[i - 1]) / h[i - 1])
    second = np.linalg.solve(matrix, rhs)

    def function(points: np.ndarray) -> np.ndarray:
        values = np.asarray(points, dtype=float)
        index = np.clip(np.searchsorted(xs, values) - 1, 0, n - 2)
        dx = values - xs[index]
        step = h[index]
        a = (xs[index + 1] - values) / step
        b = dx / step
        return (
            a * ys[index]
            + b * ys[index + 1]
            + ((a**3 - a) * second[index] + (b**3 - b) * second[index + 1]) * (step**2) / 6.0
        )

    return function


def curve_points(
    function: Callable[[np.ndarray], np.ndarray],
    lo: float,
    hi: float,
    count: int = 200,
) -> tuple[list[float], list[float]]:
    """Evaluate a fitted function across a range, ready for the display list."""
    xs = np.linspace(lo, hi, max(int(count), 2))
    ys = function(xs)
    return [float(v) for v in xs], [float(v) for v in ys]
