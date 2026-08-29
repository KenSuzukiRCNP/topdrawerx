"""The version lives in three files; they must agree.

This is the test that would have caught the 0.6.0/0.6.1 skew before the tag was
pushed. The release workflow makes the same comparison against the git tag, but
by then the mistake has already been published as a tag and a GitHub Release —
this one fails on your machine, before any of that.
"""

import pathlib
import re

import topdrawerx

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _match(path: pathlib.Path, pattern: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    found = re.search(pattern, text, re.M)
    assert found, f"no version found in {path}"
    return found.group(1).strip()


def test_the_three_version_strings_agree():
    package = topdrawerx.__version__
    assert _match(pathlib.Path("pyproject.toml"), r'^version = "([^"]+)"') == package
    assert _match(pathlib.Path("CITATION.cff"), r"^version: (.+)$") == package


def test_the_changelog_mentions_this_version():
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## {topdrawerx.__version__}" in changelog
