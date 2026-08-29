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

Replay costs one pass over the log.  For a typical frame that is microseconds;
it stays comfortable to about 10^4 data points (~20 ms per command) and starts
to drag near 10^5 (~1 s), because the data lives in the log as text and is
re-read each time.  Loading is batched (see :meth:`Session.run`) so reading a
file is linear, not quadratic.  If very large datasets become normal, the fix
is to memoise parsed datasets per log slice rather than to abandon replay.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .data import DataBuffer
from .display import Frame
from .errors import TdxError
from .lexer import LineKind, classify, scan_line
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
    #: The title most recently given, as ``(target, prefix, raw text)``, where
    #: the target is a frame side or a placed text item.  CASE and MORE act on
    #: it, and only on it — as in the original, where a CASE line had to sit
    #: directly under its string.
    last_title: tuple[object, str, str] | None = None

    @property
    def frame(self) -> Frame:
        return self.frames[-1]

    def warn(self, message: str) -> None:
        where = f"line {self.lineno}: " if self.lineno else ""
        self.warnings.append(f"{where}{message}")

    def say(self, message: str) -> None:
        self.messages.append(message)

    def pen(self) -> str:
        """The colour this drawing verb should use.

        With a palette on, each *dataset* takes the next colour — not each
        verb, so the ``PLOT`` then ``JOIN`` idiom keeps one colour for the
        points and the line through them.  A fresh dataset is one the buffer
        has not yet been drawn from.
        """
        from .palettes import color_at

        state = self.state
        if state.palette == "none":
            return state.style.color
        if not self.buffer.sealed:
            state.palette_index += 1
        return color_at(state.palette, max(state.palette_index, 0)) or state.style.color

    def new_frame(self, keep: bool = False) -> None:
        """Close the current frame and start the next one.

        With *keep* the settings carry over untouched — limits, titles and all
        — which is what ``CLEAR`` means; otherwise the per-frame settings go
        back to their defaults, which is what ``NEW FRAME`` means.
        """
        self.frame.apply_state(self.state)
        self.state = self.state.copy() if keep else self.state.next_frame()
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
        """Run a whole script.

        Loading is batched: the lines go into the log and the replay happens
        once, not once per line.  A file of ten thousand data points is
        otherwise ten thousand replays, which is quadratic and, at any real
        data size, unusable.  Correctness is unaffected because nothing can
        observe the picture until the batch ends -- with one exception, meta
        commands (``SAVE``, ``SHOW``, ``LIST``), which look at the current
        state and therefore close the batch before they run.

        With ``lenient=True`` a line that fails does not stop the run: it is
        replaced in the log by a comment recording why it was skipped, and the
        rest of the file still plots.  That is how legacy files are read -- a
        `.top` file will always contain something not implemented yet, and a
        picture missing one feature beats no picture at all.  The comment keeps
        the omission visible, including in whatever ``SAVE`` writes out.
        """
        messages: list[str] = []
        batch: list[tuple[int, str]] = []

        for lineno, raw in enumerate(script.splitlines(), start=1):
            meta = self._meta_command(raw)
            if meta is None:
                batch.append((lineno, raw.rstrip("\n")))
                continue
            messages.extend(self._flush_batch(batch, lenient))
            batch = []
            ctx = self._live_context()
            try:
                meta.handler(ctx, scan_line(raw).tokens[1:])
            except TdxError as exc:
                if not lenient:
                    raise
                self.skipped.append(f"line {lineno}: {exc.message}  [{raw.strip()}]")
            messages.extend(ctx.messages)

        messages.extend(self._flush_batch(batch, lenient))
        return messages

    def _meta_command(self, raw: str):
        """The meta command on this line, if it is one, else ``None``."""
        try:
            line = scan_line(raw)
        except TdxError:
            return None
        if line.kind is not LineKind.COMMAND:
            return None
        try:
            cmd = COMMANDS.resolve(line.tokens[0].text)
        except TdxError:
            return None
        return cmd if cmd.meta else None

    def _flush_batch(self, batch: list[tuple[int, str]], lenient: bool) -> list[str]:
        """Append a batch of lines to the log and replay once.

        A line that fails is identified by the replay (which reports the log
        position), dropped, and the replay retried -- so the cost is one replay
        plus one per bad line, rather than one per line.
        """
        if not batch:
            return []
        start = len(self.log)
        sources = [lineno for lineno, _ in batch]
        self.log.extend(raw for _, raw in batch)

        while True:
            try:
                self._refresh()
                return []
            except TdxError as exc:
                index = (exc.lineno or 0) - 1
                if index < start or index >= len(self.log):
                    # Not one of ours: put the log back and let it surface.
                    del self.log[start:]
                    self._refresh()
                    raise
                raw = self.log[index]
                lineno = sources[index - start]
                if not lenient:
                    del self.log[start:]
                    self._refresh()
                    exc.lineno = lineno  # report the script line, not the log slot
                    raise
                self.skipped.append(f"line {lineno}: {exc.message}  [{raw.strip()}]")
                self.log[index] = f"! tdx skipped ({exc.message}): {raw.strip()}"

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
        # The cached classifier rather than scan_line: replay runs over the
        # same lines again and again, and this is the hot loop.
        kind, tokens = classify(raw)
        ctx.lineno = lineno
        if kind in (LineKind.BLANK, LineKind.COMMENT):
            continue
        if kind is LineKind.DATA:
            ctx.buffer.add_row([t.value for t in tokens], lineno)
            continue
        cmd = COMMANDS.resolve(tokens[0].text, lineno)
        cmd.handler(ctx, list(tokens[1:]))
    ctx.frame.apply_state(ctx.state)
    return Replay(frames=ctx.frames, state=ctx.state, buffer=ctx.buffer, warnings=ctx.warnings)


def render_script(script: str) -> list[Frame]:
    """Convenience: text in, display list out."""
    session = Session()
    session.run(script)
    return session.frames
