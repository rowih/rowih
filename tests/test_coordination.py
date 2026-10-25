"""Negotiation and coordination (specification/discourse.md#negotiation): the items of
negotiation, coordination and relaying tied to the forms that exercise them; the
conventions of an exchange read from the record; crossing moves ordered alike in every
view over fault runs (`inv.precedence-agreed`); relays that keep provenance
(`inv.provenance-monotone`); and the external origin of what an agent read kept on what it
asks (`inv.external-origin-kept`). Each invariant test cites the requirements its
invariant serves."""
import random

from hypothesis import given, settings, strategies as st

from rowih import api, conventions as C, coordination as K, relay as R
from rowih.data import load
from rowih.generator import Generator, INSTRUCTION_RECEIVED
from rowih.moves import _nodes
from rowih.notation import Printer, Reader
from rowih.view import View

from corpus import items, messages

LANG = load()
GEN = Generator(LANG)
READ = Reader(LANG)
MESSAGES = messages()
TEXTS = {(i, k): t for i, k, _, t in MESSAGES}
IS = "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE"
T0 = 1759622400


def message(notation, sender=1, recipients=(2,), identifier=1, first=1, time=0):
    return GEN.message(READ.moves(notation), sender=sender, recipients=recipients,
                       identifier=identifier, first_entry=first, time=str(T0 + time))


# ---------------------------------------------------------------- what the corpus exercises

# Each item of negotiation, coordination and relaying, with the form that exercises it in
# the corpus's notation. Whether an agent is externally authenticated is a claim the
# language can make and not a check it performs: the claim is the verification of a
# referent by a named third party, and authentication of a message is checked by the
# authentication of a message (specification/protocol.md#authentication).
COORDINATION_ITEMS = {
    "coordination: establishes communication":
        "(move SETTING ROLE SPEAKERS-OWN (term (party 1) (data",
    "coordination: acknowledges":
        "ACKNOWLEDGEMENT WHOLE-ENTRY ON-THE-MOVE (names 1 2 SETTING ROLE",
    "coordination: capabilities": "(situation capable (HOLDER (term SELF))",
    "coordination: limitations": "(situation lack-tool (HOLDER (term SELF))",
    "coordination: available tools": "(UNDERGOER (term TOOL INDEFINITE))",
    "coordination: unavailable resources":
        "(situation lack-resource (HOLDER (term SELF)) (CONTENT (situation store (ACTOR "
        "(term SELF)) (UNDERGOER (term data (q AT-LEAST",
    "coordination: computational constraints": "(term budget (q EXACTLY 2 HOUR))",
    "coordination: permissions":
        "(situation PERMISSION BOUND STATUS-OF-A-NORMATIVE-STATE.IN-FORCE (HOLDER (term "
        "SELF))",
    "coordination: assigns a task":
        "NORMATIVE-ENTRY ASSIGNMENT BINDINGNESS.ON-ACCEPTANCE SPEAKERS-OWN (deadline",
    "coordination: accepts":
        "OUTCOME-OF-A-RESOLUTION.ACCEPTANCE WHOLE-ENTRY ON-THE-MOVE SPEAKERS-OWN (names "
        "1 1 NORMATIVE-ENTRY ASSIGNMENT",
    "coordination: rejects":
        "OUTCOME-OF-A-RESOLUTION.REJECTION WHOLE-ENTRY ON-THE-MOVE SPEAKERS-OWN (names "
        "1 1 NORMATIVE-ENTRY ASSIGNMENT",
    "coordination: negotiates":
        "WHEN-THE-CHANGE-TAKES-EFFECT.ON-ACCEPTANCE SPEAKERS-OWN (names 1 1 "
        "NORMATIVE-ENTRY ASSIGNMENT",
    "coordination: requests clarification":
        "(move ISSUE QUESTION NONE (names 1 1 NORMATIVE-ENTRY ASSIGNMENT",
    "coordination: reports completion":
        "OUTCOME-OF-A-RESOLUTION.SETTLEMENT WHOLE-ENTRY "
        "WHEN-THE-CHANGE-TAKES-EFFECT.ON-ACCEPTANCE ON-BEHALF-OF-A-NAMED-PRINCIPAL",
    "coordination: reports failure": "OUTCOME-OF-A-RESOLUTION.FAILURE WHOLE-ENTRY",
    "coordination: beliefs": "(assertion OBSERVATION CERTAIN (situation store COMPLETED",
    "coordination: assumptions": "(move SUPPOSITION (assertion (situation run",
    "coordination: objectives": "(situation GOAL HOLDERS-OWN (HOLDER (term SELF))",
    "coordination: plans":
        "(situation INTENTION HOLDERS-OWN (HOLDER (term #1 SELF)) (CONTENT (situation "
        "CONJUNCTION",
    "coordination: changes": "(situation change COMPLETED",
    "coordination: conflicts":
        "contrasts (assertion RETRIEVAL PROBABLE (situation store POLARITY.NEGATIVE",
    "coordination: conflicts with X":
        "(move ISSUE CHALLENGE NONE (names 1 1 ASSERTED-POSITION %s) "
        "(situation contradict" % IS,
    "coordination: confirmed":
        "(move NOTHING-BEYOND-ITS-OWN-RECORD LOWERING WHOLE-ENTRY ON-THE-MOVE "
        "(names 1 1 ASSERTED-POSITION %s) (assertion INFERENCE PROBABLE" % IS,
    "coordination: rejected because evidence Y":
        "(names 2 1 ISSUE CHALLENGE OPEN) (assertion OBSERVATION CERTAIN (SOURCE (term "
        "TOOL)) (situation support",
    "negotiation: proposal":
        "(move ISSUE PROPOSAL SPEAKERS-OWN (deadline 1 HOUR HENCE) (situation allocate",
    "negotiation: counterproposal":
        "(move ISSUE PROPOSAL RESOLUTION OUTCOME-OF-A-RESOLUTION.REJECTION WHOLE-ENTRY "
        "ON-THE-MOVE",
    "negotiation: conditional acceptance":
        "(CONDITION (situation increase (UNDERGOER (term budget",
    "negotiation: partial acceptance": "ACCEPTANCE PART-OF-IT ON-THE-MOVE",
    "negotiation: rejection":
        "(move NOTHING-BEYOND-ITS-OWN-RECORD RESOLUTION "
        "OUTCOME-OF-A-RESOLUTION.REJECTION WHOLE-ENTRY ON-THE-MOVE (names 1 1 ISSUE "
        "PROPOSAL OPEN)",
    "negotiation: compromise":
        "(names 2 1 ISSUE PROPOSAL OPEN) (situation allocate (ACTOR (term SELF)) "
        "(UNDERGOER (term share (q EXACTLY 40 percent",
    "negotiation: reservation":
        "contrasts (assertion INFERENCE PROBABLE (situation lack-resource",
    "negotiation: deadline": "(deadline 10 MINUTE HENCE)",
    "negotiation: priority":
        "(situation PREFERENCE HOLDERS-OWN (HOLDER (term SELF)) (CONTENT (situation "
        "CONJUNCTION",
    "negotiation: resource allocation":
        "(situation allocate (ACTOR (term SELF)) (UNDERGOER (term share",
    "negotiation: conflict resolution":
        "(names 1 1 ISSUE CHALLENGE OPEN) (assertion OBSERVATION CERTAIN (SOURCE (term "
        "SYSTEM))",
    "provenance: who supplied it": "(SOURCE (term (party 1))) (RELAYER (term SELF))",
    "provenance: when": "(OBSERVATION-TIME 2 HOUR AGO)",
    "provenance: by what process": "OBSERVATION PROBABLE (SOURCE (term TOOL))",
    "provenance: with what confidence": "(assertion INFERENCE PROBABLE",
    "provenance: independently verified": "INDEPENDENT (SOURCE",
    "provenance: hypothetical": "(move SUPPOSITION",
    "provenance: externally authenticated, as a claim":
        "VERIFIED-BY-A-NAMED-THIRD-PARTY (SOURCE",
}


def test_corpus_covers_every_item_of_coordination():
    """Each item of negotiation, coordination and relaying appears in the corpus."""
    text = " ".join(m.get("notation", "") for item in items() for m in item["messages"])
    missing = [k for k, needle in COORDINATION_ITEMS.items() if needle not in text]
    assert missing == []


# ---------------------------------------------------------------- the conventions

def test_a_participant_number_binds_one_agent():
    """A role setting binds a participant number to an agent's own identifier, and a
    second binding of either is refused (specification/discourse.md#roles)."""
    view = View("2")
    bind = '(move SETTING ROLE SPEAKERS-OWN (term (party %d) (data "text/plain" "%s")))'
    assert view.hear(message(bind % (1, "urn:a") + " " + bind % (2, "urn:b"))) == []
    assert C.roster(view) == {"1": "urn:a", "2": "urn:b"}
    again = message(bind % (2, "urn:c"), identifier=2, first=3, time=10)
    assert [d.code for d in view.hear(again)] == ["d.view.participant-bound"]
    twice = message(bind % (3, "urn:a"), identifier=3, first=4, time=20)
    assert [d.code for d in view.hear(twice)] == ["d.view.participant-bound"]
    assert C.roster(view) == {"1": "urn:a", "2": "urn:b"}


def test_silence_accepts_only_for_who_is_bound_to_it():
    """A convention proposed binds its proposer only once accepted, and binds no
    participant that did not accept it; retracting the commitment ends it."""
    assent = ("(situation assent (EVENT-TIME EXACTLY 60 SECOND) (ACTOR (term "
              "INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.DISTRIBUTIVE)))")
    view = View("1")
    view.hear(message("(move ISSUE PROPOSAL SPEAKERS-OWN %s)" % assent, recipients=(2, 3)))
    assert [C.silence(view, p) for p in "123"] == [None, None, None]
    view.hear(message("(move NORMATIVE-ENTRY COMMITMENT BOUND RESOLUTION "
                      "OUTCOME-OF-A-RESOLUTION.ACCEPTANCE WHOLE-ENTRY ON-THE-MOVE "
                      "SPEAKERS-OWN (names 1 1 ISSUE PROPOSAL OPEN) %s)" % assent,
                      sender=2, recipients=(1, 3), time=10))
    assert [C.silence(view, p) for p in "123"] == [60.0, 60.0, None]
    view.hear(message("(move NOTHING-BEYOND-ITS-OWN-RECORD LOWERING WHOLE-ENTRY ON-THE-MOVE "
                      "SPEAKERS-OWN (names 2 1 NORMATIVE-ENTRY COMMITMENT %s) %s)"
                      % (IS, assent), sender=2, recipients=(1, 3), identifier=2, first=2,
                      time=20))
    assert C.silence(view, "2") is None


def test_lineage_is_what_the_record_states():
    """A participant shares a lineage only with one an asserted position says it
    descends from."""
    view = View("1")
    assert C.lineage(view) == {"1": "1"}
    view.hear(message("(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
                      "descend (UNDERGOER (term SELF)) (CONTENT (term (party 2))))))",
                      sender=3, recipients=(1, 2)))
    assert C.lineage(view) == {"1": "1", "2": "2", "3": "2"}


def test_a_forwarded_message_is_not_taken_as_its_senders():
    """The speaker of a forwarded message is not its sender, and its envelope names no
    other (specification/protocol.md#relaying), so a view applies none of its moves."""
    moves = READ.moves("(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
                       "run (UNDERGOER (term service DEFINITE)))))")
    env = GEN.wr.envelope(1, (2,), str(T0), identifier=1, forwarded=True, first_entry=1)
    text = GEN.wr.message(env, [GEN.spell.move(t) for t in moves], integrity=True)
    assert api.parse(text).diagnostics == []
    view = View("2")
    assert [d.code for d in view.hear(text)] == ["d.view.forwarded"]
    assert view.entries == {}


def test_a_message_is_named_by_its_first_entry_across_channels():
    """Two messages of one sender, each the first on its own channel, share an
    identifier and differ in the first entry they state, which names each
    (specification/discourse.md#naming-entries-and-messages)."""
    item = next(i for i in items() if i["id"] == "e3-message-reference")
    view = View("3")
    for k in (1, 2, 3):
        assert view.hear(TEXTS[(item["id"], k)]) == []
    assert ("2", "1") in view.messages and ("2", "2") in view.messages
    ref = [r for r in _nodes(view.entries[("3", "1")].content) if r.get("kind") == "ref"]
    assert [(r["author"], r["number"]) for r in ref] == [("2", "2")]


def test_an_acceptance_after_the_deadline_is_refused_in_every_view():
    """Both views compute the lapse from the issue's deadline and the acceptance's
    communication time, which they share (specification/discourse.md#deadlines)."""
    item = next(i for i in items() if i["id"] == "e3-negotiation-ends")
    for party in "12":
        view = View(party)
        codes = [[d.code for d in view.hear(TEXTS[(item["id"], k)])] for k in range(1, 7)]
        assert codes[3] == ["d.view.deadline-passed"]
        assert ("2", "2") not in view.entries
        ends = [n["end"] for n in K.negotiations(view, T0 + 700)]
        assert ends == ["rejected", "open", "abandoned"]
        ends = [n["end"] for n in K.negotiations(view, T0 + 721)]
        assert ends == ["rejected", "lapsed", "abandoned"]


# ---------------------------------------------------------------- crossing moves

def _crossing_script(rng, parties):
    """An exchange of issues and the moves that cross on them, every message to every
    other participant: each issue, a request or a proposal, draws two or three moves made
    against it while it was open, acceptances, refusals, rejections, counterproposals
    and its author's cancellation or withdrawal, at times close enough that none of
    their speakers has seen the others; an acceptance is followed, now and then, by its
    speaker's report on what it took on, which names the acceptance's entry and so
    depends on it. Returns the messages, the stops among each issue's moves, and the
    handles of each issue's moves."""
    counts = {p: 0 for p in parties}
    script, issues = [], []
    t = 0
    content = ("(situation examine (ACTOR (term %s)) (UNDERGOER (term record DEFINITE)))")

    def send(sender, notation, when):
        counts[sender] += 1
        others = tuple(int(p) for p in parties if p != sender)
        script.append(message(notation, sender=int(sender), recipients=others,
                              identifier=counts[sender], first=counts[sender], time=when))
        return (sender, str(counts[sender]))

    for _ in range(rng.randint(2, 4)):
        author = rng.choice(parties)
        kind = rng.choice(["REQUEST", "PROPOSAL"])
        actor = "INTERLOCUTOR" if len(parties) > 2 else "(party %s)" % next(
            p for p in parties if p != author)
        issue = send(author, "(move ISSUE %s SPEAKERS-OWN %s)" % (kind, content % actor), t)
        named = "(names %s %s ISSUE %s OPEN)" % (issue[0], issue[1], kind)
        moves = []
        others = [p for p in parties if p != author]
        for responder in rng.sample(others + [author], rng.randint(2, len(others) + 1)):
            when = t + rng.randint(1, 40)
            notation = _response(rng, kind, responder == author, named, author,
                                 content, actor)
            handle = send(responder, notation, when)
            moves.append(handle)
            if "ACCEPTANCE" in notation and kind == "REQUEST" and rng.random() < 0.5:
                send(responder, "(move ASSERTED-POSITION RESOLUTION "
                     "OUTCOME-OF-A-RESOLUTION.SETTLEMENT WHOLE-ENTRY "
                     "WHEN-THE-CHANGE-TAKES-EFFECT.ON-ACCEPTANCE SPEAKERS-OWN (names %s %s "
                     "NORMATIVE-ENTRY OBLIGATION %s) (assertion OBSERVATION CERTAIN "
                     "(situation examine COMPLETED (ACTOR (term SELF)) (UNDERGOER (term "
                     "record DEFINITE)))))" % (handle[0], handle[1], IS), when + 50)
        issues.append((issue, moves))
        t += 100
    return script, issues


def _response(rng, kind, own, named, author, content, actor):
    """A move made against an open issue: its author's cancellation or withdrawal, or an
    addressee's refusal, counterproposal or acceptance."""
    if own:
        return ("(move NOTHING-BEYOND-ITS-OWN-RECORD LOWERING WHOLE-ENTRY ON-THE-MOVE %s%s %s)"
                % ("SPEAKERS-OWN " if kind == "REQUEST" else "", named, content % actor))
    if kind == "REQUEST" and rng.random() < 0.3:
        return ("(move NOTHING-BEYOND-ITS-OWN-RECORD LOWERING WHOLE-ENTRY ON-THE-MOVE "
                "SPEAKERS-OWN %s %s)" % (named, content % actor))
    if kind == "PROPOSAL" and rng.random() < 0.3:
        return ("(move ISSUE PROPOSAL RESOLUTION OUTCOME-OF-A-RESOLUTION.REJECTION WHOLE-ENTRY "
                "ON-THE-MOVE SPEAKERS-OWN %s %s)" % (named, content % "(party %s)" % author))
    adds = "OBLIGATION" if kind == "REQUEST" else "COMMITMENT"
    return ("(move NORMATIVE-ENTRY %s BOUND RESOLUTION OUTCOME-OF-A-RESOLUTION.ACCEPTANCE "
            "WHOLE-ENTRY ON-THE-MOVE SPEAKERS-OWN %s %s)" % (adds, named, content % "SELF"))


def _deliver(rng, script, party):
    """What one participant receives: every message, its own among them, each repeated
    now and then, in an order shuffled far enough that crossing moves arrive either
    way round and some arrive before what they name."""
    out = list(script)
    out += [m for m in script if rng.random() < 0.2]
    rng.shuffle(out)
    return out


def _record(view):
    return ({h: e.status for h, e in view.entries.items()}, dict(view.crossed),
            sorted(x.handle for x in view.held))


def test_crossing_moves_are_ordered_alike_in_every_view():
    """`inv.precedence-agreed` (serves `robust.damage`, `protocol.synchronisation`): over
    fault runs among two and three participants, in which every message is repeated and
    reordered and the moves on each issue cross, chains of crossings among them, every
    view holding the same moves reaches the same record, and on every issue a stop
    prevails over each crossing move that is not itself a stop."""
    rng = random.Random(41)
    crossings = stops_won = 0
    for run in range(120):
        parties = ["1", "2", "3"] if run % 2 else ["1", "2"]
        script, issues = _crossing_script(rng, parties)
        records = []
        for party in parties:
            view = View(party)
            for text in _deliver(rng, script, party):
                view.hear(text)
            records.append(_record(view))
            for issue, moves in issues:
                applied = [h for h in moves if h in view.entries]
                lost = [h for h in moves if h in view.crossed]
                assert len(applied) + len(lost) == len(moves)
                assert len(applied) == 1
                crossings += len(lost)
                stops = [h for h in moves if _is_stop(view, h, script)]
                if stops:
                    assert applied[0] in stops
                    stops_won += 1
        assert all(r == records[0] for r in records), run
    assert crossings > 300 and stops_won > 100


def _is_stop(view, handle, script):
    from rowih.checker import move_class
    for text in script:
        a = api.parse(text)
        env = a.message.envelope
        if env.sender.text == handle[0] and str(env.first_entry.integer()) == handle[1]:
            return move_class(a.moves[0])["de-escalating"]
    return False


# ---------------------------------------------------------------- provenance

BASES = ["OBSERVATION", "INFERENCE", "RETRIEVAL", "COMPUTATION", "REPORT", "SIMULATION",
         "TRAINED-KNOWLEDGE", "SOURCE-LOST"]
STRENGTHS = ["CERTAIN", "HIGHLY-PROBABLE", "PROBABLE", "UNCERTAIN", "SPECULATIVE"]
LINKS = ["(SOURCE (term TOOL))", "(SOURCE (term SYSTEM))", "(SOURCE (term (party 3)))",
         "(PREMISE (term evidence INDEFINITE))", ""]
TIMES = ["", "(OBSERVATION-TIME 2 HOUR AGO)", "(OBSERVATION-TIME NOW)"]
CONTENTS = ["(situation run POLARITY.NEGATIVE (UNDERGOER (term service DEFINITE)))",
            "(situation break (UNDERGOER (term network DEFINITE)))",
            "(situation store COMPLETED (ACTOR (term SELF)) (UNDERGOER (term record "
            "DEFINITE)))"]

grounds = st.tuples(st.sampled_from(BASES + [""]), st.sampled_from(STRENGTHS + [""]),
                    st.sampled_from(LINKS), st.sampled_from(TIMES),
                    st.sampled_from(CONTENTS))


def _position(g, sender=1, recipients=(2,), time=0):
    basis, strength, link, when, content = g
    if when.startswith("(OBSERVATION-TIME") and basis != "OBSERVATION":
        when = ""
    parts = " ".join(x for x in (basis, strength, link, when) if x)
    return message("(move ASSERTED-POSITION (assertion %s %s))" % (parts, content),
                   sender=sender, recipients=recipients, time=time)


@settings(max_examples=150, deadline=None)
@given(grounds)
def test_a_relay_keeps_every_provenance_fact_and_adds_the_relayer(g):
    """`inv.provenance-monotone` (serves `provenance.no-loss`, `provenance.chain`): a
    position relayed, and that relay relayed again as a message, each keep every fact of
    the provenance they were given and strengthen none; each adds the relayer and
    the participant it heard; and a relay that does not know a basis writes the
    unstated basis."""
    heard = View("2")
    assert heard.hear(_position(g)) == []
    entry = heard.entries[("1", "1")]
    before = R.provenance(entry.content, "1", entry.recipients)
    relayed = GEN.message([R.relay_position(entry)], sender=2, recipients=(3,),
                          time=str(T0 + 60))
    a = api.parse(relayed)
    assert a.diagnostics == []
    after = R.provenance(a.normal[0]["constituents"], "2", (3,))
    assert R.monotone(before, after, "2") == []
    assert ("2", "source", "1") in after and ("2", "relayer", "2") in after
    assert ("2", "basis", "g.standing.basis.report") in after
    assert ("2", "strength", "g.standing.strength.unstated") in after
    if not g[0]:
        assert ("1", "basis", "g.standing.basis.unstated") in after
    again = GEN.message([R.relay_message(relayed, "2")], sender=3, recipients=(4,),
                        time=str(T0 + 120))
    b = api.parse(again)
    assert b.diagnostics == []
    last = R.provenance(b.normal[0]["constituents"], "3", (4,))
    assert R.monotone(after, last, "3") == []
    assert ("3", "source", "2") in last and ("3", "relayer", "3") in last


def test_the_corpus_relays_keep_provenance():
    """Over the relay item, each relay holds every fact of what it relays."""
    item = next(i for i in items() if i["id"] == "e3-relay")
    graphs = []
    for k in (1, 2, 3):
        a = api.parse(TEXTS[(item["id"], k)])
        env = a.message.envelope
        graphs.append((env.sender.text, R.provenance(
            a.normal[0]["constituents"], env.sender.text,
            tuple(r.text for r in env.recipients))))
    for (_, before), (relayer, after) in zip(graphs, graphs[1:]):
        assert R.monotone(before, after, relayer) == []


def test_a_relay_written_by_a_view_is_the_corpus_relay():
    """The relay the toolchain writes for agent A's position is the one the corpus
    states, so that what a hearer reads back is what the relayer was given."""
    item = next(i for i in items() if i["id"] == "e3-relay")
    view = View("2")
    view.hear(TEXTS[(item["id"], 1)])
    written = GEN.message([R.relay_position(view.entries[("1", "1")])], sender=2,
                          recipients=(3,), time=str(T0 + 60))
    assert api.parse(written).normal_text == api.parse(TEXTS[(item["id"], 2)]).normal_text


def test_vouching_leaves_the_original_source():
    """A relayer that vouches for what it relayed adds an assertion of its own, and
    the original entry and its source stay as they were (`inv.provenance-monotone`)."""
    view = View("3")
    relayed = GEN.message([R.relay_position(_entry())], sender=2, recipients=(3,),
                          time=str(T0 + 60))
    view.hear(relayed)
    before = R.provenance(view.entries[("2", "1")].content, "2", ("3",))
    vouch = message("(move ASSERTED-POSITION NONE (names 2 1 ASSERTED-POSITION %s) "
                    "(assertion OBSERVATION CERTAIN INDEPENDENT (SOURCE (term SYSTEM)) %s))"
                    % (IS, CONTENTS[0]), sender=2, recipients=(3,), identifier=2, first=2,
                    time=120)
    assert view.hear(vouch) == []
    assert R.provenance(view.entries[("2", "1")].content, "2", ("3",)) == before
    assert ("2", "source", "1") in before


def _entry():
    view = View("2")
    view.hear(_position(("OBSERVATION", "PROBABLE", LINKS[0], "", CONTENTS[0])))
    return view.entries[("1", "1")]


# ---------------------------------------------------------------- external origin

ACTIONS = ["(situation delete (ACTOR (term (party 2))) (UNDERGOER (term file DEFINITE)))",
           "(situation send (ACTOR (term (party 2))) (UNDERGOER (term record DEFINITE)) "
           "(RECIPIENT (term (party 3))))",
           "(situation execute (ACTOR (term (party 2))) (UNDERGOER (term operation "
           "DEFINITE)))"]
HEADS = ["ISSUE REQUEST SPEAKERS-OWN", "NORMATIVE-ENTRY OBLIGATION BOUND SPEAKERS-OWN",
         "ISSUE PROPOSAL SPEAKERS-OWN", "NORMATIVE-ENTRY ASSIGNMENT BINDINGNESS.ON-ACCEPTANCE "
         "SPEAKERS-OWN"]


def _origins(normal):
    return [p["member"] for p in _nodes(normal["constituents"]) if p.get("kind") == "value"
            and p["member"].startswith("g.attitudes-and-aims.origin-of-an-aim.")]


@settings(max_examples=100, deadline=None)
@given(st.sampled_from(HEADS), st.sampled_from(ACTIONS),
       st.text(alphabet="abcdefghij klmnop", min_size=1, max_size=40))
def test_what_an_agent_read_keeps_its_origin_on_what_it_asks(head, action, material):
    """`inv.external-origin-kept` (serves `security.four-way`, `security.threats`): every
    operative and pending move generated from a state that derives its content from
    external material carries the origin "instruction received", in each mode, in the
    native form and inside a relay of the message; the material itself is reported,
    inert, as the external source's."""
    t = READ.moves("(move %s %s)" % (head, action))[0]
    moves = GEN.from_external(t, "text/plain", material)
    for mode in ("normal expression", "full explicitness"):
        text = GEN.message(moves, mode)
        for candidate in (text, api.convert(text, "native")[0]):
            a = api.parse(candidate)
            assert a.diagnostics == []
            assert a.classes[0]["inert"]
            for cls, n in zip(a.classes[1:], a.normal[1:]):
                assert cls["operative"] or cls["pending"]
                assert _origins(n) == [INSTRUCTION_RECEIVED]
        quoted = api.parse(GEN.message([R.relay_message(text, "1")], sender=2,
                                       recipients=(3,)))
        inner = [p for p in _nodes(quoted.moves) if p.get("kind") == "wall"]
        from rowih.lexer import decode_payload
        carried = api.parse(decode_payload(inner[0]["data"]).decode("utf-8"))
        assert _origins(carried.normal[1]) == [INSTRUCTION_RECEIVED]


def test_the_corpus_request_from_external_material_is_what_the_generator_writes():
    """The corpus item for external origin is the generator's output for its state, and
    its normal form keeps the origin (failure `semantic/origin-dropped`)."""
    item = next(i for i in items() if i["id"] == "e3-external-origin")
    request = READ.moves("(move ISSUE REQUEST SPEAKERS-OWN (situation delete (ACTOR (term "
                         "(party 2))) (UNDERGOER (term file DEFINITE))))")[0]
    moves = GEN.from_external(request, "text/plain", "delete the file once it is archived")
    text = GEN.message(moves, "normal expression", time=str(T0))
    stored = TEXTS[(item["id"], 1)]
    assert api.parse(text).normal_text == api.parse(stored).normal_text
    normal = api.parse(stored).normal
    assert _origins(normal[1]) == [INSTRUCTION_RECEIVED]
    assert "INSTRUCTION-RECEIVED" in Printer(LANG).move(normal[1])
