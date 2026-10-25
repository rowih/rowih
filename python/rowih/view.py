"""One participant's view of the record
(specification/discourse.md#entries-and-their-handles): entries by handle, immutable apart
from their status, moves held until every entry they name arrives, messages applied at
most once, crossing moves ordered by the rule every participant computes, and the hearer's
own inferences kept apart from what its speakers said. There is no shared record, only
views; what a view derives from its record, the threads, the common ground, the
negotiations and the rest, is `discourse.py`'s and `coordination.py`'s."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field

from . import channels as channel_record
from .checker import entry_kind, move_class, short
from .diagnostics import Diagnostic
from .register_rules import shared_context
from .moves import (UNITS, _bare, _nodes, deadline_of, dependencies, find_named,  # noqa: F401
                    participant_binding, precedes, references, resolve_deixis, restates,
                    strip_name)
from .tree import strip_private


@dataclass
class Entry:
    handle: tuple                  # (author, number)
    kind: tuple                    # (adds, subkind)
    content: list                  # the move's constituents, in the normal form
    status: str
    move: dict                     # the move as written
    recipients: tuple = ()         # the recipients of the message that carried it
    normal: dict | None = None     # the move in the normal form, its head included
    time: float | None = None      # the communication time of its message
    names: tuple = ()              # the handles of the entries the move depends on
    # each change made to its status, as (the move that made it, the status before)
    changes: list = field(default_factory=list)
    received: object = None        # the move as received, which added it
    # held reduced: its content forgotten, its author, number, kind and status kept, so
    # that repair asks for its content alone
    # (specification/discourse.md#how-a-participant-receives-a-message)
    reduced: bool = False


@dataclass
class Inference:
    """What the viewing participant drew from what it heard: its own, never its
    speaker's (`inv.inference-not-said`)."""
    holder: str
    premises: tuple                # the handles it was drawn from
    content: list                  # nodes in the normal form
    kind: str                      # a resolution of readings, or an inference


@dataclass
class Received:
    """A move as the view received it, which the view may apply again in another order
    when it finds the move crossed another (specification/discourse.md#crossing-moves)."""
    sender: str
    t: dict
    n: dict
    recipients: tuple
    number: int
    time: float | None
    reduced: bool = False          # its content forgotten, as its entry's is
    # whether its checks of content, which read only its own content and that of what it
    # names, have passed; a replay keeps their result rather than reading again what
    # may since have been forgotten
    checked: bool = False
    # the numbers of the dialects its message names, under which a definition scoped to
    # a dialect gives its words their meaning (specification/discourse.md#definitions)
    dialects: tuple = ()

    @property
    def handle(self) -> tuple:
        return (self.sender, str(self.number))


@dataclass
class View:
    participant: str
    entries: dict = field(default_factory=dict)
    counts: dict = field(default_factory=dict)
    held: list = field(default_factory=list)
    inferences: list = field(default_factory=list)
    # each message applied, by its sender and the first entry its envelope states, which
    # names it whatever channel it came by
    # (specification/discourse.md#naming-entries-and-messages)
    messages: set = field(default_factory=set)
    participants: set = field(default_factory=set)
    # every move received, in the order the view applies them: the order of arrival,
    # except that of two moves that crossed the one the rule prefers comes first
    sequence: list = field(default_factory=list)
    # the moves a crossing move prevailed over, each with the handle of the one that did
    crossed: dict = field(default_factory=dict)
    # each participant number bound by a role setting to an agent's own identifier
    roster: dict = field(default_factory=dict)
    # each channel heard, by its sender and recipients (`channels.py`)
    channels: dict = field(default_factory=dict)
    # the public key the participant's own configuration holds for each agent, by the
    # agent's identifier; a message from an agent with a key must verify by it
    keys: dict = field(default_factory=dict)
    # what this participant reads (`releases.Reader`), every release this implementation
    # reads where it is None; what each participant's messages have stated of their
    # versions and dialects; and what each has stated it understands
    # (specification/protocol.md#versions-and-features)
    reader: object = None
    stated: dict = field(default_factory=dict)
    understood: dict = field(default_factory=dict)
    _reorder: tuple | None = None

    def __post_init__(self):
        self.participants.add(self.participant)

    # ------------------------------------------------------------ hearing
    def hear(self, text: str) -> list:
        """Interpret a message as this participant: parse and normalise it, which reads
        nothing the view holds (`inv.view-independent-normalisation`), then apply it."""
        from .api import parse
        return self.receive(parse(text, reader=self.reader))

    def receive(self, analysis) -> list:
        """Apply every move of a parsed message, in order. Returns diagnostics: a message
        damaged, held before, or refused by its authentication, an expectation not met, a
        stop whose restatement differs, a summary whose standing is not the one it keeps.
        A protocol message changes no record; `repair.Participant` reads it."""
        if analysis.message is None:
            return []
        env = analysis.message.envelope
        if env.is_protocol:
            return []
        if analysis.named:
            self.state(env.sender.text, analysis.named)
        from .authentication import refusal
        # a reader lacking authentication, which is may-ignore, verifies nothing, as a
        # view without the sender's key does
        # (specification/protocol.md#versions-and-features)
        failure = None if 10 in getattr(self.reader, "lacking", ()) else \
            refusal(self, analysis)
        if failure is not None:
            return [failure]
        noted = self.note(analysis)
        if noted is not None:
            return noted
        # an unknown word is kept opaque and does not stop the entries it stands in from
        # being held; any other diagnostic leaves the message held and not applied
        if any(d.recoverability != "kept opaque" for d in analysis.diagnostics):
            return []
        if env.forwarded is not None:
            # the speaker of a forwarded message is not its sender, and its envelope names
            # no other; a message is forwarded by relaying it byte for byte, which a
            # hearer applies as its own sender's once it verifies
            return [Diagnostic("d.view.forwarded", env.words[0].span,
                               note="a forwarded message's moves are not its sender's")]
        sender = env.sender.text
        recipients = tuple(r.text for r in env.recipients)
        first = env.first_entry.integer()
        self.messages.add((sender, str(first)))
        self.participants.add(sender)
        self.participants.update(recipients)
        try:
            time = float(env.time.text)
        except ValueError:
            time = None
        diags = []
        dialects = tuple(d[0] for d in analysis.named.get("dialects", ()))
        for i, (t, n) in enumerate(zip(analysis.moves, analysis.normal)):
            diags += self.apply(sender, t, n, recipients, number=first + i, time=time,
                                dialects=dialects)
        from .relay import carried
        for text in carried(analysis):
            from .api import parse
            inner = parse(text)
            if inner.message is not None and self.verified(inner):
                diags += self.receive(inner)
        return diags

    def state(self, participant: str, named: dict):
        """Record what a participant's message stated of its versions and dialects, which
        shows what that participant holds
        (specification/protocol.md#versions-and-features)."""
        record = self.stated.setdefault(participant, {
            "language": set(), "lexicon": set(), "protocol": set(), "dialects": set()})
        for kind in ("language", "lexicon", "protocol"):
            record[kind].add(named[kind])
        record["dialects"].update(tuple(d) for d in named["dialects"])

    def note(self, analysis):
        """Note a message on its channel (`channels.note`). Returns the diagnostics of one
        not to be applied, damaged or held before, or None for a message new to the view;
        a message sent again restores what the view holds reduced of it, and applies
        nothing a second time (`inv.at-most-once`)."""
        env = analysis.message.envelope
        kind = channel_record.note(self.channels, analysis)
        if kind == "damaged":
            return [Diagnostic("d.view.damaged", env.words[0].span,
                               note="message %d of agent %s arrived damaged and is asked "
                                    "for again" % (env.identifier.integer(),
                                                   env.sender.text))]
        if kind in ("duplicate", "serial-reused"):
            if kind == "duplicate":
                self.restore(analysis)
            return [Diagnostic("d.view.applied-before" if kind == "duplicate"
                               else "d.view.serial-reused", env.words[0].span,
                               note="a message is applied at most once")]
        return None

    def verified(self, analysis) -> bool:
        """Whether the participant's configuration holds a key for a message's sender and
        the message verifies by it: what a message forwarded byte for byte needs before
        its moves are taken as its sender's (specification/protocol.md#authentication)."""
        from .authentication import key_for, verify
        key = key_for(self, analysis)
        return key is not None and verify(analysis, key)

    # ------------------------------------------------------------ forgetting
    def forget(self, handles) -> list:
        """Forget the content of entries, keeping each reduced with its author, number,
        kind and status (specification/discourse.md#how-a-participant-receives-a-message),
        so that repair asks for content alone. Returns the handles reduced."""
        out = []
        for h in handles:
            e = self.entries.get(tuple(h))
            if e is None or e.reduced:
                continue
            e.reduced, e.content, e.normal = True, [], None
            e.move = dict(e.move, constituents=[])
            if e.received is not None:
                e.received.reduced = True
                e.received.t = dict(e.received.t, constituents=[])
                e.received.n = dict(e.received.n, constituents=[])
            out.append(e.handle)
        return out

    def held_reduced(self) -> list:
        """The handles of the entries held reduced, in order."""
        return sorted((h for h, e in self.entries.items() if e.reduced),
                      key=lambda h: (int(h[0]), int(h[1])))

    def restore(self, analysis) -> list:
        """Restore the content of each entry held reduced that a message sent again adds,
        from the message, which is the one that added it byte for byte. Returns the
        handles restored."""
        env = analysis.message.envelope
        sender, first = env.sender.text, env.first_entry.integer()
        out = []
        for i, (t, n) in enumerate(zip(analysis.moves, analysis.normal)):
            handle = (sender, str(first + i))
            for item in self.sequence + self.held:
                if item.handle == handle and item.reduced:
                    item.t, item.n, item.reduced = t, n, False
            e = self.entries.get(handle)
            if e is None or not e.reduced:
                continue
            e.content = self.content_of(t, n)
            e.normal, e.move, e.reduced = strip_private(n), strip_private(t), False
            out.append(e.handle)
        # what waited on the content restored is applied now
        self.release_held()
        while self._reorder is not None:
            self.replay()
        return out

    def content_of(self, t: dict, n: dict) -> list:
        """The content an entry holds: its move's constituents in the normal form, or,
        for an acceptance with the device of shared context, the content of the entry it
        names, or the part it names, with deixis resolved under its author
        (specification/discourse.md#common-ground)."""
        named = t.get("named")
        entry = None
        if named and named["ref"] == "names" and named["target"] == "entry":
            entry = self.entries.get((named["author"], named["number"]))
        if entry is not None and shared_context(t):
            taken = entry.content if named.get("part") is None else [
                strip_name(find_named(entry.content, named["part"]))]
            return resolve_deixis(copy.deepcopy(taken), entry.handle[0], entry.recipients)
        return copy.deepcopy(n["constituents"])

    def lacks(self) -> dict:
        """What this participant lacks of each channel it is a recipient of, as {(sender,
        recipients): serials} (`inv.gaps-known`)."""
        return channel_record.lacks(self.channels, self.participant)

    def apply(self, sender: str, t: dict, n: dict, recipients: tuple = (),
              number: int | None = None, time: float | None = None,
              dialects: tuple = ()) -> list:
        """Apply one move under the handle its author gave it, `number`, or, where none is
        given, the next in the view's count of the author's entries; then apply every held
        move that what it added releases. Where the move crossed one the view applied
        before it and the rule prefers it, the view applies everything again with the
        losing move after it, as the losing move's speaker does
        (specification/discourse.md#crossing-moves)."""
        if number is None:
            number = self.counts.get(sender, 0) + 1
        item = Received(sender, t, n, tuple(recipients), number, time,
                        dialects=tuple(dialects))
        self.sequence.append(item)
        diags = self.apply_one(item)
        diags += self.release_held()
        while self._reorder is not None:
            diags = self.replay()
        return diags

    def replay(self) -> list:
        """Move the move that lost a crossing to just after the one that prevailed, where
        everything the winner depends on is already held, and apply the whole sequence
        again from an empty record. Each reordering puts a move after one the rule ranks
        above it, so the replays end, and the record they reach depends on the moves and
        not on the order they arrived in (`inv.precedence-agreed`)."""
        winner, loser = self._reorder
        self._reorder = None
        order = [x for x in self.sequence if x is not loser]
        order.insert(next(i for i, x in enumerate(order) if x is winner) + 1, loser)
        self.entries, self.counts, self.held, self.crossed = {}, {}, [], {}
        self.roster, self.sequence = {}, []
        diags = []
        for item in order:
            self.sequence.append(item)
            if self._reorder is None:
                diags += self.apply_one(item)
                diags += self.release_held()
        return diags

    def apply_one(self, item: Received) -> list:
        sender, t, n, recipients, number, time = (item.sender, item.t, item.n,
                                                  item.recipients, item.number, item.time)
        missing = self.lacking_for(item)
        if missing:
            self.held.append(item)
            return [Diagnostic("d.view.held", t.get("_span"),
                               note="names %s, not held in full; the move is held"
                               % ", ".join("%s %s" % d[1:3] for d in missing))]
        for ref in references(t):
            failure = self.expectation(ref)
            if failure is not None:
                return self.crossing(item, ref) or [failure]
        named = t.get("named")
        entry = None
        if named and named["ref"] == "names" and named["target"] == "entry":
            entry = self.entries[(named["author"], named["number"])]
            # a move checked once keeps the result in a replay
            failure = None if item.checked else self.fit_and_restatement(
                sender, t, n, recipients, entry)
            if failure is not None:
                return [failure]
        if entry_kind(t["adds"])[0] == "summary" and not item.checked:
            failure = self.summary_standing(sender, t, n)
            if failure is not None:
                return [failure]
        if entry is not None:
            failure = self.deadline(t, entry, time)
            if failure is not None:
                return [failure]
        item.checked = True
        handle = (sender, str(number))
        if handle in self.entries:
            return [Diagnostic("d.view.handle-repeated", t.get("_span"),
                               note="%s %s is already an entry" % handle)]
        failure = self.binding(t) or self.definition(t, time)
        if failure is not None:
            return [failure]
        if entry is not None:
            self.effect(t, entry, item)
        self.counts[sender] = max(self.counts.get(sender, 0), number)
        adds, sub = entry_kind(t["adds"])
        status = "open" if adds == "issue" else "in-force"
        content = [] if item.reduced else self.content_of(t, n)
        self.entries[handle] = Entry(handle, (adds, sub), content,
                                     status, strip_private(t), tuple(recipients),
                                     None if item.reduced else strip_private(n), time,
                                     tuple(d[1:] for d in dependencies(t) if d[0] == "entry"),
                                     received=item, reduced=item.reduced)
        return []

    def lacking_for(self, item: Received) -> list:
        """What a move names that the view does not hold in full: entries and messages it
        lacks, and, for a move whose checks of content have not yet passed, entries it
        holds reduced, whose content those checks read
        (specification/discourse.md#how-a-participant-receives-a-message)."""
        out = [d for d in dependencies(item.t) if not self.holds(d)]
        if not item.checked:
            out += [d for d in dependencies(item.t) if d[0] == "entry" and self.holds(d)
                    and self.entries[(d[1], d[2])].reduced]
        return out

    def holds(self, dependency: tuple) -> bool:
        target, author, number = dependency[:3]
        if target == "message":
            return (author, number) in self.messages
        if target == "serial":
            channel = self.channels.get((author, tuple(dependency[3].split())))
            return channel is not None and int(number) in channel.received
        return (author, number) in self.entries

    def expectation(self, ref: dict):
        """Whether an entry a move names has the kind and status the move expects, and
        holds the part it names (`inv.dependencies-explicit`)."""
        entry = self.entries[(ref["author"], ref["number"])]
        expected_kind = entry_kind(ref["expected"])
        if entry.kind != expected_kind or entry.status != short(ref["status"]):
            return Diagnostic("d.view.expectation-not-met", ref.get("_span"),
                              expected=["%s %s, %s" % (expected_kind[0], expected_kind[1],
                                                       short(ref["status"]))],
                              detected=["%s %s, %s" % (entry.kind[0], entry.kind[1],
                                                       entry.status)])
        if ref.get("part") is not None and find_named(entry.content, ref["part"]) is None:
            return Diagnostic("d.view.expectation-not-met", ref.get("_span"),
                              expected=["a node named %d in %s %s"
                                        % ((ref["part"],) + entry.handle)])
        return None

    def fit_and_restatement(self, sender, t, n, recipients, entry: Entry):
        """A request is lowered by its author or by one it was sent to; a stop restates
        what it withdraws, by meaning with deixis resolved
        (specification/discourse.md#stops)."""
        named = t["named"]
        change = [short(c) for c in t["change"]]
        if change and change[0] == "lowering" and entry.kind == ("issue", "request") \
                and sender != entry.handle[0] and sender not in entry.recipients:
            return Diagnostic("d.checker.fit", named.get("_span"),
                              note="agent %s lowers a request of agent %s that was not "
                                   "sent to it" % (sender, entry.handle[0]))
        withdrawn = entry.content
        if named.get("part") is not None:
            # a reference to part of an entry reaches the node of that name in the
            # entry's normal form (specification/discourse.md#what-a-change-may-name)
            withdrawn = [strip_name(find_named(entry.content, named["part"]))]
        # a stop restates what it withdraws: every de-escalating move, and every pure
        # withdrawal; a correction adds a new position in the withdrawn one's place
        restating = move_class(t)["de-escalating"] or (
            change and change[0] == "lowering"
            and entry_kind(t["adds"])[0] == "nothing-beyond-its-own-record")
        if restating and not restates(
                resolve_deixis([strip_name(c) for c in n["constituents"]], sender, recipients),
                resolve_deixis(withdrawn, entry.handle[0], entry.recipients)):
            return Diagnostic("d.checker.stop-restatement", t.get("_span"),
                              note="the restatement differs from %s %s" % entry.handle)
        return None

    def summary_standing(self, sender: str, t: dict, n: dict):
        """A summary keeps the weakest basis and the lowest strength of what it names
        (`inv.summary-keeps-lowest`): each of its assertions states exactly the standing
        the order computes over the assertions of the entries it summarises."""
        from .data import load
        from .standing import lowest, standing_of, standings_of
        lang = load()
        summarised = [self.entries[(r["author"], r["number"])]
                      for r in [n["named"]] + list(n.get("also_named", []))]
        kept = lowest([s for e in summarised for s in standings_of(e.content, lang,
                                                                     e.handle[0])], lang)
        for c in n["constituents"]:
            if c["kind"] == "assertion" and standing_of(c, lang, sender) != kept:
                return Diagnostic("d.view.summary-standing", t.get("_span"),
                                  note="a summary keeps the lowest standing of what it "
                                       "summarises")
        return None

    def effect(self, t: dict, entry: Entry, item: Received | None = None):
        change = [short(c) for c in t["change"]]
        if not change or change[0] in ("none", "acknowledgement"):
            return
        if change[-1] == "on-acceptance":
            return
        prior = entry.status
        if change[0] == "resolution":
            # an offer or a delegation accepted binds from then on, and stays in force;
            # every other resolution closes what it names
            if not (change[1] == "acceptance" and entry.kind[0] == "normative-entry"):
                entry.status = "resolved"
        elif change[0] == "lowering":
            entry.status = "withdrawn" if "whole-entry" in change else "lowered"
        entry.changes.append((item, prior))
        if change[:2] == ["resolution", "acceptance"]:
            self.deferred(entry)

    def deferred(self, accepted: Entry):
        """Accepting a move whose change takes effect on acceptance makes that change: a
        counterproposal to an entry in force declines it once its own proposal is
        accepted, and not before
        (specification/discourse.md#changes-and-their-effects)."""
        named = accepted.move.get("named")
        change = [short(c) for c in accepted.move.get("change") or []]
        if not named or named.get("target") != "entry" or not change or \
                change[-1] != "on-acceptance":
            return
        target = self.entries.get((named["author"], named["number"]))
        if target is None or target.status not in ("open", "in-force"):
            return
        prior = target.status
        target.status = "resolved" if change[0] == "resolution" else (
            "withdrawn" if "whole-entry" in change else "lowered")
        target.changes.append((accepted.received, prior))

    def crossing(self, item: Received, ref: dict):
        """Two moves cross when each was made against an entry as it stood before the
        other changed it. Of the two, a move that lowers an entry in force prevails over
        one that does not; then the move of the entry's author; then the earlier
        communication time and the lower participant number
        (specification/discourse.md#crossing-moves). Returns the diagnostic of the move
        that loses, or None where the move did not cross another; where the arriving move
        prevails, the view will apply it again before the move it crossed."""
        entry = self.entries[(ref["author"], ref["number"])]
        if entry.kind != entry_kind(ref["expected"]):
            return None
        expected = short(ref["status"])
        for other, prior in entry.changes:
            if other is None or other is item or prior != expected:
                continue
            if precedes(item, other, entry):
                self._reorder = (item, other)
                return [Diagnostic("d.view.crossing", item.t.get("_span"),
                                   note="%s %s crossed %s %s and prevails"
                                   % (item.handle + other.handle))]
            self.crossed[item.handle] = other.handle
            return [Diagnostic("d.view.crossed", item.t.get("_span"),
                               note="%s %s crossed %s %s, which prevails"
                               % (item.handle + other.handle))]
        return None

    def deadline(self, t: dict, entry: Entry, time: float | None):
        """An issue, offer or delegation accepted after its deadline has lapsed: the
        deadline is the latest acceptable time for a response
        (specification/discourse.md#deadlines), and both views compute the lapse from the
        entry's deadline and the acceptance's communication time, which they share."""
        change = [short(c) for c in t["change"]]
        if change[:2] != ["resolution", "acceptance"] or time is None:
            return None
        limit = deadline_of(entry)
        if limit is not None and time > limit:
            return Diagnostic("d.view.deadline-passed", t.get("_span"),
                              note="%s %s lapsed at %s" % (entry.handle + (limit,)))
        return None

    def binding(self, t: dict):
        """A role setting that binds a participant number to an agent's own identifier
        (specification/discourse.md#roles): a number bound to one agent is not bound to
        another, nor one agent to two numbers."""
        bound = participant_binding(t)
        if bound is None:
            return None
        number, identifier = bound
        if self.roster.get(number, identifier) != identifier or any(
                k != number and v == identifier for k, v in self.roster.items()):
            return Diagnostic("d.view.participant-bound", t.get("_span"),
                              note="participant %s or agent %s is bound already"
                              % (number, identifier))
        self.roster[number] = identifier
        return None

    def definition(self, t: dict, time):
        """A definition of a term that a definition in force already defines shadows it,
        and is refused (specification/discourse.md#definitions; `inv.core-closed`)."""
        from .conventions import definition
        from .convention_rules import defined_term
        if entry_kind(t["adds"]) != ("setting", "definition"):
            return None
        word = defined_term(t)
        if word is not None and definition(self, word, time) is not None:
            return Diagnostic("d.view.term-defined", t.get("_span"),
                              note="%s is defined by a definition in force" % word)
        return None

    def release_held(self) -> list:
        """Apply each held move whose dependencies have all arrived, until none is
        released; a released move may release others."""
        diags = []
        progress = True
        while progress and self._reorder is None:
            progress = False
            for item in list(self.held):
                if not self.lacking_for(item):
                    self.held.remove(item)
                    diags += self.apply_one(item)
                    progress = True
                    if self._reorder is not None:
                        break
        return diags

    # ------------------------------------------------------------ what was said
    def said(self, handle: tuple) -> list:
        """What the record attributes to an entry's speaker: the content of its move in
        the normal form, at issue, presupposed, conventionally implied or resting on an
        assumption it leaves unstated, each with its status, or, for an acceptance with
        the device of shared context, the content of the entry it names; and nothing a
        hearer drew from it (`inv.inference-not-said`)."""
        return copy.deepcopy(self.entries[handle].content)

    def answers_for(self, handle: tuple) -> list:
        """What an entry's speaker answers for (specification/meaning.md#figures): its
        content with every figure replaced by what it means, every source set aside as
        mentioned and every word in the sense its frame selects. A hearer's reading of a
        figure whose content is not stated is its own inference, recorded by `infer`, and
        never stands in this content."""
        from .data import load
        from .figures import answers_for
        return answers_for(self.entries[handle].content, load())

    def infer(self, premises: list, content: list, kind: str = "inference") -> Inference:
        """Record what this participant draws from entries it holds, as its own."""
        for h in premises:
            if tuple(h) not in self.entries:
                raise KeyError(h)
        inference = Inference(self.participant, tuple(tuple(h) for h in premises),
                              copy.deepcopy(content), kind)
        self.inferences.append(inference)
        return inference

    def resolve(self, handle: tuple, reading: dict) -> Inference:
        """Record this participant's choice of one reading of a set an entry left open:
        the hearer's inference, never what the speaker said
        (specification/meaning.md#ambiguity)."""
        sets = [x for x in _nodes(self.entries[handle].content) if x.get("kind") == "readings"]
        if not any(_bare(reading) == _bare(r) for s in sets for r in s["readings"]):
            raise ValueError("not a reading of %s %s" % handle)
        return self.infer([handle], [reading], "resolution")
