"""Figures (specification/meaning.md#figures): each figure's relation fitted to its type,
what a speaker answers for through a figure, the conventional figurative senses with the
mappings that motivate them, the items F1 to F9 with F2 and F7 in place of domain item D6,
and the mechanisms and kinds of text of figures."""
import copy
import json
import os

import pytest
from hypothesis import HealthCheck, given, settings

from rowih import api, data, figures, lexicon_checks as lc, senses
from rowih.english import English
from rowih.figure_rules import RELATION, figure_type
from rowih.generator import Generator
from rowih.notation import NotationError, Printer, Reader, sexp
from rowih.view import View

from corpus import ROOT, items, messages
from test_properties import variants

LANG = data.load()
GEN = Generator(LANG)
READ = Reader(LANG)
PRINT = Printer(LANG)
MESSAGES = messages()
TEXTS = {(i, k): t for i, k, _, t in MESSAGES}
FIGURE = "g.ambiguity-and-figures.figurative-type."
PROFILE = settings(max_examples=120, deadline=None,
                   suppress_health_check=[HealthCheck.too_slow])


def entry(key):
    return next(i for i, e in LANG.entries.items() if e["key"] == key)


def written(item_id, k):
    a = api.parse(TEXTS[(item_id, k)])
    assert a.diagnostics == [], [d.as_text() for d in a.diagnostics]
    return a


def answers(item_id, k, move=0):
    return [PRINT.node(x) for x in figures.answers_for(
        written(item_id, k).normal[move]["constituents"], LANG)]


def mentions(item_id, k, move=0):
    return [PRINT.node(x) for x in figures.sources(
        written(item_id, k).normal[move]["constituents"])]


def message(notation, sender=1, recipients=(2,)):
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from build_corpus import substitute
    return GEN.message(READ.moves(substitute(notation, LANG)), "as written", sender,
                       list(recipients), "1759622400", 1, integrity=True)


def codes(notation):
    return [d.code for d in api.parse(message(notation)).diagnostics]


def walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from walk(v)
    elif isinstance(node, list):
        for x in node:
            yield from walk(x)


SUITE = '(term (formed "record~examine") DEFINITE)'
UNAVAILABLE = ("(situation capable POLARITY.NEGATIVE (HOLDER (term INCLUSIVE-COLLECTIVE "
               "READING-OF-A-COLLECTIVE.DISTRIBUTIVE)) (CONTENT (situation use (ACTOR (term "
               "INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.DISTRIBUTIVE)) (INSTRUMENT %s))))"
               % SUITE)


# ---------------------------------------------------------------- the theory's items

def test_f1_a_conventional_sense_is_read_unmarked_in_its_frame():
    """The lexicon lists the conventional sense apart from the basic one, with the mapping
    that motivates it, and a speaker who uses it unmarked, in a precision-bound move too,
    answers for the conventional sense."""
    take, understand = entry("take"), entry("understand")
    assert LANG.senses[take] == [understand]
    sense = LANG.entries[understand]
    assert sense["orthographic form"] == LANG.entries[take]["orthographic form"]
    assert sense["sort"] == LANG.entries[take]["sort"] and sense["definition"] != \
        LANG.entries[take]["definition"]
    mapping = LANG.mappings[sense["motivating mapping"]]
    assert mapping["name"] == "IDEAS ARE OBJECTS" and understand in mapping["motivates"]
    assert sense["constructed history"].startswith("Constructed history: ")
    assert "(situation understand" in answers("e6-conventional-senses", 1)[0]
    bound = written("e6-conventional-senses", 2)
    assert bound.classes[0]["operative"]
    assert answers("e6-conventional-senses", 2)[0].startswith("(situation settle")
    assert "(term burst" in answers("e6-conventional-senses", 3)[0]
    # the normal form writes the word as the speaker wrote it: the frame selects the sense
    assert "(situation take" in PRINT.move(written("e6-conventional-senses", 1).normal[0])


def test_f2_the_figure_states_its_content_and_answers_for_it():
    """The mark stays in what the hearer records, the source is mentioned and not
    asserted, and the target content stated in the same move is what the speaker
    answers for: the same content as the literal statement of it, so that one
    proposition is expressed literally and as a figure (requirement `creative.modes`)."""
    a = written("d06-metaphor-with-content", 1)
    normal = PRINT.move(a.normal[0])
    assert "METAPHOR" in normal and "TARGET-CONTENT" in normal
    source = normal[normal.index("confine"):normal.index("TARGET-CONTENT")]
    assert "MENTIONED-WITHOUT-EXISTENCE-ASSERTED" in source
    assert "ASSERTED-TO-EXIST" not in source.replace("WITHOUT-EXISTENCE-ASSERTED", "")
    view = View("2")
    view.receive(a)
    view.receive(written("d06-metaphor-with-content", 2))
    held = PRINT.node(view.said(("1", "1"))[0])
    assert "METAPHOR" in held and "TARGET-CONTENT" in held
    assert answers("d06-metaphor-with-content", 1) == answers("d06-metaphor-with-content", 2)
    assert view.answers_for(("1", "1")) == view.answers_for(("1", "2"))
    assert [m.split()[1] for m in mentions("d06-metaphor-with-content", 1)] == ["confine"]


def test_f3_correspondences_are_literal_with_the_word_of_correspondence():
    """Each correspondence pairs an element of the source, mentioned, with an element of
    the target, in an elaboration naming the figure."""
    a = written("e6-correspondences", 2)
    t = a.normal[0]
    assert t["named"]["author"] == "1" and t["named"]["number"] == "1"
    pairs = [u for u in walk(t["constituents"]) if u.get("kind") == "situation"
             and senses.head_word(u) and senses.head_word(u)["entry"] == entry("correspond")]
    assert len(pairs) == 2
    for u in pairs:
        roles = {p["role"].rsplit(".", 1)[-1]: p["filler"] for p in u["parts"]
                 if p["kind"] == "filler"}
        source = PRINT.node(roles["content"])
        assert "MENTIONED-WITHOUT-EXISTENCE-ASSERTED" in source
        assert "ASSERTED-TO-EXIST" in PRINT.node(roles["undergoer"]).replace(
            "WITHOUT-EXISTENCE-ASSERTED", "")
    assert figures.sources(t["constituents"]) == []


def test_f4_an_analogy_asserts_a_relation_of_relations_literally():
    a = written("e6-analogy", 1)
    t = a.normal[0]
    analogy = next(u for u in walk(t["constituents"]) if u.get("kind") == "situation"
                   and senses.head_word(u)
                   and senses.head_word(u)["entry"] == entry("analogous"))
    fillers = [p["filler"] for p in analogy["parts"] if p["kind"] == "filler"]
    assert [f["kind"] for f in fillers] == ["situation", "situation"]
    assert all(senses.head_word(f)["entry"] == entry("cause") for f in fillers)
    assert figures.answers_for(t["constituents"], LANG) == t["constituents"]


def test_f5_a_metonym_states_what_it_stands_for():
    """The mark stands on the term, the rest of the move is literal, and the speaker
    answers for the predication about the referent the term stands for, which the normal
    form writes as asserted; in a precision-bound request the referent is required."""
    normal = PRINT.move(written("e6-metonymy", 1).normal[0])
    referent = normal[normal.index("STANDS-FOR"):]
    assert "ASSERTED-TO-EXIST GIVEN (party 3)" in referent
    assert "(ACTOR (term ASSERTED-TO-EXIST GIVEN (party 3)))" in answers("e6-metonymy", 1)[0]
    request = written("e6-metonymy", 2)
    assert request.classes[0]["pending"]
    assert "(RECIPIENT (term ASSERTED-TO-EXIST GIVEN (party 3)))" in \
        answers("e6-metonymy", 2)[0]


def test_f6_the_mark_is_scoped_to_its_constituent():
    """The marked move and the same words unmarked differ in meaning and in what their
    speaker answers for, and the literal cause of the marked move is answered for as the
    unmarked move's is."""
    literal, marked = written("e6-figure-beside-literal", 1), \
        written("e6-figure-beside-literal", 2)
    assert literal.normal_text != marked.normal_text
    a, b = answers("e6-figure-beside-literal", 1)[0], answers("e6-figure-beside-literal", 2)[0]
    assert a != b
    cause = a[a.index("(ACTOR"):a.index("(CONTENT")]
    assert cause == b[b.index("(ACTOR"):b.index("(CONTENT")]
    assert "possess" in a and "possess" not in b and "(situation shut" in b


def test_f7_a_figure_meant_both_ways_answers_for_both_readings():
    """A set of readings typed creative whose readings are one predication without and
    with the mark; the speaker answers for the literal reading and the figure's content."""
    t = written("d06-figure-meant-both-ways", 1).normal[0]
    sets = [u for u in walk(t["constituents"]) if u.get("kind") == "readings"]
    assert len(sets) == 1 and sets[0]["ambiguity"].endswith(".creative")
    literal, figurative = sets[0]["readings"]
    assert figure_type(literal) is None and figure_type(figurative) == "metaphor"
    bare = copy.deepcopy(figurative)
    bare["parts"] = [p for p in bare["parts"] if not (
        p["kind"] == "value" and p["member"].startswith(FIGURE)) and not (
        p["kind"] == "filler" and p["role"].startswith(RELATION))]
    assert PRINT.node(bare).replace("MENTIONED-WITHOUT-EXISTENCE-ASSERTED", "X") == \
        PRINT.node(literal).replace("ASSERTED-TO-EXIST", "X")
    answered = answers("d06-figure-meant-both-ways", 1)[0]
    assert "(readings CREATIVE (situation confine" in answered
    assert "(situation capable" in answered and "METAPHOR" not in answered


def test_f8_a_figure_in_a_precision_bound_move_needs_its_relation():
    request = written("e6-figure-precision-bound", 1)
    assert request.classes[0]["pending"]
    base = ("(move ISSUE REQUEST SPEAKERS-OWN EXPLANATORY (situation open (ACTOR (term "
            "(party 2))) (UNDERGOER %s) (CONDITION (situation confine %%s (ACTOR (term service "
            "DEFINITE)) (UNDERGOER %s) %%s))))" % (SUITE, SUITE))
    target = "(TARGET-CONTENT %s)" % UNAVAILABLE
    for figure in ("METAPHOR", "IRONY", "HYPERBOLE"):
        assert codes(base % (figure, target)) == []
        assert codes(base % (figure, "")) == ["d.checker.figure-without-target"]


def test_f9_the_hearer_extends_the_figure_as_its_own_inference():
    """The extension is the hearer's own assertion, on the basis of inference, marked as
    a metaphor, with a premise naming the figure it extends; the record of what the first
    speaker said is unchanged by it (`inv.inference-not-said`)."""
    view = View("1")
    view.receive(written("e6-extension", 1))
    first = view.said(("1", "1"))
    view.receive(written("e6-extension", 2))
    assert view.said(("1", "1")) == first
    extension = view.entries[("2", "1")]
    printed = PRINT.node(extension.content[0])
    assert printed.startswith("(assertion INFERENCE PROBABLE")
    assert "(PREMISE (names 1 1" in printed and "METAPHOR" in printed
    assert "evidence" in PRINT.node(view.answers_for(("2", "1"))[0])
    assert "evidence" not in PRINT.node(view.answers_for(("1", "1"))[0])


# ---------------------------------------------------------------- what a speaker answers for

FIGURATIVE = [(i, k, m, t) for i, k, m, t in MESSAGES
              if any(w in m.get("notation", "") for w in ("METAPHOR", "METONYMY", "IRONY", "HYPERBOLE"))]


@pytest.mark.parametrize("item_id,k,m,text", FIGURATIVE,
                         ids=["%s.%d" % (i, k) for i, k, _, _ in FIGURATIVE])
def test_every_corpus_figure_answers_for_its_content_and_mentions_its_source(
        item_id, k, m, text):
    """For every figurative corpus message, what the speaker answers for holds no mark
    and no figure's relation, and every marked figure is set apart as mentioned
    (`inv.figure-not-literal`)."""
    a = api.parse(text)
    assert a.diagnostics == []
    marked = 0
    for n in a.normal:
        answered = figures.answers_for(n["constituents"], LANG)
        for u in walk(answered):
            assert not (u.get("kind") == "value" and u["member"].startswith(FIGURE))
            assert not (u.get("kind") == "filler" and u["role"].startswith(RELATION))
            assert u.get("kind") != "unstated"
        marked += len(figures.sources(n["constituents"]))
    assert marked >= 1


def test_a_figurative_term_answers_for_the_situation_it_means():
    """Statement 19's storm on the network means that the network changes again and
    again: the term's target content stands for the situation the term stands in."""
    answered = answers("s19-metaphor", 1)[0]
    assert "(situation change ITERATIVE" in answered and "locate" not in answered
    assert "storm" not in answered


def test_a_figure_without_its_content_answers_for_an_unstated_content():
    a = api.parse(message("(move ASSERTED-POSITION EXPLANATORY (assertion OBSERVATION "
                          "PROBABLE (situation confine METAPHOR (ACTOR (term service "
                          "DEFINITE)) (UNDERGOER %s))))" % SUITE))
    assert a.diagnostics == []
    answered = figures.answers_for(a.normal[0]["constituents"], LANG)
    assert PRINT.node(answered[0]) == "(assertion OBSERVATION PROBABLE (unstated METAPHOR))"


def test_irony_and_hyperbole_answer_for_their_contents():
    irony, hyperbole = answers("e6-irony-hyperbole", 1)[0], answers("e6-irony-hyperbole", 2)[0]
    assert "(situation change ITERATIVE" in irony and "quiet" not in irony
    assert "(q AT-LEAST 10)" in hyperbole and "1000000" not in hyperbole
    assert "1000000" in mentions("e6-irony-hyperbole", 2)[0]


def test_a_blend_answers_for_the_inferences_it_projects_into_the_actual_world():
    t = written("e6-blend", 1).normal[0]
    normal = PRINT.move(t)
    assert "WITHIN-A-FICTION" in normal and "(TARGET-CONTENT (situation cause" in normal
    answered = answers("e6-blend", 1)[0]
    assert "WITHIN-A" not in answered and "ACTUAL" in answered
    assert "water" not in answered and "water" in mentions("e6-blend", 1)[0]


def test_the_poem_answers_for_what_the_specification_states():
    """Each line of the poem, a marked metaphor in the explanatory register and the
    poetic diction, answers for what the matching line of the specification, in the
    formal register, states literally; the first and last lines share one shape."""
    spec = [answers("e6-specification-and-poem", k)[0] for k in (1, 2, 3)]
    poem = [answers("e6-specification-and-poem", k)[0] for k in (4, 5, 6)]
    assert spec == poem
    lines = [written("e6-specification-and-poem", k).moves[0] for k in (4, 5, 6)]
    assert all(t["register"] == "g.ambiguity-and-figures.register.explanatory" and
               LANG.entries[t["diction"]]["key"] == "poetic" for t in lines)
    specification = [written("e6-specification-and-poem", k).moves[0] for k in (1, 2, 3)]
    assert all(t["register"] == "g.ambiguity-and-figures.register.formal"
               for t in specification)

    first, last = (written("e6-specification-and-poem", k).normal[0]["constituents"]
                   for k in (4, 6))
    figure_of = [next(u for u in walk(c) if figure_type(u)) for c in (first, last)]
    roles = [[p["role"] for p in f["parts"] if p["kind"] == "filler"] for f in figure_of]
    assert roles[0] == roles[1]


def test_the_joke_answers_for_one_word_in_two_senses():
    answered = answers("e6-joke", 2)[0]
    assert "(situation freeze" in answered and "(situation settle" in answered


# ---------------------------------------------------------------- conventional senses

def test_every_sense_is_selected_in_its_frame_and_nowhere_else():
    """Each sense is read where the unit its root heads has the frame's role filled by the
    frame's kind of constituent, the basic sense where the role is filled otherwise, and
    the basic sense inside a figure's source."""
    fillers = {"situation": "(situation run (UNDERGOER (term service DEFINITE)))",
               "term": "(term record)"}
    for root, sense_ids in LANG.senses.items():
        for ident in sense_ids:
            frame = LANG.entries[ident]["frame"]
            role = frame["role"].rsplit(".", 1)[-1].upper()
            other = "term" if frame["filler"] == "situation" else "situation"
            kind = LANG.entries[root]["grammatical category"]
            unit = "situation" if kind == "predicate root" else "term"
            key = LANG.entries[root]["key"]
            selected = READ.node(sexp("(%s %s (%s %s))" % (unit, key, role,
                                                          fillers[frame["filler"]]))[0])
            basic = READ.node(sexp("(%s %s (%s %s))" % (unit, key, role, fillers[other]))[0])
            bare = READ.node(sexp("(%s %s)" % (unit, key))[0])
            assert senses.sense_of(selected, LANG) == ident
            assert senses.sense_of(basic, LANG) is None
            assert senses.sense_of(bare, LANG) is None


def test_a_sense_is_never_written_in_the_notation():
    with pytest.raises(NotationError):
        READ.node(sexp("(situation understand (UNDERGOER (situation run)))")[0])


def test_the_english_explanation_reads_each_word_in_its_sense():
    english = api.translate(TEXTS[("e6-conventional-senses", 1)])[0]
    assert "understand" in english and " take " not in english
    english = api.translate(TEXTS[("d01-simple-fact", 1)])[0]
    assert "freeze" in english and "settle" not in english
    # inside a figure's source a word keeps its basic sense, and its target content is
    # read in the senses its frames select
    figure = written("e6-specification-and-poem", 6).normal[0]
    english = English().move(figure)
    assert "freeze the water" in english and "settle" in english
    marked = api.parse(message(
        "(move ASSERTED-POSITION EXPLANATORY (assertion OBSERVATION PROBABLE (situation take "
        "METAPHOR (ACTOR (term SELF)) (UNDERGOER (situation run (UNDERGOER (term service)))) "
        "(TARGET-CONTENT (situation take (ACTOR (term SELF)) (UNDERGOER (situation break "
        "(UNDERGOER (term service)))))))))"))
    assert marked.diagnostics == []
    english = English().move(marked.normal[0])
    assert english.count("take") == 1 and english.count("understand") == 1
    assert english.index("take") < english.index("understand")


def test_lookup_finds_a_sense_by_its_form_and_its_key():
    form = LANG.entries[entry("take")]["orthographic form"]
    found = {i.identifier for i in api.lookup(form)}
    assert {entry("take"), entry("understand")} <= found
    assert [i.identifier for i in api.lookup("understand")] == [entry("understand")]


def test_release_0_5_adds_its_senses_roots_and_mappings():
    added = [i for i in LANG.release["entries"]
             if LANG.entries[i]["version"]["introduced"] == "0.5"]
    keys = [LANG.entries[i]["key"] for i in added]
    assert keys == ["analogous", "confine", "elegant", "clumsy", "understand", "conclude",
                    "settle", "urgency", "burst", "clarity"]
    # the release's own mappings and senses; lexicon 1.0 adds more
    fifth = data.load("0.5")
    assert len(fifth.mappings) == 9 and fifth.release["mappings"] == sorted(fifth.mappings)
    motivated = {m for r in fifth.mappings.values() for m in r["motivates"]}
    figure_idioms = {i for i in fifth.idioms if fifth.entries[i]["route"] == "figure"}
    assert figure_idioms - motivated == {entry("memory deleting memory")}
    assert set(fifth.senses) == {entry(k) for k in ("take", "arrive", "freeze", "pressure",
                                                     "storm", "light")}
    # no earlier release changes: release 0.4 is what it was
    earlier = data.load("0.4")
    assert earlier.senses == {} and earlier.mappings == {}


def planted(change):
    lang = copy.copy(LANG)
    lang.entries = copy.deepcopy(LANG.entries)
    lang.mappings = copy.deepcopy(LANG.mappings)
    lang.senses = copy.deepcopy(LANG.senses)
    change(lang)
    return {code for code, _ in lc.check_senses(lang)}


def test_two_senses_with_one_frame_are_found():
    def overlap(lang):
        twin = copy.deepcopy(lang.entries[entry("understand")])
        twin["machine identifier"] = "lx.999999"
        lang.entries["lx.999999"] = twin
        lang.mappings[twin["motivating mapping"]]["motivates"].append("lx.999999")
    assert planted(overlap) == {"sense-frames-overlap"}


def test_a_sense_without_its_mapping_is_found():
    def orphan(lang):
        lang.mappings["mp.000001"]["motivates"].remove(entry("understand"))
    assert planted(orphan) == {"sense-without-mapping"}


def test_a_sense_that_differs_from_its_root_is_found():
    def drift(lang):
        lang.entries[entry("understand")]["sort"] = "s.sort.state"
    assert planted(drift) == {"sense-differs-from-root"}


def test_a_mapping_that_motivates_no_figure_is_found():
    def stray(lang):
        lang.mappings["mp.000002"]["motivates"].append(entry("examine"))
    assert planted(stray) == {"mapping-motivates-no-figure"}


def test_an_ill_formed_frame_is_found():
    def frame(lang):
        lang.entries[entry("burst")]["frame"]["filler"] = "wall"
    assert planted(frame) == {"sense-frame-ill-formed"}


# ---------------------------------------------------------------- the checker

def test_each_figure_states_the_relation_its_type_takes():
    term = ("(move ISSUE REQUEST SPEAKERS-OWN EXPLANATORY (situation send (ACTOR (term "
            "(party 2))) (UNDERGOER %s) (RECIPIENT (term service DEFINITE %%s))))" % SUITE)
    assert codes(term % "METONYMY (STANDS-FOR (term (party 3)))") == []
    assert codes(term % "METONYMY") == ["d.checker.figure-without-target"]
    assert codes(term % "METONYMY (TARGET-CONTENT (term (party 3)))") == [
        "d.checker.figure-relation", "d.checker.figure-without-target"]
    assert codes(term % "METAPHOR (TARGET-CONTENT (term (party 3)))") == []
    assert codes(term % "METAPHOR (STANDS-FOR (term (party 3)))") == [
        "d.checker.figure-relation", "d.checker.figure-without-target"]
    assert codes(term % "(STANDS-FOR (term (party 3)))") == ["d.checker.figure-relation"]


def test_the_negative_items_of_figures_draw_their_codes():
    negative = json.load(open(os.path.join(ROOT, "corpus", "source", "negative.json"),
                              encoding="utf-8"))["items"]
    ours = [i for i in negative if 106 <= int(i["id"].split("-")[0][1:]) <= 113]
    assert len(ours) == 8
    for item in ours:
        with open(os.path.join(ROOT, "corpus", "negative", item["id"] + ".txt"),
                  encoding="utf-8") as f:
            assert [d.code for d in api.parse(f.read()).diagnostics] == [item["code"]]


@PROFILE
@given(variants())
def test_generated_meanings_answer_for_no_mark_and_no_relation(moves):
    """Over generated variants of the corpus's moves, what a speaker answers for never
    holds a figurative mark or a figure's relation, and every source it sets apart is
    a marked unit of the move."""
    for t in moves:
        answered = figures.answers_for(t["constituents"], LANG)
        for u in walk(answered):
            assert not (u.get("kind") == "value" and u["member"].startswith(FIGURE))
            assert not (u.get("kind") == "filler" and u["role"].startswith(RELATION))
        for s in figures.sources(t["constituents"]):
            assert figure_type(s) is not None


# ------------------------------------------------ the mechanisms and kinds of text

MECHANISMS = {
    "metaphor": "d06-metaphor-with-content", "simile": "e6-simile-personification",
    "analogy": "e6-analogy", "personification": "e6-simile-personification",
    "metonymy": "e6-metonymy", "conceptual blending": "e6-blend",
    "irony": "e6-irony-hyperbole", "humour": "e6-joke", "wordplay": "e6-joke",
    "rhetorical parallelism": "e6-specification-and-poem",
    "deliberate ambiguity": "d06-figure-meant-both-ways",
    "aesthetic judgments": "e6-aesthetic-imaginative",
    "imaginative concepts": "e6-aesthetic-imaginative", "hypothetical worlds": "s11-hypothetical",
    "fictional scenarios": "e6-aesthetic-imaginative", "jokes": "e6-joke",
    "compressed metaphors": "e6-conventional-senses",
}
KINDS = {
    "proverb": "e6-proverb", "joke": "e6-joke", "metaphor": "d06-metaphor-with-content",
    "dialogue": "e2-discourse-architecture", "poem": "e6-specification-and-poem",
    "technical specification": "e6-specification-and-poem",
    "scientific statement": "d01-simple-fact",
    "philosophical argument": "d07-proposition-interpretation",
    "negotiation": "e3-negotiation", "emotional/affective expression": "e6-aesthetic-imaginative",
    "deliberately ambiguous utterance": "s18-intentional",
}


def test_every_mechanism_and_kind_of_text_has_an_item():
    """Eleven mechanisms of figurative language and six things to communicate, and eleven
    kinds of text, each tied to the corpus item that exemplifies it."""
    assert len(MECHANISMS) == 17 and len(KINDS) == 11
    ids = {i["id"] for i in items()}
    assert set(MECHANISMS.values()) | set(KINDS.values()) <= ids
    for item_id in set(MECHANISMS.values()) | set(KINDS.values()):
        for k in range(1, 1 + next(len(i["messages"]) for i in items() if i["id"] == item_id)):
            assert api.parse(TEXTS[(item_id, k)]).diagnostics == []


def test_the_corpus_writes_every_figurative_type_and_relation():
    text = " ".join(m.get("notation", "") for item in items() for m in item["messages"])
    for needle in ("METAPHOR", "METONYMY", "IRONY", "HYPERBOLE", "TARGET-CONTENT",
                   "STANDS-FOR", "WITHIN-A-FICTION", "(readings CREATIVE"):
        assert needle in text, needle
