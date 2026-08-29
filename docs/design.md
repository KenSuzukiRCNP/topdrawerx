# Design notes

How topdrawerx is put together, and why. If you want to add a command, the last
section is the short version.

## The rule

> Anything in TopDrawer that exists to serve the **user** is reproduced.
> Anything that exists to serve a 1978 card reader, a pen plotter or a 6-bit
> character set is accepted for compatibility but is never the recommended way.

Kept, because it is the reason to do this at all:

- verb-then-qualifier word order, no punctuation, no parentheses;
- unique-prefix abbreviation — `HIST`, `JOI`, `SET LIM`;
- stateful `SET`, then data, then a drawing verb;
- a plot file that is plain text and readable by a colleague.

Accepted but superseded:

| legacy | modern |
| --- | --- |
| `CASE` lines | read and converted; write Unicode (`σ`, `Ξ`) or `$maths$` directly |
| `SET SYMBOL 5O` | read; or `SET SYMBOL SQUARE` |
| `SET FONT DUPLEX` | read as "serif"; or `SET FONT Helvetica SIZE 13` |
| `SET DEVICE POSTSCRIPT` | the output file name |
| `SET INTENSITY` (pen overstriking) | `SET WIDTH` |
| inline data only | `READ 'run042.csv'`, or numpy arrays through the Python API |
| uppercase, fixed columns, 80 characters | case-insensitive, free-format, UTF-8 |

## Three things that are deliberately not like the original

**The whole log is replayed after every command.** A frame keeps the commands
that built it; each new command rebuilds the display list from scratch. So `SET
LIMITS` typed *after* `PLOT` still applies, `UNDO` is one line of code, and an
interactive session *is* a script. TopDrawer could not do this — it drew onto a
storage tube, where a stroke was final.

Replay costs one pass over the log. That is microseconds for a typical frame,
comfortable to about 10⁴ data points (~20 ms a command), and starts to drag near
10⁵ (~1 s), because data lives in the log as text and is re-read each time.
*Loading* is batched into a single replay, so reading a file is linear —
`tests/test_session.py` has a regression guard, because the first implementation
replayed per line and took minutes on 10⁴ points. If very large datasets become
normal, the fix is to memoise parsed datasets per log slice, not to abandon
replay.

**Unknown commands degrade, they do not abort.** Running a legacy file skips
what topdrawerx cannot do yet, records why, and plots the rest; the skipped line
stays visible in the log as a comment, so nothing disappears silently.

**Placement is explicit.** Frames are positioned on a page in inches or in zone
cells, and matplotlib's automatic layout is kept out of it. That is what makes a
"page" mean something and lets two panels share an edge exactly.

## The shape

```
text → lexer → command registry → interpreter (state + data buffer)
     → display list (polylines, markers, error bars, boxes, arrows, text)
     → layout (frames onto pages)
     → backend (matplotlib | json)
```

```
src/topdrawerx/
  lexer.py       words, numbers, quoted strings; data line vs command line
  registry.py    the command table and unique-prefix abbreviation
  state.py       the graphics state SET writes and the verbs read
  data.py        the data buffer, SET ORDER, file reading
  text.py        Unicode / $maths$ / CASE → the text a backend draws
  charsets.py    the manual's character sets, each citing its section
  display.py     the display list, and the page layout pass
  session.py     the command log and its replay
  styles.py      style lookup, and writing the current settings out as one
  palettes.py    colour palettes
  backends/      matplotlib (default) and json (the test oracle)
  commands/      one small module per command
  compat.py      the --check coverage report
  repl.py, cli.py
```

Three boundaries carry most of the design:

**The interpreter never imports matplotlib.** Everything crosses into graphics
through the display list. That is why a second backend (native SVG, an
interactive canvas) could be added without touching a command, and why the tests
compare readable JSON instead of pixels.

**Commands are a registry, not a grammar.** Each is a small self-registering
object with a name, a minimum abbreviation, a usage line and a handler. Prefix
abbreviation falls out of it, the `HELP` text comes from it, and so does
`docs/reference.md`.

**`SET` dispatches into a second registry**, so a new setting is a decorated
function and nothing else.

## Testing

Golden tests compare the JSON display list rather than images: stable across
matplotlib versions, readable in a diff, and a failure tells you what changed.
A handful of thin tests check that matplotlib really writes files.

```sh
python -m pytest
TDX_UPDATE_GOLDEN=1 python -m pytest tests/test_golden.py   # after an intended change
python tools/gen_reference.py                               # after adding a command
python tools/render_examples.py                             # after changing an example
```

## Adding a command

One file under `commands/`, one line in `commands/__init__.py`:

```python
@COMMANDS.define("CIRCLE", min_abbrev=3, usage="CIRCLE <x> <y> RADIUS <r>")
def cmd_circle(ctx, args):
    """Draw a circle."""
    ...
    ctx.frame.add(...)
```

The handler gets a `Context`: the graphics `state`, the data `buffer`, the
current `frame`, `warn()` for anything the user should know, and `pen()` for the
colour this dataset should use. If it needs a shape the display list does not
have, add a primitive — deliberately, and with a `points()` method so automatic
limits keep working.

Then regenerate the reference and add tests: one for the parse, one for what
lands in the display list, and one for the error when it is used wrongly.
