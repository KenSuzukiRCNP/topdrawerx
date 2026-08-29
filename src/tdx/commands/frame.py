"""NEW FRAME and friends.

``NEW FRAME`` closes the current picture and starts the next.  Limits and
titles reset (they describe one picture); symbol, colour, line style and data
order carry over (they describe how you like to draw).
"""

from __future__ import annotations

from ..lexer import Token
from ..registry import COMMANDS
from ..session import Context


@COMMANDS.define("NEW", min_abbrev=3, usage="NEW FRAME")
def cmd_new(ctx: Context, args: list[Token]) -> None:
    """Start a new frame."""
    for tok in args:
        if tok.is_word and not tok.upper.startswith("FRAM"):
            ctx.warn(f"NEW {tok.text.upper()}: only NEW FRAME is understood")
    ctx.new_frame()


@COMMANDS.define("CLEAR", min_abbrev=3, usage="CLEAR")
def cmd_clear(ctx: Context, args: list[Token]) -> None:
    """Forget the data accumulated so far without drawing it."""
    ctx.buffer.clear()
