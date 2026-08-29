"""Command registry with unique-prefix abbreviation.

Every command in tdx is a small object registered in a table, not a branch in
a parser.  Adding a command later means adding one file under ``tdx/commands``
and decorating a function -- the lexer, the session and the backends never
change.

Abbreviation is resolved here, so ``HIST``, ``JOI`` and ``SET LIM`` work the
way they did in the original.  A prefix that matches more than one command is
an error naming the candidates rather than a silent pick.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, TYPE_CHECKING

from .errors import AmbiguousCommand, UnknownCommand

if TYPE_CHECKING:  # pragma: no cover
    from .lexer import Token
    from .session import Context

Handler = Callable[["Context", list["Token"]], None]


@dataclass
class Command:
    """One verb (or one ``SET`` property)."""

    name: str
    handler: Handler
    min_abbrev: int = 3
    usage: str = ""
    summary: str = ""
    #: Meta commands act on the session itself (SAVE, UNDO, HELP...).  They run
    #: immediately and are never recorded in the frame log, so they cannot
    #: change what the picture looks like.
    meta: bool = False


@dataclass
class Registry:
    """A namespace of commands resolvable by unique prefix."""

    label: str = "command"
    commands: dict[str, Command] = field(default_factory=dict)

    def register(self, cmd: Command) -> Command:
        self.commands[cmd.name.upper()] = cmd
        return cmd

    def define(
        self,
        name: str,
        *,
        min_abbrev: int = 3,
        usage: str = "",
        summary: str = "",
        meta: bool = False,
    ) -> Callable[[Handler], Handler]:
        """Decorator form of :meth:`register`."""

        def deco(fn: Handler) -> Handler:
            doc = (fn.__doc__ or "").strip()
            first_line = doc.splitlines()[0] if doc else ""
            self.register(
                Command(
                    name=name.upper(),
                    handler=fn,
                    min_abbrev=min_abbrev,
                    usage=usage or name.upper(),
                    summary=summary or first_line,
                    meta=meta,
                )
            )
            return fn

        return deco

    def match(self, word: str) -> list[Command]:
        """Return every command *word* could abbreviate."""
        key = word.upper()
        if key in self.commands:
            return [self.commands[key]]
        return [
            cmd
            for name, cmd in self.commands.items()
            if name.startswith(key) and len(key) >= cmd.min_abbrev
        ]

    def resolve(self, word: str, lineno: int | None = None) -> Command:
        candidates = self.match(word)
        if not candidates:
            raise UnknownCommand(word, lineno, self.label)
        if len(candidates) > 1:
            raise AmbiguousCommand(word, [c.name for c in candidates], lineno, self.label)
        return candidates[0]

    def names(self) -> list[str]:
        return sorted(self.commands)


#: Top-level verbs (PLOT, JOIN, TITLE, ...).
COMMANDS = Registry("command")

#: Properties of ``SET`` (LIMITS, ORDER, SCALE, ...).
SETTERS = Registry("SET property")
