"""The declared source of the writing-system specification: the lattice the components are
drawn on, the bounds of the search that chose them, the code points, and the shapes and
metrics of the signs drawn whole and of the four forms. `tools/search_components.py`
chooses the components within these bounds and records them in
`tools/component_search.json`; `tools/build_writing.py` assigns them to the symbols and
writes `language/writing.json`. No shape is assigned to a symbol by hand.

Coordinates are integers in display units, x to the right and y downward, so that both
implementations draw the same numbers.
"""

# The ten points of the lattice, rows of three, four and three, each row half a column
# from the next, so that every stroke is horizontal or at the same steep slant either
# way. A unit stroke joins two points four units apart in a row or neighbouring points
# of neighbouring rows. The box is 12 by 12.
LATTICE = [(2, 0), (6, 0), (10, 0),
           (0, 6), (4, 6), (8, 6), (12, 6),
           (2, 12), (6, 12), (10, 12)]
BOX = (12, 12)


def unit_strokes() -> list:
    """The unit strokes of the lattice, each a sorted pair of points, in a fixed order."""
    out = []
    for i, a in enumerate(LATTICE):
        for b in LATTICE[i + 1:]:
            dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
            if (dy == 0 and dx == 4) or (dy == 6 and dx == 2):
                out.append(tuple(sorted((a, b))))
    return sorted(out)


# The lattice maps onto itself under the mirror about its upright axis, the mirror about
# its level axis and the half-turn; these are the turns and mirrors a component is
# compared under, so that no component is another turned or mirrored.
def mirror_x(p):
    return (BOX[0] - p[0], p[1])


def mirror_y(p):
    return (p[0], BOX[1] - p[1])


def half_turn(p):
    return (BOX[0] - p[0], BOX[1] - p[1])


SYMMETRIES = [lambda p: p, mirror_x, mirror_y, half_turn]

# The bounds of the search: a component has four to six unit strokes, is connected, can
# be written in at most two strokes of the pen, spans the box from top to bottom and at
# least six tenths of its width, and resembles no letter of a listed writing system as
# drawn: its F-measure stays under 0.90 against every reference alphabet and under 0.85
# against every style of Latin, Greek and Cyrillic. A chosen component whose F-measure
# reaches 0.95 against any letter, digit or symbol Unicode encodes is set aside, and the
# choice made again.
SEARCH = {
    "strokes": [4, 6],
    "pen strokes": 2,
    "width share": 0.6,
    "resemblance": 0.90,
    "resemblance, Latin, Greek and Cyrillic": 0.85,
    "strict systems": ["Latin", "Greek", "Cyrillic"],
    "near-identical": 0.95,
    "seed": 20261011,
    "restarts": 30,
    "inventory": 19,
}

# The native digital form: one code point for each symbol, in the order of the phonology,
# from U+F3A0, in a block the Under-ConScript Unicode Registry reserves for private use
# outside the registry and no current or earlier Nerd Fonts set occupies
# (specification/writing-system.md#the-native-digital-form). U+F3A0 to U+F3BF is reserved
# for the writing system.
CODE_POINT_BLOCK = (0xF3A0, 0xF3BF)

# Signs drawn whole. Each unit is drawn as a tray: an upright side at its opening word
# and at its closing word, joined by a rule below the line, and the side carries a
# closed mark at its top whose number of edges names the unit, so that no mark is a turn
# or mirror of another.
UNIT_MARKS = {
    "assertion": [(0, 0), (2, -6), (4, 0), (0, 0)],
    "situation": [(0, 0), (2, -6), (6, -6), (4, 0), (0, 0)],
    "term": [(0, 0), (2, -6), (6, -6), (8, 0), (0, 0)],
    "readings": [(0, 0), (-2, -6), (2, -12), (6, -12), (8, -6), (4, 0), (0, 0)],
}

# The metrics of the display form, all even, so that the compact form is the display
# form at half size, exactly: the gap between components and between words, the width a
# side or a wall takes, the extra space a number's frame takes at each end, the height
# the marks need above the line, the depth of the first rule below the line and the step
# between rules, the space below the last rule, the height of the overline and of the
# frame's ends above and below the middle of the line, the envelope's strip above and
# below the line, the margin, the space between lines, the width of a character of
# embedded material and its height, and the widths of a stroke and of a hairline, the joins of the
# handwritten form.
METRICS = {"gap": 4, "word gap": 8, "side": 8, "frame space": 8, "above": 16,
           "rule depth": 8, "rule step": 4, "below": 6, "overline": 4, "frame": 12,
           "strip": 8, "margin": 8, "line gap": 4, "character": 6, "text size": 8,
           "stroke": 1.5,
           "hairline": 0.75}
# The PNG output draws this many pixels to a unit of either form: from specification 0.2,
# four, so that a component of the display form is 48 pixels tall and one of the compact
# form 24, the sizes a reader read.
PIXELS_PER_UNIT = 4

# The ceremonial forms set an upright serif across each free end of a stroke, this far
# above and below it (no component has an upright stroke, so that a serif is never read
# as part of one), and double the rules of the trays and the overline, this far apart.
SERIF = 2
DOUBLE = 2
