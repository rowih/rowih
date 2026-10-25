"""The conformance corpus: every message parses without a diagnostic, its moves compute
the classes the corpus states, every exchange reads in each participant's view, and the
invariants (specification/conformance.md#the-invariants) hold over it."""
import os
import sys

import pytest

from rowih import api, data
from rowih.generator import Generator
from rowih.normal import Normaliser
from rowih.serialise import check_value
from rowih.tree import Spell, strip_private
from rowih.view import View

from corpus import ROOT, items, language_of, messages, moves_of

sys.path.insert(0, os.path.join(ROOT, "tools"))
from build_corpus import corpus_key, protocol_message  # noqa: E402

MESSAGES = messages()
IDS = ["%s.%d" % (i, k) for i, k, _, _ in MESSAGES]


def flags(cls):
    return {k for k, v in cls.items() if v and k != "inert"} or {"inert"}


@pytest.mark.parametrize("item_id,k,m,text", MESSAGES, ids=IDS)
def test_message_parses_cleanly(item_id, k, m, text):
    a = api.parse(text)
    assert [d.code for d in a.diagnostics] == m.get("diagnostics", [])


@pytest.mark.parametrize("item_id,k,m,text", MESSAGES, ids=IDS)
def test_classes_are_the_stated_ones(item_id, k, m, text):
    a = api.parse(text)
    stated = [set(c.split("+")) for c in m["classes"]]
    assert [flags(c) for c in a.classes] == stated


@pytest.mark.parametrize("item_id,k,m,text", MESSAGES, ids=IDS)
def test_native_form_parses_alike(item_id, k, m, text):
    a = api.parse(text)
    native, diags = api.convert(text, "native")
    b = api.parse(native)
    assert [d.code for d in b.diagnostics] == m.get("diagnostics", [])
    assert b.canonical == a.canonical and b.normal_text == a.normal_text


@pytest.mark.parametrize("item_id,k,m,text", MESSAGES, ids=IDS)
def test_canonical_serialisation_is_what_was_written(item_id, k, m, text):
    assert api.parse(text).canonical == text


@pytest.mark.parametrize("item_id,k,m,text", MESSAGES, ids=IDS)
def test_round_trip_and_normal_form_unique(item_id, k, m, text):
    """parse(generate(x)) has the normal form of x, in both modes; normalising a normal
    form changes nothing. A protocol message, which has no moves, reads as the statement
    its record states."""
    lang = language_of(m)
    if "statement" in m:
        def tupled(x):
            return tuple(tupled(y) for y in x) if isinstance(x, list) else x
        assert api.parse(text).statement == {"kind": m["statement"]["kind"],
                                             "parts": [[p[0]] + [tupled(x) for x in p[1:]]
                                                       for p in m["statement"]["parts"]]}
        return
    norm, spell, gen = Normaliser(lang), Spell(lang), Generator(lang)
    moves = moves_of(m)
    expected = "".join(" ".join(spell.move(norm.move(t))) + "\n" for t in moves)
    for mode in ("normal expression", "full explicitness"):
        out = gen.message(moves, mode, m["sender"], m["recipients"], m["time"],
                          m["identifier"], first_entry=m["first entry"])
        a = api.parse(out)
        assert [d.code for d in a.diagnostics] == m.get("diagnostics", [])
        assert a.normal_text == expected
        assert [strip_private(n) for n in a.normal] == [norm.move(t) for t in moves]
        again = [norm.move(t) for t in a.normal]
        assert again == a.normal


@pytest.mark.parametrize("item_id,k,m,text", MESSAGES, ids=IDS)
def test_generation_is_deterministic(item_id, k, m, text):
    if "statement" in m:
        assert protocol_message(m, data.load()) == text
        return
    gen = Generator(language_of(m))
    out = gen.message(moves_of(m), m.get("mode", "normal expression"), m["sender"],
                      m["recipients"], m["time"], m["identifier"],
                      semantic=m.get("semantic", False), first_entry=m["first entry"])
    if m.get("signed"):
        # Ed25519 signs deterministically (RFC 8032 § 5.1.6), so a signed message is
        # written again byte for byte
        from rowih.authentication import sign
        out = sign(out, corpus_key(m["sender"]))
    assert out == text


PLAIN = [i for i in items() if i["set"] != "adversarial"]


def deliveries(item, party):
    """The indices of the messages `party` sends or receives, in the order it receives
    them: the item's order, unless the item states another for that party, as an item
    whose moves cross does."""
    order = item.get("order", {}).get(party, range(1, len(item["messages"]) + 1))
    return [k for k in order
            if party == str(item["messages"][k - 1]["sender"])
            or party in {str(r) for r in item["messages"][k - 1]["recipients"]}]


def parties_of(item):
    parties = set()
    for m in item["messages"]:
        parties.add(str(m["sender"]))
        parties.update(str(r) for r in m["recipients"])
    return sorted(parties, key=int)


@pytest.mark.parametrize("item", PLAIN, ids=[i["id"] for i in PLAIN])
def test_exchange_reads_in_every_view(item):
    """Each participant's view applies the exchange's messages in the order it receives
    them: every reference resolves to an entry of the kind and status it expects, every
    stop restates, and a view reports exactly what the item states it must, a crossing
    move that lost or an acceptance after a deadline."""
    texts = {(i, k): t for i, k, _, t in MESSAGES}
    for party in parties_of(item):
        view = View(party)
        stated = item.get("view diagnostics", {}).get(party, {})
        for k in deliveries(item, party):
            diags = view.receive(api.parse(texts[(item["id"], k)]))
            assert [d.code for d in diags] == stated.get(str(k), []), (party, k)
        assert len(view.held) == item.get("held", {}).get(party, 0)


def test_semantic_check_value_is_over_the_normal_form():
    item_id, k, m, text = next(x for x in MESSAGES if x[2].get("semantic"))
    a = api.parse(text)
    assert a.message.envelope.semantic.integer() == check_value(a.normal_text)


def test_corpus_covers_the_core():
    """The core's capabilities each appear in the corpus."""
    text = " ".join(m.get("notation", "") for item in items() for m in item["messages"])
    for needle in ("OBSERVATION", "INFERENCE", "REPORT", "PREMISE", "SOURCE", "BELIEF",
                   "INTENTION", "ISSUE REQUEST", "ISSUE PROPOSAL", "ISSUE CHALLENGE",
                   "NORMATIVE-ENTRY OBLIGATION", "NORMATIVE-ENTRY COMMITMENT",
                   "NORMATIVE-ENTRY ASSIGNMENT", "LOWERING", "RESOLUTION", "(names",
                   "(quote", "(data", "(readings", "METAPHOR", "(q ", "@1", "deadline",
                   "VALIDITY-INTERVAL", "IN-A-NAMED-ROLE", "SUPPOSITION", "CONDITION"):
        assert needle in text, needle


@pytest.mark.parametrize("item_id,k,m,text", [x for x in MESSAGES if "normal" in x[2]],
                         ids=[i for i, k, m, t in MESSAGES if "normal" in m])
def test_item_parses_to_its_stated_normal_form(item_id, k, m, text):
    """The attitude items carry their normal forms, reviewed and stored."""
    from rowih.notation import Printer, Reader
    a = api.parse(text)
    assert [Printer().move(n) for n in a.normal] == m["normal"]
    # and the stated normal form, read back, generates the same normal form
    reread = Reader().moves(" ".join(m["normal"]))
    assert [Printer().move(Normaliser(data.load()).move(t)) for t in reread] == m["normal"]


@pytest.mark.parametrize("item", items(), ids=[i["id"] for i in items()])
def test_hearer_files_entries_under_their_authors(item):
    """A hearer's view files what it hears under the speaker's handle, never among its
    own entries (`inv.hearing-not-believing`)."""
    texts = {(i, k): t for i, k, _, t in MESSAGES}
    # the first message that carries moves, a protocol message changing no record
    k, first = next((k, m) for k, m in enumerate(item["messages"], 1) if "statement" not in m)
    hearer = str(first["recipients"][0])
    view = View(hearer)
    view.receive(api.parse(texts[(item["id"], k)]))
    authors = {h[0] for h in view.entries}
    assert authors == {str(first["sender"])}


def test_names_are_numbered_by_the_normal_form_not_as_written():
    """Shared nodes are numbered in the normal form's traversal, whatever numbers the
    speaker wrote (`units/numbering-differs`)."""
    from rowih.notation import Reader
    written = Reader().moves(
        "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation INTENTION "
        "(HOLDER (term #7 SELF)) (CONTENT (situation examine (ACTOR @7) (UNDERGOER "
        "(term #4 record DEFINITE)))))))")[0]
    norm = Normaliser(data.load())
    n = norm.move(written)
    names = [x.get("name") for x in _nodes(n) if x.get("kind") == "term" and x.get("name")]
    assert names == [1, 2]


def _nodes(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _nodes(v)
    elif isinstance(node, list):
        for x in node:
            yield from _nodes(x)


def test_an_unlisted_formation_is_read_from_its_parts():
    """A root with a suffix the release does not list is segmented into its entries,
    not reported unknown (`units/formation-not-from-parts`)."""
    lang = data.load()
    root = lang.items[next(i for i, e in lang.entries.items() if e["key"] == "detect")].form
    suffix = next(f for f, it in lang.suffixes.items() if it.name == "agent")
    from rowih.notation import Reader
    from rowih.generator import Generator
    gen = Generator(lang)
    moves = Reader(lang).moves("(move ASSERTED-POSITION (assertion OBSERVATION (situation run "
                               "(ACTOR (term (unknown \"%s\"))))))" % (root + suffix))
    a = api.parse(gen.message(moves))
    assert a.diagnostics == []
    word = next(w for w in a.words if w.form == root + suffix)
    assert word.kind == "formation" and [m.name for m in word.morphemes] == ["detect", "agent"]


DERIVED = [i for i in items() if i.get("derived")]


def compact(view, now, keys):
    """The parts of a view's derived structure an item states, in the item's terms."""
    from rowih import conventions as C
    from rowih import coordination as K
    from rowih import discourse as D
    out = {}
    if "negotiations" in keys:
        out["negotiations"] = [
            {k: v for k, v in dict(
                n, opening=D.handle_text(n["opening"]),
                rounds=[D.handle_text(r["entry"]) for r in n["rounds"]],
                by=D.handle_text(n["by"]) if n["by"] else None).items()
             if k in ("opening", "rounds", "end", "by")
             or (k in ("extent", "conditional") and (v != "whole" and v is not False))}
            for n in K.negotiations(view, now)]
    if "conflicts" in keys:
        out["conflicts"] = [{"challenge": D.handle_text(c["challenge"]),
                             "position": D.handle_text(c["position"]), "state": c["state"]}
                            for c in K.conflicts(view)]
    if "crossed" in keys:
        out["crossed"] = {D.handle_text(k): D.handle_text(v) for k, v in view.crossed.items()}
    if "roster" in keys:
        out["roster"] = C.roster(view)
    if "silence" in keys:
        out["silence"] = {p: C.silence(view, p) for p in sorted(view.participants, key=int)}
    if "threads" in keys:
        out["threads"] = {D.handle_text(r): [D.handle_text(h) for h in hs]
                          for r, hs in D.threads(view).items()}
    if "open issues" in keys:
        out["open issues"] = [D.handle_text(i["entry"]) for i in D.open_issues(view)]
    if "action items" in keys:
        out["action items"] = [[D.handle_text(i["entry"]), i["responsible"]]
                               for i in D.action_items(view)]
    if "common ground" in keys:
        out["common ground"] = [[D.handle_text(c["entry"]), c["part"]]
                                for c in D.common_ground(view, now)]
    if "corroboration" in keys:
        out["corroboration"] = {D.handle_text(e.handle): [D.handle_text(c["entry"])
                                                          for c in D.corroboration(view,
                                                                                   e.handle)]
                                for e in view.entries.values()
                                if D.corroboration(view, e.handle)}
    if "relations" in keys:
        out["relations"] = [[D.handle_text(r["entry"]), r["relation"],
                             [D.handle_text(h) for h in r["bears on"]]]
                            for r in D.relations(view)]
    if "topics" in keys:
        out["topics"] = {D.handle_text(r): [[D.handle_text(t["entry"]), t["topic"]]
                                            for t in ts] for r, ts in D.topics(view).items()}
    if "conclusions" in keys:
        out["conclusions"] = [[D.handle_text(c["entry"]),
                               [D.handle_text(h) for h in c["premises"]]]
                              for c in D.conclusions(view)]
    if "terms" in keys:
        out["terms"] = [[t["term"], D.handle_text(t["definition"]), t["status"],
                         [D.handle_text(h) for h in t["uses"]]] for t in C.terms(view)]
    if "summaries" in keys:
        out["summaries"] = [[D.handle_text(s["entry"]),
                             [D.handle_text(h) for h in s["summarises"]]]
                            for s in D.summaries(view)]
    return out


@pytest.mark.parametrize("item", DERIVED, ids=[i["id"] for i in DERIVED])
def test_view_derives_the_stated_structure(item):
    """Each participant's view derives the threads, open issues, action items, common
    ground, corroboration, relations, topics, conclusions and summaries the item states
    (specification/discourse.md#threads-and-other-derived-structures)."""
    texts = {(i, k): t for i, k, _, t in MESSAGES}
    now = float(item["now"]) if "now" in item else None
    for party, expected in item["derived"].items():
        view = View(party)
        for k in deliveries(item, party):
            view.hear(texts[(item["id"], k)])
        assert compact(view, now, set(expected)) == expected


# Each item of the record's discourse, with the form that exercises it in the corpus's
# notation or, for a default, its normal forms.
DISCOURSE_ITEMS = {
    "referent status: physically present": "PRESENT)",
    "referent status: absent": "ABSENT)",
    "referent status: hypothetical": "EXISTENCE-COMMITMENT.WITHIN-A-SUPPOSITION",
    "referent status: fictional": "WITHIN-A-DECLARED-FICTION",
    "referent status: predicted": "PREDICTED-TO-EXIST",
    "referent status: impossible, contradictory": "ASSERTED-NOT-TO-EXIST",
    "referent status: uncertain":
        "INFERENCE UNCERTAIN (situation locate (UNDERGOER (term record INDEFINITE "
        "ASSERTED-TO-EXIST",
    "referent status: newly introduced": "INDEFINITE NEW SPECIFIC",
    "referent status: externally referenced":
        "EXTERNAL VERIFIED-BY-A-NAMED-THIRD-PARTY (SOURCE",
    "referent status: internally represented": "INTERNAL)",
    "referent status: mentioned, existence not asserted":
        "MENTIONED-WITHOUT-EXISTENCE-ASSERTED",
    "information structure: topic": "TOPIC",
    "information structure: focus": "FOCUS",
    "information structure: contrast": "CONTRASTIVE-FOCUS",
    "information structure: given information": "GIVEN",
    "information structure: inference": "INFERABLE",
    "information structure: presupposition": "PRESUPPOSED",
    "information structure: correction": "NONE (names 1 1",
    "information structure: unstated shared assumption":
        "RESTING-ON-AN-UNSTATED-ASSUMPTION",
    "reference: universal": "UNIVERSAL",
    "reference: existential": "EXISTENTIAL",
    "reference: definite": "DEFINITE",
    "reference: indefinite": "INDEFINITE",
    "reference: generic": "GENERIC",
    "reference: distributive": "QUANTIFIER.DISTRIBUTIVE",
    "reference: collective": "COLLECTIVE (q",
    "reference: approximate": "(q APPROXIMATELY 3)",
    "reference: at least": "(q AT-LEAST 3)",
    "reference: representative": "(q AS-A-REPRESENTATIVE-QUANTITY 3)",
    "reference: according to source A": "(SOURCE (term (party 1))) (situation count",
    "reference: fuzzy": "(q 2~4)",
    "discourse structure: summary": "(move SUMMARY NONE",
    "discourse structure: digression": "digresses",
    "discourse structure: elaboration": "elaborates",
    "discourse structure: quotation": "(quote",
    "discourse structure: unresolved question":
        "(move ISSUE QUESTION (situation POLAR run",
    "what came before: previous utterance": "(names-message 1 3)",
    "what came before: previous state":
        "ASSERTED-POSITION EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE part 1",
    "what came before: previous task": "(names 1 3 ISSUE REQUEST OPEN)",
    "what came before: previous assumption": "(names 1 2 SUPPOSITION",
    "participant: self": "SELF",
    "participant: interlocutor": "INTERLOCUTOR",
    "participant: third agent": "THIRD-AGENT",
    "participant: collective": "INCLUSIVE-COLLECTIVE JOINT",
    "participant: system": "(term SYSTEM)",
    "participant: tool": "(term TOOL)",
    "participant: environment": "(term ENVIRONMENT)",
    "participant: external source": "EXTERNAL-SOURCE",
}


def test_corpus_covers_every_item_of_discourse():
    from rowih.notation import Printer
    text = " ".join(m.get("notation", "") for item in items() for m in item["messages"])
    text += " ".join(Printer().move(n) for _, _, _, t in MESSAGES for n in api.parse(t).normal)
    missing = [k for k, needle in DISCOURSE_ITEMS.items() if needle not in text]
    assert missing == []
