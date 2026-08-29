# Contributing

This is a personal project shared in case it is useful. Issues and pull
requests are welcome; replies may be slow, and there is no support promise.

The most useful thing anyone can send is **a real TopDrawer file that does not
render correctly**, with what it should look like. Second most useful: a note
from someone who remembers how the original actually behaved, where this
reimplementation has guessed.

## Working on it

```sh
git clone <this repo> && cd topdrawerx
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest
```

If you add or change a command:

```sh
python tools/gen_reference.py     # docs/reference.md is generated; a test checks it
python tools/render_examples.py   # only if an example or the look changed
TDX_UPDATE_GOLDEN=1 python -m pytest tests/test_golden.py   # if the change is intended
```

`docs/design.md` has the architecture and a short "adding a command" section.
New commands want three tests: the parse, what lands in the display list, and
the error when it is used wrongly.

## House style

- The interpreter must not import matplotlib — graphics go through the display
  list.
- Prefer a command that reads like a sentence with no punctuation.
- When the 1978 behaviour and the 2026 user disagree, the user wins — but say so
  in a comment, and keep the legacy form working if it is cheap.
