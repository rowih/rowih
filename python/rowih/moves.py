"""What a move names and how contents compare, for a view (`view.py`) and what it derives
(`discourse.py`, `coordination.py`): the references and dependencies of a move, the node a
part names, deixis resolved for comparison by meaning, the rank of two crossing moves, the
time a deadline falls at and the participant a role setting binds. Each reads moves and
entries and keeps no state."""
from __future__ import annotations

from .checker import entry_kind, move_class, short
from .temporal import UNIT_SECONDS, seconds
from .tree import strip_private

UNITS = ("assertion", "situation", "term")


def precedes(a, b, entry) -> bool:
    """Whether move `a` comes before move `b`, which crossed it on `entry`: the rank is
    computed from the two moves alone, so every participant that holds both ranks them
    alike."""
    def rank(x):
        return (not move_class(x.t)["de-escalating"], x.sender != entry.handle[0],
                x.time if x.time is not None else float("inf"), int(x.sender), x.number)
    return rank(a) < rank(b)


def deadline_of(entry):
    """The time an entry's deadline falls at, in seconds, where its head states one the
    view can place: now, a time, or an offset from its communication time."""
    spec = (entry.normal or {}).get("deadline")
    if not spec or entry.time is None:
        return None
    if spec["kind"] == "now":
        return entry.time
    if spec["kind"] == "absolute":
        value = seconds(spec["number"])
        return value[1] if value else None
    if spec["kind"] == "offset":
        value = seconds(spec["number"])
        if value is None:
            return None
        span = value[1] * UNIT_SECONDS[short(spec["unit"])]
        return entry.time + span if short(spec["anchor"]) == "hence" else entry.time - span
    return None


def participant_binding(t: dict):
    """The participant number and agent identifier a role setting binds, where its content
    is a term holding exactly a participant and the agent's identifier as declared data
    (specification/discourse.md#roles), or None."""
    if entry_kind(t["adds"]) != ("setting", "role") or len(t["constituents"]) != 1:
        return None
    term = t["constituents"][0]
    if term.get("kind") != "term":
        return None
    parties = [p for p in term["parts"] if p.get("kind") == "party"]
    walls = [p for p in term["parts"] if p.get("kind") == "wall"]
    if len(parties) != 1 or len(walls) != 1 or walls[0].get("data") is None:
        return None
    from .lexer import decode_payload
    return parties[0]["number"], decode_payload(walls[0]["data"]).decode("utf-8", "replace")


def references(t: dict) -> list:
    """Every reference by which a move names an entry, in its head and its content."""
    out = []
    for r in [t.get("named")] + list(t.get("also_named") or []):
        if r and r["ref"] == "names" and r["target"] == "entry":
            out.append(r)
    for r in _nodes(t["constituents"]):
        if r.get("kind") == "ref" and r["ref"] == "names" and r["target"] == "entry":
            out.append(r)
    if t.get("authority_term"):
        out += [r for r in _nodes(t["authority_term"]) if r.get("kind") == "ref"
                and r["ref"] == "names" and r["target"] == "entry"]
    return out


def dependencies(t: dict) -> list:
    """What a move depends on: every entry it names, and every message it names, each as
    (target, author, number), a message named by its serial with the recipients of its
    channel after them (specification/protocol.md#channels-acknowledgement-and-repair).
    What it mentions is not resolved against the record and is no dependency."""
    out = [("entry", r["author"], r["number"]) for r in references(t)]
    for r in [t.get("named")] + list(t.get("also_named") or []) + list(_nodes(
            t["constituents"])):
        if r and r.get("kind") == "ref" and r["ref"] == "names" and r["target"] == "message":
            out.append(("message", r["author"], r["number"]))
        elif r and r.get("kind") == "ref" and r["ref"] == "names" and r["target"] == "serial":
            out.append(("serial", r["author"], r["number"],
                        " ".join(str(x) for x in sorted(int(x) for x in r["recipients"]))))
    seen, unique = set(), []
    for d in out:
        if d not in seen:
            seen.add(d)
            unique.append(d)
    return unique


def _nodes(node):
    if isinstance(node, dict):
        yield node
        for k, v in node.items():
            if not k.startswith("_"):
                yield from _nodes(v)
    elif isinstance(node, list):
        for x in node:
            yield from _nodes(x)


def _bare(node):
    return strip_private(node)


def find_named(node, name: int):
    if isinstance(node, dict):
        if node.get("kind") in UNITS and node.get("name") == name:
            return node
        for v in node.values():
            found = find_named(v, name)
            if found is not None:
                return found
    elif isinstance(node, list):
        for x in node:
            found = find_named(x, name)
            if found is not None:
                return found
    return None


def strip_name(node):
    """A node without its own name, which belongs to the entry's numbering and not to the
    content restated."""
    if isinstance(node, dict) and node.get("kind") in UNITS:
        return dict(node, name=None)
    return node


def resolve_deixis(node, speaker: str, recipients: tuple):
    """The content with the speaker and, where there is one recipient, the interlocutor
    written as the participants they are, so that 'I' in an entry and 'you' in its
    restatement by another compare as the same referent (restatement by handle: meaning
    compared with deixis resolved)."""
    if isinstance(node, list):
        return [resolve_deixis(x, speaker, recipients) for x in node]
    if not isinstance(node, dict):
        return node
    out = {k: resolve_deixis(v, speaker, recipients) for k, v in node.items()}
    if out.get("kind") == "term":
        parts = []
        for p in out["parts"]:
            member = p.get("member") if p.get("kind") == "value" else None
            if member == "g.reference.person.self":
                parts.append({"kind": "party", "number": speaker})
            elif member == "g.reference.person.interlocutor" and len(recipients) == 1:
                parts.append({"kind": "party", "number": recipients[0]})
            else:
                parts.append(p)
        out["parts"] = sorted(parts, key=repr)
    return out


def restates(restatement: list, content: list) -> bool:
    """Compare a restatement with the content it restates by meaning: their normal forms,
    with every entry named inside compared by its handle alone (restatement by handle)."""
    return _by_handle(restatement) == _by_handle(content)


def _by_handle(node):
    if isinstance(node, dict):
        out = {}
        for k, v in node.items():
            if k.startswith("_"):
                continue
            if node.get("kind") == "ref" and k in ("status", "expected"):
                continue
            out[k] = _by_handle(v)
        return out
    if isinstance(node, list):
        return [_by_handle(x) for x in node]
    return node
