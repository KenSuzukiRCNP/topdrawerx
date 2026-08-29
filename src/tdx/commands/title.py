"""TITLE, MORE and CASE.

Titles are Unicode by default::

    TITLE LEFT 'dσ/dΩ  (μb/sr)'
    TITLE BOTTOM '$p_{K^-}$  (GeV/c)'

A legacy file writes the same thing with a ``CASE`` line under the text::

    TITLE LEFT 'DS/DW'
    CASE     ' G  G'

``CASE`` modifies the string immediately before it — a ``TITLE`` or a ``MORE``
— exactly as the original required, and converts it into modern tdx text.  See
:mod:`tdx.charsets` for what each case letter means.
"""

from __future__ import annotations

from ..errors import ArgumentError
from ..lexer import Token
from ..registry import COMMANDS
from ..session import Context
from ..state import TITLE_SLOTS
from ..text import apply_case
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
    ctx.last_title = (slot, "", text)


@COMMANDS.define("MORE", min_abbrev=3, usage="MORE '<text>'")
def cmd_more(ctx: Context, args: list[Token]) -> None:
    """Add more text to the title just given."""
    text = next((tok.text for tok in args if tok.is_string), None)
    if text is None:
        raise ArgumentError("MORE needs quoted text")
    if ctx.last_title is None:
        raise ArgumentError("MORE must follow a TITLE")
    slot, _prefix, _raw = ctx.last_title
    prefix = ctx.state.titles.get(slot, "")
    ctx.state.titles[slot] = prefix + text
    ctx.last_title = (slot, prefix, text)


@COMMANDS.define("CASE", min_abbrev=4, usage="CASE '<case letters>'")
def cmd_case(ctx: Context, args: list[Token]) -> None:
    """Apply legacy per-character character sets to the title just given."""
    case = next((tok.text for tok in args if tok.is_string), None)
    if case is None:
        raise ArgumentError("CASE needs a quoted case string")
    if ctx.last_title is None:
        ctx.warn("CASE with no title before it, ignored")
        return
    slot, prefix, raw = ctx.last_title
    ctx.state.titles[slot] = prefix + apply_case(raw, case, ctx.warn)
