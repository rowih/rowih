"""The 14 adversarial messages (specification/conformance.md#the-conformance-suite): every
demand the core answers is checked here, each residue is shown in the form that reveals
its limit, and every demand is accounted for as core, met beyond the core, residue, or not
met."""
import json
import os

import pytest

from rowih import api, conformance as C, data, report
from rowih.lexer import decode_payload
from rowih.notation import Printer
from rowih.serialise import check_value
from rowih.view import View

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = json.load(open(os.path.join(ROOT, "corpus", "source", "adversarial.json"),
                        encoding="utf-8"))["items"]
ITEMS = {i["id"]: i for i in SOURCE}
LANG = data.load()
PRINT = Printer(LANG)


def text(item_id, k=1):
    with open(os.path.join(ROOT, "corpus", "adversarial", "%s.%d.txt" % (item_id, k)),
              encoding="utf-8") as f:
        return f.read()


def literal(a):
    return " ".join(PRINT.move(n) for n in a.normal)


def test_every_demand_is_accounted_for():
    statuses = [s for i in SOURCE for s in i["demands"].values()]
    assert len(SOURCE) == 14
    assert {s for s in statuses if not s.startswith("the ")} <= {"core", "met", "residue",
                                                                 "not met"}
    assert statuses.count("not met") == 1


def test_a01_standing_survives_the_most_compressed_mode():
    from rowih.generator import Generator
    from rowih.notation import Reader
    gen = Generator(LANG)
    moves = Reader(LANG).moves(ITEMS["a01-compressed-uncertain"]["messages"][0]["notation"])
    terse = api.parse(gen.message(moves, "normal expression"))
    full = api.parse(gen.message(moves, "full explicitness"))
    assert LANG.form_of("g.standing.strength.speculative") in terse.canonical
    assert terse.normal_text == full.normal_text
    assert len(terse.words) < len(full.words)


def test_a01_compression_beyond_normal_expression_keeps_the_standing():
    """The mode of compression of the registers: for a hearer that holds the lexicon the
    compressed form writes the conventional forms and keeps the standing, and for a hearer
    whose holdings are unknown it is full explicitness, which normalises alike."""
    from rowih.economy import Holdings
    from rowih.generator import Generator
    gen = Generator(LANG)
    notation = ITEMS["a01-compressed-uncertain"]["messages"][0]["notation"]
    held = gen.generate(notation, holdings=Holdings(lexicon=(LANG.version,)))
    unknown = gen.generate(notation)
    compressed, full = api.parse(held["compressed form"]), api.parse(unknown["compressed form"])
    assert compressed.diagnostics == [] and full.diagnostics == []
    assert LANG.form_of("g.standing.strength.speculative") in compressed.canonical
    assert compressed.normal_text == full.normal_text
    assert len(compressed.words) < len(full.words) and unknown["declared"]


def test_a02_one_expression_two_views():
    challenge = api.parse(text("a02-two-contexts", 3))
    named = challenge.moves[0]["named"]
    assert named["expected"] and named["status"]
    a_view, c_view, d_view = View("1"), View("3"), View("4")
    first, retraction = api.parse(text("a02-two-contexts", 1)), api.parse(text("a02-two-contexts", 2))
    a_view.receive(first)
    c_view.receive(first)
    c_view.receive(retraction)
    assert a_view.receive(challenge) == []
    # A challenged a position whose retraction it never received: the challenge crossed
    # the retraction, and the retraction, its author's, prevails
    assert [d.code for d in c_view.receive(challenge)] == ["d.view.crossed"]
    assert c_view.crossed == {("1", "1"): ("2", "2")}
    assert [d.code for d in d_view.receive(challenge)] == ["d.view.held"]
    assert d_view.entries == {} and len(d_view.held) == 1


def test_a03_quotation_and_payload_are_inert():
    a = api.parse(text("a03-quoted-instruction"))
    assert a.diagnostics == [] and a.classes[0]["inert"]
    wall_words = [w for t in a.moves for p in _walk(t) if p.get("kind") == "wall"
                  for w in p.get("words", [])]
    closers = {LANG.form_of("g.structure.end-situation"), LANG.form_of("g.structure.end-assertion")}
    assert closers <= set(wall_words)
    lit = literal(a)
    assert '(data "text/plain"' in lit and "EXTERNAL-SOURCE" in lit and "UNVERIFIED" in lit


def test_a03_a_quotation_cannot_be_ended_from_inside():
    end_wall = LANG.form_of("g.structure.end-wall")
    t = text("a03-quoted-instruction")
    quote_start = t.index(LANG.form_of("g.message.embedded-material.quotation"))
    planted = t[:quote_start] + t[quote_start:].replace(" ", " %s " % end_wall, 1)
    assert api.parse(planted).diagnostics != []


def test_a04_figure_over_technical_vocabulary():
    a = api.parse(text("a04-technical-metaphor"))
    assert a.diagnostics == [] and a.classes[0]["pending"]
    lit = literal(a)
    assert "burn" in lit and "METAPHOR" in lit and "TARGET-CONTENT" in lit
    source = lit[lit.index("burn"):lit.index("TARGET-CONTENT")]
    assert "MENTIONED-WITHOUT-EXISTENCE-ASSERTED" in source
    target = lit[lit.index("TARGET-CONTENT"):]
    assert "ASSERTED-TO-EXIST" in target and "MENTIONED" not in target
    metaphor = LANG.form_of("g.ambiguity-and-figures.figurative-type.metaphor")
    for other in ("metonymy", "irony", "hyperbole"):
        edited = text("a04-technical-metaphor").replace(
            metaphor, LANG.form_of("g.ambiguity-and-figures.figurative-type." + other))
        assert api.parse(edited).diagnostics != []


def test_a05_retraction_of_part():
    view = View("2")
    assert view.receive(api.parse(text("a05-partial-retraction", 1))) == []
    assert view.receive(api.parse(text("a05-partial-retraction", 2))) == []
    entry = view.entries[("1", "1")]
    assert entry.status == "lowered"


def test_a05_a_restatement_of_the_wrong_part_is_refused():
    other = text("a05-partial-retraction", 2)
    a = api.parse(other)
    part = a.moves[0]["named"]["part"]
    wrong = other.replace(" ".join(_name_words(part)), " ".join(_name_words(3 - part)), 1)
    view = View("2")
    view.receive(api.parse(text("a05-partial-retraction", 1)))
    codes = [d.code for d in view.receive(api.parse(_reseal(wrong)))]
    assert codes == ["d.checker.stop-restatement"]


def _name_words(n):
    from rowih.writer import Writer
    return [LANG.form_of("g.structure.part")] + Writer(LANG).name(n)


def _reseal(t):
    import sys
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    from build_negative import lines_of, reseal
    return reseal(lines_of(t))


def test_a06_sources_attributed_with_shared_lineage():
    a = api.parse(text("a06-disagreeing-sources", 1))
    assert a.diagnostics == []
    lit = literal(a)
    assert lit.count("RELAYER") == 2 and "(party 3)" in lit and "(party 4)" in lit
    assert "(SOURCE @1)" in lit and "(SOURCE (term #1" in lit
    challenge = api.parse(text("a06-disagreeing-sources", 2))
    assert challenge.diagnostics == []
    view = View("1")
    view.receive(a)
    assert view.receive(challenge) == []


def test_a07_delegation_retains_responsibility():
    delegation = api.parse(text("a07-delegation-retained", 1))
    assert [c["operative"] for c in delegation.classes] == [True, True]
    assert all(t["authority"].endswith("in-a-named-role") for t in delegation.moves)
    report_text = text("a07-delegation-retained", 2)
    assert api.parse(report_text).diagnostics == []
    own = report_text.split("\n")
    planted = report_text.replace(LANG.form_of("g.force.authority-claimed.on-behalf-of-a-named-principal"),
                                  LANG.form_of("g.force.authority-claimed.speakers-own"))
    codes = [d.code for d in api.parse(_reseal(_drop_authority_term(planted))).diagnostics]
    assert "d.checker.authority-attenuates" in codes
    assert own


def _drop_authority_term(t):
    """Remove the principal's term that followed the authority word."""
    lines = t.split("\n")
    words = lines[1].split(" ")
    i = words.index(LANG.form_of("g.force.authority-claimed.speakers-own"))
    j = words.index(LANG.form_of("g.structure.end-term"), i)
    lines[1] = " ".join(words[:i + 1] + words[j + 1:])
    return "\n".join(lines)


def test_a08_crossing_is_detected_by_both_and_ordered_alike():
    """Both participants detect the crossing, and both compute one order: the
    cancellation, a stop, prevails over the acceptance, which each view then refuses,
    so that the two records end alike (`inv.precedence-agreed`)."""
    request, cancel, accept = (api.parse(text("a08-crossing", k)) for k in (1, 2, 3))
    a_view, b_view = View("1"), View("2")
    a_view.receive(request)
    b_view.receive(request)
    assert a_view.receive(cancel) == []
    assert b_view.receive(accept) == []
    assert [d.code for d in a_view.receive(accept)] == ["d.view.crossed"]
    assert [d.code for d in b_view.receive(cancel)] == ["d.view.crossed"]
    assert [d.code for d in b_view.receive(cancel)] == ["d.view.applied-before"]
    for view in (a_view, b_view):
        assert view.entries[("1", "1")].status == "withdrawn"
        assert ("2", "1") not in view.entries
        assert view.crossed == {("2", "1"): ("1", "2")}


def test_a09_instruction_is_the_speakers_own_and_open_to_question():
    command, question = api.parse(text("a09-instruction-as-own", 1)), api.parse(
        text("a09-instruction-as-own", 2))
    assert command.moves[0]["authority"].endswith("speakers-own")
    view = View("2")
    view.receive(command)
    assert view.entries[("3", "1")].kind == ("normative-entry", "obligation")
    assert view.receive(question) == []


def test_a10_relay_check_values_and_byte_exact_quotation():
    a = api.parse(text("a10-rewriting-relay"))
    assert a.diagnostics == []
    walls = [p for t in a.moves for p in _walk(t) if p.get("kind") == "wall"]
    quoted = decode_payload(walls[0]["data"]).decode("utf-8")
    original = open(os.path.join(ROOT, "corpus", "conformance", "s01-observed.1.txt"),
                    encoding="utf-8").read()
    assert quoted == original
    assert "RELAYER (term ASSERTED-TO-EXIST GIVEN SELF)" in literal(a)
    q = api.parse(quoted)
    semantic = check_value(q.normal_text)
    integrity = q.message.envelope.integrity.integer()
    assert semantic != integrity
    service = LANG.items[next(i for i, e in LANG.entries.items() if e["key"] == "service")].form
    record = LANG.items[next(i for i, e in LANG.entries.items() if e["key"] == "record")].form
    rewritten = api.parse(original.replace(service, record))
    assert check_value(rewritten.normal_text) != semantic


def test_a11_dialect_form_is_unknown_vocabulary():
    a = api.parse(text("a11-registers-dialect"))
    assert [d.code for d in a.diagnostics] == ["d.lexer.unknown-word"]
    assert a.diagnostics[0].recoverability == "kept opaque"


def test_a11_one_core_two_registers():
    """The demand that one move be written in two registers: the message's move written in
    the protocol register, precision-bound by default, and in the ceremonial one has one
    core, and the conversion between them declares exactly what it changed; the dialect
    form stays unknown vocabulary in both, since no message here names a dialect."""
    from rowih.generator import Generator
    gen = Generator(LANG)
    a = api.parse(text("a11-registers-dialect"))
    protocol = api.parse(gen.generate(a.moves, register="R1")["transliteration"])
    ceremonial = api.parse(gen.generate(a.moves, register="R7")["transliteration"])
    assert protocol.normal_text == ceremonial.normal_text == a.normal_text
    assert [d.code for d in ceremonial.diagnostics] == ["d.lexer.unknown-word"]
    assert "d.checker.unknown-in-precision-bound" in [d.code for d in protocol.diagnostics]
    out, changes, diags = api.translate(ceremonial.text, "R1")
    assert out == "" and [d.code for d in diags] == ["d.convert.register-cannot-carry"]
    out, changes, diags = api.translate(protocol.text, "R7")
    assert out == "" and diags, "a message its own register rejects is not converted"
    out, changes, diags = api.translate(ceremonial.text, "R2")
    assert [d.code for d in diags] == ["d.lexer.unknown-word"]
    assert api.parse(out).normal_text == a.normal_text
    assert changes == [["register", "relation between participants", "wording"]]


def test_a12_compound_unknown_and_broken():
    a = api.parse(text("a12-novel-unknown-broken"))
    compound = next(w for w in a.words if w.kind == "formation")
    assert [m if m == "linker" else m.name for m in compound.morphemes] == \
        ["network", "linker", "service"]
    assert [w.kind for w in a.words if w.form == "rokiwomab"] == ["unknown"]
    broken = text("a12-novel-unknown-broken").replace(compound.form, compound.form[:-1], 1)
    assert api.parse(broken).diagnostics != []


def test_a13_recursion_to_the_limit_and_past():
    at_limit = api.parse(text("a13-recursion-limit"))
    assert at_limit.diagnostics == []
    assert LANG.protocol["maxima"]["nesting"] == 5
    beyond = open(os.path.join(ROOT, "corpus", "negative",
                               "n50-nesting-beyond-the-maximum-short.txt"), encoding="utf-8").read()
    d = api.parse(beyond).diagnostics
    assert [x.code for x in d] == ["d.parser.maximum"]
    assert api.parse(report.render(d[0])).diagnostics == []


def test_a14_damage_and_transport():
    t = text("a14-damaged-transport")
    cut = "\n".join(t.split("\n")[:2]) + "\n"
    assert "d.check-values.integrity-mismatch" in [d.code for d in api.parse(cut).diagnostics]
    lowering = LANG.form_of("g.situations-and-contents.polarity.negative")
    edited = t.replace(lowering, lowering[:-1] + ("a" if lowering[-1] != "a" else "e"), 1)
    assert api.parse(edited).diagnostics != []
    assert api.parse(t.replace(" ", " ‮", 1)).diagnostics != []
    export, _ = api.convert(t, "json")
    assert api.parse(export).diagnostics != []


def test_a14_residues_show_their_limit():
    """Without the integrity check value, a cut between inert moves and some edits to
    the envelope pass: the limits the adversarial test records."""
    from rowih.generator import Generator
    from rowih.notation import Reader
    gen = Generator(LANG)
    moves = Reader(LANG).moves(ITEMS["a14-damaged-transport"]["messages"][0]["notation"])
    bare = gen.message(moves, integrity=False)
    cut = "\n".join(bare.split("\n")[:2]) + "\n"
    assert api.parse(cut).diagnostics == []
    assert C.enumerate_prefixes(bare) != []


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for x in node:
            yield from _walk(x)
