"""The font of the native digital form (specification/writing-system.md#the-font): the
committed font is the build of the current specification, byte for byte; each code point
is drawn by its component; each sign word and each protected word is replaced by its
ligature where it stands as a whole word and never inside a longer one; and the ceremonial
stylistic set draws each with its serifs. Shaping is HarfBuzz's, as browsers and terminals
shape."""
import os
import sys

import pytest

from rowih import api, data, writing

from corpus import ROOT, messages

hb = pytest.importorskip("uharfbuzz")
pytest.importorskip("fontTools")
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_font  # noqa: E402

LANG = data.load()
SPEC = LANG.writing
with open(build_font.OUT, "rb") as f:
    FONT_BYTES = f.read()
FONT = hb.Font(hb.Face(FONT_BYTES))


def native(form: str) -> str:
    return "".join(LANG.code_points[ch] for ch in form)


def shape(text: str, features: dict | None = None) -> list:
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(FONT, buf, features or {})
    return [FONT.glyph_to_string(i.codepoint) for i in buf.glyph_infos]


def component(ch: str) -> str:
    return "uni%04X" % ord(LANG.code_points[ch])


def ligatures() -> dict:
    """Each ligature's glyph name by its word's form."""
    out = {}
    for unit, sign in SPEC["units"].items():
        out[LANG.form_of(sign["opens"])] = "sign.%s.opens" % unit
        out[LANG.form_of(sign["closes"])] = "sign.%s.closes" % unit
    out[LANG.form_of(SPEC["walls"]["opens"])] = "sign.wall.opens"
    out[LANG.form_of(SPEC["walls"]["closes"])] = "sign.wall.closes"
    for item in LANG.items.values():
        if item.protected and item.form:
            out[item.form] = "word." + item.form
    return out


def test_the_committed_font_is_the_build_of_the_current_specification():
    first = build_font.build(LANG)
    assert first == build_font.build(LANG)
    assert first == FONT_BYTES


def test_every_code_point_is_drawn_by_its_component():
    from fontTools.ttLib import TTFont
    import io
    font = TTFont(io.BytesIO(FONT_BYTES))
    cmap, glyf = font.getBestCmap(), font["glyf"]
    half = SPEC["metrics"]["stroke"] * build_font.SCALE / 2
    for ch in LANG.letters:
        name = cmap[ord(LANG.code_points[ch])]
        assert name == component(ch) and shape(LANG.code_points[ch]) == [name]
        pts = [p for path in writing.pen_strokes(ch, LANG) for p in path]
        g = glyf[name]
        g.recalcBounds(glyf)
        s, box = build_font.SCALE, SPEC["lattice"]["box"]
        expected = (min(x for x, _ in pts) * s, (box[1] - max(y for _, y in pts)) * s,
                    max(x for x, _ in pts) * s, (box[1] - min(y for _, y in pts)) * s)
        assert abs(g.xMin - (expected[0] - half)) <= 1 and abs(g.yMin - (expected[1] - half)) <= 1
        assert abs(g.xMax - (expected[2] + half)) <= 1 and abs(g.yMax - (expected[3] + half)) <= 1
    assert cmap[0x20] == "space"


def test_each_sign_and_protected_word_shapes_to_its_ligature():
    other = native("napa")
    found = ligatures()
    assert len(found) == 8 + 2 + len({i.form for i in LANG.items.values() if i.protected})
    for form, name in found.items():
        word = native(form)
        assert shape(word) == [name]
        assert shape(" ".join([other, word, other])) == \
            [component(c) for c in "napa"] + ["space", name, "space"] + \
            [component(c) for c in "napa"]


def test_no_ligature_fires_inside_a_longer_word():
    for form in ligatures():
        for longer in ("n" + form, form + "n", "na" + form + "pa"):
            assert shape(native(longer)) == [component(c) for c in longer], longer


def test_the_ceremonial_set_adds_serifs_and_doubles_the_overline():
    for ch in LANG.letters:
        assert shape(LANG.code_points[ch], {"ss01": True}) == [component(ch) + ".ss01"]
    for form, name in ligatures().items():
        expected = name + ".ss01" if name.startswith("word.") else name
        assert shape(native(form), {"ss01": True}) == [expected]


def test_every_corpus_line_shapes_as_its_words():
    found = ligatures()
    shaped = 0
    for _, _, _, text in messages():
        a = api.parse(text)
        if a.message is None:
            continue
        for words in [a.message.envelope.words] + a.message.lines:
            if not words or any(w.kind == "payload" or not w.form or
                                any(c not in LANG.code_points for c in w.form) for w in words):
                continue
            expected = []
            for w in words:
                expected += [found[w.form]] if w.form in found else [component(c) for c in w.form]
                expected.append("space")
            assert shape(" ".join(native(w.form) for w in words)) == expected[:-1]
            shaped += 1
    assert shaped >= 600    # 663 lines hold no embedded material and no foreign character
