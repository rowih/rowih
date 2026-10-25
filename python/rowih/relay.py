"""Relaying, and the provenance a relay keeps (`inv.provenance-monotone`;
specification/protocol.md#relaying). A relay is the relayer's own assertion, inert however
imperative what it relays (specification/meaning.md#standing-and-provenance): on report,
from the participant it heard, with itself added as relayer, and with no strength of its
own, since a relayer that vouches does so in a new assertion. It takes one of two forms.

- A position relayed: the relayer reports that the author holds what it asserted, the
  author's assertion carried whole inside the report, its grounds, links and times
  with it, and its deixis resolved, since "I" in it is the author and "now" the
  author's communication time.
- A message relayed: the relayer reports that the author sent it the message, carried
  byte for byte as declared data of the language's media type, so that whatever
  provenance and authentication the message holds stay checkable. A relay of a relay
  takes this form, which nests nothing however long the chain.

`provenance` computes the graph a content carries, as facts (holder, kind, value), and
`monotone` checks that a transformation kept every fact and strengthened none."""
from __future__ import annotations

import json

from .checker import short
from .conventions import participants_of
from .data import load
from .lexer import decode_payload
from .moves import resolve_deixis
from .notation import Printer, Reader
from .temporal import UNIT_SECONDS

UNSTATED = {"g.standing.basis.unstated", "g.standing.strength.unstated"}


def relay_position(entry, lang=None) -> dict:
    """The relayer's move reporting `entry`, a position its author asserted, as a move
    tree for the generator: an assertion on report from the author, the relayer added,
    no strength claimed, and the author's assertions carried whole as what the author
    holds."""
    lang = lang or load()
    printer = Printer(lang)
    author = entry.handle[0]
    held = []
    for c in entry.content:
        if c.get("kind") != "assertion":
            raise ValueError("only an asserted content is relayed as a position; a "
                             "message is relayed byte for byte")
        if entry.time is None:
            raise ValueError("a position is relayed with its author's communication time")
        held.append(printer.node(anchor_times(resolve_deixis(c, author, entry.recipients),
                                              entry.time)))
    situations = " ".join("(situation BELIEF (HOLDER (term (party %s))) (CONTENT %s))"
                          % (author, h) for h in held)
    notation = ("(move ASSERTED-POSITION (assertion REPORT (SOURCE (term (party %s))) "
                "(RELAYER (term SELF)) %s))" % (author, situations))
    return Reader(lang).moves(notation)[0]


def relay_message(text: str, sender: str, lang=None) -> dict:
    """The relayer's move reporting that `sender` sent it the message `text`, carried
    byte for byte (adversarial item a10's form)."""
    lang = lang or load()
    notation = ("(move ASSERTED-POSITION (assertion REPORT (SOURCE (term (party %s))) "
                "(RELAYER (term SELF)) (situation send (ACTOR (term (party %s))) "
                "(UNDERGOER (data %s %s)) (RECIPIENT (term SELF)))))"
                % (sender, sender, json.dumps(lang.protocol["media type"]), json.dumps(text)))
    return Reader(lang).moves(notation)[0]


def carried(analysis) -> list:
    """The messages a parsed message carries byte for byte, as declared data of the
    language's media type, in the order it writes them: what a hearer may take as their
    own senders' once each verifies (specification/protocol.md#relaying)."""
    out = []

    def walk(node):
        if isinstance(node, list):
            for x in node:
                walk(x)
        elif isinstance(node, dict):
            if node.get("kind") == "wall" and node.get("type") == media_type \
                    and node.get("data") is not None:
                data = decode_payload(node["data"])
                if data is not None:
                    out.append(data.decode("utf-8", "replace"))
                return
            for k, v in node.items():
                if not k.startswith("_"):
                    walk(v)
    media_type = load().protocol["media type"]
    walk(analysis.moves)
    return out


def anchor_times(node, time: float):
    """The content with every time that depends on its move's communication time, now,
    an offset from it, or the communication time itself, written as the absolute time
    it denotes in the author's move, so that a relay sent later means what the author
    meant. An offset in months or years has no exact length, and is not relayed so."""
    if isinstance(node, list):
        return [anchor_times(x, time) for x in node]
    if not isinstance(node, dict):
        return node
    kind = node.get("kind")
    if kind == "now" or (kind == "index" and short(node.get("index")) == "communication-time"):
        return {"kind": "absolute", "number": _number(time)}
    if kind == "offset":
        unit = short(node["unit"])
        if unit in ("month", "year"):
            raise ValueError("an offset in %ss is not relayed as a position" % unit)
        span = float(node["number"]) * UNIT_SECONDS[unit]
        hence = short(node["anchor"]) == "hence"
        return {"kind": "absolute", "number": _number(time + span if hence else time - span)}
    return {k: anchor_times(v, time) for k, v in node.items()}


def _number(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else repr(float(x))


# ---------------------------------------------------------------- the provenance graph

def provenance(nodes: list, speaker: str, recipients: tuple = (), lang=None) -> set:
    """The provenance a content carries, as facts (holder, kind, value): for each
    assertion, at its speaker, and each attitude, at its holder, the basis, the
    strength and each link with what it points to; inside each content an attitude
    holds, the facts of its holder; and inside each message carried byte for byte, the
    facts of that message's moves at its sender. Participants are written by number,
    deixis resolved, so that facts compare across speakers."""
    lang = lang or load()
    facts = set()
    for n in nodes:
        _facts(n, speaker, speaker, recipients, facts, lang)
    return facts


def _facts(node, holder, speaker, recipients, facts, lang):
    if isinstance(node, list):
        for x in node:
            _facts(x, holder, speaker, recipients, facts, lang)
        return
    if not isinstance(node, dict):
        return
    kind = node.get("kind")
    if kind == "wall" and node.get("type") == lang.protocol["media type"] \
            and node.get("data") is not None:
        _quoted(node, facts, lang)
        return
    if kind not in ("assertion", "situation"):
        for k, v in node.items():
            if not k.startswith("_"):
                _facts(v, holder, speaker, recipients, facts, lang)
        return
    parts = node["parts"]
    attitude = kind == "situation" and any(
        p.get("kind") == "value" and p["member"].startswith("g.attitudes-and-aims.kind-of-attitude")
        for p in parts)
    here = holder
    if attitude:
        holders = [p["filler"] for p in parts if p.get("kind") == "filler"
                   and short(p["role"]) == "holder"]
        found = sorted(participants_of(holders[0], speaker, recipients), key=int) \
            if holders else []
        here = ",".join(found) or _key(holders[0] if holders else None, speaker, recipients)
    if kind == "assertion" or attitude:
        for p in parts:
            if p.get("kind") == "value" and p["member"].startswith(("g.standing.basis",
                                                                    "g.standing.strength")):
                facts.add((here, short(p["member"].rsplit(".", 1)[0]), p["member"]))
            elif p.get("kind") == "quantity":
                facts.add((here, "strength", json.dumps(
                    [p.get("comparator"), p.get("number")])))
            elif p.get("kind") == "filler" and p["role"].startswith("g.standing.provenance-link"):
                facts.add((here, short(p["role"]), _key(p["filler"], speaker, recipients)))
    for p in parts:
        if p.get("kind") == "filler":
            inner = here if (attitude and short(p["role"]) == "content") else holder
            _facts(p["filler"], inner, speaker, recipients, facts, lang)
        elif p.get("kind") in ("assertion", "situation", "wall"):
            _facts(p, here if kind == "assertion" else holder, speaker, recipients, facts,
                   lang)


def _quoted(wall, facts, lang):
    from .api import parse
    text = decode_payload(wall["data"]).decode("utf-8", "replace")
    a = parse(text)
    if a.message is None:
        return
    env = a.message.envelope
    rec = tuple(r.text for r in env.recipients)
    for n in a.normal:
        for c in n["constituents"]:
            _facts(c, env.sender.text, env.sender.text, rec, facts, lang)


def _key(node, speaker, recipients) -> str:
    """What a link points to: participants by number, anything else by its content."""
    if node is None:
        return "none"
    if node.get("kind") == "term":
        found = participants_of(node, speaker, recipients)
        if found:
            return ",".join(sorted(found, key=int))
    return json.dumps(_bare(resolve_deixis(node, speaker, recipients)), sort_keys=True)


HOW_SAID = ("g.reference.discourse-status.", "g.situations-and-contents.status-of-content.")


def _bare(node):
    """A node as what it names: without names, and without the values that say how it
    was said, new or given, at issue or presupposed, which a relay may restate."""
    if isinstance(node, dict):
        out = {k: _bare(v) for k, v in node.items() if not k.startswith("_") and k != "name"}
        if "parts" in out:
            out["parts"] = [p for p in out["parts"] if not (
                p.get("kind") == "value" and p["member"].startswith(HOW_SAID))]
        return out
    if isinstance(node, list):
        return [_bare(x) for x in node]
    return node


def monotone(before: set, after: set, relayer: str) -> list:
    """What a transformation did wrong to provenance, as a list of findings, empty when
    it kept every fact and strengthened none: each fact before is a fact after, and
    every basis or strength after at a holder other than the relayer is unstated or one
    that holder had before (`inv.provenance-monotone`)."""
    findings = ["dropped %s" % (f,) for f in sorted(before - after)]
    had = {}
    for h, kind, value in before:
        had.setdefault((h, kind), set()).add(value)
    for h, kind, value in sorted(after - before):
        if h == relayer or kind not in ("basis", "strength") or value in UNSTATED:
            continue
        if value not in had.get((h, kind), set()):
            findings.append("added %s" % ((h, kind, value),))
    return findings
