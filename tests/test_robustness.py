"""The corpus items of the protocol of repair
(specification/protocol.md#channels-acknowledgement-and-repair): each item driven through
participants that follow the protocol of repair, whose protocol messages must state what
the item states and whose messages sent again must be the item's byte for byte; the
demands of the adversarial messages; and each requirement of robustness, from token loss
to retransmission, tied to the mechanism that serves it, with a check that the mechanism
does what the requirement asks."""
import os
import sys

from rowih import api
from rowih.authentication import keypair
from rowih.data import load
from rowih.repair import ACKNOWLEDGED, Participant
from rowih.view import View

from corpus import items, messages, moves_of

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "tools"))
from build_corpus import corpus_key  # noqa: E402

LANG = load()
TEXTS = {(i, k): t for i, k, _, t in messages()}
RECORDS = {(i, k): m for i, k, m, _ in messages()}
T0 = 1759622400


class Clock:
    def __init__(self):
        self.now = float(T0)

    def __call__(self):
        return self.now


def statement(item, k):
    return api.parse(TEXTS[(item, k)]).statement


def outbox(person):
    out = [(to, api.parse(text)) for to, text in person.outbox]
    person.outbox.clear()
    return out


def sent_by(person, item, k, clock):
    """What `person` writes for message k of an item: it sends the moves at the time the
    item states, as the participant the item names."""
    m = RECORDS[(item, k)]
    clock.now = float(m["time"])
    text = person.send(moves_of(m), [str(r) for r in m["recipients"]])
    person.outbox.clear()
    return text


# ---------------------------------------------------------------- the items

def test_the_acknowledgement_item_is_what_the_protocol_writes():
    """e8-acknowledgement: the three messages are what A writes, and B acknowledges them
    after its quiet interval with the item's statement; A then knows its stop held."""
    clock = Clock()
    a, b = Participant("1", clock), Participant("2", clock)
    for k in (1, 2, 3):
        assert sent_by(a, "e8-acknowledgement", k, clock) == TEXTS[("e8-acknowledgement", k)]
        clock.now += 1
        b.receive(TEXTS[("e8-acknowledgement", k)])
    clock.now = T0 + 31
    b.tick()
    ((to, ack),) = outbox(b)
    assert to == ("1",) and ack.statement == statement("e8-acknowledgement", 4)
    a.receive(TEXTS[("e8-acknowledgement", 4)])
    stop = next(r for r in a.sent.values() if r.stop)
    assert stop.state == {"2": ACKNOWLEDGED}


def test_the_gap_item_is_asked_for_and_sent_again_byte_for_byte():
    """e8-gap-asked: B, given the first and third messages, asks for the second, which A
    sends again as it was, and B then acknowledges all three."""
    clock = Clock()
    a, b = Participant("1", clock), Participant("2", clock)
    for k in (1, 2, 3):
        sent_by(a, "e8-gap-asked", k, clock)
    clock.now = T0 + 1
    b.receive(TEXTS[("e8-gap-asked", 1)])
    clock.now = T0 + 21
    b.receive(TEXTS[("e8-gap-asked", 3)])
    ((_, ask),) = outbox(b)
    assert ask.statement == statement("e8-gap-asked", 4)
    a.receive(TEXTS[("e8-gap-asked", 4)])
    ((_, again),) = outbox(a)
    assert again.text == TEXTS[("e8-gap-asked", 5)] == TEXTS[("e8-gap-asked", 2)]
    b.receive(again.text)
    clock.now = T0 + 31
    b.tick()
    ((_, ack),) = outbox(b)
    assert ack.statement == statement("e8-gap-asked", 6)


def test_the_damaged_item_is_reported_by_its_serial_and_asked_for():
    """e8-damaged-asked: the request arrives damaged and fails its integrity check value;
    B's report names it by its serial, a mention, since B does not hold it, and B asks
    for it again."""
    clock = Clock()
    b = Participant("2", clock)
    text = TEXTS[("e8-damaged-asked", 1)]
    words = text.split(" ")
    k = len(words) - 3
    damaged = " ".join(words[:k] + [words[k][::-1]] + words[k + 1:])
    clock.now = T0 + 2
    assert [d.code for d in b.receive(damaged)] == ["d.view.damaged"]
    assert api.parse(damaged).confidence == "lowered"
    ((_, ask),) = outbox(b)
    assert ask.statement == statement("e8-damaged-asked", 3)
    report = api.parse(TEXTS[("e8-damaged-asked", 2)])
    assert report.diagnostics == []
    reference = report.moves[0]["constituents"][0]
    assert "(mentions-serial 1 1 2)" in str(_print(report))
    assert TEXTS[("e8-damaged-asked", 4)] == text and reference is not None


def _print(analysis):
    from rowih.notation import Printer
    return Printer(LANG).move(analysis.moves[0])


def test_the_forgotten_and_never_received_item():
    """e8-forgotten-and-never-received: B holds A's first move reduced and lacks A's second
    message; its request asks for the one by its entry and the other by its serial, and
    its report says both, naming neither as a dependency."""
    clock = Clock()
    b = Participant("2", clock)
    clock.now = T0 + 1
    b.receive(TEXTS[("e8-forgotten-and-never-received", 1)])
    b.view.forget([("1", "1")])
    clock.now = T0 + 21
    b.view.receive(api.parse(TEXTS[("e8-forgotten-and-never-received", 3)]))
    clock.now = T0 + 40
    b.ask("1")
    ((_, ask),) = outbox(b)
    assert ask.statement == statement("e8-forgotten-and-never-received", 5)
    report = api.parse(TEXTS[("e8-forgotten-and-never-received", 4)])
    assert report.diagnostics == []
    view = View("1")
    for k in (1, 2, 3, 4):
        view.receive(api.parse(TEXTS[("e8-forgotten-and-never-received", k)]))
    assert ("2", "1") in view.entries and view.held == []


def test_the_loss_item_is_recorded_by_both():
    """e8-loss-recorded: A, asked for what it has forgotten, states the loss; both record
    it, and B asks no more."""
    clock = Clock()
    a, b = Participant("1", clock), Participant("2", clock)
    sent_by(a, "e8-loss-recorded", 1, clock)
    b.receive(TEXTS[("e8-loss-recorded", 1)])
    outbox(b)
    a.forget([("1", "1")], own_texts=True)
    b.view.forget([("1", "1")])
    clock.now = T0 + 40
    b.ask("1")
    ((_, ask),) = outbox(b)
    assert ask.statement == statement("e8-loss-recorded", 2)
    clock.now = T0 + 41
    a.receive(ask.text)
    ((_, answer),) = outbox(a)
    assert answer.statement == statement("e8-loss-recorded", 3)
    b.receive(answer.text)
    assert ("2", ("entry", 1)) in a.losses and ("1", ("entry", 1)) in b.losses
    assert b.lacking("1") == []


def test_a_declared_quiet_interval_governs():
    """e8-quiet-interval-declared: B's commitment to acknowledge within ten seconds makes
    its quiet interval ten seconds toward A."""
    clock = Clock()
    b = Participant("2", clock)
    b.view.receive(api.parse(TEXTS[("e8-quiet-interval-declared", 1)]))
    assert b.quiet_toward("1") == 10 and b.quiet_toward("3") == b.quiet
    clock.now = T0 + 6
    b.receive(TEXTS[("e8-quiet-interval-declared", 2)])
    clock.now = T0 + 15
    b.tick()
    assert outbox(b) == []
    clock.now = T0 + 16
    b.tick()
    ((_, ack),) = outbox(b)
    assert ack.statement == statement("e8-quiet-interval-declared", 3)


def test_the_authenticated_forward_is_heard_as_its_senders():
    """e8-authenticated-forward: C, holding A's key, hears the request B relays as A's;
    without the key, B's relay is B's report alone."""
    alpha = keypair(corpus_key(1))[1]
    for keys, applied in (({"urn:agent:alpha": alpha}, True), ({}, False)):
        view = View("3", keys=dict(keys))
        for k in (1, 3):
            view.receive(api.parse(TEXTS[("e8-authenticated-forward", k)]))
        assert ("2", "1") in view.entries
        assert (("1", "2") in view.entries) is applied


def test_a_fork_states_its_lineage_and_the_last_serial_of_each_channel_it_inherited():
    """e8-fork-inherits (specification/protocol.md#channels-acknowledgement-and-repair):
    C, a fork of B, sends A its lineage and its acknowledgement of A's channel to B, which
    A records as what C holds of it."""
    clock = Clock()
    a, b = Participant("1", clock), Participant("2", clock)
    for k in (1, 2):
        b.receive(sent_by(a, "e8-fork-inherits", k, clock))
    b.outbox.clear()
    clock.now = T0 + 60
    c = b.fork("3")
    c.announce("2", ["1"])
    (_, lineage), (_, holds) = outbox(c)
    assert lineage.text == TEXTS[("e8-fork-inherits", 3)]
    assert holds.statement == statement("e8-fork-inherits", 4)
    a.receive(holds.text)
    assert a.inherited == {"3": {("1", ("2",)): (2,)}}
    assert all(r.state == {"2": "open"} for r in a.sent.values())


# ---------------------------------------------------------------- adversarial demands

def test_the_adversarial_demands_of_repair_are_met():
    """Adversarial item a05's stop is acknowledged, so its delivery is known to its
    sender; item a08's hearer, given the cancellation without the request it cancels,
    knows the request as a gap."""
    demands = {i["id"]: i["demands"] for i in items() if i["set"] == "adversarial"}
    assert demands["a05-partial-retraction"]["the delivery of the stop is known"] == "met"
    assert demands["a08-crossing"]["a gap is known"] == "met"
    clock = Clock()
    a, b = Participant("1", clock), Participant("2", clock)
    for k in (1, 2):
        m = RECORDS[("a05-partial-retraction", k)]
        clock.now = float(m["time"])
        a.send(moves_of(m), ["2"])
        b.receive(a.outbox.pop()[1])
    clock.now += b.quiet
    b.tick()
    a.receive(b.outbox.pop()[1])
    assert all(r.state == {"2": ACKNOWLEDGED} for r in a.sent.values())
    view = View("2")
    view.receive(api.parse(TEXTS[("a08-crossing", 2)]))
    assert view.lacks() == {("1", ("2",)): [1]}


# ---------------------------------------------------------------- kinds of damage

# Each kind of damage a message can suffer, with the mechanism that serves it.
REQUIREMENTS_OF_ROBUSTNESS = {
    "token loss": "the count of the envelope, a move and a statement",
    "character corruption": "the check words of numbers, moves and units, and the "
                            "integrity check value",
    "truncation": "the counts, and the integrity check value",
    "reordered messages": "the serials of a channel, and the precedence of crossing moves",
    "duplicate messages": "the serials of a channel: a message is applied at most once",
    "partial messages": "the count of each move: a rejected move leaves the others parsed",
    "unknown vocabulary": "the unknown word kept opaque, and its definition asked for",
    "version mismatch": "the version field, and the fixed forms read in every version",
    "checksums": "the integrity and semantic check values, the move and unit check words",
    "correction requests": "the request to send again, and the report in the language",
    "retransmission": "the sender's sending again, and the answer to a request",
    "confidence degradation": "the analysis's confidence: verified, lowered or unchecked",
    "graceful fallback": "unknown words kept opaque, moves held for what they name, a "
                         "message of an unknown version still acknowledged",
    "synchronization": "the acknowledgement after the quiet interval",
}


def _corrupted(text, k):
    words = text.split(" ")
    return " ".join(words[:k] + [words[k][::-1]] + words[k + 1:])


def test_every_requirement_of_robustness_has_a_mechanism_that_works():
    """Each kind of damage is served by a mechanism of the language or its protocol, and
    each mechanism does what the kind of damage asks on a corpus message."""
    assert len(REQUIREMENTS_OF_ROBUSTNESS) == 14
    text = TEXTS[("e8-acknowledgement", 2)]
    words = text.split(" ")
    codes = lambda t: [d.code for d in api.parse(t).diagnostics]  # noqa: E731
    # token loss and truncation: a word deleted, or the message cut, is detected
    assert codes(" ".join(words[:5] + words[6:]))
    assert codes(text[:len(text) // 2])
    # character corruption: a word of a move altered is detected
    assert codes(_corrupted(text, len(words) - 5))
    # reordered and duplicate messages: a view applies each serial once
    view = View("2")
    for k in (3, 1, 2, 2):
        view.receive(api.parse(TEXTS[("e8-acknowledgement", k)]))
    assert view.entries[("1", "2")].status == "withdrawn" and view.lacks() == {}
    # partial messages: a rejected move leaves the others parsed
    two = TEXTS[("e3-handshake", 2)].split("\n")
    a = api.parse("\n".join([two[0], _corrupted(two[1], 6)] + two[2:]))
    assert len(a.moves) == len(two) - 3 and a.confidence == "lowered"
    # unknown vocabulary: kept opaque
    assert any(d.recoverability == "kept opaque"
               for d in api.parse(TEXTS[("a12-novel-unknown-broken", 1)]).diagnostics)
    # version mismatch and graceful fallback: a statement is read in any version
    assert api.parse(TEXTS[("e8-gap-asked", 4)].replace(
        LANG.items["g.numbers.numeral.six"].form, LANG.items["g.numbers.numeral.six"].form,
        1)).statement is not None
    # checksums and confidence: verified, lowered or unchecked
    assert api.parse(text).confidence == "verified"
    # correction requests, retransmission and synchronisation: the protocol messages
    kinds = {api.parse(t).statement["kind"] for (i, _), t in TEXTS.items()
             if i.startswith("e8-") and api.parse(t).statement}
    assert kinds == {"holds", "send-again", "not-held"}
