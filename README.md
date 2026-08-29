# tdx

A plotting program with TopDrawer's grammar and a modern engine underneath.

TopDrawer (SLAC, late 1970s) was a pleasure to use: you typed a verb, some
numbers and another verb, and you had a figure. tdx keeps that, drops the parts
that only existed because of card readers and pen plotters, and renders through
matplotlib.

```
SET ORDER X Y DY
 2.0   1.1   0.4
 4.0   3.6   0.5
 6.0   6.2   0.6
PLOT
JOIN DASHES
TITLE LEFT 'σ  (μb)'
TITLE BOTTOM '$p_{K^-}$  (GeV/c)'
```

## Install

```sh
pip install -e ".[repl]"     # -e for now; [repl] adds line editing and a live window
```

Python ≥ 3.10, matplotlib ≥ 3.7. `prompt_toolkit` is optional.

## Use

```sh
tdx                          # interactive session
tdx figure.tdx               # run the file, then stay interactive
tdx figure.tdx -o fig.pdf    # batch: run it and write the figure
tdx --check old/*.top        # what would these legacy files need?
```

The output format comes from the file name — `.pdf`, `.png`, `.svg`. There is
no `SET DEVICE` to get wrong. Several frames going to a PDF become one
multi-page file; to PNG they become `fig-1.png`, `fig-2.png`.

From Python:

```python
import tdx

s = tdx.Session()
s.run(open("figure.tdx").read())
fig = tdx.figure(s.frame)        # a real matplotlib Figure, yours to adjust
tdx.save(s.frames, "out.pdf")
```

## The design rule

> Anything in TopDrawer that exists to serve the **user** is reproduced.
> Anything that exists to serve a 1978 card reader, a pen plotter or a 6-bit
> character set is accepted for compatibility but is never the recommended way.

Kept, because it is the reason to do this at all:

- verb-then-qualifier word order, no punctuation, no parentheses;
- unique-prefix abbreviation — `HIST`, `JOI`, `SET LIM`;
- stateful `SET`, then data, then a drawing verb; `NEW FRAME` as the page break;
- a plot file that is plain text and readable by a colleague.

Accepted but superseded:

| legacy | modern |
| --- | --- |
| `CASE` lines | read and converted; write Unicode (`σ`, `Ξ`) or `$maths$` directly |
| `SET SYMBOL 5O` | read; or `SET SYMBOL SQUARE` |
| `SET FONT DUPLEX` | read as "serif"; or `SET FONT Helvetica` |
| `SET DEVICE POSTSCRIPT` | the output file name |
| `SET INTENSITY` (pen overstriking) | `SET WIDTH` |
| inline data only | `READ 'run042.csv'`, or numpy arrays via the Python API |
| uppercase, fixed columns, 80 characters | case-insensitive, free-format, UTF-8 |

### CASE lines

A legacy title and its `CASE` line are converted into ordinary modern tdx text
— Unicode with `$maths$` where a shift is needed — once, on the way in. Nothing
downstream knows the difference:

```
TITLE TOP 'K2-3P R D2-3X0C12+3'      →   K⁻p → D⁻Ξ_c⁺
CASE     ' X XL W  X XFXLXX X'
```

| case | set | tdx |
| --- | --- | --- |
| blank | Roman | the character as typed |
| `L` | Roman lower case | lower-cased |
| `G` / `F` | Greek | σ, π … / Σ, Π … |
| `X` | sub/superscript | `0` `1` `2` `3` shift controls |
| `M` `W` `K` | maths, arrows, physics | ±, ∞, →, ħ … |
| `O` | markers | via `SET SYMBOL 5O` |

Cyrillic, punctuation, typographic, theoretic, astronomical, drawing,
movement, size and position sets are recognised, warned about, and left as
typed — see `charsets.py`, which cites the manual section for each table.

## Two things that are deliberately not like the original

**The whole log is replayed after every command.** A frame keeps the commands
that built it; each new command rebuilds the display list from scratch. So
`SET LIMITS` typed *after* `PLOT` still applies, `UNDO` is one line of code, and
an interactive session *is* a script — `SAVE work.tdx` writes it out and it runs
unchanged in batch. TopDrawer could not do this: it drew onto a storage tube.

**Unknown commands degrade, they do not abort.** Running a legacy file skips
what tdx cannot do yet, records why, and plots the rest; the skipped line stays
visible in the log as a comment. `--strict` turns that off. `tdx --check`
reports which commands a pile of old files actually uses — that, not the
manual's index, is the implementation order.

## Layout

```
src/tdx/
  lexer.py       words, numbers, quoted strings; data line vs command line
  registry.py    command table + unique-prefix abbreviation
  state.py       the graphics state SET writes and verbs read
  data.py        the data buffer, SET ORDER, file reading
  text.py        Unicode / $maths$ / (CASE, milestone 2) → styled runs
  display.py     the display list: polylines, markers, error bars, frames
  session.py     the command log and its replay
  backends/      matplotlib (default) and json (test oracle)
  commands/      one small module per command
  compat.py      the --check coverage report
  repl.py, cli.py
```

The interpreter never imports matplotlib. Everything crosses into graphics
through the display list, which is why a native SVG backend can be added later
without touching a command, and why the tests compare readable JSON instead of
pixels.

Adding a command means adding one file under `commands/` and one import line:

```python
@COMMANDS.define("ARROW", min_abbrev=3, usage="ARROW <x1> <y1> <x2> <y2>")
def cmd_arrow(ctx, args):
    """Draw an arrow."""
    ...
```

## What works now

**M1** — `SET LIMITS / SCALE / ORDER / SYMBOL / PATTERN / COLOR / SIZE / WIDTH /
FILL`, `PLOT`, `JOIN`, `HISTOGRAM`, `TITLE`, `READ`, `NEW FRAME`, `CLEAR`, and
the meta commands `HELP`, `SHOW`, `LIST`, `UNDO`, `SAVE`, `EXIT`. Error bars
from `DX`/`DY` columns. Frames, log axes, automatic limits, PDF/PNG/SVG.

**M2** — `CASE` lines (Greek, sub/superscript, maths, arrows, physics), `MORE`,
`SET FONT` with the plotter names, and the legacy marker codes on `SET SYMBOL`
and `PLOT`. Symbol names: circle, square, triangle, invtriangle, diamond,
cross, diagcross, plus, star, dot, octagon, fancydiamond, fancysquare,
fancycross, fancydiagcross, none.

**M3** — axis furniture, annotations and fills:

```
SET TICKS SIZE 0.06 LONG 3 OUT        length in inches, ratio of major to minor
SET TICKS TOP OFF RIGHT OFF           ALL | X | Y | TOP | BOTTOM | LEFT | RIGHT
SET LABELS SIZE 11 PERMANENT          points; PERMANENT survives NEW FRAME
SET HATCH DIAGONAL                    none diagonal backdiagonal cross
                                      horizontal vertical dots dense
TITLE 1.0 13.6 'preliminary' SIZE 13 ANGLE 30 CENTER
TITLE FRAME 0.72 0.06 'run 42'        0-1 across the frame
BOX 2 1 4 3 FILL                      a rectangle
BOX                                   one per data point from DX/DY —
                                      systematic error boxes
ARROW 1 8 3 6.5 NOHEAD                an arrow
ARROW DOWN LENGTH 1.4                 one from each data point — upper limits
HISTOGRAM FILL                        filled or hatched to the baseline
```

`examples/annotate.tdx` uses all of it. `SIZE=0.06` also works: `=` is treated
as a separator, so `SET TICKS SIZE=0.06` from an old file parses.

The per-data-point forms of `BOX` and `ARROW` are the point of those commands:
systematic error boxes and upper limits are ordinary requests in a physics
figure and tedious everywhere else.

**M4** — speed, a key, and a look you can save:

```
SET STYLE TALK                        classic paper talk poster notebook,
                                      or your own from ~/.config/tdx/styles
SAVE STYLE 'ken'                      write the current settings out as one
SET PALETTE OKABE                     a colour per dataset; SET COLOR turns it off
SET FONT SIMPLEX SIZE 16              family and base text size
PLOT
LEGEND 'K⁻ beam'                      names what was just drawn
LEGEND TOP LEFT BOX                   or AT 0.65 0.85, or OFF
```

`examples/styles.tdx` is one figure; change `TALK` to `PAPER` and it becomes a
journal figure. A style *is* a tdx script of `SET` commands — that is the whole
mechanism, which is why you can read one, write one, or save one.

Colour cycling advances once per **dataset**, not once per verb, so `PLOT`
followed by `JOIN` keeps one colour for the points and the line through them.

Four commands changed meaning in M4 to match the manual:

| | |
| --- | --- |
| `LIST` | lists the data points in the buffer (was: the command log) |
| `HISTORY` | lists the command log |
| `CLEAR` | starts a new frame keeping every setting |
| `FLUSH` | throws away the data buffer (was: `CLEAR`) |
| `STOP` | leaves, like `EXIT` and `QUIT` |

And loading got fast. Reading a file used to replay the whole log after every
line, which is quadratic: 1 000 points took 2.6 s and 10 000 took minutes.
Loading is now batched into one replay — 10 000 points in about 70 ms — with a
test to keep it that way. Interactive replay stays comfortable to ~10⁴ points
(20 ms a command) and drags near 10⁵ (~1 s); if that becomes normal, the fix is
to memoise parsed datasets, not to abandon replay.

## Next

- **M5** — `ZONE` and `SET WINDOW`: several frames on one page, and with them
  ratio panels.
- **M6** — `FIT` (line, polynomial, gaussian, exponential) and `SPLINE`. numpy
  does the polynomial work; scipy is imported lazily for the rest, so it stays
  an optional dependency.
- **M7** — `CONTOUR` and 3-D data: `SET ORDER X Y Z` with triplets or a plain
  grid file as the way in, `SET PALETTE` for colour maps, TD mesh format only
  as a legacy convenience.
- **M8** — file-watch mode, a Jupyter cell magic, numpy datasets from the
  Python API.

Not planned, by decision: control flow (`IF`, `REPEAT`, `DEFINE COMMAND`) —
Python is the better scripting language and the API is the seam; HBOOK
(`DEFINE HISTOGRAM`); `BARGRAPH`; and most of the data arithmetic, with
`DIVIDE` held back in case ratio panels want it.

## Tests

```sh
python -m pytest
TDX_UPDATE_GOLDEN=1 python -m pytest tests/test_golden.py   # after an intended change
```

Golden tests compare display lists, not images; a couple of thin tests check
that matplotlib really writes files.
