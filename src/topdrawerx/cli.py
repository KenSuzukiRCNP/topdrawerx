"""Command line entry point.

    tdx                        interactive session
    tdx figure.tdx             run the file, then stay interactive
    tdx figure.tdx -o fig.pdf  run it and write the figure (batch)
    tdx --check old/*.top      report which commands old files need

Output format comes from the file name.  There is no SET DEVICE to get wrong.
"""

from __future__ import annotations

import argparse
import sys

from .errors import TdxError
from .session import Session


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tdx", description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="*", help="script(s) to run")
    parser.add_argument("-o", "--output", help="write the figure here and exit (.pdf/.png/.svg)")
    parser.add_argument("--check", action="store_true", help="report command coverage and exit")
    parser.add_argument("--no-window", action="store_true", help="do not open a plot window")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="stop at the first command a script gets wrong (default: skip it and carry on)",
    )
    parser.add_argument("-c", "--command", action="append", default=[], help="run a command first")
    parser.add_argument("--version", action="store_true", help="print the version and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.version:
        from . import __version__

        print(f"tdx {__version__}")
        return 0

    if args.check:
        from .compat import report

        if not args.files:
            print("--check needs at least one file", file=sys.stderr)
            return 2
        print(report(args.files))
        return 0

    session = Session()
    try:
        for path in args.files:
            with open(path, "r", encoding="utf-8") as fh:
                for message in session.run(fh.read(), lenient=not args.strict):
                    print(message)
        for command in args.command:
            for message in session.execute(command):
                print(message)
    except TdxError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for skipped in session.skipped:
        print(f"skipped: {skipped}", file=sys.stderr)
    for warning in session.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    if session.skipped:
        print(
            f"({len(session.skipped)} line(s) skipped; run tdx --check to see what a file needs)",
            file=sys.stderr,
        )

    if args.output:
        from .backends import matplotlib_backend

        try:
            written = matplotlib_backend.save(session.frames, args.output)
        except (ValueError, OSError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print("wrote " + ", ".join(written))
        return 0

    from . import repl

    repl.run(session, show=not args.no_window)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
