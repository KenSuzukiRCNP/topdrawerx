"""NEW FRAME and friends.

``NEW FRAME`` closes the current picture and starts the next.  Limits and
titles reset (they describe one picture); symbol, colour, line style and data
order carry over (they describe how you like to draw).
"""

from __future__ import annotations

from ..lexer import Token
from ..registry import COMMANDS
from ..session import Context


@COMMANDS.define("NEW", min_abbrev=3, usage="NEW FRAME | NEW PAGE")
def cmd_new(ctx: Context, args: list[Token]) -> None:
    """Start a new frame, or a new page.

    ``NEW PAGE`` starts a frame *and* breaks the page, leaving the rest of the
    zone empty — the way to end a page early.
    """
    page_break = False
    for tok in args:
        if not tok.is_word:
            continue
        word = tok.upper
        if word.startswith("PAG"):
            page_break = True
        elif not word.startswith("FRAM"):
            ctx.warn(f"NEW {word}: only NEW FRAME and NEW PAGE are understood")
    ctx.new_frame()
    ctx.frame.page_break = page_break


@COMMANDS.define("CLEAR", min_abbrev=3, usage="CLEAR")
def cmd_clear(ctx: Context, args: list[Token]) -> None:
    """Start a new frame keeping every setting, titles included.

    The manual's meaning: clear the screen, the next plot uses the same
    parameters.  ``NEW FRAME`` is the one that starts fresh.
    """
    ctx.new_frame(keep=True)


@COMMANDS.define("FLUSH", min_abbrev=3, usage="FLUSH")
def cmd_flush(ctx: Context, args: list[Token]) -> None:
    """Throw away the data accumulated so far without drawing it."""
    ctx.buffer.clear()
