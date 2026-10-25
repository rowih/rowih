"""Registers (specification/lexicon.md#registers): the register a move states, what each
register admits, register-marked words, dictions, compression by shared context, and
conversion between registers with `inv.loss-declared` tested as the invariants state
(specification/conformance.md#the-invariants); the jargon of the eleven communities is
`test_jargon.py`'s."""
import pytest
from hypothesis import HealthCheck, assume, given, settings, strategies as st

from rowih import api, data, registers
from rowih.checker import precision_bound
from rowih.economy import Holdings
from rowih.generator import Generator
from rowih.marking import mark
from rowih.moves import resolve_deixis
from rowih.normal import Normaliser
from rowih.notation import Printer, Reader
from rowih.register_rules import devices_used
from rowih.tree import strip_private
from rowih.view import View
from rowih.writer import Envelope

from corpus import language_of, messages
from test_properties import variants

LANG = data.load()
GEN = Generator(LANG)
NORM = Normaliser(LANG)
READ = Reader(LANG)
PRINT = Printer(LANG)
MESSAGES = messages()
TEXTS = {(i, k): t for i, k, _, t in MESSAGES}
CODES = ["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7"]
PROFILE = settings(max_examples=120, deadline=None,
                   suppress_health_check=[HealthCheck.too_slow])
# the table of registers: each register's modes and its precision bound by default
REGISTER_TABLE = {
    "R0": (["full explicitness", "normal expression", "compression"], False),
    "R1": (["full explicitness", "normal expression"], True),
    "R2": (["full explicitness", "normal expression", "compression", "idiom"], False),
    "R3": (["full explicitness", "normal expression", "creative expression"], False),
    "R4": (["full explicitness", "normal expression"], True),
    "R5": (["normal expression", "compression", "idiom"], False),
    "R6": (["normal expression", "idiom", "creative expression"], False),
    "R7": (["full explicitness", "normal expression", "idiom"], False),
}


def entry(key):
    return next(i for i, e in LANG.entries.items() if e["key"] == key)


def codes(text):
    return [d.code for d in api.parse(text).diagnostics]


# the envelope of an answer from participant 2 to participant 1
TO_ONE = Envelope(2, (1,), "1759622400")


def message(notation, sender=1, recipients=(2,), mode="as written"):
    """The notation written as it states each move, with the check words, the counts and
    the integrity check value the writer adds."""
    return GEN.message(READ.moves(notation), mode, sender, recipients)


ASSERTION = ("(move ASSERTED-POSITION %s (assertion OBSERVATION CERTAIN (situation run "
             "(UNDERGOER (term service DEFINITE)))))")


# ---------------------------------------------------------------- the register of a move

def test_each_register_has_its_modes_and_bound():
    for code, (modes, bound) in REGISTER_TABLE.items():
        record = LANG.registers[code]
        assert record["modes admitted"] == modes
        assert record["precision-bound by default"] is bound
        assert (record["member"] in registers.BOUND) is bound
        assert LANG.register_code[record["member"]] == code


def test_a_move_states_its_register_and_the_standard_is_the_default():
    for code in CODES:
        gloss = LANG.items[LANG.registers[code]["member"]].gloss
        a = api.parse(message(ASSERTION % ("" if code == "R2" else gloss)))
        assert a.diagnostics == [] and a.social[0]["register"] == code
    written_standard = api.parse(message(ASSERTION % "STANDARD"))
    assert written_standard.social[0]["register"] == "R2"
    assert written_standard.normal_text == api.parse(message(ASSERTION % "")).normal_text


def test_two_registers_make_an_inert_move_precision_bound():
    """An inert move in the protocol or formal register is held to the precision bound,
    refused where it fails it and required to travel with the integrity check value."""
    for gloss, bound in (("PROTOCOL", True), ("FORMAL", True), ("STANDARD", False),
                         ("CEREMONIAL", False)):
        t = READ.moves(ASSERTION % gloss)[0]
        assert precision_bound(t) is bound, gloss
    readings = ("(move ASSERTED-POSITION %s (assertion INFERENCE (readings PRODUCTIVE "
                "(situation break (UNDERGOER (term network DEFINITE))) (situation break "
                "(UNDERGOER (term service DEFINITE))))))")
    assert "d.checker.precision-bound" in codes(message(readings % "FORMAL"))
    assert "d.checker.precision-bound" not in codes(message(readings % "STANDARD"))
    def without_value(gloss):
        # the generator never omits the value a precision-bound move needs, so the
        # defective message is written by the writer itself
        t = READ.moves(ASSERTION % gloss)[0]
        return GEN.wr.message(GEN.wr.envelope(), [GEN.spell.move(t)], integrity=False)
    assert GEN.message(READ.moves(ASSERTION % "PROTOCOL"), integrity=False).count(
        GEN.wr.w("g.message.message-field.integrity-check-value")) == 1
    for gloss in ("PROTOCOL", "FORMAL", "PRECISION-BOUND"):
        assert "d.checker.integrity-value-required" in codes(without_value(gloss))
    assert "d.checker.integrity-value-required" not in codes(without_value("CASUAL"))


def test_the_normal_form_sets_the_component_aside():
    """A register, a politeness word, a diction and register-marked words are records of
    the social and textual component, which the normal form sets aside; the analysis
    keeps them (specification/lexicon.md#registers)."""
    plain = api.parse(message(ASSERTION % ""))
    marked = api.parse(message(
        "(move ASSERTED-POSITION familiar terse CASUAL (assertion OBSERVATION CERTAIN "
        "(situation hum (UNDERGOER (term box DEFINITE)))))"))
    assert marked.diagnostics == [] and marked.normal_text == plain.normal_text
    social = marked.social[0]
    assert (social["register"], social["diction"], social["politeness"]) == (
        "R5", entry("terse"), entry("familiar"))
    assert social["marked"] == [LANG.items[entry("hum")].form,
                                LANG.items[entry("box")].form]


# ---------------------------------------------------------------- what a register admits

def test_each_marked_word_stands_only_in_the_registers_it_lists():
    for key in ("operate", "hum", "proceed", "daemon", "box", "establishment", "audit",
                "eyeball", "scrutinise"):
        e = LANG.entries[entry(key)]
        base = LANG.entries[e["synonym of"]]
        slot = "run" if base["key"] == "run" else "service" if base["key"] == "service" \
            else "examine"
        notation = {"run": "(situation %s (UNDERGOER (term service DEFINITE)))",
                    "service": "(situation run (UNDERGOER (term %s DEFINITE)))",
                    "examine": "(situation %s (UNDERGOER (term service DEFINITE)))"}[slot]
        for code in CODES:
            gloss = LANG.items[LANG.registers[code]["member"]].gloss
            text = message("(move ASSERTED-POSITION %s (assertion OBSERVATION CERTAIN %s))"
                           % (gloss, notation % key))
            excluded = "d.checker.register-excludes-word" in codes(text)
            assert excluded is (code not in e["register"]), (key, code)


def test_each_device_stands_only_in_a_register_whose_modes_admit_it():
    """Decoding idioms in the registers with the mode of idiom, figures and creative
    ambiguity in those with creative expression, shared context in those with
    compression, and formulas everywhere but raw exchange."""
    devices = {
        "idioms": "(move ASSERTED-POSITION %s (assertion OBSERVATION CERTAIN (situation "
                  "quiet IDIOM-ENTRY (UNDERGOER (term network DEFINITE)))))",
        "marked figures": "(move ASSERTED-POSITION %s (assertion OBSERVATION PROBABLE "
                          "(situation burn METAPHOR (UNDERGOER (term network DEFINITE)) "
                          "(TARGET-CONTENT (situation increase (UNDERGOER (term data)))))))",
        "formulas": "(move ASSERTED-POSITION %s (assertion INTROSPECTION CERTAIN (situation "
                    "open IDIOM-ENTRY (UNDERGOER (term memory)))))",
    }
    for device, notation in devices.items():
        for code in CODES:
            record = LANG.registers[code]
            gloss = "" if code == "R2" else LANG.items[record["member"]].gloss
            found = codes(message(notation % gloss))
            admitted = record["formulas admitted"] if device == "formulas" else \
                device in record["devices admitted"]
            assert ("d.checker.register-excludes-device" not in found) is admitted, (
                device, code, found)
    accept = ("(move NORMATIVE-ENTRY OBLIGATION BOUND RESOLUTION "
              "OUTCOME-OF-A-RESOLUTION.ACCEPTANCE WHOLE-ENTRY ON-THE-MOVE SPEAKERS-OWN "
              "(names 1 1 ISSUE REQUEST OPEN) %s)")
    for code in CODES:
        record = LANG.registers[code]
        gloss = "" if code == "R2" else LANG.items[record["member"]].gloss
        found = codes(message(accept % gloss, sender=2, recipients=(1,)))
        assert ("d.checker.register-excludes-device" not in found) is (
            "shared context" in record["devices admitted"]), code


def test_canonical_registers_refuse_siblings_out_of_order():
    disordered = ("(move ASSERTED-POSITION %s (assertion CERTAIN OBSERVATION (situation run "
                  "(UNDERGOER (term service DEFINITE)))))")
    for code in CODES:
        record = LANG.registers[code]
        gloss = "" if code == "R2" else LANG.items[record["member"]].gloss
        found = codes(message(disordered % gloss))
        assert ("d.checker.register-order" in found) is (record["order"] == "canonical")


# ---------------------------------------------------------------- one core, every register

@pytest.mark.parametrize("item_id,k,m,text", [x for x in MESSAGES if x[0].startswith("e")
                                              and "statement" not in x[2]],
                         ids=["%s.%d" % (i, k) for i, k, m, _ in MESSAGES
                              if i.startswith("e") and "statement" not in m])
def test_each_meaning_realised_in_every_register_keeps_its_core(item_id, k, m, text):
    """The generator's realisation of a corpus meaning in each register that can carry its
    core normalises to the bytes it had, with no diagnostic
    (`inv.realisations-normalise`); a register that cannot carry it is one without the
    mode its figures or creative ambiguity need, or one precision-bound by default whose
    standard the core fails."""
    a = api.parse(text)
    if a.diagnostics:
        return
    # in the release and with the dialects the message names
    lang = language_of(m)
    gen, norm = Generator(lang), Normaliser(lang)
    for code in CODES:
        out = gen.generate(a.moves, register=code, envelope=Envelope(
            m["sender"], tuple(m["recipients"]), m["time"], identifier=m["identifier"]))
        b = api.parse(out["transliteration"])
        used = set().union(*(devices_used(t, lang, norm) for t in a.moves))
        # what the core holds, which no realisation removes, and the reference the
        # device of shared context names, which only the record restates
        lacking = used & {"marked figures", "creative ambiguity", "shared context"} - set(
            LANG.registers[code]["devices admitted"])
        if lacking:
            assert "d.checker.register-excludes-device" in [d.code for d in b.diagnostics]
            continue
        if b.diagnostics and LANG.registers[code]["precision-bound by default"]:
            assert {d.code for d in b.diagnostics} <= {"d.checker.precision-bound",
                                                       "d.checker.figure-without-target",
                                                       "d.checker.unknown-in-precision-bound"}
            continue
        assert b.diagnostics == [], (code, [d.as_text() for d in b.diagnostics])
        assert b.normal_text == a.normal_text, code


def test_one_core_in_a_precision_bound_and_a_ceremonial_move():
    """The protocol move and the ceremonial one of one exchange have one core, and a
    conversion between them declares exactly what it changed."""
    protocol = api.parse(TEXTS[("e5-one-core-two-registers", 1)])
    ceremonial = api.parse(TEXTS[("e5-one-core-two-registers", 2)])
    assert protocol.diagnostics == [] and ceremonial.diagnostics == []
    assert protocol.normal == ceremonial.normal
    assert precision_bound(protocol.moves[0]) and not precision_bound(ceremonial.moves[0])
    out, changes, diags = api.translate(protocol.text, "ceremonial")
    assert diags == [] and api.parse(out).normal_text == protocol.normal_text
    assert changes == [["register", "relation between participants", "wording"]]


# ---------------------------------------------------------------- conversion

def independent_social(a, i):
    """The five records of a move's social and textual component, read from the
    analysis and the lexicon without the code that declares a conversion's changes."""
    t, s = a.moves[i], a.social[i]
    stance = [x for x in ([s["act"]] if s["act"] else []) + s["idioms"]
              if "stance" in LANG.entries[x]["declared loss"]]
    wording = {k: v for k, v in strip_private(t).items()
               if k not in ("losses", "politeness", "diction", "register")}
    return {"register": s["register"], "diction": s["diction"], "stance": stance,
            "relation between participants": s["politeness"], "wording": wording}


CONVERTED = [(i, k, t) for i, k, _, t in MESSAGES if not api.parse(t).diagnostics]


@pytest.mark.parametrize("item_id,k,text", CONVERTED,
                         ids=["%s.%d" % (i, k) for i, k, _ in CONVERTED])
def test_every_conversion_keeps_the_core_and_declares_exactly_what_it_changed(
        item_id, k, text):
    """`inv.loss-declared` over register conversion: each corpus message converted to
    each register keeps its normal form, so that the semantic check value is the same,
    and declares exactly the records of the social and textual component that differ;
    where the target cannot carry the core, nothing is converted and the diagnostic
    says why (specification/lexicon.md#registers)."""
    a = api.parse(text)
    order = ["register", "diction", "stance", "relation between participants", "wording"]
    for code in CODES:
        out, changes, diags = api.translate(text, code)
        if diags:
            assert out == "" and changes == []
            assert {d.code for d in diags} <= {"d.convert.register-cannot-carry",
                                               "d.convert.record-needed"}, code
            continue
        b = api.parse(out)
        assert b.diagnostics == [] and b.normal_text == a.normal_text, code
        for i in range(len(a.moves)):
            before, after = independent_social(a, i), independent_social(b, i)
            assert changes[i] == [r for r in order if before[r] != after[r]], (code, i)


def test_a_conversion_refuses_a_core_its_target_cannot_carry():
    metaphor = TEXTS[("s19-metaphor", 1)]
    for code in ("R0", "R1", "R2", "R4", "R5", "R7"):
        out, changes, diags = api.translate(metaphor, code)
        assert out == "" and [d.code for d in diags] == ["d.convert.register-cannot-carry"]
    out, changes, diags = api.translate(metaphor, "playful")
    assert diags == [] and changes == [["register", "relation between participants"]]


def test_a_conversion_restates_shared_context_only_from_the_record():
    request, acceptance = (TEXTS[("e5-shared-context", k)] for k in (1, 2))
    out, changes, diags = api.translate(acceptance, "R1")
    assert [d.code for d in diags] == ["d.convert.record-needed"]
    view = View("2")
    view.hear(request)
    record = {h: (e.content, e.recipients) for h, e in view.entries.items()}
    out, changes, diags = api.translate(acceptance, "R1", record)
    assert diags == [] and changes[0][-1] == "wording"
    explicit = View("1")
    explicit.hear(request)
    explicit.hear(out)
    shared = View("1")
    shared.hear(request)
    shared.hear(acceptance)
    assert resolve_deixis(explicit.entries[("2", "1")].content, "2", ("1",)) == \
        shared.entries[("2", "1")].content


# ---------------------------------------------------------------- compression

def test_shared_context_gives_the_view_an_explicit_acceptance_gives():
    request, acceptance = (TEXTS[("e5-shared-context", k)] for k in (1, 2))
    explicit = GEN.message(READ.moves(
        "(move NORMATIVE-ENTRY OBLIGATION BOUND RESOLUTION OUTCOME-OF-A-RESOLUTION.ACCEPTANCE "
        "WHOLE-ENTRY ON-THE-MOVE SPEAKERS-OWN (names 1 1 ISSUE REQUEST OPEN) familiar CASUAL "
        "(situation examine (ACTOR (term SELF)) (UNDERGOER (term fault DEFINITE))))"),
        sender=2, recipients=(1,), time="1759622460")
    views = []
    for second in (acceptance, explicit):
        v = View("1")
        assert v.hear(request) == [] and v.hear(second) == []
        views.append(v)
    assert resolve_deixis(views[0].entries[("2", "1")].content, "2", ("1",)) == \
        resolve_deixis(views[1].entries[("2", "1")].content, "2", ("1",))


def test_compression_names_only_what_the_hearer_holds():
    """`inv.devices-admissible` for the devices of compression: the generator writes the
    device of shared context only for a hearer whose holdings include the entry, an entry
    sent counting as held, and devices that need the lexicon only for a hearer that holds
    its version; otherwise the compressed form is full explicitness."""
    request = READ.moves("(move ISSUE REQUEST SPEAKERS-OWN (situation examine (ACTOR (term "
                         "(party 2))) (UNDERGOER (term fault DEFINITE))))")
    view = View("2")
    view.hear(GEN.message(request))
    accept = READ.moves(
        "(move NORMATIVE-ENTRY OBLIGATION BOUND RESOLUTION OUTCOME-OF-A-RESOLUTION.ACCEPTANCE "
        "WHOLE-ENTRY ON-THE-MOVE SPEAKERS-OWN (names 1 1 ISSUE REQUEST OPEN) (situation "
        "examine (ACTOR (term SELF)) (UNDERGOER (term fault DEFINITE))))")
    holds = Holdings.from_view(view, "2", "1", (LANG.version,))
    compressed = api.parse(GEN.generate(accept, holdings=holds, envelope=TO_ONE)[
        "compressed form"])
    assert compressed.diagnostics == [] and compressed.moves[0]["constituents"] == []
    assert "shared context" in devices_used(compressed.moves[0], LANG, NORM)
    lacking = Holdings("2", ("1",), (LANG.version,), {})
    kept = api.parse(GEN.generate(accept, holdings=lacking, envelope=TO_ONE)[
        "compressed form"])
    assert kept.moves[0]["constituents"] and not kept.moves[0].get("act") is None
    unknown = api.parse(GEN.generate(accept, holdings=None, envelope=TO_ONE)[
        "compressed form"])
    assert devices_used(unknown.moves[0], LANG, NORM) == set()
    other = Holdings("2", ("1",), ("0.3",), holds.entries)
    older = api.parse(GEN.generate(accept, holdings=other, envelope=TO_ONE)[
        "compressed form"])
    assert devices_used(older.moves[0], LANG, NORM) == set()


@PROFILE
@given(variants(), st.sampled_from(CODES), st.sampled_from(
    ["full explicitness", "normal expression", "compression", "idiom"]))
def test_generated_meanings_in_every_register_keep_their_core(moves, code, mode):
    """Over generated utterances, the realisation in any register and mode normalises to
    the meaning's normal form and uses only devices the register admits."""
    # a meaning ill-formed on its own, or whose core holds a figure or a creative
    # ambiguity the register's modes do not admit, is not the register's to carry
    own = api.parse(GEN.message(moves))
    assume(not own.diagnostics)
    held = set().union(*(devices_used(t, LANG, NORM) for t in moves))
    assume(not held & {"marked figures", "creative ambiguity"} - set(
        LANG.registers[code]["devices admitted"]))
    out = GEN.generate(moves, register=code, mode=mode)
    text = out["transliteration"]
    assume(len(text.split()) <= LANG.protocol["maxima"]["message words"])
    a = api.parse(text)
    # nor is a core that fails the standard of a register precision-bound by default
    assume(not [d for d in a.diagnostics if d.code in (
        "d.checker.precision-bound", "d.checker.figure-without-target",
        "d.checker.unknown-in-precision-bound")])
    assert a.diagnostics == []
    assert [strip_private(n) for n in a.normal] == [NORM.move(t) for t in moves]
    admitted = set(LANG.registers[code]["devices admitted"]) | {"formulas"}
    for t in a.moves:
        assert devices_used(t, LANG, NORM) <= admitted


# ---------------------------------------------------------------- dictions

def test_a_diction_is_requested_undertaken_and_declared():
    texts = [TEXTS[("e5-diction", k)] for k in (1, 2, 3)]
    for t in texts:
        assert api.parse(t).diagnostics == []
    request = api.parse(texts[0])
    terms = [p for p in request.moves[0]["constituents"][0]["parts"]
             if p.get("kind") == "filler" and p["role"].endswith("instrument")]
    assert terms[0]["filler"]["parts"][0]["entry"] == entry("terse")
    third = api.parse(texts[2])
    assert [s["diction"] for s in third.social] == [entry("terse"), entry("tentative")]


def test_no_diction_changes_the_core_and_each_chooses_its_mode():
    meaning = READ.moves(
        "(move ISSUE REQUEST SPEAKERS-OWN (situation examine (ACTOR (term (party 2))) "
        "(UNDERGOER (term fault DEFINITE)))) (move ASSERTED-POSITION (assertion INFERENCE "
        "PROBABLE (situation change ITERATIVE (UNDERGOER (term network DEFINITE)))))")
    canonical = GEN.generate(meaning)["canonical form"]
    for e in [e for e in LANG.entries.values() if e["grammatical category"] == "diction"]:
        for code in CODES:
            out = GEN.generate(meaning, register=code, diction=e["key"])
            a = api.parse(out["transliteration"])
            assert a.diagnostics == [], (e["key"], code)
            assert "".join(" ".join(GEN.spell.move(n)) + "\n" for n in a.normal) == canonical
            admitted = LANG.registers[code]["modes admitted"]
            assert out["mode"] == next(m for m in e["modes"] if m in admitted)
            assert all(s["diction"] == entry(e["key"]) for s in a.social)
    terse = api.parse(GEN.generate(meaning, register="R5", diction="terse")["transliteration"])
    elaborate = api.parse(GEN.generate(meaning, register="R7",
                                       diction="elaborate")["transliteration"])
    assert len(terse.words) < len(elaborate.words)


# ---------------------------------------------------------------- the lexicon

def test_release_0_4_marks_its_words_by_register():
    by_code = {r["politeness word"]: code for code, r in LANG.registers.items()
               if r["politeness word"]}
    for ident, e in LANG.entries.items():
        if "synonym of" in e:
            base = LANG.entries[e["synonym of"]]
            assert (e["grammatical category"], e["sort"], e["argument structure"]) == (
                base["grammatical category"], base["sort"], base["argument structure"])
            assert e["register"] == [c for c in CODES
                                     if LANG.registers[c]["vocabulary"] == e["vocabulary"]]
        elif e["grammatical category"] == "politeness word":
            assert e["register"] == [c for c in CODES
                                     if LANG.registers[c]["politeness word"] == e["key"]]
            assert e["key"] in by_code
        elif e["grammatical category"] == "diction":
            assert set(e["modes"]) <= {"full explicitness", "normal expression",
                                       "compression", "idiom", "creative expression"}
            assert e["register"] == CODES
    honorific = [e for e in LANG.entries.values() if registers.marked(e)
                 and e["grammatical category"] == "derivational suffix"]
    assert len(honorific) == 1 and honorific[0]["register"] == ["R7"]
    assert len([e for e in LANG.entries.values() if e["grammatical category"] == "diction"]) \
        == 12


def test_marking_never_changes_the_normal_form_of_a_corpus_move():
    for item_id, k, m, text in MESSAGES:
        a = api.parse(text)
        if a.diagnostics:
            continue
        for t in a.moves:
            for code in CODES:
                marked = mark(strip_private(t), LANG, code)
                assert NORM.move(marked) == NORM.move(t), (item_id, k, code)
