"""matplotlib backend.

The default look aims at the plain, black-on-white, ticks-inward style of a
particle-physics figure rather than at matplotlib's defaults.  It is set here
and nowhere else, so restyling the whole program is one dictionary.
"""

from __future__ import annotations

from typing import Any

from ..display import ErrorBars, Frame, Markers, Polyline
from ..text import to_matplotlib

#: TopDrawer-ish page: a little wider than tall, generous margins.
FIGSIZE = (6.4, 5.0)

RC_PARAMS: dict[str, Any] = {
    "font.family": "serif",
    "font.serif": ["STIXGeneral", "DejaVu Serif", "Times New Roman"],
    "mathtext.fontset": "stix",
    "font.size": 12,
    "axes.linewidth": 1.0,
    "axes.labelsize": 13,
    "axes.titlesize": 13,
    "axes.grid": False,
    "xtick.direction": "in",
    "ytick.direction": "in",
    "xtick.top": True,
    "ytick.right": True,
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "xtick.major.size": 6,
    "ytick.major.size": 6,
    "xtick.minor.size": 3,
    "ytick.minor.size": 3,
    "legend.frameon": False,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
}

SYMBOLS = {
    "circle": "o",
    "square": "s",
    "triangle": "^",
    "invtriangle": "v",
    "diamond": "D",
    "plus": "+",
    "star": "*",
    "dot": ".",
    "octagon": "8",
    "none": "",
    # The legacy marker set (manual §12.11).  "Fancy" shapes were the plain
    # shape with a cross through it; matplotlib has no such marker, so those
    # four are the nearest filled equivalents.
    "cross": "+",
    "diagcross": "x",
    "fancydiamond": "d",
    "fancysquare": "p",
    "fancycross": "P",
    "fancydiagcross": "X",
}

DASHES = {
    "solid": "-",
    "dashes": "--",
    "dots": ":",
    "dotdash": "-.",
}


def marker_for(symbol: str) -> str:
    return SYMBOLS.get(symbol.lower(), "o")


def dash_for(dash: str) -> str:
    return DASHES.get(dash.lower(), "-")


def apply_style() -> None:
    import matplotlib as mpl

    mpl.rcParams.update(RC_PARAMS)


def draw_frame(frame: Frame, ax) -> None:
    """Draw one :class:`~tdx.display.Frame` onto a matplotlib axes."""
    ax.clear()
    for item in frame.items:
        if isinstance(item, Polyline):
            ax.plot(
                item.x,
                item.y,
                linestyle=dash_for(item.dash),
                linewidth=item.width,
                color=item.color,
                marker="",
            )
        elif isinstance(item, Markers):
            marker = marker_for(item.symbol)
            if not marker:
                continue
            ax.plot(
                item.x,
                item.y,
                linestyle="none",
                marker=marker,
                markersize=item.size,
                color=item.color,
                markerfacecolor=item.color if item.fill else "none",
                markeredgecolor=item.color,
                markeredgewidth=1.0,
            )
        elif isinstance(item, ErrorBars):
            ax.errorbar(
                item.x,
                item.y,
                xerr=item.dx,
                yerr=item.dy,
                fmt="none",
                ecolor=item.color,
                elinewidth=item.width,
                capsize=0,
            )

    xlim, ylim = frame.resolved_limits()
    if frame.xlog:
        ax.set_xscale("log")
    if frame.ylog:
        ax.set_yscale("log")
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)

    # Ticks at 1/2/5-style intervals: 2.5 reads as a computer's choice, not a
    # physicist's.
    from matplotlib.ticker import MaxNLocator

    if not frame.xlog:
        ax.xaxis.set_major_locator(MaxNLocator(steps=[1, 2, 5, 10]))
    if not frame.ylog:
        ax.yaxis.set_major_locator(MaxNLocator(steps=[1, 2, 5, 10]))

    titles = frame.titles
    font = {"fontfamily": frame.font}
    if titles.get("TOP"):
        ax.set_title(to_matplotlib(titles["TOP"]), **font)
    if titles.get("BOTTOM"):
        ax.set_xlabel(to_matplotlib(titles["BOTTOM"]), **font)
    if titles.get("LEFT"):
        ax.set_ylabel(to_matplotlib(titles["LEFT"]), **font)
    if titles.get("RIGHT"):
        right = ax.twinx()
        right.set_ylim(*ylim)
        right.set_yticks([])
        right.set_ylabel(to_matplotlib(titles["RIGHT"]), **font)
    for label in (*ax.get_xticklabels(), *ax.get_yticklabels()):
        label.set_fontfamily(frame.font)


def make_figure(frame: Frame, figsize: tuple[float, float] = FIGSIZE):
    """Render one frame into a fresh figure."""
    apply_style()
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=figsize)
    draw_frame(frame, ax)
    fig.tight_layout()
    return fig


def save(frames: list[Frame], path: str, figsize: tuple[float, float] = FIGSIZE) -> list[str]:
    """Write *frames* to *path*.

    Multiple frames go into one multi-page PDF when the target is a PDF, and
    into ``name-1.png``, ``name-2.png`` ... otherwise.  Format comes from the
    file name -- there is no ``SET DEVICE`` to get wrong.
    """
    import os

    import matplotlib.pyplot as plt

    apply_style()
    if not frames:
        raise ValueError("nothing to save: no frames")

    root, ext = os.path.splitext(path)
    ext = ext.lower()
    written: list[str] = []

    if ext == ".pdf" and len(frames) > 1:
        from matplotlib.backends.backend_pdf import PdfPages

        with PdfPages(path) as pdf:
            for frame in frames:
                fig = make_figure(frame, figsize)
                pdf.savefig(fig)
                plt.close(fig)
        return [path]

    for i, frame in enumerate(frames, start=1):
        target = path if len(frames) == 1 else f"{root}-{i}{ext}"
        fig = make_figure(frame, figsize)
        fig.savefig(target, dpi=200)
        plt.close(fig)
        written.append(target)
    return written
