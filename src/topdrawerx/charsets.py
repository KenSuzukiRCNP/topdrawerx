"""The TopDrawer character sets, transcribed from the manual.

A legacy title is two lines: the text, and a ``CASE`` line whose n-th
character says which character set the n-th character of the text comes from.

    TITLE LEFT 'DS/DT'
    CASE     ' G  '

Chapter 12 of the reference manual (§12.1 LIST_OF_FONTS) assigns one letter to
each set.  What tdx does with them:

=========  ===================  ==========================================
case       set                  tdx
=========  ===================  ==========================================
blank      Roman                the character as typed
``L``      Roman lower case     lower-cased
``G``      Greek                lower-case Greek (σ, π, ...)
``F``      Greek                upper-case Greek (Σ, Π, ...)
``M``      Math symbols         ±, ∞, ∫, ...
``W``      Arrows               ←, →, ↑, ↓, ↔
``K``      Physics symbols      ħ, λ̄
``X``      Sub/superscript      the shift controls, §12.14
``O``      Markers              (used by SET SYMBOL, not inside titles)
=========  ===================  ==========================================

The rest — Cyrillic (``B``/``C``), punctuation (``P``), typographic (``S``),
theoretic (``T``), astronomical (``A``), drawing (``D``), movement (``U``/
``V``), size (``Y``) and position (``Z``) — are recognised, warned about and
passed through unchanged. They are rare, and inventing them would be worse
than saying so.

Each entry is ``(display, tex)``: the Unicode character to print normally, and
the TeX spelling to use when the character lands inside a sub- or superscript,
where matplotlib's maths renderer is doing the work.

Source: Topdrawer Reference Manual §12.1, §12.3, §12.6, §12.8, §12.9, §12.11,
§12.14 (https://web.pa.msu.edu/reference/topdrawer-docs/).
"""

from __future__ import annotations

# -- §12.3 GREEK --------------------------------------------------------
# Case G gives the lower-case letter, case F the upper-case one.
_GREEK = {
    "A": ("alpha", "Alpha"),
    "B": ("beta", "Beta"),
    "G": ("gamma", "Gamma"),
    "D": ("delta", "Delta"),
    "E": ("epsilon", "Epsilon"),
    "Z": ("zeta", "Zeta"),
    "H": ("eta", "Eta"),
    "Q": ("theta", "Theta"),
    "I": ("iota", "Iota"),
    "K": ("kappa", "Kappa"),
    "L": ("lambda", "Lambda"),
    "M": ("mu", "Mu"),
    "N": ("nu", "Nu"),
    "X": ("xi", "Xi"),
    "O": ("omicron", "Omicron"),
    "P": ("pi", "Pi"),
    "R": ("rho", "Rho"),
    "S": ("sigma", "Sigma"),
    "T": ("tau", "Tau"),
    "U": ("upsilon", "Upsilon"),
    "F": ("phi", "Phi"),
    "C": ("chi", "Chi"),
    "Y": ("psi", "Psi"),
    "W": ("omega", "Omega"),
}

_GREEK_UNICODE_LOWER = "αβγδεζηθικλμνξοπρστυφχψω"
_GREEK_UNICODE_UPPER = "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ"
_GREEK_ORDER = "ABGDEZHQIKLMNXOPRSTUFCYW"

#: case ``G`` — lower-case Greek
GREEK_LOWER: dict[str, tuple[str, str]] = {
    key: (_GREEK_UNICODE_LOWER[i], "\\" + _GREEK[key][0])
    for i, key in enumerate(_GREEK_ORDER)
}

#: case ``F`` — upper-case Greek.  TeX has no macro for the upper-case letters
#: that coincide with Roman ones (Alpha, Beta, ...), so those keep the letter.
GREEK_UPPER: dict[str, tuple[str, str]] = {}
for _i, _key in enumerate(_GREEK_ORDER):
    _char = _GREEK_UNICODE_UPPER[_i]
    _name = _GREEK[_key][1]
    _tex = "\\" + _name if _name in (
        "Gamma", "Delta", "Theta", "Lambda", "Xi", "Pi", "Sigma", "Upsilon",
        "Phi", "Psi", "Omega",
    ) else _char
    GREEK_UPPER[_key] = (_char, _tex)

# -- §12.6 MATH_SYMBOLS (case M) ---------------------------------------
# NOTE: the manual's table lists 'M' twice (entry 5 "group multiply" and entry
# 10 "less than or equal").  Group multiply wins here; ≤ is reachable as a
# literal character.  Worth checking against a paper copy of the manual.
MATH: dict[str, tuple[str, str]] = {
    ".": ("⋅", "\\cdot"),
    "X": ("×", "\\times"),
    "/": ("÷", "\\div"),
    "P": ("Σ", "\\sum"),
    "M": ("Π", "\\prod"),
    "+": ("±", "\\pm"),
    "-": ("∓", "\\mp"),
    "L": ("<", "<"),
    "G": (">", ">"),
    "H": ("≥", "\\geq"),
    "N": ("≠", "\\neq"),
    "=": ("≡", "\\equiv"),
    "A": ("≈", "\\approx"),
    "C": ("≅", "\\cong"),
    "S": ("∼", "\\sim"),
    "R": ("∝", "\\propto"),
    "T": ("⊥", "\\perp"),
    "2": ("√", "\\sqrt{}"),
    "D": ("°", "^\\circ"),
    "I": ("∫", "\\int"),
    "J": ("∮", "\\oint"),
    "Y": ("∂", "\\partial"),
    "Z": ("∇", "\\nabla"),
    "(": ("⌊", "\\lfloor"),
    ")": ("⌋", "\\rfloor"),
    "B": ("⌈", "\\lceil"),
    "E": ("⌉", "\\rceil"),
    "0": ("∞", "\\infty"),
}

# -- §12.8 ARROWS (case W) ---------------------------------------------
ARROWS: dict[str, tuple[str, str]] = {
    "U": ("↑", "\\uparrow"),
    "D": ("↓", "\\downarrow"),
    "L": ("←", "\\leftarrow"),
    "R": ("→", "\\rightarrow"),
    "B": ("↔", "\\leftrightarrow"),
}

# -- §12.9 PHYSICS (case K) --------------------------------------------
PHYSICS: dict[str, tuple[str, str]] = {
    "H": ("ħ", "\\hbar"),
    "L": ("λ̄", "\\bar{\\lambda}"),
}

#: case letter → character set
CASE_SETS: dict[str, dict[str, tuple[str, str]]] = {
    "G": GREEK_LOWER,
    "F": GREEK_UPPER,
    "M": MATH,
    "W": ARROWS,
    "K": PHYSICS,
}

#: §12.14 sub/superscript control, selected by case ``X``
SHIFTS = {
    "0": "enter subscript",
    "1": "leave subscript",
    "2": "enter superscript",
    "3": "leave superscript",
}

#: Case letters we recognise but do not implement (see the module docstring).
UNIMPLEMENTED_CASES = {
    "B": "Cyrillic",
    "C": "Cyrillic",
    "P": "punctuation",
    "S": "typographic symbols",
    "T": "theoretic symbols",
    "A": "astronomical symbols",
    "D": "drawing symbols",
    "U": "horizontal movement",
    "V": "vertical movement",
    "Y": "character size",
    "Z": "position save/restore",
    "O": "markers",
}

# -- §12.11 MARKERS (case O) -------------------------------------------
# Legacy symbol codes: SET SYMBOL 5O is the character '5' from the marker set.
# "Fancy" symbols are the plain shape with a cross through it, which matplotlib
# has no exact match for; those four are approximations and marked as such.
MARKER_CODES: dict[str, str] = {
    "0": "cross",  # vertical cross  +
    "1": "diagcross",  # diagonal cross  ×
    "2": "diamond",
    "3": "square",
    "4": "fancydiamond",  # approximated
    "5": "fancysquare",  # approximated
    "6": "fancycross",  # approximated
    "7": "fancydiagcross",  # approximated
    "8": "star",  # star burst
    "9": "octagon",
}

#: Symbol names tdx understands, legacy shapes included.
SYMBOL_NAMES = (
    "CIRCLE",
    "SQUARE",
    "TRIANGLE",
    "INVTRIANGLE",
    "DIAMOND",
    "CROSS",
    "DIAGCROSS",
    "PLUS",
    "STAR",
    "DOT",
    "OCTAGON",
    "FANCYDIAMOND",
    "FANCYSQUARE",
    "FANCYCROSS",
    "FANCYDIAGCROSS",
    "NONE",
)


def resolve_symbol(word: str) -> str | None:
    """Resolve a symbol given as a legacy code (``5O``, ``5``) or a name.

    Returns the canonical lower-case name, or ``None`` if *word* is neither.
    Names are resolved elsewhere by unique prefix; this only handles the codes,
    so that ``SET SYMBOL 5O`` from a 1980s file still means a fancy square.
    """
    key = word.upper()
    if key.endswith("O") and key[:-1].isdigit() and len(key) == 2:
        return MARKER_CODES.get(key[0])
    if key.isdigit() and len(key) == 1:
        return MARKER_CODES.get(key)
    return None


#: Fonts.  DUPLEX and EXTENDED were stroke fonts on a plotter; what the user
#: meant by choosing one was "serif" or "plain", so that is what they map to.
#: Anything else is passed to matplotlib as a font family name.
FONT_ALIASES = {
    "DUPLEX": "serif",
    "TRIPLEX": "serif",
    "ROMAN": "serif",
    "SERIF": "serif",
    "SIMPLEX": "sans-serif",
    "EXTENDED": "sans-serif",
    "SANS": "sans-serif",
    "TYPEWRITER": "monospace",
    "MONO": "monospace",
}
