"""matplotlib backend.

The default look aims at the plain, black-on-white, ticks-inward style of a
particle-physics figure rather than at matplotlib's defaults.  It is set here
and nowhere else, so restyling the whole program is one dictionary.
"""

from __future__ import annotations

from typing import Any

from ..display import (
    Arrow,
    Box,
    ErrorBars,
    Frame,
    Markers,
    PageLayout,
    Polygon,
    Polyline,
    Text,
    layout,
)
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

HATCHES = {
    "none": None,
    "diagonal": "//",
    "backdiagonal": "\\\\",
    "cross": "xx",
    "horizontal": "--",
    "vertical": "||",
    "dots": "..",
    "dense": "////",
}

#: Tick sizes are given in inches, as on the plotter; matplotlib wants points.
POINTS_PER_INCH = 72.0


def marker_for(symbol: str) -> str:
    return SYMBOLS.get(symbol.lower(), "o")


def dash_for(dash: str) -> str:
    return DASHES.get(dash.lower(), "-")


def apply_style() -> None:
    import matplotlib as mpl

    mpl.rcParams.update(RC_PARAMS)


def apply_axis_furniture(frame: Frame, ax) -> None:
    """Ticks and numeric labels, from ``SET TICKS`` and ``SET LABELS``."""
    ticks, labels = frame.ticks, frame.labels
    short = ticks.size * POINTS_PER_INCH
    sides = {
        "top": ticks.on.get("TOP", True),
        "bottom": ticks.on.get("BOTTOM", True),
        "left": ticks.on.get("LEFT", True),
        "right": ticks.on.get("RIGHT", True),
    }
    ax.tick_params(
        which="major",
        direction=ticks.direction,
        length=short * ticks.long,
        **sides,
    )
    ax.tick_params(which="minor", direction=ticks.direction, length=short, **sides)
    ax.tick_params(
        which="both",
        labeltop=labels.on.get("TOP", False),
        labelbottom=labels.on.get("BOTTOM", True),
        labelleft=labels.on.get("LEFT", True),
        labelright=labels.on.get("RIGHT", False),
        **({"labelsize": labels.size} if labels.size else {}),
    )


def draw_legend(frame: Frame, ax) -> None:
    """Draw the key, if anything asked to be in it.

    Entries come from the artists themselves, so a legend line always carries
    the symbol, colour and dash the data was drawn with.
    """
    legend = frame.legend
    if not legend.on:
        return
    handles, labels = ax.get_legend_handles_labels()
    if not handles:
        return
    kwargs = {
        "frameon": legend.box,
        # A bare "sans-serif" reads as a fontconfig pattern and trips on the
        # hyphen; a list is taken as a family name.
        "prop": {"family": [frame.font]},
    }
    if frame.font_size:
        kwargs["fontsize"] = frame.font_size * 0.9
    if legend.at:
        kwargs["loc"] = "upper left"
        kwargs["bbox_to_anchor"] = legend.at
    else:
        kwargs["loc"] = legend.position
    ax.legend(handles, labels, **kwargs)


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
                label=item.label,
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
                label=item.label,
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
        elif isinstance(item, Polygon):
            ax.fill(
                item.x,
                item.y,
                facecolor=item.facecolor or "none",
                edgecolor=item.color,
                linewidth=item.width,
                linestyle=dash_for(item.dash),
                hatch=HATCHES.get(item.hatch),
                label=item.label,
            )
        elif isinstance(item, Box):
            from matplotlib.patches import Rectangle

            ax.add_patch(
                Rectangle(
                    (item.x0, item.y0),
                    item.x1 - item.x0,
                    item.y1 - item.y0,
                    facecolor=item.facecolor or "none",
                    edgecolor=item.color,
                    linewidth=item.width,
                    linestyle=dash_for(item.dash),
                    hatch=HATCHES.get(item.hatch),
                )
            )
        elif isinstance(item, Arrow):
            ax.annotate(
                "",
                xy=(item.x1, item.y1),
                xytext=(item.x0, item.y0),
                arrowprops={
                    "arrowstyle": "-|>" if item.head else "-",
                    "color": item.color,
                    "linewidth": item.width,
                    "shrinkA": 0,
                    "shrinkB": 0,
                },
            )
        elif isinstance(item, Text):
            ax.text(
                item.x,
                item.y,
                to_matplotlib(item.text),
                fontsize=item.size,
                rotation=item.angle,
                color=item.color,
                ha=item.align,
                va="baseline",
                fontfamily=frame.font,
                transform=ax.transAxes if item.frame_coords else ax.transData,
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

    apply_axis_furniture(frame, ax)

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

    if frame.font_size:
        for text in (ax.title, ax.xaxis.label, ax.yaxis.label):
            text.set_fontsize(frame.font_size)
        if not frame.labels.size:
            ax.tick_params(which="both", labelsize=frame.font_size * 0.9)

    draw_legend(frame, ax)


def make_page(page: PageLayout):
    """Render one page: a figure, with an axes per frame at its rectangle.

    Positions come from the layout pass, so nothing here has to know about
    zones or windows — and matplotlib's automatic layout stays out of the way,
    which is what makes a physical page mean something.
    """
    apply_style()
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=page.size)
    for frame in page.frames:
        x0, y0, x1, y1 = frame.rect
        ax = fig.add_axes((x0, y0, max(x1 - x0, 1e-3), max(y1 - y0, 1e-3)))
        draw_frame(frame, ax)
    return fig


def make_figure(frame: Frame, figsize: tuple[float, float] | None = None):
    """Render one frame on a page of its own."""
    page = PageLayout(size=figsize or (frame.page.width, frame.page.height), frames=[frame])
    if frame.rect == (0.0, 0.0, 1.0, 1.0):
        layout([frame])
    return make_page(page)


def save(frames: list[Frame], path: str, figsize: tuple[float, float] | None = None) -> list[str]:
    """Write *frames* to *path*, laid out onto pages.

    Several pages going to a PDF become one multi-page file; to any other
    format they become ``name-1.png``, ``name-2.png`` ...  The format comes
    from the file name -- there is no ``SET DEVICE`` to get wrong.
    """
    import os

    import matplotlib.pyplot as plt

    apply_style()
    if not frames:
        raise ValueError("nothing to save: no frames")

    pages = layout(frames)
    if figsize is not None:
        for page in pages:
            page.size = figsize

    root, ext = os.path.splitext(path)
    ext = ext.lower()
    written: list[str] = []

    if ext == ".pdf" and len(pages) > 1:
        from matplotlib.backends.backend_pdf import PdfPages

        with PdfPages(path) as pdf:
            for page in pages:
                fig = make_page(page)
                pdf.savefig(fig)
                plt.close(fig)
        return [path]

    for i, page in enumerate(pages, start=1):
        target = path if len(pages) == 1 else f"{root}-{i}{ext}"
        fig = make_page(page)
        fig.savefig(target, dpi=200)
        plt.close(fig)
        written.append(target)
    return written
