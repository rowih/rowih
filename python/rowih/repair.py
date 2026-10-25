"""The protocol of repair (specification/protocol.md#channels-acknowledgement-and-repair):
one participant of an exchange, with its view, the messages it has sent and the protocol
messages it exchanges, under a clock it is given rather than one it reads.

- The sender keeps each message it sends open until each addressee acknowledges it,
  sends it again to each addressee that has not, after the interval before sending
  again and up to the times sent again, and then records it as unacknowledged by that
  addressee (`inv.stop-delivery-known`, `inv.gaps-known`).
- Every addressee acknowledges a sender after its quiet interval, which runs from the
  first message it receives from that sender after its last acknowledgement to it,
  stating for each of the sender's channels it is on the last serial it holds with none
  missing before it and each serial it holds beyond that one, and carrying the integrity
  check value. A message sent again counts, so that an acknowledgement lost is
  replaced; a protocol message takes no serial, and none is acknowledged.
- The hearer asks for what it knows it lacks: a gap in a channel's serials or a
  damaged message, by its channel and serial, and the content of an entry it holds
  reduced, by the entry's number; it asks again after the interval, up to the times
  sent again, and then records a loss.
- A sender asked for what it holds sends it again byte for byte; asked for what it no
  longer holds, it says so, and both record a loss.

Crossing moves are ordered by the view (`View.crossing`); a protocol message changes no
record of the view.

A participant states what it understands to a peer (`negotiate`), records what each peer
states, writes to a peer whose statement it holds in the common subset of the two
(`negotiation.common`), and answers a message it cannot interpret by naming it and what it
lacks of it, with what it understands
(specification/protocol.md#versions-and-features)."""
from __future__ import annotations

from dataclasses import dataclass, field

from .checker import move_class
from .data import load
from .view import View

OPEN, ACKNOWLEDGED, UNACKNOWLEDGED = "open", "acknowledged", "unacknowledged"


@dataclass
class Sent:
    """A message this participant sent, with each addressee's state of it."""
    text: str | None               # None once the participant has forgotten sending it
    channel: tuple
    serial: int
    first: int                     # the first entry it adds
    entries: int                   # how many entries it adds
    stop: bool                     # whether it carries a de-escalating move
    state: dict = field(default_factory=dict)        # addressee -> OPEN, ...
    sendings: dict = field(default_factory=dict)     # addressee -> times sent
    last: dict = field(default_factory=dict)         # addressee -> time last sent
    # addressee -> the communication time of the acknowledgement that first stated it
    # held the message
    acknowledged_at: dict = field(default_factory=dict)


@dataclass
class Asked:
    """What this participant asked a sender for and does not yet hold."""
    times: int
    last: float


class Participant:
    def __init__(self, number: str, clock, view: View | None = None, signer=None,
                 quiet: float | None = None, interval: float | None = None,
                 times: int | None = None, reader=None):
        defaults = load().protocol["repair defaults"]
        self.number = str(number)
        self.view = view or View(self.number)
        if reader is not None:
            self.view.reader = reader
        self.clock = clock
        self.signer = signer          # a raw private key, which signs every message sent
        self.quiet = defaults["quiet interval"] if quiet is None else quiet
        self.interval = (defaults["interval before sending again"] if interval is None
                         else interval)
        self.times = defaults["times sent again"] if times is None else times
        self.sent: dict = {}          # (channel, serial) -> Sent
        self.serials: dict = {}       # channel -> the last serial sent on it
        self.entries = 0              # the count of this participant's own entries
        self.waiting: dict = {}       # sender -> time of the first message since the last
        self.asked: dict = {}         # (sender, what) -> Asked
        self.losses: set = set()      # (sender, ("serial", channel, s) | ("entry", n))
        self.outbox: list = []        # (addressee or addressees, text)
        self.acknowledgements = 0
        # what each fork holds of this participant's channels it inherited, by the fork's
        # acknowledgement of them
        self.inherited: dict = {}     # fork -> {channel: (last held, held beyond...)}
        # what each addressee stated it lacked of a message sent to it, by (addressee,
        # channel, serial), and the peers this participant has stated its holdings to
        self.uninterpreted: dict = {}
        self.stated_to: set = set()

    # ------------------------------------------------------------ sending
    def send(self, moves: list, recipients, time: float | None = None,
             dialects: tuple = ()) -> str:
        """Write and send a message of `moves` (move trees) to `recipients`, with the next
        serial of its channel and the next entries of this participant's count, enter it
        in this participant's own view, and keep it open for each addressee. The message
        is written in the common subset with a single addressee whose statement this
        participant holds, and names `dialects`, each (number, version), whose forms the
        moves use."""
        from .generator import Generator
        recipients = tuple(sorted(str(r) for r in recipients))
        channel = (self.number, recipients)
        serial = self.serials.get(channel, 0) + 1
        self.serials[channel] = serial
        first = self.entries + 1
        self.entries += len(moves)
        when = self.clock() if time is None else time
        signer = None
        if self.signer is not None:
            from .authentication import signer as make_signer
            signer = make_signer(self.signer)
        text = Generator(self.writing_release(recipients, dialects)).message(
            moves, sender=int(self.number),
                                         recipients=tuple(int(r) for r in recipients),
                                         identifier=serial, first_entry=first,
                                         time=_time_text(when), signer=signer)
        stop = any(move_class(t)["de-escalating"] for t in moves)
        record = Sent(text, channel, serial, first, len(moves), stop)
        now = self.clock()
        for r in recipients:
            if r != self.number:
                record.state[r], record.sendings[r], record.last[r] = OPEN, 1, now
        self.sent[(channel, serial)] = record
        self.view.hear(text)
        self.outbox.append((recipients, text))
        return text

    # ------------------------------------------------------------ hearing
    def receive(self, text: str) -> list:
        """Hear a message as this participant: a protocol message addressed to it is
        answered under the rules of repair; any other is given to the view, noted for
        the next acknowledgement and checked for what it shows to be lacking."""
        from .api import parse
        a = parse(text, reader=self.view.reader)
        if a.message is None:
            return a.diagnostics
        env = a.message.envelope
        if env.is_protocol:
            if a.statement is None or a.diagnostics or \
                    env.recipients[0].text != self.number:
                return a.diagnostics
            self.answer(env.sender.text, a.statement, float(env.time.text))
            return []
        diags = self.view.receive(a)
        sender = env.sender.text
        recipients = {r.text for r in env.recipients}
        if self.number in recipients and sender != self.number:
            if any(d.code == "d.view.authentication-failed" for d in diags):
                return diags
            self.waiting.setdefault(sender, self.clock())
            self.ask(sender)
            if a.lacking:
                self.report_lacking(sender, env, a.lacking)
        return diags

    def answer(self, peer: str, statement: dict, when: float):
        if statement["kind"] == "holds":
            self.acknowledged(peer, statement["parts"], when)
        elif statement["kind"] == "send-again":
            self.send_again(peer, statement["parts"])
        elif statement["kind"] == "understands":
            from .negotiation import read_statement
            self.view.understood[peer] = read_statement(statement["parts"])
        elif statement["kind"] == "lacks":
            from .negotiation import read_statement
            channel = statement["parts"][0]
            key = (peer, (self.number, tuple(str(r) for r in channel[1])), channel[2][0])
            self.uninterpreted[key] = read_statement(statement["parts"][1:])
        else:
            self.record_losses(peer, statement["parts"])

    # ------------------------------------------------------------ negotiating
    def negotiate(self, peer: str):
        """State to `peer` what this participant understands: the versions it reads, the
        dialects it offers for the exchange and the features it lacks (protocol 0.4)."""
        from .negotiation import understood_parts
        from .releases import FULL
        self.stated_to.add(str(peer))
        self.protocol(str(peer), "understands", understood_parts(self.view.reader or FULL))

    def report_lacking(self, sender: str, env, lacking: dict):
        """Name to `sender` a message of its this participant could not interpret, by its
        channel and serial, with what of it the participant lacks; and state what it
        understands, where it has not yet."""
        from .negotiation import lacks_parts
        channel = tuple(int(r.text) for r in env.recipients)
        self.protocol(sender, "lacks", lacks_parts(channel, env.identifier.integer(), lacking))
        if sender not in self.stated_to:
            self.negotiate(sender)

    def common_with(self, peer: str) -> dict | None:
        """The common subset of what this participant and `peer` understand, where `peer`
        has stated it."""
        from .negotiation import common, read_statement, understood_parts
        from .releases import FULL
        theirs = self.view.understood.get(str(peer))
        if theirs is None:
            return None
        return common(read_statement(understood_parts(self.view.reader or FULL)), theirs)

    def writing_release(self, recipients, dialects: tuple = ()):
        """The language a message to `recipients` is written in: the common subset with a
        single addressee whose statement this participant holds, and its own release
        otherwise, with the dialects the message uses."""
        shared = self.common_with(recipients[0]) if len(recipients) == 1 else None
        if shared is None:
            return load(None, None, tuple(dialects))
        return load(shared["lexicon"], shared["language"], tuple(dialects))

    def acknowledged(self, peer: str, parts: list, when: float):
        """An acknowledgement from `peer`, written at `when`: each message it states it
        holds is acknowledged by it, and no other (`inv.stop-delivery-known`)."""
        for part in parts:
            if part[0] != "channel":
                continue
            channel = (self.number, tuple(str(r) for r in part[1]))
            if peer not in channel[1]:
                # a fork acknowledging a channel it inherited from its ancestor: what it
                # holds of it, which gives it a grade of sharing
                self.inherited.setdefault(peer, {})[channel] = tuple(part[2])
                continue
            through, beyond = part[2][0], set(part[2][1:])
            for (ch, serial), record in self.sent.items():
                if ch == channel and peer in record.state and \
                        (serial <= through or serial in beyond):
                    if record.state[peer] != ACKNOWLEDGED:
                        record.acknowledged_at[peer] = when
                    record.state[peer] = ACKNOWLEDGED

    def send_again(self, peer: str, parts: list):
        """Send `peer` each message it asks for byte for byte, the message that added
        each entry it asks for included; say which it asks for that this participant no
        longer holds."""
        missing = []
        for part in parts:
            if part[0] == "channel":
                channel = (self.number, tuple(str(r) for r in part[1]))
                lost = []
                for serial in part[2]:
                    record = self.sent.get((channel, serial))
                    if record is None or record.text is None:
                        lost.append(serial)
                        self.losses.add((peer, ("serial", channel, serial)))
                    else:
                        self.outbox.append(((peer,), record.text))
                if lost:
                    missing.append(("channel", part[1], tuple(lost)))
            else:
                lost = []
                for n in part[1]:
                    record = next((r for r in self.sent.values()
                                   if r.first <= n < r.first + r.entries), None)
                    if record is None or record.text is None:
                        lost.append(n)
                        self.losses.add((peer, ("entry", n)))
                    else:
                        self.outbox.append(((peer,), record.text))
                if lost:
                    missing.append(("entries", tuple(lost)))
        if missing:
            self.protocol(peer, "not-held", missing)

    def record_losses(self, peer: str, parts: list):
        """A sender's statement that it no longer holds what was asked for: both record
        the loss, and this participant asks for it no more."""
        for part in parts:
            if part[0] == "channel":
                channel = (peer, tuple(str(r) for r in part[1]))
                record = self.view.channels.get(channel)
                for serial in part[2]:
                    if record is not None:
                        record.lost.add(serial)
                    self.losses.add((peer, ("serial", channel, serial)))
                    self.asked.pop((peer, ("serial", channel, serial)), None)
            else:
                for n in part[1]:
                    self.losses.add((peer, ("entry", n)))
                    self.asked.pop((peer, ("entry", n)), None)

    # ------------------------------------------------------------ asking
    def lacking(self, sender: str) -> list:
        """What this participant knows it lacks of `sender`'s: each serial missing or
        damaged on the sender's channels it is on, and each of the sender's entries it
        holds reduced, none recorded as lost."""
        out = []
        for (s, recipients), serials in sorted(self.view.lacks().items()):
            if s == sender:
                out += [("serial", (s, recipients), n) for n in serials]
        for author, number in self.view.held_reduced():
            if author == sender:
                out.append(("entry", int(number)))
        return [w for w in out if (sender, w) not in self.losses]

    def ask(self, sender: str, again: bool = False):
        """Ask `sender` for what this participant lacks of its messages and has not
        asked for, or, with `again`, for what it asked for an interval ago."""
        now = self.clock()
        lacking = self.lacking(sender)
        for k in [k for k in self.asked if k[0] == sender and k[1] not in lacking]:
            del self.asked[k]
        wanted = []
        for what in lacking:
            asked = self.asked.get((sender, what))
            if asked is None:
                self.asked[(sender, what)] = Asked(1, now)
                wanted.append(what)
            elif again and now - asked.last >= self.interval:
                if asked.times > self.times:
                    self.record_lost(sender, what)
                    continue
                asked.times += 1
                asked.last = now
                wanted.append(what)
        if wanted:
            self.protocol(sender, "send-again", _parts(wanted))

    def record_lost(self, sender: str, what: tuple):
        """A request asked as often as the protocol allows and never answered: the loss
        is recorded on this side, and asked for no more."""
        self.losses.add((sender, what))
        self.asked.pop((sender, what), None)
        if what[0] == "serial":
            record = self.view.channels.get(what[1])
            if record is not None:
                record.lost.add(what[2])

    def forget(self, handles, own_texts: bool = False) -> list:
        """Forget the content of entries, which the view keeps reduced, and ask each
        author for the content of its own. With `own_texts`, this participant also
        forgets having sent the messages that added its own entries among them."""
        reduced = self.view.forget(handles)
        if own_texts:
            own = {int(h[1]) for h in reduced if h[0] == self.number}
            for record in self.sent.values():
                if any(record.first <= n < record.first + record.entries for n in own):
                    record.text = None
        for author in sorted({h[0] for h in reduced if h[0] != self.number}, key=int):
            self.ask(author)
        return reduced

    # ------------------------------------------------------------ time
    def tick(self):
        """Do what the passing of time asks: acknowledge each sender whose quiet interval
        has run, send again what an addressee has not acknowledged, and ask again for
        what is still lacking."""
        now = self.clock()
        for sender in sorted(self.waiting, key=int):
            if now - self.waiting[sender] >= self.quiet_toward(sender):
                self.acknowledge(sender)
        for (channel, serial), record in sorted(self.sent.items()):
            for peer in sorted(record.state, key=int):
                if record.state[peer] == ACKNOWLEDGED or record.text is None:
                    continue
                if now - record.last[peer] < self.interval:
                    continue
                if record.sendings[peer] > self.times:
                    record.state[peer] = UNACKNOWLEDGED
                    continue
                record.sendings[peer] += 1
                record.last[peer] = now
                self.outbox.append(((peer,), record.text))
        for sender in sorted({s for s, _ in self.asked}, key=int):
            self.ask(sender, again=True)

    def quiet_toward(self, sender: str) -> float:
        """The quiet interval this participant keeps toward `sender`: the one it has
        committed itself to in the exchange, or the one it was configured with, which is
        the protocol register's default unless given."""
        from .conventions import quiet_interval
        declared = quiet_interval(self.view, self.number, sender)
        return declared if declared is not None else self.quiet

    def acknowledge(self, sender: str):
        """The acknowledgement to `sender`: for each of its channels this participant is
        on, the last serial held with none missing before it and each held beyond it."""
        parts = []
        for (s, recipients), record in sorted(self.view.channels.items()):
            if s == sender and self.number in recipients:
                parts.append(("channel", tuple(int(r) for r in recipients),
                              record.holding()))
        self.waiting.pop(sender, None)
        if parts:
            self.acknowledgements += 1
            self.protocol(sender, "holds", parts)

    def protocol(self, peer: str, kind: str, parts: list):
        """Send `peer` a protocol message: identifier and first entry zero, one recipient,
        the integrity check value, and the signature where this participant signs."""
        from .writer import Writer
        w = Writer(load())
        envelope = w.envelope(sender=int(self.number), recipients=(int(peer),),
                              time=_time_text(self.clock()), identifier=0, first_entry=0)
        signer = None
        if self.signer is not None:
            from .authentication import signer as make_signer
            signer = make_signer(self.signer)
        text = w.message(envelope, [w.statement(kind, parts)], integrity=True, signer=signer)
        self.outbox.append(((peer,), text))

    def fork(self, number: str) -> "Participant":
        """A fork of this participant: a new participant with its own number, holding a
        copy of this one's view, the entries' authors unchanged, and none of the messages
        this one sent, which stay this one's."""
        import copy
        child = Participant(number, self.clock, view=copy.deepcopy(self.view),
                            quiet=self.quiet, interval=self.interval, times=self.times)
        child.view.participant = str(number)
        child.view.participants.add(str(number))
        return child

    def announce(self, ancestor: str, counterparts) -> None:
        """A fork's first message to its counterparts: its lineage, then to each its
        acknowledgement of the counterpart's channels it inherited, stating the last
        serial of each."""
        from .notation import Reader
        moves = Reader(load()).moves(
            "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation descend "
            "(UNDERGOER (term SELF)) (CONTENT (term (party %s))))))" % ancestor)
        self.send(moves, counterparts)
        for peer in sorted(counterparts, key=int):
            parts = [("channel", tuple(int(r) for r in recipients), record.holding())
                     for (s, recipients), record in sorted(self.view.channels.items())
                     if s == str(peer) and str(ancestor) in recipients]
            if parts:
                self.protocol(str(peer), "holds", parts)

    def state_of(self, entry: int) -> dict:
        """Each addressee's state of the message that added this participant's entry."""
        for record in self.sent.values():
            if record.first <= entry < record.first + record.entries:
                return dict(record.state)
        return {}


def _parts(wanted: list) -> list:
    """The parts of a request: each channel's serials, then the entries."""
    channels, entries = {}, []
    for what in wanted:
        if what[0] == "serial":
            channels.setdefault(what[1][1], []).append(what[2])
        else:
            entries.append(what[1])
    parts = [("channel", tuple(int(r) for r in recipients), tuple(sorted(serials)))
             for recipients, serials in sorted(channels.items())]
    if entries:
        parts.append(("entries", tuple(sorted(entries))))
    return parts


def _time_text(when: float) -> str:
    return str(int(when)) if float(when).is_integer() else repr(float(when))

