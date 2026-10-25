"""Act words, formulas and idioms
(specification/lexicon.md#conventional-expressions-and-idioms) read by their entries and
the declared loss, with `inv.realisations-normalise` tested as the invariants state
(specification/conformance.md#the-invariants). Word formation and the act of definition
are `test_formation.py`'s."""
import copy

import pytest
from hypothesis import HealthCheck, assume, given, settings, strategies as st

from rowih import api, data, formation, idioms, lexicon_checks as lc
from rowih.checker import move_class
from rowih.economy import economy
from rowih.generator import Generator
from rowih.lexer import segment
from rowih.normal import Normaliser
from rowih.notation import Printer, Reader, sexp
from rowih.tree import strip_private

from corpus import language_of, messages, moves_of
from test_properties import variants

LANG = data.load()
GEN = Generator(LANG)
NORM = Normaliser(LANG)
READ = Reader(LANG)
PRINT = Printer(LANG)
MESSAGES = messages()
TEXTS = {(i, k): t for i, k, _, t in MESSAGES}
PROFILE = settings(max_examples=150, deadline=None,
                   suppress_health_check=[HealthCheck.too_slow])


def entry(key):
    return next(i for i, e in LANG.entries.items() if e["key"] == key)


def written(item_id, k):
    return api.parse(TEXTS[(item_id, k)])


def sent(m, moves, mode="normal expression"):
    return Generator(language_of(m)).message(moves, mode, m["sender"], m["recipients"],
                                             m["time"], m["identifier"],
                                             first_entry=m["first entry"])


# ---------------------------------------------------------------- realisations

REALISED = [(i, k, m, t) for i, k, m, t in MESSAGES if m.get("realisations")]


@pytest.mark.parametrize("item_id,k,m,text", REALISED,
                         ids=["%s.%d" % (i, k) for i, k, _, _ in REALISED])
def test_each_realisation_normalises_to_the_same_bytes(item_id, k, m, text):
    """Every realisation an item states of one meaning, with act words and idioms or
    written out, normalises to the same bytes (`inv.realisations-normalise`)."""
    a = api.parse(text)
    for notation in m["realisations"]:
        b = api.parse(sent(m, READ.moves(notation)))
        assert b.diagnostics == [] and b.normal_text == a.normal_text
        assert [c for c in b.classes] == [c for c in a.classes]


# a protocol message has no moves, and so no mode
MOVING = [x for x in MESSAGES if "statement" not in x[2]]


@pytest.mark.parametrize("item_id,k,m,text", MOVING,
                         ids=["%s.%d" % (i, k) for i, k, _, _ in MOVING])
def test_every_corpus_meaning_normalises_alike_in_every_mode(item_id, k, m, text):
    """Each corpus meaning, realised in each mode with the devices the mode admits
    applied wherever they apply, normalises to the bytes it had, with the diagnostics
    it had (`inv.realisations-normalise`)."""
    a = api.parse(text)
    moves = moves_of(m)
    gen = Generator(language_of(m))
    for mode in ("full explicitness", "normal expression", "idiom"):
        b = api.parse(sent(m, gen.economy(moves, mode), mode))
        assert b.normal_text == a.normal_text, mode
        assert [d.code for d in b.diagnostics] == [d.code for d in a.diagnostics], mode


@PROFILE
@given(variants(), st.sampled_from(["normal expression", "idiom"]))
def test_generated_meanings_normalise_alike_in_every_mode(moves, mode):
    """Over generated utterances, the generator's choice of devices never changes the
    normal form (`inv.realisations-normalise`)."""
    text = GEN.message(GEN.economy(moves, mode), mode)
    assume(len(text.split()) <= LANG.protocol["maxima"]["message words"])
    a = api.parse(text)
    assert [strip_private(n) for n in a.normal] == [NORM.move(t) for t in moves]


def test_devices_are_chosen_by_the_mode():
    """Normal expression writes the act words and the formulas; the mode of idiom adds
    the decoding idioms; full explicitness writes neither."""
    meaning = READ.moves(
        "(move ISSUE REQUEST SPEAKERS-OWN (situation examine (ACTOR (term (party 2))) "
        "(UNDERGOER (term fault DEFINITE)))) (move ASSERTED-POSITION (assertion OBSERVATION "
        "PROBABLE (situation change ITERATIVE (UNDERGOER (term network DEFINITE))))) (move "
        "ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation benefit (CONTENT "
        "(situation run (UNDERGOER (term service DEFINITE)))) (RECIPIENT (term SELF)))))")
    social = {}
    for mode in ("full explicitness", "normal expression", "idiom"):
        a = api.parse(GEN.message(GEN.economy(meaning, mode), mode))
        social[mode] = [(s["act"], s["idioms"]) for s in a.social]
    assert social["full explicitness"] == [(None, [])] * 3
    assert social["normal expression"] == [(entry("request"), []), (None, []),
                                           (None, [entry("thanks")])]
    assert social["idiom"] == [(entry("request"), []), (None, [entry("storm on the network")]),
                               (None, [entry("thanks")])]


def test_the_longest_act_word_is_chosen():
    """Where the head of an acceptance begins with a promise, the act word for the whole
    acceptance is written, not the promise followed by the rest."""
    t = READ.moves("(move NORMATIVE-ENTRY COMMITMENT BOUND RESOLUTION "
                   "OUTCOME-OF-A-RESOLUTION.ACCEPTANCE WHOLE-ENTRY ON-THE-MOVE SPEAKERS-OWN "
                   "(names 2 1 ISSUE PROPOSAL OPEN) (situation allocate (ACTOR (term SELF)) "
                   "(UNDERGOER (term share)) (RECIPIENT (term (party 2)))))")[0]
    assert economy(t, LANG, "normal expression")["act"] == entry("acceptance")


# ---------------------------------------------------------------- the theory's items

def test_j1_an_idiom_is_read_by_its_entry():
    """The core of the idiom is its conventional meaning, taken from its entry, and not
    its literal predication; the entry records its literal structure and the route by
    which it became conventional."""
    a = written("s20-idiom", 1)
    normal = PRINT.move(a.normal[0])
    assert "(situation possess" not in normal and "(situation capable " in normal
    assert "POLARITY.NEGATIVE" in normal
    assert a.social[0]["idioms"] == [entry("held by the service")]
    e = LANG.entries[entry("held by the service")]
    assert e["literal structure"].startswith("(situation possess (HOLDER (term service))")
    assert e["route"] == "figure" and e["constructed history"].startswith(
        "Constructed history:")
    assert e["decomposition"] == [{"slot": 1, "literal role": "UNDERGOER",
                                   "expansion role": "INSTRUMENT"}]


def test_j2_the_idiom_differs_from_its_words_read_literally():
    """The idiom's words read literally and read as the idiom differ in meaning, and a
    pun on them is a set of readings typed creative whose readings are both."""
    a = written("e4-literal-idiom-pun", 1)
    literal, idiom = [PRINT.move(n) for n in a.normal]
    assert "(situation delete" in literal and "(situation delete" not in idiom
    assert "(situation possess " in idiom and "POLARITY.NEGATIVE" in idiom
    pun = PRINT.move(written("e4-literal-idiom-pun", 2).normal[0])
    assert "(readings CREATIVE" in pun
    assert "(situation delete" in pun and "(situation possess " in pun


def test_j3_a_short_form_expands_to_its_explicit_move():
    """A conventional form one word long stands for a longer explicit form with the same
    core: the act words, and the compressed expression."""
    item_id, k, m, text = next(x for x in REALISED if x[:2] == ("e4-act-words", 1))
    a = api.parse(text)
    explicit = api.parse(sent(m, READ.moves(m["realisations"][0])))
    assert a.social[0]["act"] == entry("request") and explicit.social[0]["act"] is None
    assert len(a.words) < len(explicit.words) and a.normal_text == explicit.normal_text
    running = written("e4-conversational-idioms", 3)
    assert running.social[0]["idioms"] == [entry("running")]
    assert "(situation run PROGRESSIVE" in PRINT.move(running.normal[0]) or \
        ("(situation run " in PRINT.move(running.normal[0])
         and " PROGRESSIVE " in PRINT.move(running.normal[0]))
    assert "service DEFINITE" in PRINT.move(running.normal[0])


def test_j4_softening_and_register_lie_outside_the_core():
    """The thanks of the formulas declares that its expansion loses the stance and the
    relation between the participants; the declaration and the formula stand in the
    social and textual component, the force is unchanged, and the normal form is the
    explicit move's."""
    a = written("e4-formulas", 3)
    assert a.social[0]["losses"] == [
        "g.ambiguity-and-figures.declared-loss.stance",
        "g.ambiguity-and-figures.declared-loss.relation-between-participants"]
    assert a.social[0]["idioms"] == [entry("thanks")]
    assert "losses" not in a.normal[0] and "act" not in a.normal[0]
    assert move_class(a.moves[0]) == move_class(a.normal[0])


def test_j5_an_idiom_in_a_precision_bound_move():
    """A request whose content is an idiom stands, since the mark selects its entry and
    the expansion is complete; one whose marked words select no entry is refused."""
    a = written("e4-idiom-precision-bound", 1)
    assert a.diagnostics == [] and a.classes[0]["pending"]
    refused = api.parse(open("corpus/negative/n91-idiom-absent-in-a-request.txt").read())
    assert [d.code for d in refused.diagnostics] == ["d.checker.idiom-absent"]


def test_an_unmarked_grammatical_idiom_is_read_literally():
    """Without the mark the idiom's words mean what they say: the mark is what puts the
    expansion in the core
    (specification/lexicon.md#conventional-expressions-and-idioms)."""
    plain = READ.moves("(move ASSERTED-POSITION (assertion OBSERVATION (situation locate "
                       "(UNDERGOER (term network DEFINITE)) (CONTENT (term storm)))))")
    a = api.parse(GEN.message(plain))
    assert a.social[0]["idioms"] == [] and "(situation locate" in PRINT.move(a.normal[0])


def test_an_extragrammatical_idiom_is_recognised_by_its_words():
    a = written("e4-conversational-idioms", 2)
    assert a.social[0]["idioms"] == [entry("run run")]
    assert "(situation run " in PRINT.move(a.normal[0])
    assert " CONTINUATIVE " in PRINT.move(a.normal[0])


# ---------------------------------------------------------------- act words

# The class each act word's acts have in the act table (specification/meaning.md#force),
# and the entry an act that changes one names: an independent statement of what each act
# word must mean.
ACT_CLASSES = {
    "question": (None, "inert"), "request": (None, "pending"),
    "proposal": (None, "pending"), "challenge": (None, "inert"),
    "command": (None, "operative"), "promise": (None, "operative"),
    "offer": (None, "operative"), "delegation": (None, "operative"),
    "grant": (None, "operative"), "recommendation": (None, "inert"),
    "definition": (None, "operative"), "role assignment": (None, "operative"),
    "counterproposal": ("ISSUE PROPOSAL OPEN", "pending"),
    "acceptance": ("ISSUE PROPOSAL OPEN", "operative"),
    "undertaking": ("ISSUE REQUEST OPEN", "operative"),
    "partial acceptance": ("ISSUE PROPOSAL OPEN", "operative"),
    "rejection": ("ISSUE REQUEST OPEN", "operative+de-escalating"),
    "acknowledgement": ("NORMATIVE-ENTRY COMMITMENT EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE",
                        "inert"),
    "withdrawal": ("NORMATIVE-ENTRY COMMITMENT EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE",
                   "operative+de-escalating"),
    "partial withdrawal": ("NORMATIVE-ENTRY COMMITMENT EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE",
                           "operative+de-escalating"),
    "answer": ("ISSUE QUESTION OPEN", "inert"),
    "completion report": ("NORMATIVE-ENTRY OBLIGATION EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE",
                          "pending"),
    "error report": ("NORMATIVE-ENTRY OBLIGATION EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE",
                     "pending"),
    "confirmation": ("ASSERTED-POSITION EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE", "inert"),
    "correction": ("ASSERTED-POSITION EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE", "inert"),
}


def flags(cls):
    return "+".join(k for k in ("operative", "pending", "de-escalating") if cls[k]) or "inert"


def test_every_act_word_has_the_class_of_its_acts():
    """Each act word, read as the parser reads it, makes a move of the class its acts have
    in the act table (specification/meaning.md#force; `inv.class-computed`): a word for a
    request that read as a command would make a pending move operative."""
    acts = {e["key"]: i for i, e in LANG.entries.items()
            if e["grammatical category"] == "act word"}
    assert set(acts) == set(ACT_CLASSES)
    for key, ident in acts.items():
        named, expected = ACT_CLASSES[key]
        ref = " (names 2 1 %s)" % named if named else ""
        notation = "(move %s SPEAKERS-OWN%s (situation examine (ACTOR (term SELF)) " \
                   "(UNDERGOER (term record))))" % (LANG.items[ident].gloss, ref)
        a = api.parse(GEN.message(READ.moves(notation)))
        assert not [d for d in a.diagnostics if d.code.startswith("d.parser")], key
        assert a.social[0]["act"] == ident
        assert flags(a.classes[0]) == expected, key


def test_act_words_are_force_words_covered_by_the_check_word():
    """An act word carries values of several critical dimensions, so it stands at a
    distance of three from every word and has a code the move check word covers
    (`inv.one-critical-dimension`)."""
    acts = [i for i, e in LANG.entries.items() if e["grammatical category"] == "act word"]
    for ident in acts:
        item = LANG.items[ident]
        assert item.protected and item.critical_code > 0 and len(item.form) == 6
        assert item.form[0] == "k"
    assert lc.check_release(LANG) == []


# ---------------------------------------------------------------- coverage

# Each kind of conventional expression and idiom and each mechanism of word formation
# (specification/lexicon.md#conventional-expressions-and-idioms), with the entry that
# answers it and the conformance item that exercises it.
CONVENTIONS = {
    "greetings": ("memory open", "e4-formulas"),
    "acknowledgements": ("acknowledgement", "e4-act-words-stops"),
    "confirmations": ("confirmation", None),
    "thanks": ("thanks", "e4-formulas"),
    "apologies": ("apology", "e4-formulas-repair"),
    "requests for clarification": ("meaning asked", "e4-formulas-repair"),
    "warnings": ("not quiet", "e4-formulas-warning-uncertainty"),
    "agreement": ("acceptance", "e4-act-words-negotiation"),
    "disagreement": ("challenge", None),
    "uncertainty": ("evidence wanting", "e4-formulas-warning-uncertainty"),
    "closure": ("memory shut", "e4-formulas"),
    "conversational repair": ("damaged arrival", "e4-formulas-repair"),
    "conversational idioms": ("quiet network", "e4-conversational-idioms"),
    "agentic idioms": ("word counting", "e4-agentic-idioms"),
    "computational idioms": ("held by the service", "s20-idiom"),
    "epistemic idioms": ("taken from the air", "e4-agentic-idioms"),
    "negotiation idioms": ("water price", "e4-negotiation-idioms"),
    "metaphorical expressions": ("storm on the network", "e4-metaphor-conventionalised"),
    "humorous expressions": ("memory deleting memory", "e4-literal-idiom-pun"),
    "compressed expressions": ("running", "e4-conversational-idioms"),
}
FORMATIONS = {
    "compounding": "memory~record", "derivation": "detect.agent",
    "abstraction": "service.abstraction", "nominalization": "run.nominalisation",
    "verbalization": "file.verbalisation", "adjectivization": "water.adjectivisation",
    "agent nouns": "detect.agent", "process nouns": "examine.process",
    "result nouns": "freeze.result", "tool nouns": "use.instrument",
    "property nouns": "quiet.property", "relational terms": "conjunction.role content",
    "conceptual compression": "burn~memory",
}


def test_every_kind_of_conventional_expression_and_idiom_has_a_form():
    """Each kind of conventional expression and idiom has an entry, read by the corpus
    where an item exercises it; transitions are the discourse relation words, which open
    and join moves, and each idiom's entry has the fields an idiom requires
    (specification/lexicon.md#entries-and-their-identifiers)."""
    social = {}
    for item_id, k, m, text in MESSAGES:
        a = api.parse(text)
        for s in a.social:
            social.setdefault(item_id, set()).update(s["idioms"])
            if s["act"]:
                social[item_id].add(s["act"])
    for kind, (key, item_id) in CONVENTIONS.items():
        ident = entry(key)
        if item_id is not None:
            assert ident in social.get(item_id, set()), kind
        e = LANG.entries[ident]
        for field in ("literal structure", "definition", "pragmatic conditions", "register",
                      "usage restrictions", "expansion"):
            assert e.get(field) not in (None, ""), (kind, field)
    relations = [e["key"] for e in LANG.entries.values()
                 if e["grammatical category"] == "discourse relation"]
    # the core's five, and the six of lexicon 1.0
    assert relations == ["elaborates", "restates", "contrasts", "supports move", "digresses",
                         "exemplifies", "concludes", "qualifies", "corrects", "generalises",
                         "continues"]


def test_every_mechanism_of_word_formation_forms_a_word():
    """Each mechanism of word formation (specification/lexicon.md#word-formation) forms an
    unlisted word whose meaning its parts give."""
    import sys
    sys.path.insert(0, "tools")
    from build_corpus import formed
    for mechanism, spec in FORMATIONS.items():
        if spec.startswith("conjunction"):
            form = LANG.form_of("g.situations-and-contents.connective.conjunction") + next(
                f for f, it in LANG.suffixes.items() if it.name == "role content")
        else:
            form = formed(spec, LANG)
        morphemes = segment(form, LANG)
        assert morphemes is not None and LANG.by_form.get(form) is None, mechanism
        assert formation.compose(morphemes, LANG) is not None, mechanism


# ---------------------------------------------------------------- the lexicon's checks

def planted(change):
    lang = copy.copy(LANG)
    lang.entries = copy.deepcopy(LANG.entries)
    lang.idioms = list(LANG.idioms)
    change(lang)
    return {code for code, _ in lc.check_idioms(lang)}


def test_an_act_word_whose_expansion_the_parser_cannot_read_is_found():
    def disorder(lang):
        e = lang.entries[entry("request")]
        e["expansion"] = list(reversed(e["expansion"]))
    assert "act-word-expansion" in planted(disorder)


def test_an_idiom_whose_form_selects_two_entries_is_found(monkeypatch):
    """Two entries whose literal structures one constituent could match would let a form
    select either, which the rule that a form determines its entry forbids
    (specification/lexicon.md#conventional-expressions-and-idioms); planted as two
    structures with their slots in different places."""
    original = idioms.literal
    possess_service = READ.node(sexp(
        "(situation possess (HOLDER (term service)) (UNDERGOER (slot 1)))")[0])
    possess_file = READ.node(sexp(
        "(situation possess (HOLDER (slot 1)) (UNDERGOER (term file DEFINITE)))")[0])

    def literal(lang, ident):
        if ident == entry("held by the service"):
            return copy.deepcopy(possess_service)
        if ident == entry("thanks"):
            return copy.deepcopy(possess_file)
        return original(lang, ident)
    monkeypatch.setattr(idioms, "literal", literal)
    found = [x for code, x in lc.check_idioms(LANG) if code == "idiom-form-selects-two"]
    assert found == [" ".join(sorted([entry("held by the service"), entry("thanks")]))]


def test_an_expansion_holding_an_idiom_is_found():
    def nest(lang):
        e = lang.entries[entry("running")]
        e["expansion"] = "(situation IDIOM-ENTRY run)"
    assert "idiom-inside-an-expansion" in planted(nest)


def test_an_expansion_that_drops_a_slot_is_found():
    def drop(lang):
        e = lang.entries[entry("thanks")]
        e["expansion"] = "(situation benefit (RECIPIENT (term SELF)))"
    assert "idiom-slots-differ" in planted(drop)


def test_two_idioms_one_substitution_apart_are_found(monkeypatch):
    """Where one substitution of a word without a code would turn one marked idiom into
    another whose expansion differs in a critical value, only the integrity check value
    would detect the edit; the release's checks refuse such a pair. Planted as the
    formula the enumeration found it in, a damaged arrival written as its root and its
    slot alone, one substitution from the quiet network."""
    original = idioms.literal
    bare = READ.node(sexp("(situation corrupt (UNDERGOER (slot 1)))")[0])

    def literal(lang, ident):
        return copy.deepcopy(bare) if ident == entry("damaged arrival") else original(lang,
                                                                                     ident)
    monkeypatch.setattr(idioms, "literal", literal)
    found = {tuple(sorted(x.split())) for code, x in lc.check_idioms(LANG)
             if code == "idiom-one-edit-from-another"}
    assert tuple(sorted([entry("damaged arrival"), entry("quiet network")])) in found
    assert tuple(sorted([entry("memory open"), entry("memory shut")])) not in found


def test_an_idiom_whose_literal_structure_is_its_expansion_is_found(monkeypatch):
    """An idiom whose literal structure, normalised, is its expansion's normal form says
    nothing the mark adds, so the writer leaves the mark out and no hearer can tell the
    entry was used; planted as the release step first rewrote *working*, its literal
    given the actor its expansion states."""
    original = idioms.literal
    same = READ.node(sexp("(situation work PROGRESSIVE (ACTOR (term SELF)))")[0])

    def literal(lang, ident):
        return copy.deepcopy(same) if ident == entry("working") else original(lang, ident)
    monkeypatch.setattr(idioms, "literal", literal)
    found = [x for code, x in lc.check_idioms(LANG) if code == "idiom-literal-is-its-expansion"]
    assert found == [entry("working")]

def test_two_idioms_one_substitution_apart_once_defaults_are_supplied_are_found(monkeypatch):
    """A marked unit is read by the entry whose literal structure its normal form matches,
    so the distance between two idioms is counted with the defaults the normaliser
    supplies, not as the literal structures are written. Planted as the release's gate
    found it: *working* written with the progressive aspect that its root, a process,
    takes by default, and *running* without it, one substitution of the root apart, the
    enumeration's edit of *run* into *work* changing who acts."""
    original = idioms.literal
    written = READ.node(sexp("(situation work PROGRESSIVE)")[0])

    def literal(lang, ident):
        return copy.deepcopy(written) if ident == entry("working") else original(lang, ident)
    monkeypatch.setattr(idioms, "literal", literal)
    found = {tuple(sorted(x.split())) for code, x in lc.check_idioms(LANG)
             if code == "idiom-one-edit-from-another"}
    assert tuple(sorted([entry("running"), entry("working")])) in found
    assert tuple(sorted([entry("memory open"), entry("memory shut")])) not in found
