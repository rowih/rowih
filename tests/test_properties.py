"""The properties of the language over generated utterances (`generate_utterances`):
variants of the corpus's moves drawn by Hypothesis, with members replaced within their
classes, roots within their category, numbers redrawn and times added."""
import copy

from hypothesis import HealthCheck, assume, given, settings, strategies as st

from rowih import api, data
from rowih.generator import Generator
from rowih.normal import Normaliser
from rowih.tree import Spell, strip_private

from corpus import in_current_release, items, moves_of

LANG = data.load()
GEN = Generator(LANG)
NORM = Normaliser(LANG)
SPELL = Spell(LANG)
# the meanings of records written in the current release, with no dialect, which the
# current release's generator writes
BASES = [moves_of(m) for item in items() for m in item["messages"] if in_current_release(m)]
SWAPPABLE = {"g.situations-and-contents.aspect", "g.situations-and-contents.polarity",
             "g.situations-and-contents.quantifier", "g.reference.specificity",
             "g.reference.access", "g.standing.basis", "g.standing.strength",
             "g.attitudes-and-aims.kind-of-attitude", "g.situations-and-contents.comparator",
             "g.situations-and-contents.status-of-content",
             "g.situations-and-contents.information-structure"}
ROOTS = {}
for ident, e in LANG.entries.items():
    if e["grammatical category"] in ("predicate root", "nominal root"):
        ROOTS.setdefault(e["grammatical category"], []).append(ident)


def units(node):
    if isinstance(node, dict):
        if node.get("kind") in ("assertion", "situation", "term"):
            yield node
        for v in node.values():
            yield from units(v)
    elif isinstance(node, list):
        for x in node:
            yield from units(x)


@st.composite
def variants(draw):
    moves = copy.deepcopy(draw(st.sampled_from(BASES)))
    for _ in range(draw(st.integers(0, 6))):
        us = list(units(moves))
        if not us:
            break
        u = draw(st.sampled_from(us))
        parts = u["parts"]
        choice = draw(st.integers(0, 3))
        if choice == 0:
            vals = [p for p in parts if p["kind"] == "value"
                    and p["member"].rsplit(".", 1)[0] in SWAPPABLE]
            if vals:
                p = draw(st.sampled_from(vals))
                cls = LANG.classes[p["member"].rsplit(".", 1)[0]]
                p["member"] = draw(st.sampled_from([m["identifier"] for m in cls["members"]]))
        elif choice == 1:
            words = [p for p in parts if p["kind"] == "word" and p.get("entry")]
            if words:
                p = draw(st.sampled_from(words))
                cat = LANG.entries[p["entry"]]["grammatical category"]
                if cat in ROOTS:
                    p["entry"] = draw(st.sampled_from(ROOTS[cat]))
                    p["form"] = LANG.items[p["entry"]].form
        elif choice == 2:
            qs = [p for p in parts if p["kind"] == "quantity" and not p["number"].startswith("0.")]
            if qs:
                p = draw(st.sampled_from(qs))
                whole = draw(st.integers(0, 10 ** 6))
                frac = draw(st.integers(0, 999))
                p["number"] = "%d.%d" % (whole, frac) if draw(st.booleans()) else str(whole)
        elif u["kind"] == "situation" and not any(p["kind"] == "time" for p in parts):
            n = draw(st.integers(1, 500))
            unit = draw(st.sampled_from(["second", "minute", "hour", "day"]))
            anchor = draw(st.sampled_from(["ago", "hence"]))
            parts.append({"kind": "time", "index": "g.time.time-index.event-time",
                          "spec": {"kind": "offset", "number": str(n),
                                   "unit": "g.time.time-unit." + unit,
                                   "anchor": "g.time.time-anchor." + anchor}})
    return moves


def normal_text(moves):
    return "".join(" ".join(SPELL.move(NORM.move(t))) + "\n" for t in moves)


PROFILE = settings(max_examples=150, deadline=None,
                   suppress_health_check=[HealthCheck.too_slow])


@PROFILE
@given(variants(), st.sampled_from(["normal expression", "full explicitness"]))
def test_round_trip(moves, mode):
    """The normal form of parse(generate(x)) is the normal form of x."""
    text = GEN.message(moves, mode)
    assume(len(text.split()) <= LANG.protocol["maxima"]["message words"])
    a = api.parse(text)
    assert a.message is not None and len(a.moves) == len(moves)
    # compared as trees, so that a defect shared by both serialisations is not hidden
    assert [strip_private(n) for n in a.normal] == [NORM.move(t) for t in moves]


@PROFILE
@given(variants())
def test_determinism(moves):
    assert GEN.message(moves) == GEN.message(copy.deepcopy(moves))


@PROFILE
@given(variants())
def test_transliteration_and_native_agree(moves):
    text = GEN.message(moves)
    assume(len(text.split()) <= LANG.protocol["maxima"]["message words"])
    a = api.parse(text)
    native, _ = api.convert(text, "native")
    b = api.parse(native)
    assert b.canonical == a.canonical and b.normal_text == a.normal_text
    assert [d.code for d in b.diagnostics] == [d.code for d in a.diagnostics]


@PROFILE
@given(variants())
def test_normal_form_is_a_fixed_point(moves):
    once = [NORM.move(t) for t in moves]
    assert [NORM.move(t) for t in once] == once


@PROFILE
@given(st.text(max_size=300))
def test_no_input_raises(text):
    api.parse(text)


@PROFILE
@given(variants(), st.randoms(use_true_random=False))
def test_sibling_order_does_not_change_the_normal_form(moves, rnd):
    """Siblings marked by role stand in any order (specification/grammar.md#units):
    shuffling them changes the realisation and never the normal form."""
    shuffled = copy.deepcopy(moves)
    for u in units(shuffled):
        rnd.shuffle(u["parts"])
    assert [NORM.move(t) for t in shuffled] == [NORM.move(t) for t in moves]
