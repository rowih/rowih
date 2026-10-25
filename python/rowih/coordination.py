"""What one participant's view derives about negotiation and coordination
(specification/discourse.md#negotiation): each negotiation, a sequence of proposals and
counterproposals on one issue, with the end it reached; each conflict a challenge opened,
with how it was resolved; the moves the view refused because a move they crossed
prevailed; and the conventions the participants stated. Negotiation is not a single act,
so nothing here is written in a move: each is recomputed from the record, and none can
disagree with the entries."""
from __future__ import annotations

from . import conventions
from .checker import short
from .discourse import _jsonable, accepts, handle_text, head_names, structure as discourse
from .moves import _nodes, deadline_of

CONDITION = "g.situations-and-contents.connective.condition"


def _offered(entry) -> bool:
    """Whether a normative entry binds only once accepted: an offer or a delegation."""
    return any(short(i) == "on-acceptance" for i in entry.move["adds"])


def opens(entry) -> bool:
    """Whether an entry can open a negotiation: a request, a proposal, an offer or a
    delegation, each of which awaits the addressee's acceptance."""
    return entry.kind in (("issue", "request"), ("issue", "proposal")) or (
        entry.kind[0] == "normative-entry" and _offered(entry))


def _changer(view, entry):
    """The entry added by the move that last changed `entry`'s status, with the move's
    change, or (None, None) where nothing changed it."""
    for item, _prior in reversed(entry.changes):
        if item is None:
            continue
        return view.entries.get(item.handle), [short(c) for c in item.t["change"]]
    return None, None


def _counter(view, entry):
    """The counterproposal that declined `entry`, if one did."""
    found, change = _changer(view, entry)
    if found is not None and found.kind == ("issue", "proposal") and \
            change[:2] == ["resolution", "rejection"]:
        return found
    return None


def negotiations(view, now=None) -> list:
    """Every negotiation on record: its opening, each counterproposal in turn, and how it
    ended. The end is an agreement, of the whole or of a part and with or without a
    condition, a rejection, a refusal, an abandonment by the proposer, a lapse past the
    last proposal's deadline at time `now`, or nothing yet
    (specification/discourse.md#negotiation)."""
    out = []
    for first in sorted((e for e in view.entries.values() if opens(e)),
                        key=lambda e: (int(e.handle[0]), int(e.handle[1]))):
        if first.kind == ("issue", "proposal") and first.move.get("named"):
            continue                       # a counterproposal continues another's
        rounds, last = [first], first
        while True:
            nxt = _counter(view, last)
            if nxt is None:
                break
            rounds.append(nxt)
            last = nxt
        out.append({"opening": first.handle,
                    "rounds": [{"entry": r.handle, "author": r.handle[0],
                                "deadline": deadline_of(r)} for r in rounds],
                    **_end(view, last, now)})
    return out


def _end(view, last, now) -> dict:
    found, change = _changer(view, last)
    if found is None or change is None:
        limit = deadline_of(last)
        if now is not None and limit is not None and now > limit and last.status != "withdrawn":
            return {"end": "lapsed", "by": None}
        return {"end": "open", "by": None}
    if change[0] == "lowering":
        end = "abandoned" if found.handle[0] == last.handle[0] else "refused"
        return {"end": end, "by": found.handle}
    if change[:2] == ["resolution", "acceptance"]:
        conditional = any(p.get("kind") == "filler" and p.get("role") == CONDITION
                          for p in _nodes(found.content))
        return {"end": "agreed", "by": found.handle,
                "extent": "part" if "part-of-it" in change else "whole",
                "conditional": conditional}
    if change[:2] == ["resolution", "rejection"]:
        return {"end": "rejected", "by": found.handle}
    return {"end": change[0], "by": found.handle}


def conflicts(view) -> list:
    """Every challenge on record, with the position it challenges and how the conflict
    stands (specification/discourse.md#challenges-and-disagreement): open; ended by the
    holder's retraction of the position; or defended by grounds, after which it is agreed
    where the challenger accepts the position and otherwise a disagreement both record."""
    out = []
    for c in sorted((e for e in view.entries.values() if e.kind == ("issue", "challenge")),
                    key=lambda e: (int(e.handle[0]), int(e.handle[1]))):
        named = [h for h, _ in head_names(c)]
        if not named or named[0] not in view.entries:
            continue
        position = view.entries[named[0]]
        defence = next((e for e in view.entries.values()
                        if e.handle[0] == position.handle[0] and e.status == "in-force"
                        and any(h == c.handle for h, _ in head_names(e))
                        and [short(x) for x in e.move["change"]][:2] == ["resolution", "answer"]),
                       None)
        if position.status in ("withdrawn", "lowered"):
            state = "retracted"
        elif defence is None:
            state = "open"
        elif any(e.handle[0] == c.handle[0] and accepts(view, e, position.handle)
                 for e in view.entries.values()):
            state = "agreed"
        else:
            state = "disagreement recorded"
        out.append({"challenge": c.handle, "position": position.handle,
                    "defence": defence.handle if defence else None, "state": state})
    return out


def exchange(view) -> dict:
    """The conventions the participants stated: the agent each number names, each
    participant's lineage, and the interval over which each one's silence accepts."""
    lineage = conventions.lineage(view)
    return {"roster": conventions.roster(view),
            "lineage": {p: lineage.get(p, p) for p in sorted(view.participants, key=int)},
            "silence": {p: conventions.silence(view, p)
                        for p in sorted(view.participants, key=int)},
            "settings": conventions.settings(view),
            "terms": conventions.terms(view)}


def structure(view, now=None) -> dict:
    """Everything the view derives, the discourse structure and the coordination, as plain
    data."""
    out = discourse(view, now)
    out.update(_jsonable({
        "negotiations": negotiations(view, now), "conflicts": conflicts(view),
        "crossed": {handle_text(k): handle_text(v) for k, v in view.crossed.items()},
        "exchange": exchange(view)}))
    return out
