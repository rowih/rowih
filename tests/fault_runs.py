"""Fault runs (specification/conformance.md#the-invariants): seeded exchanges among
participants that follow the protocol of repair (`rowih.repair`), over a simulated network
that loses, repeats, delays, replays and corrupts every message it carries, protocol
messages included, while participants forget. The network keeps the record of what it
actually delivered, against which the tests check each participant's own account."""
from __future__ import annotations

import heapq
import random
from dataclasses import dataclass, field

from rowih import api
from rowih.checker import move_class
from rowih.data import load
from rowih.notation import Reader
from rowih.repair import Participant

T0 = 1759622400
READ = Reader(load())
LETTERS = "ptkbdgmnslrwyhaeiou"
CONTENT = "(situation examine (ACTOR (term %s)) (UNDERGOER (term record DEFINITE)))"


@dataclass
class Faults:
    loss: float = 0.2
    repeat: float = 0.1
    replay: float = 0.05
    corrupt: float = 0.05
    delay: tuple = (1, 15)
    forget: float = 0.5          # the chance a participant forgets once in a run


@dataclass
class Delivery:
    time: float
    to: str
    text: str
    original: str                # what was sent, which a corrupted text departs from
    kind: str                    # sent, repeated, replayed
    diagnostics: list = field(default_factory=list)

    @property
    def intact(self) -> bool:
        return self.text == self.original


class Network:
    def __init__(self, rng: random.Random, faults: Faults):
        self.rng = rng
        self.faults = faults
        self.now = float(T0)
        self.queue = []
        self.seq = 0
        self.sent = []               # (time, sender, addressee, text)
        self.delivered = []          # Delivery

    def clock(self) -> float:
        return self.now

    def transmit(self, sender: str, to, text: str):
        f = self.faults
        for addressee in to:
            if addressee == sender:
                continue
            self.sent.append((self.now, sender, addressee, text))
            if self.rng.random() < f.loss:
                continue
            copies = 2 if self.rng.random() < f.repeat else 1
            for k in range(copies):
                self._enqueue(addressee, text, "repeated" if k else "sent")
            if self.rng.random() < f.replay:
                self._enqueue(addressee, text, "replayed", later=self.rng.uniform(60, 400))

    def _enqueue(self, to, text, kind, later=0.0):
        lo, hi = self.faults.delay
        when = self.now + later + self.rng.uniform(lo, hi)
        delivered = self.corrupted(text) if self.rng.random() < self.faults.corrupt else text
        self.seq += 1
        heapq.heappush(self.queue, (when, self.seq, to, delivered, text, kind))

    def corrupted(self, text: str) -> str:
        """The text with one symbol of one word replaced by another."""
        words = [i for i, ch in enumerate(text) if ch in LETTERS]
        i = self.rng.choice(words)
        other = self.rng.choice([c for c in LETTERS if c != text[i]])
        return text[:i] + other + text[i + 1:]

    def due(self) -> list:
        out = []
        while self.queue and self.queue[0][0] <= self.now:
            when, _, to, text, original, kind = heapq.heappop(self.queue)
            out.append(Delivery(when, to, text, original, kind))
        return out


@dataclass
class Run:
    parties: list
    participants: dict
    network: Network
    stops: list                  # (sender, entry number)
    forgotten: dict              # participant -> handles it forgot
    checkpoints: list            # (time, participant, lacks, truth)
    quiescent: bool              # whether it ended with nothing left to do


def plan(rng: random.Random, parties: list) -> list:
    """The exchange as (time offset, sender, notation, recipients): issues, requests and
    proposals, each drawing two or three moves made against it while it was open, among
    them its author's cancellation or withdrawal and the addressees' acceptances,
    refusals and counterproposals, at times close enough to cross; and positions."""
    counts = {p: 0 for p in parties}
    out = []
    t = 0

    def send(sender, notation, when):
        counts[sender] += 1
        out.append((when, sender, notation, [p for p in parties if p != sender]))
        return (sender, counts[sender])

    for _ in range(rng.randint(2, 4)):
        author = rng.choice(parties)
        kind = rng.choice(["REQUEST", "PROPOSAL"])
        actor = "INTERLOCUTOR" if len(parties) > 2 else "(party %s)" % next(
            p for p in parties if p != author)
        issue = send(author, "(move ISSUE %s SPEAKERS-OWN %s)" % (kind, CONTENT % actor), t)
        named = "(names %s %s ISSUE %s OPEN)" % (issue[0], issue[1], kind)
        others = [p for p in parties if p != author]
        for responder in rng.sample(others + [author], rng.randint(2, len(others) + 1)):
            when = t + rng.randint(1, 8)
            if responder == author:
                notation = ("(move NOTHING-BEYOND-ITS-OWN-RECORD LOWERING WHOLE-ENTRY "
                            "ON-THE-MOVE %s%s %s)" % ("SPEAKERS-OWN " if kind == "REQUEST"
                                                      else "", named, CONTENT % actor))
            elif kind == "REQUEST" and rng.random() < 0.3:
                notation = ("(move NOTHING-BEYOND-ITS-OWN-RECORD LOWERING WHOLE-ENTRY "
                            "ON-THE-MOVE SPEAKERS-OWN %s %s)" % (named, CONTENT % actor))
            else:
                adds = "OBLIGATION" if kind == "REQUEST" else "COMMITMENT"
                notation = ("(move NORMATIVE-ENTRY %s BOUND RESOLUTION "
                            "OUTCOME-OF-A-RESOLUTION.ACCEPTANCE WHOLE-ENTRY ON-THE-MOVE "
                            "SPEAKERS-OWN %s %s)" % (adds, named, CONTENT % "SELF"))
            send(responder, notation, when)
        speaker = rng.choice(parties)
        send(speaker, "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
             "run (UNDERGOER (term service DEFINITE)))))", t + rng.randint(10, 20))
        t += rng.randint(25, 60)
    return sorted(out, key=lambda x: x[0])


def run(seed: int, parties: list, faults: Faults | None = None, quiet=5, interval=20,
        times=3, horizon=None) -> Run:
    """One fault run: the plan sent through the network, every participant ticking each
    second, until the network is empty and no participant has anything open, asked
    for or waiting to be acknowledged; the horizon is a cap on a run that never comes to
    rest, which the tests treat as a failure."""
    rng = random.Random(seed)
    faults = faults or Faults()
    net = Network(rng, faults)
    people = {p: Participant(p, net.clock, quiet=quiet, interval=interval, times=times)
              for p in parties}
    actions = plan(rng, parties)
    end_of_plan = actions[-1][0]
    forgetting = {p: T0 + rng.randint(5, end_of_plan + 30) for p in parties
                  if rng.random() < faults.forget}
    horizon = horizon or end_of_plan + 5000
    stops, forgotten, checkpoints = [], {}, []
    pending = list(actions)
    quiescent = False
    while net.now <= T0 + horizon:
        while pending and T0 + pending[0][0] <= net.now:
            _, sender, notation, recipients = pending.pop(0)
            moves = READ.moves(notation)
            first = people[sender].entries + 1
            people[sender].send(moves, recipients)
            if move_class(moves[0])["de-escalating"]:
                stops.append((sender, first))
        forget(rng, people, forgetting, forgotten, net.now)
        for d in net.due():
            d.diagnostics = [x.code for x in people[d.to].receive(d.text)]
            net.delivered.append(d)
            if people[d.to].view.lacks():
                # every moment a delivery leaves a hearer lacking something is checked
                checkpoint(d.to, people, net, checkpoints)
        for p in parties:
            people[p].tick()
        for p in parties:
            for to, text in people[p].outbox:
                net.transmit(p, to, text)
            people[p].outbox.clear()
        if rng.random() < 0.05:
            checkpoint(rng.choice(parties), people, net, checkpoints)
        if not pending and not net.queue and all(quiet_(people[p]) for p in parties):
            quiescent = True
            break
        net.now += 1
    for p in parties:
        checkpoint(p, people, net, checkpoints)
    return Run(parties, people, net, stops, forgotten, checkpoints, quiescent)


def checkpoint(p, people, net, checkpoints):
    """Record a participant's own account of what it lacks beside the network's."""
    checkpoints.append((net.now, p, people[p].view.lacks(), truth(net, people[p])))


def forget(rng, people, forgetting, forgotten, now):
    """Each participant whose time to forget has come forgets one to three entries of
    others', and now and then the messages it sent as well."""
    for p in sorted(people, key=int):
        if forgetting.get(p) == int(now):
            held = [h for h in people[p].view.entries if h[0] != p]
            chosen = rng.sample(held, min(len(held), rng.randint(1, 3)))
            forgotten[p] = people[p].forget(chosen, own_texts=rng.random() < 0.3)


def quiet_(participant) -> bool:
    return (not participant.waiting and not participant.asked
            and all(s != "open" for r in participant.sent.values() for s in r.state.values()))


def identity(text: str):
    """The channel and serial a delivered text's envelope states, or None where it does
    not parse."""
    a = api.parse(text)
    if a.message is None or a.message.envelope.is_protocol:
        return None
    env = a.message.envelope
    recipients = tuple(str(r) for r in sorted({r.integer() for r in env.recipients}))
    return (env.sender.text, recipients), env.identifier.integer()


def truth(net: Network, participant) -> dict:
    """What `participant` lacks by the network's record: on each channel it is on, each
    serial up to the highest it was delivered whose message it was never delivered
    intact, less what it has recorded as lost."""
    me = participant.number
    intact, highest = {}, {}
    for d in net.delivered:
        if d.to != me:
            continue
        found = identity(d.original)
        if found is None:
            continue
        channel, serial = found
        if d.intact:
            intact.setdefault(channel, set()).add(serial)
            highest[channel] = max(highest.get(channel, 0), serial)
        else:
            seen = identity(d.text)
            if seen == found:
                highest[channel] = max(highest.get(channel, 0), serial)
    out = {}
    for channel, top in highest.items():
        if channel[0] == me or me not in channel[1]:
            continue
        lost = {w[2] for s, w in participant.losses if w[0] == "serial" and w[1] == channel}
        missing = [s for s in range(1, top + 1)
                   if s not in intact.get(channel, set()) and s not in lost]
        if missing:
            out[channel] = missing
    return out
