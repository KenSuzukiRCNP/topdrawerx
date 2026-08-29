"""``SET`` and its properties.

``SET`` is itself just a command that dispatches into a second registry, so a
new setting is a decorated function and nothing else.  Properties resolve by
unique prefix, so ``SET LIM X 0 10`` works.
"""

from __future__ import annotations

from ..charsets import FONT_ALIASES, SYMBOL_NAMES, resolve_symbol
from ..errors import ArgumentError
from ..lexer import Token
from ..registry import COMMANDS, SETTERS
from ..session import Context
from ._util import choice, numbers, strip_noise

DASH_NAMES = ("SOLID", "DASHES", "DOTS", "DOTDASH")


def symbol_from(word: str) -> str:
    """Resolve a symbol given as a legacy code (``5O``) or by name."""
    legacy = resolve_symbol(word)
    if legacy is not None:
        return legacy
    return choice(word, SYMBOL_NAMES, "symbol")

AXES = {"X": "x", "Y": "y"}


@COMMANDS.define("SET", min_abbrev=3, usage="SET <property> <value> ...")
def cmd_set(ctx: Context, args: list[Token]) -> None:
    """Change a graphics setting."""
    if not args:
        raise ArgumentError("SET what?  Try HELP SET.")
    prop = SETTERS.resolve(args[0].text, ctx.lineno)
    prop.handler(ctx, args[1:])


# -- axes ---------------------------------------------------------------
@SETTERS.define("LIMITS", min_abbrev=3, usage="SET LIMITS X <lo> <hi> [Y <lo> <hi>]")
def set_limits(ctx: Context, args: list[Token]) -> None:
    """Fix the axis ranges (X or Y AUTO returns an axis to automatic)."""
    args = strip_noise(args)
    if not args:
        raise ArgumentError("SET LIMITS needs an axis: SET LIMITS X 0 10")
    axis_name: str | None = None
    pending: dict[str, list[float]] = {}
    auto: set[str] = set()
    for tok in args:
        if tok.is_word:
            word = tok.upper
            if word in AXES:
                axis_name = AXES[word]
                pending.setdefault(axis_name, [])
                continue
            if word in ("AUTO", "*"):
                if axis_name is None:
                    raise ArgumentError("say which axis: SET LIMITS X AUTO")
                auto.add(axis_name)
                continue
            raise ArgumentError(f"unexpected word {tok.text!r} in SET LIMITS")
        if axis_name is None:
            raise ArgumentError("say which axis first: SET LIMITS X 0 10")
        pending[axis_name].append(tok.value)

    for name, values in pending.items():
        axis = getattr(ctx.state, name)
        if name in auto:
            axis.lo = axis.hi = None
            continue
        if not values:
            continue
        if len(values) != 2:
            raise ArgumentError(
                f"SET LIMITS {name.upper()} needs two numbers, got {len(values)}"
            )
        lo, hi = values
        if lo == hi:
            raise ArgumentError(f"SET LIMITS {name.upper()}: limits must differ")
        axis.lo, axis.hi = lo, hi


@SETTERS.define("SCALE", min_abbrev=2, usage="SET SCALE [X|Y] LOG|LINEAR")
def set_scale(ctx: Context, args: list[Token]) -> None:
    """Switch an axis between linear and logarithmic."""
    args = strip_noise(args)
    axes = [AXES[t.upper] for t in args if t.is_word and t.upper in AXES]
    modes = [t.upper for t in args if t.is_word and t.upper not in AXES]
    if not modes:
        raise ArgumentError("SET SCALE needs LOG or LINEAR")
    mode = choice(modes[0], ("LOG", "LINEAR", "LIN"), "scale")
    log = mode.startswith("log")
    for name in axes or ("x", "y"):
        getattr(ctx.state, name).log = log


# -- data ---------------------------------------------------------------
@SETTERS.define("ORDER", min_abbrev=3, usage="SET ORDER X Y [DY] [DX]")
def set_order(ctx: Context, args: list[Token]) -> None:
    """Name the columns of the numbers that follow."""
    roles = [t.upper for t in args if t.is_word]
    if not roles:
        raise ArgumentError("SET ORDER needs column names, e.g. SET ORDER X Y DY")
    if "X" not in roles or "Y" not in roles:
        ctx.warn(f"SET ORDER {' '.join(roles)}: no X and Y pair, plots will fail")
    unknown = [r for r in roles if r not in ("X", "Y", "DX", "DY")]
    if unknown:
        ctx.warn(f"columns {', '.join(unknown)} are read but not used yet")
    ctx.buffer.set_order(tuple(roles))
    ctx.state.order = tuple(roles)


# -- style --------------------------------------------------------------
@SETTERS.define("SYMBOL", min_abbrev=3, usage="SET SYMBOL <name>|<legacy code, e.g. 5O>")
def set_symbol(ctx: Context, args: list[Token]) -> None:
    """Choose the plotting symbol, by name or by legacy marker code."""
    words = [t.text for t in args]
    if not words:
        raise ArgumentError(f"SET SYMBOL needs a name: {', '.join(s.lower() for s in SYMBOL_NAMES)}")
    ctx.state.style.symbol = symbol_from(words[0])


@SETTERS.define("PATTERN", min_abbrev=3, usage="SET PATTERN SOLID|DASHES|DOTS|DOTDASH")
def set_pattern(ctx: Context, args: list[Token]) -> None:
    """Choose the line style for JOIN and HISTOGRAM."""
    words = [t.text for t in args if t.is_word]
    if not words:
        raise ArgumentError("SET PATTERN needs a style: solid, dashes, dots, dotdash")
    ctx.state.style.dash = choice(words[0], DASH_NAMES, "pattern")


@SETTERS.define("COLOR", min_abbrev=3, usage="SET COLOR <name>")
def set_color(ctx: Context, args: list[Token]) -> None:
    """Set the drawing colour (any CSS/matplotlib colour name or #rrggbb)."""
    words = [t.text for t in args if t.is_word or t.is_string]
    if not words:
        raise ArgumentError("SET COLOR needs a colour name")
    ctx.state.style.color = words[0].lower()


@SETTERS.define("SIZE", min_abbrev=3, usage="SET SIZE <points>")
def set_size(ctx: Context, args: list[Token]) -> None:
    """Set the symbol size in points."""
    nums = numbers(args)
    if len(nums) != 1:
        raise ArgumentError("SET SIZE needs one number")
    ctx.state.style.size = nums[0]


@SETTERS.define("WIDTH", min_abbrev=3, usage="SET WIDTH <points>")
def set_width(ctx: Context, args: list[Token]) -> None:
    """Set the line width in points."""
    nums = numbers(args)
    if len(nums) != 1:
        raise ArgumentError("SET WIDTH needs one number")
    ctx.state.style.width = nums[0]


@SETTERS.define("FILL", min_abbrev=3, usage="SET FILL ON|OFF")
def set_fill(ctx: Context, args: list[Token]) -> None:
    """Draw filled symbols instead of open ones."""
    words = [t.upper for t in args if t.is_word]
    if not words:
        raise ArgumentError("SET FILL needs ON or OFF")
    ctx.state.style.fill = choice(words[0], ("ON", "OFF"), "fill") == "on"


# -- accepted for compatibility, deliberately inert ---------------------
def _inert(name: str, note: str):
    def handler(ctx: Context, args: list[Token]) -> None:
        value = " ".join(t.text for t in args)
        ctx.state.ignored[name] = value
        ctx.warn(f"SET {name} accepted and ignored -- {note}")

    handler.__doc__ = f"Accepted for compatibility; {note}."
    SETTERS.define(name, min_abbrev=3, usage=f"SET {name} ...", summary=handler.__doc__)(handler)


_inert("DEVICE", "the output format comes from the file name")
_inert("INTENSITY", "use SET WIDTH instead")


@SETTERS.define("FONT", min_abbrev=3, usage="SET FONT DUPLEX|SIMPLEX|<family>")
def set_font(ctx: Context, args: list[Token]) -> None:
    """Choose the font family for titles and labels.

    The plotter font names still work — DUPLEX and TRIPLEX mean serif, SIMPLEX
    and EXTENDED mean plain — and anything else is passed to matplotlib as a
    family name, so ``SET FONT Helvetica`` does what it looks like.
    """
    words = [t.text for t in args if t.is_word or t.is_string]
    if not words:
        raise ArgumentError("SET FONT needs a name, e.g. SET FONT DUPLEX")
    name = words[0]
    ctx.state.style.font = FONT_ALIASES.get(name.upper(), name)
