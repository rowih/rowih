"""The protocol of repair (specification/protocol.md#channels-acknowledgement-and-repair):
the protocol message and its statements, and, over fault runs among two and three
participants in which every message, protocol messages included, is lost, repeated,
delayed, replayed and corrupted and participants forget, the invariants of the known gap
(`inv.gaps-known`) and the known delivery of a stop (`inv.stop-delivery-known`), repair
after forgetting by reduced entries, and one record in every view once repair ends
(`inv.precedence-agreed`)."""
import pytest

from rowih import api
from rowih.data import load
from rowih.notation import Reader
from rowih.repair import ACKNOWLEDGED, UNACKNOWLEDGED, Participant
from rowih.writer import Writer

import fault_runs as F

LANG = load()
W = Writer(LANG)
READ = Reader(LANG)
RUNS = [(seed, ["1", "2"] if seed % 2 else ["1", "2", "3"]) for seed in range(1, 81)]


@pytest.fixture(scope="module")
def runs():
    out = [F.run(seed, parties) for seed, parties in RUNS]
    assert all(r.quiescent for r in out)
    return out


# ---------------------------------------------------------------- the protocol message

def protocol(kind, parts, sender=2, recipient=1):
    env = W.envelope(sender=sender, recipients=(recipient,), identifier=0, first_entry=0)
    return W.message(env, [W.statement(kind, parts)])


def test_a_protocol_message_states_what_it_holds_asks_for_or_has_lost():
    """Each statement parses to what it states, whatever its parts
    (specification/protocol.md#protocol-messages)."""
    cases = [("holds", [("channel", (1,), (3,)), ("channel", (1, 3), (0, 2, 5))]),
             ("send-again", [("channel", (1,), (4, 6)), ("entries", (2, 9))]),
             ("not-held", [("entries", (7,))])]
    for kind, parts in cases:
        a = api.parse(protocol(kind, parts))
        assert a.diagnostics == []
        assert a.statement == {"kind": kind, "parts": [list(p) for p in parts]}
        assert a.moves == [] and a.normal == []


def test_a_protocol_message_takes_no_serial_and_adds_no_entry():
    """Identifier and first entry are zero together, with one recipient; anything else is
    refused, and a protocol message carries the integrity check value."""
    statement = W.statement("holds", [("channel", (1,), (1,))])
    bad = [W.envelope(sender=2, recipients=(1,), identifier=0, first_entry=1),
           W.envelope(sender=2, recipients=(1, 3), identifier=0, first_entry=0)]
    for env in bad:
        codes = [d.code for d in api.parse(W.message(env, [statement])).diagnostics]
        assert codes == ["d.parser.protocol-message"]
    env = W.envelope(sender=2, recipients=(1,), identifier=0, first_entry=0)
    codes = [d.code for d in api.parse(W.message(env, [statement], integrity=False)).diagnostics]
    assert codes == ["d.checker.integrity-value-required"]


def test_a_statement_is_read_whatever_version_its_message_states():
    """The fixed forms mean the same in every version: a protocol message that states a
    version this reader lacks is still read
    (specification/protocol.md#versions-and-features)."""
    env = W.envelope(sender=2, recipients=(1,), identifier=0, first_entry=0,
                     version=("0.9", "0.7", "0.3"))
    a = api.parse(W.message(env, [W.statement("send-again", [("entries", (3,))])]))
    assert a.diagnostics == [] and a.statement["kind"] == "send-again"


def test_every_single_edit_of_a_statement_is_detected_without_the_integrity_value():
    """The statement's count and check word, and its numbers' check words, detect every
    substitution, insertion and deletion of a word, the integrity check value aside."""
    text = protocol("holds", [("channel", (1, 3), (2, 5, 7))])
    words = text.split()
    k = words.index(W.w("g.integrity-check-value") if False else
                    W.w("g.message.message-field.integrity-check-value"))
    without = words[:k] + words[k + 1 + 10:]
    start = len(W.envelope(sender=2, recipients=(1,), identifier=0, first_entry=0))
    vocabulary = sorted({w for w in LANG.by_form if len(w) == 4})
    original = api.parse(" ".join(without)).statement
    assert original is not None
    for i in range(start, len(without)):
        edits = [without[:i] + without[i + 1:]]
        edits += [without[:i] + [w] + without[i + 1:] for w in vocabulary if w != without[i]]
        edits += [without[:i] + [w] + without[i:] for w in vocabulary]
        for edited in edits:
            a = api.parse(" ".join(edited))
            assert a.statement is None or a.statement == original, (i, edited[i - 1:i + 2])


# ---------------------------------------------------------------- one exchange, step by step

def test_a_lost_message_is_asked_for_and_its_stop_applies():
    """A message lost before a stop that names it: the stop is held, the gap asked for,
    the message sent again byte for byte, and both acknowledged."""
    now = [float(F.T0)]
    a, b = Participant("1", lambda: now[0]), Participant("2", lambda: now[0])
    request = READ.moves("(move ISSUE REQUEST SPEAKERS-OWN (situation delete (ACTOR (term "
                         "(party 2))) (UNDERGOER (term file DEFINITE))))")
    stop = READ.moves("(move NOTHING-BEYOND-ITS-OWN-RECORD LOWERING WHOLE-ENTRY ON-THE-MOVE "
                      "SPEAKERS-OWN (names 1 1 ISSUE REQUEST OPEN) (situation delete (ACTOR "
                      "(term (party 2))) (UNDERGOER (term file DEFINITE))))")
    first = a.send(request, ["2"])
    second = a.send(stop, ["2"])
    a.outbox.clear()
    assert [d.code for d in b.receive(second)] == ["d.view.held"]
    assert b.view.lacks() == {("1", ("2",)): [1]}
    (_, ask), = b.outbox
    b.outbox.clear()
    a.receive(ask)
    (_, again), = a.outbox
    assert again == first
    b.receive(again)
    assert b.view.entries[("1", "1")].status == "withdrawn" and b.view.lacks() == {}
    now[0] += b.quiet
    b.tick()
    for _, text in b.outbox:
        a.receive(text)
    assert {r.serial: r.state for r in a.sent.values()} == {1: {"2": ACKNOWLEDGED},
                                                            2: {"2": ACKNOWLEDGED}}


def test_an_entry_forgotten_is_asked_for_by_its_number_and_restored():
    """`I no longer hold your move 9`: the entry is kept reduced, its content alone is
    asked for, and the message that added it, sent again, restores it
    (specification/protocol.md#channels-acknowledgement-and-repair)."""
    now = [float(F.T0)]
    a, b = Participant("1", lambda: now[0]), Participant("2", lambda: now[0])
    position = READ.moves("(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
                          "run (UNDERGOER (term service DEFINITE)))))")
    b.receive(a.send(position, ["2"]))
    a.outbox.clear()
    content = b.view.entries[("1", "1")].content
    assert b.forget([("1", "1")]) == [("1", "1")]
    e = b.view.entries[("1", "1")]
    assert e.reduced and e.content == [] and e.kind == ("asserted-position", None)
    (_, ask), = b.outbox
    assert api.parse(ask).statement == {"kind": "send-again", "parts": [["entries", (1,)]]}
    a.receive(ask)
    (_, again), = a.outbox
    assert [d.code for d in b.receive(again)] == ["d.view.applied-before"]
    assert not b.view.entries[("1", "1")].reduced
    assert b.view.entries[("1", "1")].content == content


def test_an_entry_both_have_forgotten_is_a_loss_both_record():
    """Asked for what it no longer holds, a sender says so, and both record the loss."""
    now = [float(F.T0)]
    a, b = Participant("1", lambda: now[0]), Participant("2", lambda: now[0])
    position = READ.moves("(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
                          "run (UNDERGOER (term service DEFINITE)))))")
    b.receive(a.send(position, ["2"]))
    a.outbox.clear()
    a.forget([("1", "1")], own_texts=True)
    b.forget([("1", "1")])
    (_, ask), = b.outbox
    a.receive(ask)
    (_, answer), = a.outbox
    assert api.parse(answer).statement["kind"] == "not-held"
    b.receive(answer)
    assert ("2", ("entry", 1)) in a.losses and ("1", ("entry", 1)) in b.losses
    assert b.lacking("1") == []


# ---------------------------------------------------------------- fault runs

def test_a_hearer_knows_what_it_lacks(runs):
    """`inv.gaps-known`: in every fault run each hearer's account of what it lacks from
    each sender equals the messages withheld whose serials lie below the highest it
    received, every duplicate and replay is recognised, and every move stays open at its
    sender until it is acknowledged."""
    checked = gaps = duplicates = 0
    for r in runs:
        for when, p, lacks, truth in r.checkpoints:
            assert lacks == truth, (when, p)
            checked += 1
            gaps += sum(len(v) for v in truth.values())
        first = {}
        for d in r.network.delivered:
            if not d.intact or F.identity(d.original) is None:
                continue
            key = (d.to, F.identity(d.original))
            if key in first:
                assert "d.view.applied-before" in d.diagnostics
                duplicates += 1
            elif "d.view.authentication-failed" not in d.diagnostics:
                first[key] = d
        for person in r.participants.values():
            for record in person.sent.values():
                for peer, state in record.state.items():
                    if state == ACKNOWLEDGED:
                        assert peer in record.acknowledged_at
                    else:
                        assert peer not in record.acknowledged_at
    assert checked > 300 and gaps > 50 and duplicates > 50


def test_a_stops_delivery_is_known_to_its_sender(runs):
    """`inv.stop-delivery-known`: no sender records a message as acknowledged by an
    addressee that did not hold it when it acknowledged; every message ends recorded as
    acknowledged, or as unacknowledged after the declared number of sendings; every
    addressee acknowledges within its quiet interval; and every stop that reached a hearer
    is held in its view, in full or reduced."""
    stops = acknowledged = unacknowledged = 0
    for r in runs:
        held_at = {}
        for d in r.network.delivered:
            found = F.identity(d.original)
            if d.intact and found is not None:
                held_at.setdefault((d.to, found), d.time)
        transmissions = {}
        for when, sender, addressee, text in r.network.sent:
            transmissions[(sender, addressee, text)] = \
                transmissions.get((sender, addressee, text), 0) + 1
        for person in r.participants.values():
            for record in person.sent.values():
                for peer, state in record.state.items():
                    assert state in (ACKNOWLEDGED, UNACKNOWLEDGED)
                    if state == ACKNOWLEDGED:
                        acknowledged += 1
                        got = held_at.get((peer, (record.channel, record.serial)))
                        assert got is not None and got <= record.acknowledged_at[peer]
                    else:
                        # sent as often as the protocol allows, by the network's count
                        unacknowledged += 1
                        sent = transmissions.get((person.number, peer, record.text), 0)
                        assert sent >= 1 + person.times
        _acknowledged_in_time(r)
        for sender, entry in r.stops:
            stops += 1
            for peer, person in r.participants.items():
                record = next(x for x in r.participants[sender].sent.values()
                              if x.first == entry)
                if peer == sender or (peer, (record.channel, record.serial)) not in held_at:
                    continue
                view = person.view
                handle = (sender, str(entry))
                assert handle in view.entries or handle in view.crossed or any(
                    x.handle == handle for x in view.held)
    assert stops > 60 and acknowledged > 1000 and unacknowledged > 0


def _acknowledged_in_time(r):
    """Each message with moves an addressee received was acknowledged to its sender
    within the addressee's quiet interval, a tick of the clock allowed."""
    acks = {}
    for when, sender, addressee, text in r.network.sent:
        a = api.parse(text)
        if a.statement is not None and a.statement["kind"] == "holds":
            acks.setdefault((sender, addressee), []).append(when)
    for d in r.network.delivered:
        found = F.identity(d.text)
        if found is None:
            continue
        sender, me = found[0][0], d.to
        if me not in found[0][1] or "d.view.authentication-failed" in d.diagnostics:
            continue
        quiet = r.participants[me].quiet
        assert any(d.time <= t <= d.time + quiet + 1 for t in acks.get((me, sender), [])), \
            (me, sender, d.time)


def test_repair_after_forgetting_asks_for_content_alone(runs):
    """Repair after forgetting
    (specification/protocol.md#channels-acknowledgement-and-repair): every entry a
    participant forgot is, once repair ends, restored from the message that added it or
    recorded as lost by both, unless a later crossing ranked its move below another, in
    which case it is no entry and its content is not asked for."""
    forgotten = restored = lost = 0
    for r in runs:
        for p, handles in r.forgotten.items():
            person = r.participants[p]
            for h in handles:
                forgotten += 1
                if h in person.view.crossed:
                    continue
                e = person.view.entries[h]
                if e.reduced:
                    assert (h[0], ("entry", int(h[1]))) in person.losses
                    lost += 1
                else:
                    restored += 1
    assert forgotten > 30 and restored > 20


def test_views_reach_one_record_once_repair_ends(runs):
    """`inv.precedence-agreed`, `inv.entries-immutable`: in every run where repair ended
    with nothing lost, every view holds the same record, crossings ordered alike, and
    every entry holds the content its author's message gave it, corrupted deliveries
    notwithstanding."""
    complete = crossings = 0
    for r in runs:
        originals = {}
        for when, sender, addressee, text in r.network.sent:
            a = api.parse(text)
            if a.message is None or a.message.envelope.is_protocol:
                continue
            env = a.message.envelope
            for i, n in enumerate(a.normal):
                originals[(env.sender.text, str(env.first_entry.integer() + i))] = n
        for person in r.participants.values():
            for h, e in person.view.entries.items():
                if not e.reduced:
                    from rowih.tree import strip_private
                    assert e.normal == strip_private(originals[h])
        if any(person.losses for person in r.participants.values()) or any(
                s == UNACKNOWLEDGED for person in r.participants.values()
                for record in person.sent.values() for s in record.state.values()):
            continue
        complete += 1
        records = [({h: e.status for h, e in person.view.entries.items()},
                    dict(person.view.crossed)) for person in r.participants.values()]
        assert all(x == records[0] for x in records)
        crossings += len(records[0][1])
    assert complete > 40 and crossings > 20
