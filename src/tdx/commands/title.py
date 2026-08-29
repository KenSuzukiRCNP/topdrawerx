"""TITLE, and the CASE placeholder.

Titles are Unicode by default::

    TITLE LEFT 'dσ/dΩ  (μb/sr)'
    TITLE BOTTOM '$p_{K^-}$  (GeV/c)'

The legacy ``CASE`` line is recognised so that old files do not stop dead, but
it is not interpreted yet -- it warns and is skipped.
"""

from __future__ import annotations

from ..errors import ArgumentError
from ..lexer import Token
from ..registry import COMMANDS
from ..session import Context
from ..state import TITLE_SLOTS
from ._util import choice


@COMMANDS.define("TITLE", min_abbrev=3, usage="TITLE [TOP|BOTTOM|LEFT|RIGHT] '<text>'")
def cmd_title(ctx: Context, args: list[Token]) -> None:
    """Put a title on one side of the frame."""
    slot = "TOP"
    text: str | None = None
    for tok in args:
        if tok.is_string:
            text = tok.text
        elif tok.is_word:
            slot = choice(tok.text, TITLE_SLOTS, "title position").upper()
    if text is None:
        raise ArgumentError("TITLE needs quoted text, e.g. TITLE TOP 'Missing mass'")
    ctx.state.titles[slot] = text


@COMMANDS.define("CASE", min_abbrev=4, usage="CASE '<shifts>'")
def cmd_case(ctx: Context, args: list[Token]) -> None:
    """Legacy per-character font shifts for the preceding title (not yet applied)."""
    ctx.warn("CASE lines are not interpreted yet; write Unicode or $maths$ in the title")
