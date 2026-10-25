"""The explanation in English (specification/meaning.md#the-english-explanation):
generated from the normal form, it says each unit's predicate and participants and every
value the normal form holds that is not the default the normaliser supplies there, so that
what a speaker leaves to a default is left unsaid and nothing stated is dropped."""
import glob
import os
import re

from rowih import api, data, normal
from rowih.checker import entry_kind, short
from rowih.english import English
from rowih.figure_rules import RELATION
from rowih.generator import Generator
from rowih.notation import Reader

from corpus import ROOT

GEN = Generator()
READ = Reader(GEN.lang)
LANG = data.load()
WORLD = "g.situations-and-contents.world-of-evaluation"
FIGURE = "g.ambiguity-and-figures.figurative-type."


def lines(notation: str, sender: int = 1) -> list:
    text = GEN.message(READ.moves(notation), sender=sender, recipients=(3 - sender,),
                       identifier=1, first_entry=1, time="1759622400")
    a = api.parse(text)
    assert a.diagnostics == []
    english = English(LANG, str(sender))
    return [english.move(n) for n in a.normal]


def test_a_structural_relation_is_the_predicate_and_a_quantifier_is_said():
    line, = lines("(move ASSERTED-POSITION (assertion TRAINED-KNOWLEDGE CERTAIN (situation "
                  "MEMBER-OF (UNDERGOER (term gas UNIVERSAL)) (CONTENT (term matter "
                  "GENERIC)))))")
    assert line == "Agent 1 asserts that every gas member of matter (generic) " \
                   "(trained knowledge; certain)."


def test_a_quotation_within_a_term_is_said_in_its_words():
    box, service = (LANG.form_of(next(i for i, e in LANG.entries.items() if e["key"] == w
                                      and e["grammatical category"].endswith("root")))
                    for w in ("box", "service"))
    line, = lines("(move ASSERTED-POSITION (assertion TRAINED-KNOWLEDGE CERTAIN (situation "
                  "correspond (UNDERGOER (term word (quote \"%s\") DEFINITE)) (CONTENT (term "
                  "word (quote \"%s\") DEFINITE)))))" % (box, service))
    assert line == "Agent 1 asserts that correspond the word “%s” (box) that the word " \
                   "“%s” (service) (trained knowledge; certain)." % (box, service)


def test_a_numeric_strength_keeps_its_comparator():
    line, = lines("(move ASSERTED-POSITION (assertion INFERENCE (q APPROXIMATELY 0.6) "
                  "(situation break PERFECTIVE (ACTOR (term storm DEFINITE)) (UNDERGOER (term "
                  "bridge DEFINITE)))))")
    assert line == "Agent 1 asserts that the storm break the bridge (inference; with " \
                   "strength approximately 0.6)."


def test_a_moves_discourse_relation_is_said():
    line, = lines("(move ASSERTED-POSITION NONE (names 1 1 ASSERTED-POSITION "
                  "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE) contrasts (assertion RETRIEVAL "
                  "CERTAIN (situation remember (ACTOR (term SELF)) (CONTENT (situation possess "
                  "(HOLDER (term SELF)) (UNDERGOER (term map DEFINITE)))))))", sender=2)
    assert "(relation: contrasts)" in line


def test_an_aspect_other_than_the_roots_own_is_said():
    finishing, = lines("(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
                       "IDIOM-ENTRY approach (UNDERGOER (term SELF)) (CONTENT (term end)))))")
    assert finishing == "Agent 1 asserts that me work (completive) (introspection; certain)."
    # the event's own aspect, written or not, is the default and is left unsaid
    for aspect in (" PERFECTIVE", ""):
        line, = lines("(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
                      "break%s (UNDERGOER (term bridge DEFINITE)))))" % aspect)
        assert line == "Agent 1 asserts that break the bridge (observation; certain)."


def test_a_world_is_said_where_it_is_written_and_not_again_inside_it():
    line, = lines("(move ASSERTED-POSITION (assertion SIMULATION CERTAIN "
                  "(situation happy WITHIN-A-FICTION (HOLDER (term house DEFINITE)) (CONTENT "
                  "(situation defend (ACTOR (term dog DEFINITE)) (UNDERGOER (term house "
                  "DEFINITE)))))))")
    assert line.count("(within a fiction)") == 1


def test_the_reading_of_a_collective_is_said():
    line, = lines("(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation work "
                  "(ACTOR (term INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)))))")
    assert "inclusive collective (joint) work" in line


# ---------------------------------------------------------------- over the corpus

def stated(n: dict, lang) -> list:
    """Every value of a move's normal form that is not the default the normaliser supplies
    where it stands, read with the normaliser's own rules: the world each situation passes
    to its contents, the existence a figure's source mentions, a root's aspect and a
    referent's discourse status."""
    out = []

    def walk(t: dict, world: str, mentioned: bool):
        parts = t.get("parts", [])
        if t["kind"] in ("assertion", "situation", "term") and any(
                p["kind"] == "value" and p["member"].startswith(FIGURE) for p in parts):
            mentioned = True
        if t["kind"] == "situation":
            inner = short(next(p["member"] for p in parts if p["kind"] == "value"
                               and p["member"].startswith(WORLD + ".")))
        else:
            inner = world
        for p in parts:
            if p["kind"] == "value" and not default(p["member"], t, world, mentioned, lang):
                out.append(p["member"])
            elif p["kind"] == "filler" and isinstance(p["filler"], dict):
                walk(p["filler"], inner, mentioned and not p["role"].startswith(RELATION))
            elif p["kind"] in ("assertion", "situation", "term"):
                walk(p, inner, mentioned)
            elif p["kind"] == "readings":
                for r in p["readings"]:
                    walk(r, inner, mentioned)
        for r in t.get("readings", []):
            walk(r, world, mentioned)

    world = normal.starting_world(entry_kind(n["adds"])[0])
    for c in n["constituents"] + ([n["authority_term"]] if n.get("authority_term") else []):
        walk(c, world, False)
    return out


def default(member: str, t: dict, world: str, mentioned: bool, lang) -> bool:
    cls, value = member.rsplit(".", 1)
    status = lang.classes[cls]["status"]
    if "default member" in status:
        return member == status["default member"]
    parts = t["parts"]
    return value == {
        "g.situations-and-contents.aspect": lambda: normal.lexical_aspect(parts, lang),
        WORLD: lambda: world,
        "g.reference.existence-commitment": lambda: normal.default_existence(world, mentioned),
        "g.reference.discourse-status": lambda: normal.default_discourse_status(parts),
    }.get(cls, lambda: None)()


def said(english: English, member: str, line: str) -> bool:
    word = english.value_word(member)
    return re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(word), line) is not None


def test_every_value_not_left_to_a_default_is_said_over_the_corpus():
    """Each message is read under the releases it names, as `tools/gloss_corpus.py` reads
    it, and every value its normal form holds beyond the defaults is found in its line."""
    languages, unsaid, checked, paths = {}, [], 0, 0
    files = sorted(p for s in ("conformance", "attitudes", "adversarial", "domains")
                   for p in glob.glob(os.path.join(ROOT, "corpus", s, "*.txt")))
    for path in files:
        with open(path, encoding="utf-8") as f:
            a = api.parse(f.read())
        if a.message is None:
            continue
        paths += 1
        u = a.read_under
        key = (u["version"], u["language"], tuple(u["dialects"])) if "version" in u else ()
        if key not in languages:
            languages[key] = data.load(*key)
        english = English(languages[key], a.message.envelope.sender.text)
        for n in a.normal:
            line = english.move(n)
            assert "  " not in line and "( " not in line and " )" not in line, line
            for member in stated(n, languages[key]):
                checked += 1
                if not said(english, member, line):
                    unsaid.append((os.path.basename(path), member, line))
    assert paths == len(files) > 2000 and checked > 10000 and unsaid == []
