"""Meta commands -- they act on the session, not on the picture.

Meta commands run immediately and are never written to the frame log, so they
cannot change what a saved script draws.  That is the whole reason for the
distinction: ``SAVE work.tdx`` must not save itself.
"""

from __future__ import annotations

import os

from ..errors import ArgumentError
from ..lexer import Token
from ..registry import COMMANDS, SETTERS
from ..session import Context

SCRIPT_SUFFIXES = (".tdx", ".top", ".txt", "")
FIGURE_SUFFIXES = (".pdf", ".png", ".svg", ".eps", ".ps", ".jpg", ".jpeg", ".tif", ".tiff")


@COMMANDS.define("HELP", min_abbrev=3, usage="HELP [<command>]", meta=True)
def cmd_help(ctx: Context, args: list[Token]) -> None:
    """List the commands, or explain one of them."""
    if not args:
        ctx.say("commands: " + ", ".join(COMMANDS.names()))
        ctx.say("SET properties: " + ", ".join(SETTERS.names()))
        ctx.say("HELP <command> for details.  Commands may be abbreviated.")
        return
    word = args[0].text
    if word.upper() == "SET" and len(args) > 1:
        cmd = SETTERS.resolve(args[1].text)
    else:
        cmd = COMMANDS.resolve(word)
    ctx.say(f"{cmd.usage}")
    if cmd.summary:
        ctx.say(f"    {cmd.summary}")


@COMMANDS.define("LIST", min_abbrev=3, usage="LIST", meta=True)
def cmd_list(ctx: Context, args: list[Token]) -> None:
    """Show the commands that built the current picture."""
    session = ctx.session
    if session is None or not session.log:
        ctx.say("(nothing yet)")
        return
    for i, line in enumerate(session.log, start=1):
        ctx.say(f"{i:4d}  {line}")


@COMMANDS.define("SHOW", min_abbrev=3, usage="SHOW", meta=True)
def cmd_show(ctx: Context, args: list[Token]) -> None:
    """Show the current settings."""
    state = ctx.state
    style = state.style
    ctx.say(f"limits  X {_fmt(state.x)}   Y {_fmt(state.y)}")
    drawn = ", already drawn" if ctx.buffer.sealed else ""
    ctx.say(f"order   {' '.join(state.order)}   ({len(ctx.buffer.rows)} rows{drawn})")
    ctx.say(
        f"style   symbol={style.symbol} size={style.size:g} color={style.color} "
        f"pattern={style.dash} width={style.width:g} fill={'on' if style.fill else 'off'} "
        f"hatch={style.hatch} font={style.font}"
    )
    ticks, labels = state.ticks, state.labels
    ctx.say(
        f"ticks   size={ticks.size:g}in long={ticks.long:g} {ticks.direction} "
        f"on={_sides(ticks.on)}"
    )
    ctx.say(
        f"labels  size={labels.size:g}pt on={_sides(labels.on)}"
        if labels.size
        else f"labels  size=default on={_sides(labels.on)}"
    )
    if state.titles:
        for slot, text in state.titles.items():
            ctx.say(f"title   {slot:<6} {text!r}")


def _sides(on: dict[str, bool]) -> str:
    live = [side.lower() for side, enabled in on.items() if enabled]
    return "+".join(live) if live else "none"


def _fmt(axis) -> str:
    scale = " log" if axis.log else ""
    if axis.auto:
        return f"auto{scale}"
    return f"{axis.lo:g} .. {axis.hi:g}{scale}"


@COMMANDS.define("UNDO", min_abbrev=3, usage="UNDO", meta=True)
def cmd_undo(ctx: Context, args: list[Token]) -> None:
    """Remove the last command."""
    session = ctx.session
    if session is None:
        return
    removed = session.undo()
    ctx.say(f"undid: {removed}" if removed else "nothing to undo")


@COMMANDS.define("SAVE", min_abbrev=3, usage="SAVE '<file.pdf|.png|.svg|.tdx>'", meta=True)
def cmd_save(ctx: Context, args: list[Token]) -> None:
    """Write the figure, or the session as a runnable script.

    The file name decides which: a graphics suffix writes the picture, a
    script suffix writes the commands that made it.
    """
    session = ctx.session
    if session is None:
        raise ArgumentError("nothing to save")
    if not args:
        raise ArgumentError("SAVE needs a file name")
    path = args[0].text
    ext = os.path.splitext(path)[1].lower()
    if ext in FIGURE_SUFFIXES:
        from ..backends import matplotlib_backend as mpl

        written = mpl.save(session.frames, path)
        ctx.say("wrote " + ", ".join(written))
        return
    if ext not in SCRIPT_SUFFIXES:
        raise ArgumentError(f"don't know how to save {ext!r}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(session.script())
    ctx.say(f"wrote {path} ({len(session.log)} lines)")


@COMMANDS.define("EXIT", min_abbrev=3, usage="EXIT", meta=True)
def cmd_exit(ctx: Context, args: list[Token]) -> None:
    """Leave the program."""
    if ctx.session is not None:
        ctx.session.running = False


@COMMANDS.define("QUIT", min_abbrev=3, usage="QUIT", meta=True)
def cmd_quit(ctx: Context, args: list[Token]) -> None:
    """Leave the program."""
    cmd_exit(ctx, args)
