"""READ -- take the numbers from a file instead of pasting them in.

Inline data was the only option in 1978.  It still works, but::

    SET ORDER X Y DY
    READ 'run042.csv'
    PLOT

reads whitespace- or comma-separated columns and skips headers and comment
lines, so the plot file and the data file can live apart.
"""

from __future__ import annotations

from ..data import read_table
from ..errors import ArgumentError
from ..lexer import Token
from ..registry import COMMANDS
from ..session import Context


@COMMANDS.define("READ", min_abbrev=3, usage="READ '<file>' [X Y DY ...]")
def cmd_read(ctx: Context, args: list[Token]) -> None:
    """Fill the data buffer from a text or CSV file."""
    if not args:
        raise ArgumentError("READ needs a file name")
    path = args[0].text
    roles = [t.upper for t in args[1:] if t.is_word]
    if roles:
        ctx.buffer.set_order(tuple(roles))
        ctx.state.order = tuple(roles)
    ctx.buffer.clear()
    rows = read_table(path, len(ctx.buffer.order))
    for row in rows:
        ctx.buffer.add_row(row, ctx.lineno)
