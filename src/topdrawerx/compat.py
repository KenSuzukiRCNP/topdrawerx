"""Legacy coverage: what would a real ``.top`` file need?

The original's command set is enormous and most of it is never used.  Rather
than working through the manual, run this over a directory of old files and
implement what actually appears::

    tdx --check ~/old_plots/*.top

The report lists every command found, how often, and whether tdx understands
it.  That is the roadmap, in frequency order.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .errors import TdxError
from .lexer import LineKind, scan_line
from .registry import COMMANDS, SETTERS


@dataclass
class Usage:
    name: str
    count: int
    supported: bool


def scan_text(text: str, counter: Counter | None = None) -> Counter:
    """Count command usages in one script."""
    counter = Counter() if counter is None else counter
    for raw in text.splitlines():
        try:
            line = scan_line(raw)
        except TdxError:
            counter["<unlexable line>"] += 1
            continue
        if line.kind is not LineKind.COMMAND or not line.tokens:
            continue
        word = line.tokens[0].text.upper()
        try:
            cmd = COMMANDS.resolve(word)
        except TdxError:
            counter[word] += 1
            continue
        if cmd.name == "SET" and len(line.tokens) > 1:
            prop = line.tokens[1].text.upper()
            try:
                setter = SETTERS.resolve(prop)
            except TdxError:
                counter[f"SET {prop}"] += 1
                continue
            counter[f"SET {setter.name}"] += 1
            continue
        counter[cmd.name] += 1
    return counter


def scan_files(paths: list[str]) -> Counter:
    counter: Counter = Counter()
    for path in paths:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            scan_text(fh.read(), counter)
    return counter


def is_supported(name: str) -> bool:
    try:
        if name.startswith("SET "):
            SETTERS.resolve(name[4:])
        else:
            COMMANDS.resolve(name)
    except TdxError:
        return False
    return True


def usages(counter: Counter) -> list[Usage]:
    return [
        Usage(name=name, count=count, supported=is_supported(name))
        for name, count in counter.most_common()
    ]


def report(paths: list[str]) -> str:
    counter = scan_files(paths)
    rows = usages(counter)
    if not rows:
        return "no commands found"
    width = max(len(r.name) for r in rows)
    total = sum(r.count for r in rows)
    missing = sum(r.count for r in rows if not r.supported)
    lines = [f"{len(paths)} file(s), {total} command(s), {missing} unsupported", ""]
    for row in rows:
        mark = "ok" if row.supported else "TODO"
        lines.append(f"  {mark:<4}  {row.name:<{width}}  {row.count:>5}")
    return "\n".join(lines)
