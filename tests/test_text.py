from topdrawerx.text import parse, to_matplotlib


def test_plain_unicode_is_one_literal_run():
    runs = parse("dσ/dΩ (μb/sr)")
    assert len(runs) == 1
    assert runs[0].math is False


def test_maths_runs_are_split_out():
    runs = parse("p$_{T}$ spectrum")
    assert [r.math for r in runs] == [False, True, False]
    assert runs[1].text == "_{T}"


def test_odd_dollar_is_literal():
    runs = parse("costs $5")
    assert len(runs) == 1 and runs[0].math is False
    assert to_matplotlib("costs $5") == r"costs \$5"


def test_escaped_dollar():
    assert to_matplotlib(r"\$5 each") == r"\$5 each"


def test_round_trip_of_maths():
    assert to_matplotlib("$\\sigma$ (mb)") == "$\\sigma$ (mb)"
