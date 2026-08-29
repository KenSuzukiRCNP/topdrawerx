"""The interactive front end.

The window and the prompt have to share one process, which is the fiddly part
of any REPL that draws.  Two strategies, chosen at run time:

* ``prompt_toolkit`` is installed -- the prompt runs on asyncio and a small
  background task pumps the GUI event loop, so the figure window stays alive
  (pan, zoom, resize) while you are typing;
* otherwise -- plain :func:`input`, and the window updates after each command.

Everything below is a *front end*.  It knows about the session and the
matplotlib backend and nothing else; the language does not know it exists.
"""

from __future__ import annotations

import sys

from .errors import TdxError
from .registry import COMMANDS, SETTERS
from .session import Session

BANNER = "tdx {version} -- TopDrawer-flavoured plotting.  HELP for commands, EXIT to leave."


class LiveFigure:
    """A matplotlib window that redraws the current frame after every command."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.fig = None
        self.ax = None
        if enabled:
            self._open()

    def _open(self) -> None:
        try:
            import matplotlib.pyplot as plt

            from .backends.matplotlib_backend import FIGSIZE, apply_style

            apply_style()
            plt.ion()
            self.fig = plt.figure(figsize=FIGSIZE)
            self.ax = None
            self.fig.canvas.manager.set_window_title("tdx")
            self.fig.show()
        except Exception as exc:  # no display, no GUI backend, ...
            print(f"(no plot window: {exc}; use SAVE 'fig.pdf' instead)", file=sys.stderr)
            self.enabled = False

    def update(self, session: Session) -> None:
        """Redraw the page the last frame lives on, panels and all."""
        if not self.enabled or self.fig is None:
            return
        from .backends.matplotlib_backend import draw_frame
        from .display import layout

        try:
            pages = layout(session.frames)
            self.fig.clear()
            if pages:
                page = pages[-1]
                self.fig.set_size_inches(*page.size, forward=True)
                for frame in page.frames:
                    x0, y0, x1, y1 = frame.rect
                    ax = self.fig.add_axes((x0, y0, max(x1 - x0, 1e-3), max(y1 - y0, 1e-3)))
                    draw_frame(frame, ax)
            self.fig.canvas.draw_idle()
            self.flush()
        except Exception as exc:  # pragma: no cover - GUI trouble
            print(f"(redraw failed: {exc})", file=sys.stderr)

    def flush(self) -> None:
        if not self.enabled or self.fig is None:
            return
        try:
            self.fig.canvas.flush_events()
        except Exception:  # pragma: no cover
            self.enabled = False


def _print_messages(messages: list[str]) -> None:
    for message in messages:
        print(message)


def _print_new_warnings(session: Session, shown: int) -> int:
    warnings = session.warnings
    for warning in warnings[shown:]:
        print(f"warning: {warning}", file=sys.stderr)
    return len(warnings)


def _completer():  # pragma: no cover - cosmetic
    try:
        from prompt_toolkit.completion import WordCompleter
    except ImportError:
        return None
    words = COMMANDS.names() + [f"SET {n}" for n in SETTERS.names()]
    return WordCompleter(words + [w.lower() for w in words], ignore_case=True)


def run(session: Session | None = None, show: bool = True, banner: bool = True) -> Session:
    """Run the interactive loop.  Returns the session when the user leaves."""
    from . import __version__

    session = session or Session()
    live = LiveFigure(enabled=show)
    if banner:
        print(BANNER.format(version=__version__))
    live.update(session)
    shown = len(session.warnings)

    def handle(line: str) -> None:
        nonlocal shown
        try:
            _print_messages(session.execute(line))
        except TdxError as exc:
            print(f"error: {exc}", file=sys.stderr)
        shown = _print_new_warnings(session, shown)
        live.update(session)

    if not sys.stdin.isatty():
        # Piped input: no line editing to offer, and prompt_toolkit echoes.
        _run_plain(session, handle, live, prompt="")
        return session

    try:
        import asyncio

        from prompt_toolkit import PromptSession
    except ImportError:
        _run_plain(session, handle, live)
        return session

    async def main() -> None:
        prompt = PromptSession(completer=_completer())
        pump = asyncio.ensure_future(_pump(live))
        try:
            while session.running:
                try:
                    line = await prompt.prompt_async("tdx> ")
                except EOFError:
                    break
                except KeyboardInterrupt:
                    continue
                handle(line)
        finally:
            pump.cancel()

    asyncio.run(main())
    return session


async def _pump(live: LiveFigure, interval: float = 0.05) -> None:  # pragma: no cover
    """Keep the figure window responsive while the prompt is waiting."""
    import asyncio

    while True:
        live.flush()
        await asyncio.sleep(interval)


def _run_plain(session: Session, handle, live: LiveFigure, prompt: str = "tdx> ") -> None:
    """Fallback loop: no prompt_toolkit, so the window updates between commands."""
    while session.running:
        try:
            line = input(prompt)
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            continue
        handle(line)
