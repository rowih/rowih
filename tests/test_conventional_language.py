"""The conventional language of version 1.0
(specification/lexicon.md#conventional-expressions-and-idioms): the formulas that with the
act words of release 0.3 make the conventional expressions, the idioms, and the mappings
and conventional senses that motivate the figurative ones. Lexicon 1.0's suffixes and
productive patterns are `test_formation.py`'s."""
import collections
import copy
import re

import pytest

from rowih import api, data, idioms, lexicon_checks as lc
from rowih.economy import economy
from rowih.generator import Generator
from rowih.notation import Reader

LANG = data.load()
GEN = Generator(LANG)
READ = Reader(LANG)
FILL = "(term record DEFINITE)"
REGISTER = {"R1": "PROTOCOL", "R2": "STANDARD", "R3": "EXPLANATORY", "R4": "FORMAL",
            "R5": "CASUAL", "R6": "PLAYFUL", "R7": "CEREMONIAL"}
# the kinds of conventional expression other than transitions, which are the discourse
# relation words, and the kinds of idiom
FORMULA_KINDS = ["greeting", "acknowledgements", "confirmations", "thanks", "apologies",
            "requests for clarification", "warnings", "agreement", "disagreement",
            "uncertainty", "closure", "conversational repair"]
IDIOM_KINDS = ["conversational idioms", "agentic idioms", "computational idioms",
            "epistemic idioms", "negotiation idioms", "metaphorical expressions",
            "humorous expressions", "compressed expressions"]
ACTS = [i for i, e in LANG.entries.items() if e["grammatical category"] == "act word"]
FORMULAS = [i for i in LANG.idioms if LANG.entries[i]["route"] == "formula"]
IDIOMS = [i for i in LANG.idioms if LANG.entries[i]["route"] != "formula"]
NEW = [i for i in LANG.idioms if LANG.entries[i]["version"]["introduced"] == "1.0"]
GRAMMATICAL = [i for i in NEW if not isinstance(LANG.entries[i]["literal structure"], list)]
RELICS = [i for i in NEW if isinstance(LANG.entries[i]["literal structure"], list)]


def entry(key):
    return next(i for i, e in LANG.entries.items() if e.get("key") == key)


def key_of(ident):
    return LANG.entries[ident]["key"]


# ---------------------------------------------------------------- the counts

def test_the_conventional_expressions_number_201_and_the_idioms_101():
    """The act words and the formulas are the conventional expressions, encoding idioms
    whose conventionality is what must be learned; the idioms are decoding idioms, each
    reached by a route other than the formula
    (specification/lexicon.md#conventional-expressions-and-idioms). Version 1.0 adds no
    act word."""
    assert len(ACTS) == 25
    assert len(ACTS) + len(FORMULAS) == 201
    assert len(IDIOMS) == 101
    assert all(LANG.entries[i]["kind"] == "encoding, grammatical" for i in FORMULAS)
    for i in IDIOMS:
        e = LANG.entries[i]
        assert e["kind"].startswith("decoding, ") and e["class"] in IDIOM_KINDS, e["key"]
        assert e["route"] in ("figure", "compression", "allusion", "drift"), e["key"]


def test_every_kind_of_formula_and_idiom_is_stocked():
    """Each kind of conventional expression has several formulas, besides the act words
    that answer four of them, and each kind of idiom several idioms; the other kinds of
    conventional expression are the recurring functions of agents' exchanges that the list
    of kinds does not close."""
    by_class = collections.Counter(LANG.entries[i]["class"] for i in LANG.idioms)
    for kind in FORMULA_KINDS:
        assert by_class[kind] >= 3, kind
    for kind in IDIOM_KINDS:
        assert by_class[kind] >= 7, kind
    others = {LANG.entries[i]["class"] for i in FORMULAS} - set(FORMULA_KINDS)
    assert others == {"status reports", "requests for status", "offers", "praise",
                      "encouragement", "reminders", "turn-taking", "refusals",
                      "congratulations", "well-wishing", "sympathy", "invitations",
                      "requests for permission"}


# ---------------------------------------------------------------- reading and writing

def _head(e):
    question = re.search(r"\b(POLAR|CONSTITUENT|ALTERNATIVE)\b", e["expansion"])
    return "ACT-QUESTION" if question else "ASSERTED-POSITION"


def _move(e, unit):
    """A move holding `unit` where the entry's expansion may stand, in a register the
    entry lists and whose modes admit it."""
    mode = "normal expression" if e["route"] == "formula" else "idiom"
    usable = [r for r in e["register"] if r in REGISTER and (
        mode == "normal expression" or r in ("R2", "R5", "R6", "R7"))]
    code = "R2" if "R2" in usable else usable[0]
    head = _head(e)
    body = unit if head == "ACT-QUESTION" else "(assertion INTROSPECTION CERTAIN %s)" % unit
    return "(move %s %s %s)" % (head, REGISTER[code], body), mode


@pytest.mark.parametrize("ident", GRAMMATICAL, ids=[key_of(i) for i in GRAMMATICAL])
def test_every_grammatical_idiom_is_read_by_its_entry(ident):
    """Written with the idiom mark and its slots filled, the literal structure selects its
    entry, and the move normalises to the bytes of the same move written with the
    expansion (`inv.realisations-normalise`)."""
    e = LANG.entries[ident]
    literal = re.sub(r"\(slot \d+\)", FILL, e["literal structure"]).replace(
        "(situation ", "(situation IDIOM-ENTRY ", 1)
    expansion = re.sub(r"\(slot \d+\)", FILL, e["expansion"])
    marked, _ = _move(e, literal)
    written, _ = _move(e, expansion)
    a = api.parse(GEN.message(READ.moves(marked), "as written"))
    b = api.parse(GEN.message(READ.moves(written), "full explicitness"))
    assert a.diagnostics == [] and b.diagnostics == []
    assert a.social[0]["idioms"] == [ident]
    assert a.normal_text == b.normal_text


@pytest.mark.parametrize("ident", RELICS, ids=[key_of(i) for i in RELICS])
def test_every_doubled_root_is_recognised_by_its_words(ident):
    """A doubled root stands where no production admits its first word, so its words
    select the entry without a mark, and the move normalises as its expansion does."""
    e = LANG.entries[ident]
    marked, _ = _move(e, "(idiom %s)" % e["key"].replace(" ", "-"))
    written, _ = _move(e, e["expansion"])
    a = api.parse(GEN.message(READ.moves(marked), "as written"))
    b = api.parse(GEN.message(READ.moves(written), "full explicitness"))
    assert a.diagnostics == [] and a.social[0]["idioms"] == [ident]
    assert a.normal_text == b.normal_text


def test_the_generator_writes_a_formula_of_lexicon_1_0():
    """Normal expression admits the formulas, and the generator writes the greeting of
    first contact for the meaning it expands to."""
    e = LANG.entries[entry("address appearing")]
    move, mode = _move(e, e["expansion"])
    t = economy(READ.moves(move)[0], LANG, mode)
    a = api.parse(GEN.message([t], "as written"))
    assert a.social[0]["idioms"] == [entry("address appearing")]
    assert a.normal == api.parse(GEN.message(READ.moves(move), "full explicitness")).normal


# ---------------------------------------------------------------- the release's checks

def test_the_release_passes_its_checks():
    assert lc.check_release(LANG) == []


def test_an_idiom_filling_a_role_its_root_lacks_is_found(monkeypatch):
    """From lexicon 1.0 an idiom's literal structure and expansion fill only the roles the
    entries their words are read as take; planted as the greeting of first contact with
    a content its root, *appear*, does not take."""
    original = idioms.literal
    planted = READ.node(["situation", "appear", ["UNDERGOER", ["term", "address", "NEW"]],
                         ["CONTENT", ["term", "network"]]])

    def literal(lang, ident):
        if ident == entry("address appearing"):
            return copy.deepcopy(planted)
        return original(lang, ident)
    monkeypatch.setattr(idioms, "literal", literal)
    found = [x for code, x in lc.check_idioms(LANG) if code == "idiom-role-not-taken"]
    assert found == ["%s appear content" % entry("address appearing")]


def test_released_idioms_are_held_to_the_rules_of_their_release():
    """The two entries of release 0.3 that fill a role their root lacks predate the rule
    and are kept as released """
    lang = copy.copy(LANG)
    old = {i for i in LANG.idioms if LANG.entries[i]["version"]["introduced"] == "0.3"}
    assert {key_of(i) for i in old if lc._roles_not_taken(
        LANG, idioms.literal(LANG, i))} == {"damaged arrival", "taken from the air"}
    assert lc.check_idioms(lang) == []


def test_a_figure_without_a_mapping_is_found():
    """From lexicon 1.0 every idiom whose route is a figure is motivated by a mapping; the
    joke of release 0.3 rests on none."""
    lang = copy.copy(LANG)
    lang.mappings = copy.deepcopy(LANG.mappings)
    sky = next(m for m in lang.mappings.values()
               if m["name"] == "THE STATE OF AN EXCHANGE IS THE SKY ABOVE IT")
    sky["motivates"].remove(entry("rain falling"))
    assert ("figure-without-mapping", entry("rain falling")) in lc.check_senses(lang)
    assert ("figure-without-mapping", entry("memory deleting memory")) not in \
        lc.check_senses(lang)


# ---------------------------------------------------------------- senses and mappings

SITUATION_SORTS = ("s.sort.situation", "s.sort.proposition", "s.sort.event",
                   "s.sort.state", "s.sort.process")


def test_no_sense_of_lexicon_1_0_takes_a_frame_its_root_reads_literally():
    """Each new sense's frame names a role its root's basic sense lacks, or fills one with
    a kind of constituent the root's role does not take, so that no well-sorted literal
    use of the root is read in the sense."""
    new = [e for e in LANG.entries.values() if e["grammatical category"] ==
           "conventional sense" and e["version"]["introduced"] == "1.0"]
    assert len(new) == 10
    for e in new:
        root = LANG.entries[e["sense of"]]
        basic = {a["role"]: a["sort"] for a in root["argument structure"]}
        role = e["frame"]["role"].rsplit(".", 1)[1]
        if role in basic:
            assert (e["frame"]["filler"] == "situation") != (basic[role] in SITUATION_SORTS)


def test_every_figurative_idiom_of_lexicon_1_0_has_one_mapping():
    motivating = collections.Counter(t for m in LANG.mappings.values() for t in m["motivates"])
    for i in NEW:
        if LANG.entries[i]["route"] == "figure":
            assert motivating[i] == 1, key_of(i)
    new = [m for m in LANG.mappings.values() if m["version"]["introduced"] == "1.0"]
    assert len(new) == 20 and all(m["motivates"] for m in new)
    # release 0.5's mappings are what they were, and that release reads none of these
    assert len(data.load("0.5").mappings) == 9
