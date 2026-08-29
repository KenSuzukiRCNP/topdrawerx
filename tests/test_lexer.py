import pytest

from tdx.errors import LexError
from tdx.lexer import LineKind, parse_number, scan_line, tokenize


def test_data_line_is_all_numbers():
    line = scan_line("1.0  2.0  0.1")
    assert line.kind is LineKind.DATA
    assert line.numbers == [1.0, 2.0, 0.1]


def test_command_line():
    line = scan_line("set limits x 0 10")
    assert line.kind is LineKind.COMMAND
    assert line.tokens[0].upper == "SET"
    assert line.tokens[3].value == 0.0


def test_comments_and_blanks():
    assert scan_line("").kind is LineKind.BLANK
    assert scan_line("   ").kind is LineKind.BLANK
    for prefix in "!#;":
        assert scan_line(f"{prefix} a note").kind is LineKind.COMMENT


def test_quoted_strings_keep_case_and_unicode():
    tokens = tokenize("TITLE LEFT 'dσ/dΩ (μb/sr)'")
    assert tokens[-1].is_string
    assert tokens[-1].text == "dσ/dΩ (μb/sr)"


def test_doubled_quote_is_a_literal_quote():
    tokens = tokenize("TITLE TOP 'K''s'")
    assert tokens[-1].text == "K's"


def test_unterminated_string():
    with pytest.raises(LexError):
        tokenize("TITLE TOP 'oops")


def test_fortran_exponent():
    assert parse_number("1.5D+03") == 1500.0
    assert parse_number("-.5") == -0.5
    assert parse_number("2e-3") == 0.002
    assert parse_number("X") is None


def test_commas_separate():
    assert [t.value for t in tokenize("1,2,3")] == [1.0, 2.0, 3.0]
