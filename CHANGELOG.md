# Changelog

Versions follow the milestones the project was built in. Until 1.0 the command
grammar may still change; anything that does change is listed here.

## 0.6.0 — fits and splines

- `FIT LINE | POLY <n> | GAUSSIAN | EXPONENTIAL [FROM <x> TO <x>] [POINTS <n>]
  [NODRAW]` fits the data in the buffer, draws the curve and prints the
  parameters with their errors and χ²/ndf. A `DY` column makes the fit
  weighted. `FROM`/`TO` restrict both the fit and the drawn curve.
- `SPLINE [POINTS <n>]` draws a natural cubic spline *through* the points —
  a drawing aid, not a model.
- Results are also on the session as `session.fits` for the Python API, and
  anything a command prints now reaches the REPL and the CLI.
- numpy is now an explicit dependency (it always arrived with matplotlib).
  scipy is optional, in the `fit` extra: without it, gaussian and exponential
  fits fall back to a log-linearised fit, which is a real fit but weights the
  points differently — it says so, every time.
- **Fixed**: a `SET TICKS`/`SET LABELS` change made after a style had set its
  settings `PERMANENT` was itself treated as permanent, so a one-frame tweak
  silently applied to every later frame. The permanent baseline and the
  current frame's settings are now kept apart.
- **Fixed**: `docs/reference.md` no longer carries the version, so a version
  bump cannot make it stale.

## 0.5.1 — added DOI, ORCID

- DOI added in the CITATION.cff
- ORCID added in the CITATION.cff
  
## 0.5.0 — panels, and a rename

- **Renamed**: the package is now `topdrawerx` (`pip install topdrawerx`,
  `import topdrawerx`). The command you type is still `tdx`. The plain name
  `tdx` was taken on PyPI by an unrelated package.
- `ZONE <cols> <rows>` divides the page into equal cells; each `NEW FRAME`
  takes the next one, and a new page starts when the grid fills.
- `SET WINDOW X <x0> TO <x1> Y <y0> TO <y1>` places a frame exactly, in inches.
  Adjacent windows touch, which is how a ratio panel shares an axis.
- `SET PAGE <width> <height>` sets the page; `NEW PAGE` ends one early.
- `!` and `;` now start a comment part-way along a line, not only at the start.
  (`#` still only comments at the start of a line, because colours are
  written `#ff8800`.)
- Layout runs at the end of every replay, so a `ZONE` typed late rearranges the
  frames that follow it.

## 0.4.0 — speed, a key, and styles

- **Loading is no longer quadratic.** Reading a file replayed the whole log
  after every line: 1 000 points took 2.6 s and 10 000 took minutes. Loading is
  now batched into one replay — 10 000 points in about 70 ms — with a
  regression test.
- **Renamed, to match the manual**: `LIST` lists the data points in the buffer;
  `HISTORY` lists the command log; `CLEAR` starts a new frame keeping every
  setting; `FLUSH` throws away the data buffer; `STOP` joins `EXIT` and `QUIT`.
- `LEGEND '<text>'` names the thing just drawn; `LEGEND TOP RIGHT`, `LEGEND AT
  <x> <y>`, `LEGEND OFF`, `LEGEND BOX` place it. Entries carry the real symbol
  and line style.
- `SET STYLE <name>` runs a style — a script of `SET` commands. Built in:
  `classic`, `paper`, `talk`, `poster`, `notebook`. `SAVE STYLE '<name>'` writes
  the current settings to `~/.config/tdx/styles/`, which shadows the built-ins.
- `SET PALETTE OKABE|BRIGHT|GRAYS|NONE` cycles a colour per dataset (not per
  verb, so `PLOT` then `JOIN` keep one colour). `SET COLOR` turns cycling off.
- `SET FONT <family> SIZE <points>`.

## 0.3.0 — axis furniture, annotations, fills

- `SET TICKS [SIZE <inches>] [LONG <ratio>] [IN|OUT] [ALL|X|Y|TOP|...] [ON|OFF]
  [PERMANENT]` and `SET LABELS [SIZE <points>] ... [PERMANENT]`. Without
  `PERMANENT` they apply to the current frame only, as in the original.
- `TITLE <x> <y> '<text>' [SIZE n] [ANGLE n] [CENTER]` places text at data
  coordinates; `TITLE FRAME <fx> <fy> '<text>'` uses frame coordinates.
- `BOX` and `ARROW`, each in two forms: explicit coordinates, or one per data
  point — systematic error boxes from `DX`/`DY`, and upper limits from
  `ARROW DOWN`.
- `SET HATCH` and `HISTOGRAM FILL`.
- `=` is treated as a separator, so `SET TICKS SIZE=0.06` parses.

## 0.2.0 — CASE lines, fonts, legacy symbols

- `CASE` lines are converted into modern text on the way in: Greek (`G`/`F`),
  sub- and superscripts (`X`), lower case (`L`), maths (`M`), arrows (`W`),
  physics (`K`). The remaining sets are recognised, warned about once, and left
  as typed.
- `MORE` appends to the title just given, and `CASE` can follow it.
- `SET FONT` maps the plotter names (`DUPLEX`, `SIMPLEX`, ...) onto real
  families, and passes anything else through.
- The legacy marker codes (`SET SYMBOL 5O`, `PLOT 8O`) work.

## 0.1.0 — the first working milestone

- The language: a lexer that tells data lines from commands, a command registry
  with unique-prefix abbreviation, and a session that replays its whole command
  log after every command — so settings apply retroactively, `UNDO` works, and
  `SAVE '<file>.tdx'` writes a script that reproduces the figure.
- Commands: `SET LIMITS / SCALE / ORDER / SYMBOL / PATTERN / COLOR / SIZE /
  WIDTH / FILL`, `PLOT`, `JOIN`, `HISTOGRAM`, `TITLE`, `READ`, `NEW FRAME`,
  and the meta commands `HELP`, `SHOW`, `UNDO`, `SAVE`, `EXIT`.
- An interactive REPL with a live window, batch rendering to PDF/PNG/SVG, and
  `--check` to report what a directory of legacy files would need.
