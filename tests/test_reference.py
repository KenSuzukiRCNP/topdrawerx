"""The generated command reference must match the registries.

This is what keeps documentation honest: add a command and forget to
regenerate, and this fails.
"""

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_reference_is_up_to_date():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "gen_reference.py"), "--check"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_every_command_documents_itself():
    """A command with no usage line would produce an empty reference row."""
    import topdrawerx  # noqa: F401
    from topdrawerx.registry import COMMANDS, SETTERS

    for registry in (COMMANDS, SETTERS):
        for name in registry.names():
            command = registry.commands[name]
            assert command.usage, f"{name} has no usage line"
            assert command.summary, f"{name} has no summary"
