import pytest

import topdrawerx  # noqa: F401  (fills the registries)
from topdrawerx.errors import AmbiguousCommand, UnknownCommand
from topdrawerx.registry import COMMANDS, SETTERS


def test_abbreviation():
    assert COMMANDS.resolve("HIST").name == "HISTOGRAM"
    assert COMMANDS.resolve("joi").name == "JOIN"
    assert SETTERS.resolve("lim").name == "LIMITS"


def test_exact_name_always_wins():
    assert COMMANDS.resolve("SET").name == "SET"


def test_too_short_is_unknown():
    with pytest.raises(UnknownCommand):
        COMMANDS.resolve("J")


def test_ambiguous_lists_candidates():
    from topdrawerx.registry import Registry

    reg = Registry("test")
    reg.define("PLOT", min_abbrev=2)(lambda ctx, args: None)
    reg.define("PLUNGE", min_abbrev=2)(lambda ctx, args: None)
    assert reg.resolve("PLO").name == "PLOT"
    with pytest.raises(AmbiguousCommand) as excinfo:
        reg.resolve("PL")
    assert "PLOT" in str(excinfo.value) and "PLUNGE" in str(excinfo.value)


def test_unknown_command():
    with pytest.raises(UnknownCommand):
        COMMANDS.resolve("FLURB")
