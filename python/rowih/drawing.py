"""The drawing of a message in the native written form
(specification/writing-system.md#drawing-a-word-and-a-line): a display list of paths in
integer units, from which the SVG and the PNG are both written, so that the two cannot
draw differently.

Each line is the envelope or a move, and each word of it is drawn in turn. A word of the
lexicon or an unknown word is a cluster of its components, side by side; a word that opens
or closes a unit is an upright side with the unit's mark at its top, and the unit's
extent is a rule below the line joining its two sides, a unit nested in another ruled
above it, so that each unit sits in a tray; a word that opens or closes a wall is a pair
of upright strokes through the line and its rules; embedded material is drawn as text;
a run of numerals is framed; and a protected word has a rule above it. The envelope is
drawn between two rules. A move in the ceremonial register is drawn in the ceremonial
variant of the form: a serif across each free end of a stroke, and its rules doubled.

A drawing is a view made by its receiver (specification/writing-system.md#the-renderings);
`read` recovers the words of each line from the drawing's geometry alone, which is how the
tests show that the drawing keeps every distinction the transliteration makes.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import writing
from .data import Language, load

FORMS = ("display", "compact", "handwritten")
CEREMONIAL = "R7"


@dataclass(frozen=True)
class Path:
    points: tuple           # ((x, y), ...) in units, x to the right and y downward
    weight: str = "stroke"  # "stroke", or "hairline" for the handwritten form's joins


@dataclass(frozen=True)
class Text:
    x: int
    y: int                  # the baseline
    width: int
    size: int               # the height of the text, and of its outline in the PNG
    text: str


@dataclass
class Drawing:
    form: str
    width: int = 0
    height: int = 0
    paths: list = field(default_factory=list)
    texts: list = field(default_factory=list)
    stroke: float = 0.0
    hairline: float = 0.0
    lines: list = field(default_factory=list)   # the top of each line's text, in order


def _mark_base(mark: list) -> int:
    base = [p[0] for p in mark if p[1] == 0]
    return (min(base) + max(base)) // 2


class _Line:
    """The layout of one line, in its own coordinates: the line's text from y 0 to the
    box's height, its marks above and its rules below."""

    def __init__(self, lang: Language, ceremonial: bool, envelope: bool):
        self.lang, self.spec = lang, lang.writing
        self.m = self.spec["metrics"]
        self.box = self.spec["lattice"]["box"]
        self.ceremonial, self.envelope = ceremonial, envelope
        self.paths, self.texts = [], []
        self.x = self.m["margin"]
        self.opens, self.closes = {}, {}
        for unit, sign in self.spec["units"].items():
            self.opens[sign["opens"]] = unit
            self.closes[sign["closes"]] = unit
        self.stack = []          # open units: [unit, side x, highest level inside]
        self.units = []          # (unit, opening x, closing x, level)
        self.lone = []           # (unit, side x, opens) without a partner
        self.walls = []
        self.levels = 0

    def side(self, unit: str, opens: bool):
        x = self.x + self.m["side"] // 2
        if opens:
            self.stack.append([unit, x, 0])
        elif self.stack and self.stack[-1][0] == unit:
            _, ox, inner = self.stack.pop()
            level = inner + 1
            self.units.append((unit, ox, x, level))
            self.levels = max(self.levels, level)
            if self.stack:
                self.stack[-1][2] = max(self.stack[-1][2], level)
        else:
            self.lone.append((unit, x, False))
        self.x += self.m["side"] + self.m["word gap"]

    def wall(self, opens: bool):
        self.walls.append((self.x, opens))
        self.x += self.m["side"] + self.m["word gap"]

    def payload(self, text: str):
        width = self.m["character"] * len(text)
        self.texts.append(Text(self.x, self.box[1] - 2, width, self.m["text size"], text))
        self.x += width + self.m["word gap"]

    def cluster(self, form: str, protected: bool, handwritten: bool) -> tuple:
        start, w, gap = self.x, self.box[0], self.m["gap"]
        previous_end = None
        for ch in form:
            if ch not in self.lang.code_points:
                # a character outside the alphabet has no component; it is shown as
                # itself where it is printable ASCII (the lexer's mark `?` among them) and
                # otherwise by its code point, never hidden and never drawn as a component
                label = ch if 0x20 < ord(ch) < 0x7F else "U+%04X" % ord(ch)
                width = self.m["character"] * len(label)
                self.texts.append(Text(self.x, self.box[1] - 2, width, self.m["text size"],
                                       label))
                self.x += width + gap
                previous_end = None
                continue
            pens = writing.pen_strokes(ch, self.lang)
            for path in pens:
                self.paths.append(Path(tuple((self.x + px, py) for px, py in path)))
            if handwritten and pens:
                first = (self.x + pens[0][0][0], pens[0][0][1])
                if previous_end is not None:
                    self.paths.append(Path((previous_end, first), "hairline"))
                previous_end = (self.x + pens[-1][-1][0], pens[-1][-1][1])
            if self.ceremonial:
                for px, py in writing.free_ends(ch, self.lang):
                    s = self.spec["serif"]
                    self.paths.append(Path(((self.x + px, py - s), (self.x + px, py + s))))
            self.x += w + gap
        end = self.x - gap
        if protected:
            y = -self.m["overline"]
            self.paths.append(Path(((start, y), (end, y))))
            if self.ceremonial:
                y -= self.spec["double"]
                self.paths.append(Path(((start, y), (end, y))))
        self.x = end + self.m["word gap"]
        return start, end

    def frame(self, start: int, end: int):
        h, half = self.box[1] // 2, self.m["frame"]
        a, b = start - self.m["frame space"] // 2, end + self.m["frame space"] // 2
        tip = half // 3
        self.paths.append(Path(((a, h - half), (b, h - half), (b + tip, h), (b, h + half),
                                (a, h + half), (a - tip, h), (a, h - half))))

    def rule_y(self, level: int) -> int:
        return self.box[1] + self.m["rule depth"] + (level - 1) * self.m["rule step"]

    def finish(self) -> tuple:
        """Draw the sides, rules, marks, walls and strip, and return the line's paths
        with its extent above and below its own origin."""
        for unit, x, _ in self.stack:
            self.lone.append((unit, x, True))
        top = -2
        for unit, ox, cx, level in self.units:
            y = self.rule_y(level)
            for x in (ox, cx):
                self.paths.append(Path(((x, top), (x, y))))
                self._mark(unit, x)
            self.paths.append(Path(((ox, y), (cx, y))))
            if self.ceremonial:
                d = self.spec["double"]
                self.paths.append(Path(((ox, y + d), (cx, y + d))))
        for unit, x, opens in self.lone:
            y = self.rule_y(1)
            foot = 4 if opens else -4
            self.paths.append(Path(((x, top), (x, y), (x + foot, y))))
            self._mark(unit, x)
        bottom = self.rule_y(self.levels) + (self.spec["double"] if self.ceremonial else 0) \
            if self.levels else self.box[1] + self.m["rule depth"]
        for x, opens in self.walls:
            for dx in (2, 6):
                self.paths.append(Path(((x + dx, top), (x + dx, bottom))))
            # a tick at the top turned inward, so that the two walls differ
            tick = ((x + 6, top), (x + 10, top)) if opens else ((x - 2, top), (x + 2, top))
            self.paths.append(Path(tick))
        width = self.x - self.m["word gap"] + self.m["margin"]
        h = self.box[1] // 2
        above = self.m["above"]
        below = max(bottom, h + self.m["frame"]) + self.m["below"]
        if self.envelope:
            s = self.m["strip"]
            for y in (-s, self.box[1] + s):
                self.paths.append(Path(((self.m["margin"] // 2, y),
                                        (width - self.m["margin"] // 2, y))))
            below = max(below, self.box[1] + s + self.m["below"])
        return width, above, below

    def _mark(self, unit: str, x: int):
        mark = self.spec["units"][unit]["mark"]
        dx = x - _mark_base(mark)
        self.paths.append(Path(tuple((dx + px, py - 2) for px, py in mark)))


def _registers(analysis) -> dict:
    """The register of each move line, by its place among the lines."""
    out = {}
    if analysis.message is None:
        return out
    for move, social in zip(analysis.message.moves, analysis.social):
        out[move.index - 1] = social.get("register")
    return out


def draw(analysis, form: str = "display", lang: Language | None = None) -> Drawing:
    """The drawing of a parsed message in one of the forms."""
    lang = lang or load()
    if form not in FORMS:
        raise ValueError("no form %r; the forms are %s" % (form, ", ".join(FORMS)))
    m = lang.writing["metrics"]
    out = Drawing(form, stroke=m["stroke"], hairline=m["hairline"])
    if analysis.message is None:
        return out
    registers = _registers(analysis)
    lines = [(analysis.message.envelope.words, False, True)] + [
        (words, registers.get(i) == CEREMONIAL, False)
        for i, words in enumerate(analysis.message.lines)]
    y = 0
    for words, ceremonial, envelope in lines:
        line = _Line(lang, ceremonial, envelope)
        _write(line, words, form == "handwritten")
        width, above, below = line.finish()
        offset = y + above
        for p in line.paths:
            out.paths.append(Path(tuple((px, py + offset) for px, py in p.points), p.weight))
        for t in line.texts:
            out.texts.append(Text(t.x, t.y + offset, t.width, t.size, t.text))
        out.width = max(out.width, width)
        out.lines.append(offset)
        y = offset + below + m["line gap"]
    out.height = y
    if form == "compact":
        out = _halve(out)
    return out


def _is_numeral(w, numeral: str) -> bool:
    return w is not None and w.item is not None and w.item.class_id == numeral


def _write(line: _Line, words: list, handwritten: bool):
    """Each word of a line in turn: a side, a wall, embedded material or a cluster, and
    a frame round each run of numerals."""
    spec, m = line.spec, line.m
    numeral = spec["numbers"]["class"]
    wall_opens, wall_closes = spec["walls"]["opens"], spec["walls"]["closes"]
    run = None
    for i, w in enumerate(words):
        ident = w.item.identifier if w.item is not None else ""
        is_numeral = _is_numeral(w, numeral)
        if is_numeral and run is None:
            line.x += m["frame space"]
        if ident in line.opens:
            line.side(line.opens[ident], True)
        elif ident in line.closes:
            line.side(line.closes[ident], False)
        elif ident in (wall_opens, wall_closes):
            line.wall(ident == wall_opens)
        elif w.kind == "payload":
            line.payload(w.form)
        else:
            start, end = line.cluster(w.form, w.item is not None and w.item.protected,
                                      handwritten)
            if is_numeral:
                run = (run[0] if run else start, end)
        if run is not None and not _is_numeral(words[i + 1] if i + 1 < len(words) else None,
                                               numeral):
            line.frame(*run)
            line.x += m["frame space"]
            run = None


def _halve(d: Drawing) -> Drawing:
    return Drawing(
        "compact", d.width // 2, d.height // 2,
        [Path(tuple((x // 2, y // 2) for x, y in p.points), p.weight) for p in d.paths],
        [Text(t.x // 2, t.y // 2, t.width // 2, t.size // 2, t.text) for t in d.texts],
        d.stroke / 2, d.hairline / 2, [y // 2 for y in d.lines])


def _units(points: list) -> set:
    """The unit strokes of a path: a horizontal stroke four units a step, a slanted one
    two across and six down a step."""
    out = set()
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        if ay == by:
            n, sx, sy = abs(bx - ax) // 4, (4 if bx > ax else -4), 0
        else:
            n, sx, sy = abs(by - ay) // 6, (2 if bx > ax else -2), (6 if by > ay else -6)
        for k in range(n):
            a = (ax + k * sx, ay + k * sy)
            out.add(tuple(sorted((a, (a[0] + sx, a[1] + sy)))))
    return out


def read(d: Drawing, lang: Language | None = None) -> list:
    """The words of each line, read from the drawing's geometry alone: each component by
    its unit strokes, each side by its mark and by which way its rule runs, each wall by
    its tick, and embedded material by its text. The inverse of `draw`, which the tests
    use to show that a drawing loses nothing the transliteration has."""
    lang = lang or load()
    if d.form == "compact":
        d = Drawing("display", d.width * 2, d.height * 2,
                    [Path(tuple((x * 2, y * 2) for x, y in p.points), p.weight)
                     for p in d.paths],
                    [Text(t.x * 2, t.y * 2, t.width * 2, t.size * 2, t.text) for t in d.texts],
                    d.stroke * 2, d.hairline * 2, [y * 2 for y in d.lines])
    signs = _Signs(lang)
    box = lang.writing["lattice"]["box"]
    out = []
    for top in d.lines:
        strokes, verticals, rules, marks = _classify(d.paths, top, box)
        texts = [t for t in d.texts if top <= t.y <= top + box[1]]
        items = _components(top, strokes, signs) + \
            _sides(top, verticals, rules, marks, signs) + \
            [(t.x, "word", t.text, t.x + t.width) for t in texts]
        out.append(_words(items, lang.writing))
    return out


class _Signs:
    """What a reader of a drawing knows: each component's shape, each mark's unit, and
    the form of each word drawn whole."""

    def __init__(self, lang: Language):
        spec = lang.writing
        self.shapes, self.marks, self.forms = {}, {}, {}
        for c in spec["components"]:
            units = {tuple(sorted(map(tuple, s))) for s in c["unit strokes"]}
            x0 = min(p[0] for s in units for p in s)
            self.shapes[frozenset(((a[0] - x0, a[1]), (b[0] - x0, b[1])) for a, b in units)] = \
                (c["symbol"], x0)
        for unit, sign in spec["units"].items():
            base = _mark_base(sign["mark"])
            self.marks[tuple((px - base, py) for px, py in sign["mark"])] = unit
            self.forms[(unit, True)] = lang.form_of(sign["opens"])
            self.forms[(unit, False)] = lang.form_of(sign["closes"])
        self.wall = {True: lang.form_of(spec["walls"]["opens"]),
                     False: lang.form_of(spec["walls"]["closes"])}


def _classify(paths: list, top: int, box: list) -> tuple:
    """A line's paths, as the strokes of components, the uprights of sides and walls, the
    rules and ticks, and the marks."""
    strokes, verticals, rules, marks = [], [], [], []
    for p in paths:
        if p.weight != "stroke":
            continue
        ys = [y - top for _, y in p.points]
        xs = [x for x, _ in p.points]
        upright = all(x == xs[0] for x in xs)
        # a side is upright from the top of the line, though a side with no partner
        # turns into a foot at its bottom
        side = len(p.points) >= 2 and xs[0] == xs[1] and ys[0] == -2 and ys[1] > box[1]
        if p.points[0] == p.points[-1] and max(ys) == -2:
            marks.append(p)
        elif not upright and min(ys) >= 0 and max(ys) <= box[1]:
            strokes.append(p)
        elif side:
            verticals.append(p)
        elif all(y == ys[0] for y in ys) and ys[0] > box[1]:
            rules.append(p)
        elif len(p.points) == 2 and ys[0] == ys[1] == -2:
            rules.append(p)    # a wall's tick
    return strokes, verticals, rules, marks


def _components(top: int, strokes: list, signs: _Signs) -> list:
    """The components of a line, strokes grouped by the extent they cover across it, each
    as (x, "component", symbol, right end)."""
    groups = []
    for p in sorted(strokes, key=lambda p: min(x for x, _ in p.points)):
        lo, hi = min(x for x, _ in p.points), max(x for x, _ in p.points)
        if groups and lo <= groups[-1][1]:
            groups[-1][1] = max(groups[-1][1], hi)
            groups[-1][2].append(p)
        else:
            groups.append([lo, hi, [p]])
    items = []
    for lo, hi, paths in groups:
        units = set()
        for p in paths:
            units |= _units([(x, y - top) for x, y in p.points])
        x0 = min(pt[0] for s in units for pt in s)
        key = frozenset(((a[0] - x0, a[1]), (b[0] - x0, b[1])) for a, b in units)
        symbol, inset = signs.shapes.get(key, ("?", 0))
        items.append((x0 - inset, "component", symbol, hi))
    return items


def _sides(top: int, verticals: list, rules: list, marks: list, signs: _Signs) -> list:
    """The sides and walls of a line as words: walls come in pairs four apart, ticked at
    the top, and a side is known by its mark and by which way its rule or foot runs."""
    xs = sorted(p.points[0][0] for p in verticals)
    taken, items = set(), []
    for x in xs:
        if x in taken:
            continue
        if x + 4 in xs:
            taken |= {x, x + 4}
            opens = any(r.points[0] in ((x + 4, top - 2),) and r.points[1][0] > x + 4
                        for r in rules)
            items.append((x - 2, "word", signs.wall[opens], x + 6))
            continue
        side = [p for p in verticals if p.points[0][0] == x][0]
        mark = None
        for mp in marks:
            base = [px for px, py in mp.points if py - top == -2]
            if (min(base) + max(base)) // 2 == x:
                mark = tuple((px - x, py - top + 2) for px, py in mp.points)
        unit = signs.marks.get(mark)
        if len(side.points) == 3:
            opens = side.points[2][0] > x
        else:
            y = side.points[-1][1]
            opens = any(r.points[0][1] == y and min(r.points[0][0], r.points[-1][0]) == x
                        for r in rules)
        items.append((x - 4, "word", signs.forms.get((unit, opens), "?"), x + 4))
    return items


def _words(items: list, spec: dict) -> list:
    """The words of a line from its items in order: components a gap apart join one
    word, and every other item is a word of its own."""
    box, gap = spec["lattice"]["box"], spec["metrics"]["gap"]
    words, current, last = [], "", None
    for lo, kind, value, hi in sorted(items):
        if kind == "component":
            if current and last is not None and lo - last == gap:
                current += value
            else:
                if current:
                    words.append(current)
                current = value
            last = lo + box[0]
        else:
            if current:
                words.append(current)
            current, last = "", None
            words.append(value)
    if current:
        words.append(current)
    return words
