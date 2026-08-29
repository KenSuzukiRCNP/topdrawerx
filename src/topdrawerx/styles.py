"""Styles: a look, saved as a tdx script.

``SET STYLE TALK`` finds ``talk.tdx`` and runs the ``SET`` commands in it.
That is the whole mechanism.  It means:

* a style is readable — open it and you can see every setting it changes;
* you can write one in the language you already know, with no config format
  to learn;
* ``SAVE STYLE 'ken'`` writes your current settings out as one, so a look you
  arrive at by fiddling at the prompt becomes reusable.

Styles are looked up in ``~/.config/tdx/styles`` first and in the built-in
directory second, so a style of yours shadows a built-in of the same name.
"""

from __future__ import annotations

import os
from pathlib import Path

from .errors import ArgumentError
from .lexer import LineKind, classify
from .registry import COMMANDS
from .state import SIDES, State

SUFFIX = ".tdx"
MAX_DEPTH = 4


def builtin_dir() -> Path:
    return Path(__file__).resolve().parent / "styles"


def user_dir() -> Path:
    """Where a user's own styles live (honours ``XDG_CONFIG_HOME``)."""
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(base) / "tdx" / "styles"


def search_path() -> list[Path]:
    return [user_dir(), builtin_dir()]


def find_style(name: str) -> Path:
    """Locate a style file by name, user styles first."""
    stem = name.lower()
    if stem.endswith(SUFFIX):
        stem = stem[: -len(SUFFIX)]
    for directory in search_path():
        candidate = directory / f"{stem}{SUFFIX}"
        if candidate.is_file():
            return candidate
    available = ", ".join(list_styles()) or "none found"
    raise ArgumentError(f"no style called {name!r}; available: {available}")


def list_styles() -> list[str]:
    """Every style available, user styles shadowing built-ins of the same name."""
    seen: dict[str, None] = {}
    for directory in search_path():
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob(f"*{SUFFIX}")):
            seen.setdefault(path.stem, None)
    return sorted(seen)


def apply_style(ctx, name: str) -> None:
    """Run the commands of style *name* against the current context."""
    depth = getattr(ctx, "style_depth", 0)
    if depth >= MAX_DEPTH:
        raise ArgumentError(f"styles nested too deeply at {name!r}")
    path = find_style(name)
    text = path.read_text(encoding="utf-8")
    ctx.style_depth = depth + 1
    try:
        for lineno, raw in enumerate(text.splitlines(), start=1):
            kind, tokens = classify(raw)
            if kind in (LineKind.BLANK, LineKind.COMMENT):
                continue
            if kind is LineKind.DATA:
                ctx.warn(f"{path.name} line {lineno}: data in a style file, ignored")
                continue
            cmd = COMMANDS.resolve(tokens[0].text, ctx.lineno)
            if cmd.meta or cmd.name not in ("SET",):
                ctx.warn(f"{path.name} line {lineno}: only SET belongs in a style, ignored")
                continue
            cmd.handler(ctx, list(tokens[1:]))
    finally:
        ctx.style_depth = depth


def _sides_clause(on: dict[str, bool]) -> str:
    if all(on[side] for side in SIDES):
        return "ALL ON"
    if not any(on[side] for side in SIDES):
        return "ALL OFF"
    live = " ".join(side for side in SIDES if on[side])
    return f"ALL OFF {live} ON"


def state_to_commands(state: State) -> list[str]:
    """The current look, written out as the SET commands that would restore it.

    Deliberately excludes anything about the data — limits, column order — so
    that what comes out is a style and not a snapshot of one plot.
    """
    style = state.style
    lines = [
        f"SET FONT {style.font}"
        + (f" SIZE {style.font_size:g}" if style.font_size else ""),
        f"SET COLOR {style.color}",
        f"SET WIDTH {style.width:g}",
        f"SET PATTERN {style.dash}",
        f"SET SYMBOL {style.symbol}",
        f"SET SIZE {style.size:g}",
        f"SET FILL {'ON' if style.fill else 'OFF'}",
        f"SET HATCH {style.hatch}",
        f"SET PALETTE {state.palette}",
        f"SET TICKS SIZE {state.ticks.size:g} LONG {state.ticks.long:g} "
        f"{state.ticks.direction.upper()} {_sides_clause(state.ticks.on)} PERMANENT",
    ]
    label_size = f"SIZE {state.labels.size:g} " if state.labels.size else ""
    lines.append(f"SET LABELS {label_size}{_sides_clause(state.labels.on)} PERMANENT")
    return lines


def save_style(state: State, name: str) -> Path:
    """Write the current look to the user's style directory."""
    stem = name.lower()
    if stem.endswith(SUFFIX):
        stem = stem[: -len(SUFFIX)]
    directory = user_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{stem}{SUFFIX}"
    body = "\n".join(
        [f"! {stem} -- saved by tdx SAVE STYLE", ""] + state_to_commands(state) + [""]
    )
    path.write_text(body, encoding="utf-8")
    return path
