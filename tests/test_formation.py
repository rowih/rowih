"""Word formation and the act of definition (specification/lexicon.md#word-formation):
`inv.word-formation` and `inv.core-closed`, tested as the invariants state
(specification/conformance.md#the-invariants), and whether agents interpret new
derivations and compounds from their parts; and the suffixes and the productive patterns
of lexicon 1.0 (specification/lexicon.md#the-productive-patterns)."""
import collections
import functools
import itertools
import json
import os
import random

import pytest
from hypothesis import HealthCheck, assume, given, settings, strategies as st

from rowih import api, data, formation, lexicon_checks as lc
from rowih.convention_rules import confusable, root_shaped
from rowih.coordination import structure
from rowih.generator import Generator
from rowih.lexer import segment
from rowih.notation import Printer, Reader
from rowih.view import View

from corpus import messages

LANG = data.load()
GEN = Generator(LANG)
READ = Reader(LANG)
PRINT = Printer(LANG)
TEXTS = {(i, k): t for i, k, _, t in messages()}
PROFILE = settings(max_examples=150, deadline=None,
                   suppress_health_check=[HealthCheck.too_slow])


def entry(key):
    return next(i for i, e in LANG.entries.items() if e["key"] == key)


def written(item_id, k):
    return api.parse(TEXTS[(item_id, k)])


# ---------------------------------------------------------------- word formation

EXPECTED_SORTS = {
    "detect.agent": ("agent", "s.sort.agent"),
    "file.verbalisation": ("verbalisation", "s.sort.event"),
    "water.adjectivisation": ("adjectivisation", "s.sort.state"),
    "memory~record": ("compound", "s.sort.object"),
    "examine.process": ("process", "s.sort.reified-referent"),
    "burn~memory": ("compound", "s.sort.process"),
    "quiet.property": ("property", "s.sort.kind"),
    "service.abstraction": ("abstraction", "s.sort.kind"),
    "run.nominalisation": ("nominalisation", "s.sort.proposition"),
}


def test_the_corpus_formations_mean_what_their_parts_give():
    """Every unlisted formation of the formations item is read by its mechanism, with the
    sort the mechanism gives; the listed compound is read by its entry, whose meaning has
    drifted from its parts."""
    import sys
    sys.path.insert(0, "tools")
    from build_corpus import formed
    read = {}
    for k in (1, 2):
        for f in written("e4-formations", k).formations:
            read[f["form"]] = f["meaning"]
    for spec, (mechanism, sort) in EXPECTED_SORTS.items():
        meaning = read[formed(spec, LANG)]
        assert (meaning["mechanism"], meaning["sort"]) == (mechanism, sort), spec
    burn = read[formed("burn~memory", LANG)]
    assert burn["definition"] == "[be on fire], with [the store an agent keeps records in] " \
                                 "as its undergoer"
    listed = LANG.entries[entry("budget burn")]
    assert listed["definition"] != listed["composition"] and listed["route"] == "drift"


def test_a_formations_sort_gives_its_situation_its_aspect():
    """A situation whose predicate is an unlisted formation takes the lexical aspect of
    the sort its parts give, as one headed by a root does."""
    normal = [PRINT.move(n) for n in written("e4-formations", 1).normal]
    assert " PERFECTIVE " in normal[0] and " STATIVE " in normal[1]
    assert " PROGRESSIVE " in normal[2]


SUFFIX_KEYS = sorted(it.name for it in LANG.suffixes.values())
STEM_ROOTS = sorted(i for i, e in LANG.entries.items()
                    if e["grammatical category"] in ("predicate root", "nominal root"))


def skeleton(morphemes):
    """The structure the rules of formation give a word, from its morphemes and the
    words the release lists alone: each stem a chain of suffixes on its first morpheme,
    the stems joined left to right, and a listed prefix standing as its entry. A reader
    that took the word for another listed word would give another structure."""
    def listed(form):
        item = LANG.by_form.get(form)
        return item.identifier if item is not None and item.kind in ("root", "derivation") \
            else None
    stems, cur = [], []
    for m in morphemes:
        if m == "linker":
            stems.append(cur)
            cur = []
        else:
            cur.append(m)
    stems.append(cur)

    def stem(ms):
        shape, form = None, ""
        for i, m in enumerate(ms):
            form += m.form
            shape = ("entry", m.identifier) if i == 0 else (m.name, shape)
            shape = ("entry", listed(form)) if listed(form) else shape
        return shape
    shape, form = stem(stems[0]), "".join(m.form for m in stems[0])
    for s in stems[1:]:
        shape = ("compound", shape, stem(s))
        form += "i" + "".join(m.form for m in s)
        shape = ("entry", listed(form)) if listed(form) else shape
    return shape


def shape_of(meaning):
    if "mechanism" not in meaning:
        return ("entry", meaning["entry"])
    if meaning["mechanism"] == "compound":
        return ("compound", shape_of(meaning["parts"][0]), shape_of(meaning["parts"][1]))
    return (meaning["mechanism"], shape_of(meaning["parts"][0]))


@functools.lru_cache(maxsize=None)
def means(form):
    """Whether every step of the formation the reader segments `form` into has a meaning."""
    morphemes = segment(form, LANG)
    return morphemes is not None and formation.compose(morphemes, LANG) is not None


@st.composite
def formations(draw):
    """A content word of one to three stems, each a root with up to two suffixes, every
    step of whose formation has a meaning: each stem is drawn from those the word built so
    far takes, and each suffix from those that take the stem built so far, so that no
    example is discarded for a step without one (the strategy that drew freely and then
    discarded such words failed Hypothesis's health check once). The heads of the listed
    compounds come often, so that an unlisted compound resembling a listed one is
    drawn."""
    burn = entry("burn")
    suffix = {it.name: f for f, it in LANG.suffixes.items()}
    form = ""
    for i in range(draw(st.integers(1, 3))):
        joined = form + "i" if form else ""
        roots = [r for r in STEM_ROOTS if means(joined + LANG.items[r].form)]
        if not roots:
            break
        root = burn if i == 0 and draw(st.booleans()) else draw(st.sampled_from(roots))
        form = joined + LANG.items[root].form
        for _ in range(draw(st.integers(0, 2))):
            taken = [k for k in SUFFIX_KEYS if means(form + suffix[k])]
            if not taken:
                break
            form += suffix[draw(st.sampled_from(taken))]
    return form


@PROFILE
@given(formations())
def test_every_unlisted_formation_means_the_composition_of_its_parts(form):
    """Every generated formation the release does not list is read as the composition
    its mechanisms define over its parts, a listed part standing as its entry, and as
    nothing else (`inv.word-formation`); the reader of a message gives it that meaning."""
    assume(LANG.by_form.get(form) is None)
    morphemes = segment(form, LANG)
    assert morphemes is not None
    meaning = formation.compose(morphemes, LANG)
    assert meaning is not None
    assert shape_of(meaning) == skeleton(morphemes)
    t = READ.moves("(move ASSERTED-POSITION (assertion OBSERVATION (situation detect (ACTOR "
                   "(term SELF)) (UNDERGOER (term (unknown \"%s\"))))))" % form)
    a = api.parse(GEN.message(t))
    assert [f["meaning"] for f in a.formations] == [meaning]


def test_formations_read_alike_in_both_implementations():
    """Whether agents interpret new derivations and compounds from their parts: two
    readers written apart, the Python and the TypeScript implementations, give every one
    of 300 generated formations the same meaning."""
    from rowih import parity
    rnd = random.Random(39)
    suffix = sorted(LANG.suffixes)
    texts = []
    while len(texts) < 300:
        stems = ["".join([LANG.items[rnd.choice(STEM_ROOTS)].form]
                         + rnd.sample(suffix, rnd.randint(0, 2)))
                 for _ in range(rnd.randint(1, 3))]
        form = "i".join(stems)
        if LANG.by_form.get(form) is None:
            texts.append(GEN.message(READ.moves(
                "(move ASSERTED-POSITION (assertion OBSERVATION (situation detect (UNDERGOER "
                "(term (unknown \"%s\"))))))" % form)))
    try:
        assert parity.compare_implementations(texts) == []
    except parity.ParityUnavailable as e:
        pytest.skip(str(e))


# ---------------------------------------------------------------- definitions

def definition(word, expansion="(term fault-record)"):
    return READ.moves('(move SETTING DEFINITION SPEAKERS-OWN (term (data "text/prs.rowih" '
                      '"%s")) %s)' % (word, expansion))


def distance_verdict(word):
    """Whether a defined word may be confused with a word in scope, computed apart from
    the checker: within one edit of any word of the release, or two of a critical one."""
    for form, item in LANG.by_form.items():
        limit = 3 if (item.critical_code or item.protected) else 2
        if lc.levenshtein(word, form) < limit:
            return True
    return False


ROOT_SHAPED = ["r" + "".join(p) for p in itertools.product(
    LANG.vowels, LANG.consonants, LANG.vowels, LANG.consonants)]


@PROFILE
@given(st.sampled_from(ROOT_SHAPED))
def test_a_definition_is_refused_exactly_when_its_term_is_in_scope_or_confusable(word):
    """Every definition of a root-shaped word is refused as shadowing a word of the
    release, or as confusable with any word in scope whatever its class, exactly when a
    distance computed over every word says so (`inv.core-closed`)."""
    codes = [d.code for d in api.parse(GEN.message(definition(word))).diagnostics]
    if word in LANG.by_form:
        assert codes == ["d.checker.definition-shadows"]
    else:
        assert ("d.checker.definition-confusable" in codes) == distance_verdict(word)


def test_the_confusable_term_of_the_negative_corpus_is_near_another_class():
    """The negative item's term is one edit from a move check word, not from a root, so
    that a check comparing a term only with its own class misses it."""
    near = confusable("rapek", LANG)
    assert LANG.by_form[near].kind == "move-check"
    assert not any(lc.levenshtein("rapek", f) < 2 for f, it in LANG.by_form.items()
                   if it.kind == "root")


def test_a_precision_bound_use_of_a_defined_term_is_written_expanded():
    """A defined term is unknown to the release, so a precision-bound move must write
    its expansion where it would use it, and the normal form holds the expansion
    (`inv.core-closed`)."""
    bare = READ.moves('(move ISSUE REQUEST SPEAKERS-OWN (situation store (ACTOR (term '
                      '(party 2))) (UNDERGOER (term (unknown "rapeb")))))')
    codes = [d.code for d in api.parse(GEN.message(bare)).diagnostics]
    assert "d.checker.unknown-in-precision-bound" in codes
    a = written("e4-definition", 5)
    assert a.diagnostics == [] and "fault-record" in PRINT.move(a.normal[0])


def test_a_definition_does_not_reach_a_message_sent_before_it():
    """A use of the word in a message sent before the definition stays unknown
    vocabulary, since the meaning of a message is fixed by the definitions in force at
    its communication time (specification/discourse.md#definitions)."""
    view = View("2")
    earlier = READ.moves('(move ASSERTED-POSITION (assertion OBSERVATION (situation store '
                         '(UNDERGOER (term (unknown "rapeb"))))))')
    view.hear(GEN.message(earlier, time="1759622400"))
    view.hear(GEN.message(definition("rapeb"), time="1759622460", identifier=2,
                          first_entry=2))
    terms = structure(view)["exchange"]["terms"]
    assert [(t["term"], t["uses"]) for t in terms] == [("rapeb", [])]


def test_definition_checks_read_every_constituent_order():
    """The defined term is found by its form, not its place, so a definition written
    expansion first is the same definition."""
    swapped = definition("rapeb")
    swapped[0]["constituents"].reverse()
    assert api.parse(GEN.message(swapped)).diagnostics == []
    assert root_shaped("rapeb", LANG) and not root_shaped("hapeb", LANG)


# ---------------------------------------------------------------- lexicon 1.0's suffixes
# and productive patterns

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SUFFIX = {e["key"]: e for e in LANG.entries.values()
          if e["grammatical category"] == "derivational suffix"}


def derived(root_key, suffix_key):
    return formation.derive(formation.of_entry(LANG.entries[entry(root_key)]),
                            SUFFIX[suffix_key])


def roles(meaning):
    return [(a["role"], a["sort"]) for a in meaning["arguments"]]


def test_the_suffixes_of_lexicon_1_0_have_the_roles_they_state():
    """The causative adds the actor that brings its base about and keeps the base's other
    roles; the reversative and the repetitive keep their base's roles; the potential takes
    its base's undergoer, and refuses a base without one; a place noun has none."""
    assert roles(derived("run", "causative")) == [("actor", "s.sort.agent"),
                                                   ("undergoer", "s.sort.referent")]
    assert derived("run", "causative")["sort"] == "s.sort.event"
    assert roles(derived("encode", "reversative")) == roles(
        formation.of_entry(LANG.entries[entry("encode")]))
    assert roles(derived("send", "repetitive")) == roles(
        formation.of_entry(LANG.entries[entry("send")]))
    assert roles(derived("read", "potential")) == [("undergoer", "s.sort.referent")]
    assert derived("assent", "potential") is None
    assert derived("store", "place")["sort"] == "s.sort.place"
    assert roles(derived("store", "place")) == []


def test_a_causative_that_keeps_its_base_actor_is_found(monkeypatch):
    """Planted: a causative read with its entry's roles alone loses the base's undergoer,
    which the test of the suffixes' roles finds."""
    monkeypatch.setattr(formation, "ADDS_ACTOR", ())
    assert roles(derived("run", "causative")) != [("actor", "s.sort.agent"),
                                                   ("undergoer", "s.sort.referent")]


with open(os.path.join(ROOT, "lexicon", "patterns", "1.0.json"), encoding="utf-8") as f:
    PATTERNS = json.load(f)


def test_the_productive_patterns_number_119():
    """Eighteen suffixes, three functions of compounding and 98 formations of one suffix
    on another; the combinations the rules admit that make no pattern are each excluded
    with its reason (specification/lexicon.md#the-productive-patterns)."""
    patterns = PATTERNS["patterns"]
    assert len(patterns) == 119
    assert collections.Counter(len(p["mechanisms"]) for p in patterns) == {1: 21, 2: 98}
    assert len(PATTERNS["excluded"]) == 38 and all(x["reason"] for x in PATTERNS["excluded"])


def test_every_admitted_combination_is_a_pattern_or_excluded():
    """Over every root, each formation of one suffix on another that the rules give a
    meaning is listed, as a pattern or as excluded, and nothing else is."""
    stems = [e for e in LANG.entries.values() if e["grammatical category"] in (
        "predicate root", "nominal root") and "synonym of" not in e]
    admitted = set()
    for e in stems:
        base = formation.of_entry(e)
        for a in SUFFIX.values():
            first = formation.derive(base, a)
            if first is None:
                continue
            for b in SUFFIX.values():
                if formation.derive(first, b) is not None:
                    admitted.add((a["key"], b["key"]))
    listed = {tuple(p["mechanisms"]) for p in PATTERNS["patterns"]
              if len(p["mechanisms"]) == 2} | {tuple(x["mechanisms"])
                                               for x in PATTERNS["excluded"]}
    assert listed == admitted


def test_every_pattern_example_reads_as_its_pattern_states():
    """Each pattern's example is a word no release lists, which the reader segments into
    the pattern's mechanisms and gives the meaning the pattern states."""
    for p in PATTERNS["patterns"]:
        example = p["example"]
        assert LANG.by_form.get(example["form"]) is None, p["identifier"]
        meaning = formation.compose(segment(example["form"], LANG), LANG)
        assert meaning["definition"] == example["definition"], p["identifier"]
        assert meaning["sort"] == p["gives"]
        assert [a["role"] for a in meaning["arguments"]] == example["roles"]
        steps, m = [], meaning
        while "mechanism" in m:
            steps.append(m["mechanism"])
            m = m["parts"][0]
        assert list(reversed(steps)) == p["mechanisms"], p["identifier"]


def test_the_pattern_examples_read_alike_in_both_implementations():
    """The examples of the productive patterns, each a word neither implementation lists,
    give the same records in the Python and the TypeScript readers."""
    from rowih import parity
    texts = [GEN.message(READ.moves(
        "(move ASSERTED-POSITION (assertion OBSERVATION (situation detect (UNDERGOER "
        "(term (unknown \"%s\"))))))" % p["example"]["form"])) for p in PATTERNS["patterns"]]
    try:
        assert parity.compare_implementations(texts) == []
    except parity.ParityUnavailable as e:
        pytest.skip(str(e))
