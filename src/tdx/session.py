"""The session: a command log that is replayed into pictures.

This is the heart of the design, and the one place where tdx deliberately does
*not* behave like the original.  TopDrawer drew each command straight onto a
storage tube, so a ``SET LIMITS`` typed after a ``PLOT`` came too late.  Here a
frame keeps the log of commands that built it, and every new command replays
the whole log into a fresh display list.  Consequences:

* settings apply retroactively -- type ``SET SCALE Y LOG`` at any point;
* ``UNDO`` is one line of code;
* the interactive session *is* a script: ``SAVE work.tdx`` writes it out and
  it runs unchanged in batch mode.

Replay is cheap (microseconds for a typical frame), and its cost is bounded by
the size of the log, not by the data -- data lives in the log as text and is
re-parsed, which for interactive work is nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .data import DataBuffer
from .display import Frame
from .errors import TdxError
from .lexer import Line, LineKind, scan_line
from .registry import COMMANDS
from .state import State


@dataclass
class Context:
    """What a command handler is allowed to touch."""

    state: State
    buffer: DataBuffer
    frames: list[Frame]
    session: "Session | None" = None
    warnings: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    lineno: int | None = None
    #: The title most recently given, as ``(slot, prefix, raw text)``.  CASE
    #: and MORE act on it, and only on it — as in the original, where a CASE
    #: line had to sit directly under its string.
    last_title: tuple[str, str, str] | None = None

    @property
    def frame(self) -> Frame:
        return self.frames[-1]

    def warn(self, message: str) -> None:
        where = f"line {self.lineno}: " if self.lineno else ""
        self.warnings.append(f"{where}{message}")

    def say(self, message: str) -> None:
        self.messages.append(message)

    def new_frame(self) -> None:
        """Close the current frame and start the next one."""
        self.frame.apply_state(self.state)
        self.state = self.state.next_frame()
        self.buffer.clear()
        self.last_title = None
        self.frames.append(Frame())


@dataclass
class Replay:
    frames: list[Frame]
    state: State
    buffer: DataBuffer
    warnings: list[str]


class Session:
    """A live tdx session: the log, the replay, and the resulting frames."""

    def __init__(self) -> None:
        self.log: list[str] = []
        #: Lines a lenient run could not execute (see :meth:`run`).
        self.skipped: list[str] = []
        self.running = True
        self._replay = Replay([Frame()], State(), DataBuffer(), [])
        self._refresh()

    # -- execution ------------------------------------------------------
    def execute(self, text: str) -> list[str]:
        """Run one line.  Returns messages to show the user.

        A line that fails leaves the session exactly as it was: it is popped
        from the log before the error is re-raised.
        """
        line = scan_line(text)
        if line.kind is LineKind.COMMAND:
            cmd = COMMANDS.resolve(line.tokens[0].text)
            if cmd.meta:
                ctx = self._live_context()
                cmd.handler(ctx, line.tokens[1:])
                return ctx.messages
        self.log.append(text.rstrip("\n"))
        try:
            self._refresh()
        except TdxError:
            self.log.pop()
            self._refresh()
            raise
        return []

    def run(self, script: str, lenient: bool = False) -> list[str]:
        """Run a whole script, line by line.

        With ``lenient=True`` a line that fails does not stop the run: it is
        replaced in the log by a comment recording why it was skipped, and the
        rest of the file still plots.  That is how legacy files are read -- a
        `.top` file will always contain something not implemented yet, and a
        picture missing one feature beats no picture at all.  The comment keeps
        the omission visible, including in whatever ``SAVE`` writes out.
        """
        messages: list[str] = []
        for lineno, raw in enumerate(script.splitlines(), start=1):
            try:
                messages.extend(self.execute(raw))
            except TdxError as exc:
                if not lenient:
                    raise
                self.skipped.append(f"line {lineno}: {exc.message}  [{raw.strip()}]")
                self.log.append(f"! tdx skipped ({exc.message}): {raw.strip()}")
                self._refresh()
        return messages

    def undo(self) -> str | None:
        """Remove the last recorded line.  Returns it, or ``None`` if empty."""
        while self.log:
            removed = self.log.pop()
            if removed.strip():
                self._refresh()
                return removed
        return None

    # -- state ----------------------------------------------------------
    @property
    def frames(self) -> list[Frame]:
        return self._replay.frames

    @property
    def frame(self) -> Frame:
        return self._replay.frames[-1]

    @property
    def state(self) -> State:
        return self._replay.state

    @property
    def warnings(self) -> list[str]:
        return self._replay.warnings

    def script(self) -> str:
        return "\n".join(self.log) + ("\n" if self.log else "")

    # -- internals ------------------------------------------------------
    def _live_context(self) -> Context:
        """A context over the current replay, for meta commands."""
        return Context(
            state=self._replay.state,
            buffer=self._replay.buffer,
            frames=self._replay.frames,
            session=self,
        )

    def _refresh(self) -> None:
        self._replay = replay(self.log, session=self)


def replay(lines: list[str], session: "Session | None" = None) -> Replay:
    """Execute *lines* from a clean state and return the resulting frames."""
    ctx = Context(state=State(), buffer=DataBuffer(), frames=[Frame()], session=session)
    for lineno, raw in enumerate(lines, start=1):
        line: Line = scan_line(raw, lineno)
        ctx.lineno = lineno
        if line.kind in (LineKind.BLANK, LineKind.COMMENT):
            continue
        if line.kind is LineKind.DATA:
            ctx.buffer.add_row(line.numbers, lineno)
            continue
        cmd = COMMANDS.resolve(line.tokens[0].text, lineno)
        cmd.handler(ctx, line.tokens[1:])
    ctx.frame.apply_state(ctx.state)
    return Replay(frames=ctx.frames, state=ctx.state, buffer=ctx.buffer, warnings=ctx.warnings)


def render_script(script: str) -> list[Frame]:
    """Convenience: text in, display list out."""
    session = Session()
    session.run(script)
    return session.frames
