"""The writing-system specification and its renderings
(specification/writing-system.md#the-components): components on the lattice, far apart
under every turn and mirror and none another turned or mirrored
(`inv.critical-forms-distinct`); one code point each in the declared block; the signs
drawn whole distinct; every drawing, in every form, read back to the words it draws
(`inv.encodings-agree` for the written form); and the renderings views whose text
alternative is the transliteration (specification/writing-system.md#the-renderings)."""
import itertools
import json
import os
import struct
import zlib

import pytest

from rowih import api, data, drawing, png, raster, render, writing

from corpus import ROOT, corpus_paths, messages

LANG = data.load()
SPEC = LANG.writing


def test_no_component_is_a_turn_or_mirror_of_another():
    assert writing.turned_pairs() == []


def test_components_are_far_apart_under_every_turn_and_mirror():
    least = min(writing.distance(a, b) for a, b in itertools.permutations(LANG.letters, 2))
    assert least >= 0.6
    assert round(least, 6) == SPEC["least component distance"]


def test_every_symbol_has_one_component_and_one_code_point_in_the_block():
    lo, hi = (int(x[2:], 16) for x in SPEC["code point block"])
    assert [c["symbol"] for c in SPEC["components"]] == list(LANG.letters)
    points = [ord(LANG.code_points[ch]) for ch in LANG.letters]
    assert len(set(points)) == len(points)
    assert all(lo <= p <= hi for p in points)
    assert [c["code point"] for c in SPEC["components"]] == ["U+%04X" % p for p in points]


def test_components_are_drawn_on_the_lattice_without_an_upright_stroke():
    lattice = {tuple(sorted(map(tuple, s))) for s in SPEC["lattice"]["unit strokes"]}
    box = SPEC["lattice"]["box"]
    for c in SPEC["components"]:
        units = writing.unit_strokes(c["symbol"])
        assert units <= lattice
        ys = {p[1] for s in units for p in s}
        assert min(ys) == 0 and max(ys) == box[1]
        assert all(a[0] != b[0] for a, b in units)


def test_pen_strokes_draw_the_component_in_the_declared_order():
    """At most two strokes, each written from its left end, in the order of their
    starting points, and together drawing exactly the component's unit strokes."""
    for c in SPEC["components"]:
        pens = writing.pen_strokes(c["symbol"])
        assert 1 <= len(pens) <= 2
        assert all(p[0] <= p[-1] for p in pens)
        assert [p[0] for p in pens] == sorted(p[0] for p in pens)
        assert set().union(*(drawing._units(p) for p in pens)) == \
            writing.unit_strokes(c["symbol"])


def test_marks_differ_in_their_number_of_unit_strokes():
    counts = [len(drawing._units(sign["mark"])) for sign in SPEC["units"].values()]
    assert sorted(counts) == [3, 4, 5, 6]


def test_the_originality_report_is_of_the_current_inventory_and_passes():
    """The report of `tools/compare_glyphs.py` is of the components the specification
    draws; under it no component is near-identical to a letter of a listed alphabet or to
    any letter, digit or symbol Unicode encodes, and no alphabet takes more than two
    components near; and the control, the core's inventory, fails, so that the check is
    shown able to fail."""
    with open(os.path.join(ROOT, "corpus", "reports", "glyph-originality.json"),
              encoding="utf-8") as f:
        report = json.load(f)
    assert report["components"] == {c["symbol"]: c["unit strokes"] for c in SPEC["components"]}
    identical, near = report["criteria"]["near-identical"], report["criteria"]["near"]
    for label in ("current", "core, the control"):
        for r in report[label]["as drawn"].values():
            values = [sim for _, sim in r["pairs"].values()]
            assert r["at 0.95"] == sum(v >= identical for v in values)
            assert r["at 0.90"] == sum(v >= near for v in values)
    current = report["current"]["verdict"]
    assert current["no component near-identical to a listed letter"]
    assert current["no alphabet near more than two components"]
    assert current["no component near-identical to an encoded sign"]
    assert all(n[0]["similarity"] < identical for key in ("nearest letters", "nearest symbols")
               for n in report["current"][key].values())
    control = report["core, the control"]["verdict"]
    assert not control["no component near-identical to a listed letter"]
    assert not control["no alphabet near more than two components"]


def _within_alphabet(a):
    return all(ch in LANG.code_points for line in a.message.lines + [a.message.envelope.words]
               for w in line if w.kind != "payload" for ch in w.form)


def _corpus_analyses():
    """The analysis of every corpus file, the negative items among them, that parses to
    a message."""
    out = []
    for path in corpus_paths():
        with open(path, encoding="utf-8") as f:
            a = api.parse(f.read())
        if a.message is not None:
            out.append((os.path.basename(path), a))
    return out


ANALYSES = _corpus_analyses()


@pytest.mark.parametrize("form", drawing.FORMS)
def test_every_drawing_reads_back_to_its_words(form):
    """Every corpus message within the alphabet, the negative items among them, drawn in
    the form, is read back from the drawing's geometry to its words, line by line: the
    written form loses nothing (`inv.encodings-agree`)."""
    count = 0
    for name, a in ANALYSES:
        if not _within_alphabet(a):
            continue
        want = [[w.form for w in a.message.envelope.words]] + \
            [[w.form for w in line] for line in a.message.lines]
        assert drawing.read(drawing.draw(a, form)) == want, name
        count += 1
    assert count == len(ANALYSES) - 4


def test_a_character_outside_the_alphabet_is_shown_and_not_drawn_as_a_component():
    """Each corpus message with a character outside the alphabet, which the lexer marks
    with `?`, draws that word's other symbols as components and the mark as text."""
    outside = [(name, a) for name, a in ANALYSES if not _within_alphabet(a)]
    assert len(outside) == 4
    for name, a in outside:
        d = drawing.draw(a)
        texts = [t.text for t in d.texts]
        for line in [a.message.envelope.words] + a.message.lines:
            for w in line:
                if w.kind == "payload":
                    continue
                for ch in w.form:
                    if ch not in LANG.code_points:
                        label = ch if 0x20 < ord(ch) < 0x7F else "U+%04X" % ord(ch)
                        assert label in texts, name
        assert sum(t.count("?") for t in texts) == \
            sum(w.form.count("?") for line in [a.message.envelope.words] + a.message.lines
                for w in line if w.kind != "payload"), name


def _ceremonial_and_standard():
    out = {}
    for _, _, _, text in messages():
        a = api.parse(text)
        regs = {s["register"] for s in a.social}
        if regs == {"R7"} and "R7" not in out:
            out["R7"] = a
        elif regs == {"R2"} and "R2" not in out:
            out["R2"] = a
    assert set(out) == {"R7", "R2"}
    return out


def test_ceremonial_register_draws_serifs_and_doubled_rules():
    """A move in the ceremonial register sets an upright serif across each free end and
    doubles its rules; the same in the standard register has neither, and both read back
    to their words."""
    pair = _ceremonial_and_standard()

    def serifs(a):
        d = drawing.draw(a)
        return sum(1 for p in d.paths if len(p.points) == 2 and p.points[0][0] ==
                   p.points[1][0] and abs(p.points[1][1] - p.points[0][1]) == 2 * SPEC["serif"])
    assert serifs(pair["R7"]) > 0
    assert serifs(pair["R2"]) == 0


def test_compact_form_is_the_display_form_at_half_size():
    _, _, _, text = messages()[0]
    a = api.parse(text)
    d, c = drawing.draw(a), drawing.draw(a, "compact")
    assert (c.width * 2, c.height * 2) == (d.width, d.height)
    assert [tuple((x * 2, y * 2) for x, y in p.points) for p in c.paths] == \
        [p.points for p in d.paths]


def test_handwritten_form_joins_the_components_of_a_word_by_hairlines():
    _, _, _, text = messages()[0]
    a = api.parse(text)
    joins = [p for p in drawing.draw(a, "handwritten").paths if p.weight == "hairline"]
    clusters = sum(len(w.form) - 1 for line in a.message.lines + [a.message.envelope.words]
                   for w in line if w.kind != "payload" and not _is_sign(w))
    assert len(joins) == clusters


def _is_sign(w):
    ident = w.item.identifier if w.item else ""
    signs = {s[k] for s in SPEC["units"].values() for k in ("opens", "closes")}
    return ident in signs or ident in SPEC["walls"].values()


def test_svg_is_a_view_with_the_transliteration_as_its_text():
    _, _, _, text = messages()[0]
    a = api.parse(text)
    svg = render.svg(a)
    assert svg.startswith("<svg") and "A view of the native written form" in svg
    assert a.canonical.strip().split("\n")[0][:40] in svg
    assert 'stroke="currentColor"' in svg and "#" not in svg.split("<desc>")[0]


def test_high_contrast_is_black_on_white():
    _, _, _, text = messages()[0]
    a = api.parse(text)
    svg = render.svg(a, contrast="high")
    assert 'stroke="#000000"' in svg and 'fill="#ffffff"' in svg
    image = render.png(a, contrast="high")
    assert set(_pixels(image)) <= {0, 255}


def _chunks(image: bytes) -> dict:
    assert image[:8] == b"\x89PNG\r\n\x1a\n"
    out, i = {}, 8
    while i < len(image):
        n = struct.unpack(">I", image[i:i + 4])[0]
        kind, body = image[i + 4:i + 8], image[i + 8:i + 8 + n]
        assert struct.unpack(">I", image[i + 8 + n:i + 12 + n])[0] == zlib.crc32(kind + body)
        out[kind] = body
        i += 12 + n
    return out


def _pixels(image: bytes) -> bytes:
    c = _chunks(image)
    w, h = struct.unpack(">II", c[b"IHDR"][:8])
    raw = zlib.decompress(c[b"IDAT"])
    return b"".join(raw[y * (w + 1) + 1:(y + 1) * (w + 1)] for y in range(h))


def test_png_holds_the_rasterised_drawing_and_the_transliteration():
    """The PNG decodes, by Python's own zlib, to the rasterised drawing, its chunks'
    CRCs are those zlib computes, and its description is the transliteration."""
    _, _, _, text = messages()[0]
    a = api.parse(text)
    image = render.png(a)
    c = _chunks(image)
    w, h, greys = raster.rasterise(drawing.draw(a), SPEC["pixels per unit"])
    assert struct.unpack(">II", c[b"IHDR"][:8]) == (w, h)
    assert _pixels(image) == bytes(greys)
    assert c[b"tEXt"] == b"Description\x00" + a.canonical.encode("ascii")


def test_png_compressor_round_trips_every_byte_value():
    data_ = bytes(range(256)) * 3 + bytes([7]) * 700 + bytes(range(255, -1, -1))
    for stride in (1, 17, 300, 40000):
        assert zlib.decompress(png.zlib_stream(data_, stride)) == data_


def test_html_marks_the_transliteration_and_carries_a_description():
    _, _, _, text = messages()[0]
    a = api.parse(text)
    out = render.html(a, description="An observation that the service runs.")
    assert '<code lang="art">' in out
    assert '<p class="description">An observation that the service runs.</p>' in out


def test_terminal_without_the_font_shows_the_transliteration():
    _, _, _, text = messages()[0]
    a = api.parse(text)
    assert render.terminal(a, has_font=False) == a.canonical


def test_a_comparison_of_glyphs_fails_on_a_near_sign_or_a_control_that_passes():
    import copy
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import compare_glyphs
    with open(os.path.join(ROOT, "corpus", "reports", "glyph-originality.json"),
              encoding="utf-8") as f:
        report = json.load(f)
    assert not compare_glyphs.failed(report)
    near = copy.deepcopy(report)
    near["current"]["verdict"]["no component near-identical to an encoded sign"] = False
    assert compare_glyphs.failed(near)
    passing_control = copy.deepcopy(report)
    for key, value in passing_control["core, the control"]["verdict"].items():
        if isinstance(value, bool):
            passing_control["core, the control"]["verdict"][key] = True
    assert compare_glyphs.failed(passing_control)
