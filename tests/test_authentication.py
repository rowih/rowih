"""Authentication of a message (specification/protocol.md#authentication):
`inv.authentication-covers-message`, tested as the invariants state
(specification/conformance.md#the-invariants), over the conformance corpus and generated
utterances; and the policy of a view that holds keys, which refuses what does not verify
and hears a message forwarded byte for byte as its own sender's once it does. The keys are
test fixtures, derived from the agent's name and published with the tests; no secret is
involved."""
import hashlib
import random

from hypothesis import given, settings, strategies as st

from rowih import api, authentication as A, relay as R
from rowih.data import load
from rowih.generator import Generator
from rowih.notation import Reader
from rowih.view import View
from rowih.writer import Writer

from corpus import messages, moves_of

LANG = load()
W = Writer(LANG)
GEN = Generator(LANG)
READ = Reader(LANG)
MESSAGES = messages()


def key(agent: str) -> tuple:
    """The test key pair of an agent: its private key is the SHA-256 of its name."""
    return A.keypair(hashlib.sha256(("rowih test key " + agent).encode()).digest())


def signed(text: str) -> str:
    sender = api.parse(text).message.envelope.sender.text
    return A.sign(text, key(sender)[0])


def reenveloped(text: str, **changes) -> str:
    """The signed message with its envelope written again with `changes`, its
    authentication kept and its integrity check value computed again, so that the
    authentication is the only check that can fail."""
    a = api.parse(text)
    env = a.message.envelope
    fields = {"sender": env.sender.text, "recipients": [r.text for r in env.recipients],
              "time": env.time.text, "identifier": env.identifier.integer(),
              "first_entry": env.first_entry.integer(),
              "semantic": env.semantic.integer() if env.semantic else None,
              "version": [v.text for v in env.version]}
    fields.update(changes)
    envelope = W.envelope(fields["sender"], fields["recipients"], fields["time"],
                          version=fields["version"], identifier=fields["identifier"],
                          semantic=fields["semantic"], first_entry=fields["first_entry"])
    envelope += [w.form for w in env.authentication.words]
    moves = [[w.form for w in line] for line in a.message.lines]
    return W.message(envelope, moves, integrity=env.integrity is not None)


def body_under(text: str, other: str) -> str:
    """The signed message's moves and authentication under the envelope of `other`."""
    a, b = api.parse(text), api.parse(other)
    envelope = [w.form for w in b.message.envelope.words
                if w not in b.message.envelope.integrity_words
                and (b.message.envelope.authentication is None
                     or w not in b.message.envelope.authentication.words)]
    envelope += [w.form for w in a.message.envelope.authentication.words]
    moves = [[w.form for w in line] for line in a.message.lines]
    return W.message(envelope, moves)


def _envelope(text: str) -> str:
    """The envelope's fields as written, which the authentication covers."""
    env = api.parse(text).message.envelope
    return " ".join(w.form for w in env.words if w not in env.integrity_words)


def verifies(text: str, agent: str) -> bool:
    a = api.parse(text)
    return a.message is not None and A.verify(a, key(agent)[1])


def test_every_signed_corpus_message_verifies_and_no_moved_body_does():
    """`inv.authentication-covers-message` (serves `goal.provenance-persistence`,
    `goal.channel-tolerance`): every signed corpus message verifies; each whose sender or
    time is altered, or whose body is moved under another envelope, fails; and each,
    quoted byte for byte in a relay, still verifies."""
    texts = [t for _, _, _, t in MESSAGES if api.parse(t).message is not None]
    envelopes = {t: _envelope(t) for t in texts}
    rng = random.Random(8)
    for text in texts:
        sender = api.parse(text).message.envelope.sender.text
        s = signed(text)
        assert [d.code for d in api.parse(s).diagnostics] == \
            [d.code for d in api.parse(text).diagnostics]
        assert verifies(s, sender)
        other = str(int(sender) % 9 + 1)
        assert not verifies(reenveloped(s, sender=other), other)
        assert not verifies(reenveloped(s, sender=other), sender)
        time = api.parse(s).message.envelope.time.text
        assert not verifies(reenveloped(s, time=str(int(float(time)) + 1)), sender)
        others = [t for t in texts if envelopes[t] != envelopes[text]]
        assert not verifies(body_under(s, signed(rng.choice(others))), sender)
        relayed = GEN.message([R.relay_message(s, sender)], sender=9, recipients=(int(sender),))
        (carried,) = R.carried(api.parse(relayed))
        assert carried == s and verifies(carried, sender)


@settings(max_examples=60, deadline=None)
@given(st.sampled_from([m for _, _, m, _ in MESSAGES]),
       st.integers(1, 6), st.integers(1, 6), st.integers(1, 999), st.integers(1, 10 ** 6))
def test_a_generated_message_signed_verifies_until_its_envelope_changes(
        record, sender, recipient, serial, offset):
    """The same, over generated utterances: corpus moves under generated envelopes."""
    if sender == recipient:
        recipient = sender % 6 + 1
    text = GEN.message(moves_of(record), sender=sender, recipients=(recipient,),
                       identifier=serial, first_entry=serial, time=str(1759622400 + offset))
    s = signed(text)
    assert verifies(s, str(sender))
    assert not verifies(reenveloped(s, identifier=serial % 999 + 1), str(sender))
    assert not verifies(reenveloped(s, recipients=[recipient % 6 + 1]), str(sender))


def test_the_integrity_value_covers_the_signature():
    """A signature damaged in transit fails the integrity check value, which is computed
    over the message with it, so damage is told from forgery."""
    s = signed(GEN.message(READ.moves("(move ASSERTED-POSITION (assertion OBSERVATION "
                                      "CERTAIN (situation run (UNDERGOER (term service "
                                      "DEFINITE)))))")))
    payload = api.parse(s).message.envelope.authentication.words[-1].form
    damaged = s.replace(payload, ("b" if payload[0] != "b" else "c") + payload[1:])
    codes = [d.code for d in api.parse(damaged).diagnostics]
    assert codes == ["d.check-values.integrity-mismatch"]


def _binding(view, number, agent):
    view.roster[number] = agent
    view.keys[agent] = key(agent)[1]


def test_a_view_that_holds_a_key_refuses_what_does_not_verify():
    """A message from an agent whose key the view holds must verify: one that does not is
    refused, and its serial is not taken as held, so that the genuine message is still
    received when it comes."""
    view = View("2")
    _binding(view, "1", "agent-a")
    moves = READ.moves("(move ISSUE REQUEST SPEAKERS-OWN (situation delete (ACTOR (term "
                       "(party 2))) (UNDERGOER (term file DEFINITE))))")
    genuine = A.sign(GEN.message(moves), key("agent-a")[0])
    forged = A.sign(GEN.message(moves), key("agent-x")[0])
    assert [d.code for d in view.receive(api.parse(forged))] == ["d.view.authentication-failed"]
    assert view.entries == {} and view.channels == {}
    assert view.receive(api.parse(genuine)) == []
    assert view.entries[("1", "1")].kind == ("issue", "request")


def test_a_message_forwarded_byte_for_byte_is_heard_as_its_senders_once_it_verifies():
    """Forwarding (specification/protocol.md#relaying): a relay that carries agent 1's
    signed request byte for byte is agent 3's report, and the request is agent 1's once it
    verifies by agent 1's key; carried unsigned, or signed by another, it is the report
    alone. Heard again directly, it is applied once."""
    moves = READ.moves("(move ISSUE REQUEST SPEAKERS-OWN (situation delete (ACTOR (term "
                       "(party 2))) (UNDERGOER (term file DEFINITE))))")
    original = GEN.message(moves, recipients=(2,))
    for carried, applied in ((A.sign(original, key("agent-a")[0]), True),
                             (original, False),
                             (A.sign(original, key("agent-x")[0]), False)):
        view = View("2")
        _binding(view, "1", "agent-a")
        relayed = GEN.message([R.relay_message(carried, "1")], sender=3, recipients=(2,))
        view.receive(api.parse(relayed))
        assert ("3", "1") in view.entries
        assert (("1", "1") in view.entries) is applied
        if applied:
            codes = [d.code for d in view.receive(api.parse(carried))]
            assert codes == ["d.view.applied-before"]
