"""The conventions of an exchange, which its participants state in the language and a view
reads from its record (specification/discourse.md#how-a-participant-receives-a-message):
the agent each participant number names, the lineage each participant shares, and the
interval over which a participant's silence is its acceptance. None is given to a view
from outside; each is recomputed from the entries, so nothing here can disagree with
them."""
from __future__ import annotations

from .checker import entry_kind, short
from .data import load
from .moves import resolve_deixis
from .temporal import UNIT_SECONDS, seconds

ASSENT, DESCEND, ACKNOWLEDGE = "assent", "descend", "acknowledge"
INCLUSIVE = "g.reference.person.inclusive-collective"


def _key(situation: dict) -> str | None:
    """The lexicon key of the word a situation is about, or None."""
    lang = load()
    for p in situation.get("parts", []):
        if p.get("kind") == "word" and p.get("entry"):
            entry = lang.entries.get(p["entry"])
            return entry["key"] if entry else None
    return None


def _filler(situation: dict, role: str):
    for p in situation.get("parts", []):
        if p.get("kind") == "filler" and short(p["role"]) == role:
            return p["filler"]
    return None


def _situations(nodes: list):
    """The situations a content says, those of its assertions among them, without
    descending into what they report."""
    for c in nodes:
        if c.get("kind") == "situation":
            yield c
        elif c.get("kind") == "assertion":
            yield from (p for p in c["parts"] if p.get("kind") == "situation")


def participants_of(term, speaker: str, recipients: tuple) -> set:
    """The participants a term names: a party, the speaker, the one interlocutor, or the
    speaker together with its recipients for the inclusive collective."""
    if not term or term.get("kind") != "term":
        return set()
    resolved = resolve_deixis(term, speaker, recipients)
    out = {p["number"] for p in resolved["parts"] if p.get("kind") == "party"}
    if any(p.get("kind") == "value" and p["member"] == INCLUSIVE for p in resolved["parts"]):
        out |= {speaker} | set(recipients)
    return out


def lineage(view) -> dict:
    """Each participant's lineage, named by its least participant number: participants an
    asserted position in force says descend one from another, as a fork or another
    instance of one model, share one
    (specification/discourse.md#summaries-and-confirmations). A statement of shared
    lineage can only lower what a confirmation counts, so the view honours one by any
    participant; without one, each participant is its own lineage."""
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            x = parent[x]
        return x
    for e in sorted(view.entries.values(), key=lambda e: e.handle):
        if e.kind[0] != "asserted-position" or e.status != "in-force":
            continue
        for s in _situations(e.content):
            if _key(s) != DESCEND:
                continue
            ones = participants_of(_filler(s, "undergoer"), e.handle[0], e.recipients)
            others = participants_of(_filler(s, "content"), e.handle[0], e.recipients)
            for a in ones:
                for b in others:
                    ra, rb = find(a), find(b)
                    if ra != rb:
                        low, high = sorted((ra, rb), key=int)
                        parent[high] = low
    return {p: find(p) for p in set(parent) | set(view.participants)}


def _interval(situation: dict):
    for p in situation.get("parts", []):
        if p.get("kind") == "time" and short(p["index"]) == "event-time" and \
                p["spec"]["kind"] == "duration":
            value = seconds(p["spec"]["number"])
            if value is not None:
                return value[1] * UNIT_SECONDS[short(p["spec"]["unit"])]
    return None


def silence(view, participant: str):
    """The interval, in seconds, after which `participant`'s silence toward a position it
    received is its acceptance, or None, where only its explicit acceptance counts
    (specification/discourse.md#how-a-participant-receives-a-message). A silence counts
    only where the participant itself is bound to the convention: by its own commitment in
    force, or by its proposal of the convention once another accepted it, since a proposer
    answers for its own part once accepted. Of several, the shortest governs, being the
    first to elapse."""
    found = _committed(view, participant, ASSENT)
    return min(found) if found else None


def quiet_interval(view, participant: str, sender: str | None = None):
    """The interval, in seconds, within which `participant` has bound itself to
    acknowledge what it receives
    (specification/protocol.md#channels-acknowledgement-and-repair), toward `sender` where
    one is given, or None, where the protocol register's default holds. It is declared as
    the grounding criterion is, by the participant's own commitment or its accepted
    proposal, and of several the shortest governs."""
    found = _committed(view, participant, ACKNOWLEDGE, sender)
    return min(found) if found else None


def _committed(view, participant: str, key: str, recipient: str | None = None) -> list:
    """The intervals of every situation keyed `key` whose actor is `participant`, in its
    commitments in force and its proposals another accepted, toward `recipient` where
    the situation names one and one is given."""
    found = []
    for e in view.entries.values():
        if e.handle[0] != participant:
            continue
        bound = (e.kind == ("normative-entry", "commitment") and e.status == "in-force") or (
            e.kind == ("issue", "proposal") and e.status == "resolved" and _accepted(view, e))
        if not bound:
            continue
        for s in _situations(e.content):
            actors = participants_of(_filler(s, "actor"), e.handle[0], e.recipients)
            interval = _interval(s)
            if _key(s) != key or participant not in actors or interval is None:
                continue
            whom = _filler(s, "recipient")
            if recipient is not None and whom is not None and recipient not in \
                    participants_of(whom, e.handle[0], e.recipients):
                continue
            found.append(interval)
    return found


def _accepted(view, proposal) -> bool:
    """Whether a commitment in force accepts the whole of `proposal`."""
    for e in view.entries.values():
        named = e.move.get("named")
        change = [short(c) for c in e.move.get("change") or []]
        if e.kind == ("normative-entry", "commitment") and e.status == "in-force" and \
                change[:2] == ["resolution", "acceptance"] and named and \
                (named["author"], named["number"]) == proposal.handle:
            return True
    return False


def roster(view) -> dict:
    """The agent identifier each participant number is bound to, by the role settings in
    the view (specification/discourse.md#roles)."""
    return dict(view.roster)


def settings(view) -> list:
    """Every setting in force, by handle, with its kind."""
    return [{"entry": e.handle, "kind": entry_kind(e.move["adds"])[1]}
            for e in sorted(view.entries.values(), key=lambda e: e.handle)
            if e.kind[0] == "setting" and e.status == "in-force"]


def defined_term(entry) -> str | None:
    """The word a definition entry defines, or None for any other entry."""
    if entry.kind != ("setting", "definition"):
        return None
    from .convention_rules import defined_term as term_of
    return term_of(entry.move, None)


def in_force_at(entry, time) -> bool:
    """Whether an entry was in force at a communication time: added at or before it, and
    not lowered before it. A definition never reaches a message earlier than itself
    (specification/lexicon.md#coining-a-word-by-definition)."""
    if time is None or entry.time is None or entry.time > time:
        return False
    for item, prior in entry.changes:
        if prior == "in-force" and item.time is not None and item.time <= time:
            return False
    return entry.status == "in-force" or bool(entry.changes)


def definition(view, word: str, time, dialects: tuple = ()):
    """The definition entry that gives `word` its meaning in a message sent at `time`
    naming the dialects `dialects`, by number, or None: the meaning of a message is fixed
    by the definitions in force at its communication time
    (specification/lexicon.md#coining-a-word-by-definition), and a definition scoped to a
    dialect gives a word its meaning only in a message that names that dialect
    (specification/dialects.md#naming-a-dialect-in-a-message)."""
    from .convention_rules import scope_of
    for e in sorted(view.entries.values(), key=lambda e: e.handle):
        if defined_term(e) == word and in_force_at(e, time):
            scope = scope_of(e.move)
            if scope is None or scope in dialects:
                return e
    return None


def terms(view) -> list:
    """Every term defined in the exchange: its definition, the definition's status, and
    the entries whose words it gives a meaning, each read under the definition in force
    when its message was sent."""
    out = []
    for e in sorted(view.entries.values(), key=lambda e: e.handle):
        word = defined_term(e)
        if word is None:
            continue
        uses = [u.handle for u in sorted(view.entries.values(), key=lambda u: u.handle)
                if u is not e and any(n.get("kind") == "word" and n.get("form") == word
                                      and n.get("status") == "unknown"
                                      for n in _walk(u.content))
                and definition(view, word, u.time,
                               u.received.dialects if u.received is not None else ()) is e]
        out.append({"term": word, "definition": e.handle, "status": e.status, "uses": uses})
    return out


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for x in node:
            yield from _walk(x)
