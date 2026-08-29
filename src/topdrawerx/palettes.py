"""Colour palettes for successive datasets.

Off by default: the original drew everything in one colour, and a plot for a
journal usually still should.  ``SET PALETTE OKABE`` turns cycling on, and
``SET COLOR`` turns it off again — an explicit colour always wins.

The default palette is Okabe–Ito, the standard colour-blind-safe categorical
set, because a figure that falls apart for eight per cent of readers is a bad
default whatever it looks like on your screen.
"""

from __future__ import annotations

PALETTES: dict[str, tuple[str, ...]] = {
    "none": (),
    # Okabe & Ito, "Color Universal Design" (2008).
    "okabe": (
        "#000000",  # black
        "#E69F00",  # orange
        "#56B4E9",  # sky blue
        "#009E73",  # bluish green
        "#0072B2",  # blue
        "#D55E00",  # vermillion
        "#CC79A7",  # reddish purple
        "#F0E442",  # yellow
    ),
    # Darker, higher-contrast set for projection.
    "bright": (
        "#000000",
        "#0072B2",
        "#D55E00",
        "#009E73",
        "#CC79A7",
        "#E69F00",
    ),
    # For journals that still charge for colour.
    "grays": ("#000000", "#555555", "#888888", "#bbbbbb"),
}

PALETTE_NAMES = tuple(name.upper() for name in PALETTES)


def color_at(palette: str, index: int) -> str | None:
    """The *index*-th colour of *palette*, wrapping round; None if unset."""
    colors = PALETTES.get(palette, ())
    if not colors:
        return None
    return colors[index % len(colors)]
