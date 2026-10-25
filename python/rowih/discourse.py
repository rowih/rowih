"""What one participant's view derives from its record
(specification/discourse.md#how-a-participant-receives-a-message): the public positions
with the confirmations that raise them, the common ground, the open issues, the task
ledger's action items, the threads and replies, the relations between moves, the topics in
play, the conclusions and the summaries. Each is a view of the record, recomputed from it
and never stored beside it, so that nothing here can disagree with the entries."""
from __future__ import annotations

from .checker import entry_kind, short
from .conventions import lineage as lineages, silence
from .data import load
from .notation import Printer
from .standing import standings_of
from .view import View, find_named, resolve_deixis, restates, strip_name

POSITIONS = ("asserted-position", "conceded-position")
ACCEPTING = ("asserted-position", "conceded-position")
NORMATIVE = ("commitment", "obligation", "assignment", "permission")
INDEPENDENT = "g.standing.independence-of-a-confirmation.independent"
SOURCE = "g.standing.provenance-link.source"
TOPIC = "g.situations-and-contents.information-structure.topic"


def handle_text(h: tuple) -> str:
    return "%s.%s" % h


def head_names(entry) -> list:
    """The handles an entry's head names: what it acts on, or what a summary summarises."""
    out = []
    for r in [entry.move.get("named")] + list(entry.move.get("also_named") or []):
        if r and r["ref"] == "names" and r["target"] == "entry":
            out.append(((r["author"], r["number"]), r.get("part")))
    return out


# ---------------------------------------------------------------- acceptance

PRESUPPOSED = "g.situations-and-contents.status-of-content.presupposed"
STATUSES = ("g.situations-and-contents.status-of-content.",
            "g.reference.discourse-status.")


def _said(nodes: list) -> list:
    """What a content says, its standing set aside: the situations of its assertions,
    since a hearer accepts what was said and not the grounds it was said on."""
    out = []
    for c in nodes:
        if c.get("kind") == "assertion":
            out += _said([p for p in c["parts"] if p.get("kind") in ("situation", "same",
                                                                      "readings")])
        else:
            out.append(strip_name(c))
    return out


def _proposition(node):
    """A content compared as a proposition: whether it was at issue or presupposed, and
    whether a referent was new or given, are how it was said, not what."""
    if isinstance(node, dict):
        out = {k: _proposition(v) for k, v in node.items() if not k.startswith("_")}
        if "parts" in out:
            out["parts"] = [p for p in out["parts"] if not (
                p.get("kind") == "value" and p["member"].startswith(STATUSES))]
        return out
    if isinstance(node, list):
        return [_proposition(x) for x in node]
    return node


def restates_entry(entry, target, part=None) -> bool:
    """Whether `entry` says what `target`, or its node `part`, says: their propositions
    compared by meaning, with deixis resolved and entries named inside by handle."""
    theirs = target.content if part is None else [find_named(target.content, part)]
    mine = resolve_deixis(_proposition(_said(entry.content)), entry.handle[0],
                          entry.recipients)
    return restates(mine, resolve_deixis(_proposition(_said(theirs)), target.handle[0],
                                         target.recipients))


def accepts(view: View, entry, handle: tuple, part=None) -> bool:
    """Whether a position in force accepts entry `handle`'s content, or its node
    `part`: it names the entry, or that node, with the change none and says what it
    says. Naming the whole entry and saying all of it accepts every part."""
    if entry.kind[0] not in ACCEPTING or entry.status != "in-force" or \
            [short(c) for c in entry.move["change"]] != ["none"]:
        return False
    return any(named == handle and named_part in (None, part)
               and restates_entry(entry, view.entries[handle], named_part)
               for named, named_part in head_names(entry))


def acceptance(view: View, participant: str, handle: tuple, part=None, now=None):
    """The evidence on record that `participant` accepts the content of entry `handle`
    (or its node `part`) for the purposes of the exchange, or None: its author's own
    position, or a position of the participant's that names it with the change none and
    restates it, or, where the participant is bound to the convention that its silence
    accepts, silence over the convention's interval (`conventions.silence`). An
    acknowledgement accepts nothing (`inv.common-ground-by-acceptance`)."""
    target = view.entries[handle]
    if target.status != "in-force":
        return None
    if participant == handle[0]:
        return ("author", handle)
    for e in view.entries.values():
        if e.handle[0] == participant and accepts(view, e, handle, part):
            return ("position", e.handle)
    interval = silence(view, participant)
    if interval is not None and participant in target.recipients and \
            now is not None and target.time is not None and \
            now >= target.time + interval and not objected(view, participant, handle):
        return ("silence", handle)
    return None


def objected(view: View, participant: str, handle: tuple) -> bool:
    """Whether `participant` has made a move naming the entry that may object to it:
    any but an acceptance of it, an acknowledgement, which accepts nothing and objects
    to nothing, and a move marked as elaborating or supporting what it names. An
    unmarked position naming another's that says something else may be a disagreement,
    so it counts as an objection, and silence never grounds what was answered."""
    building = {"elaborates", "supports move"}
    lang = load()
    for e in view.entries.values():
        if e.handle[0] != participant:
            continue
        for named, part in head_names(e):
            if named != handle:
                continue
            change = [short(c) for c in e.move["change"]]
            if change and change[0] == "acknowledgement":
                continue
            if accepts(view, e, handle, part):
                continue
            if change == ["none"] and building & {lang.entries[r]["key"]
                                                  for r in e.move.get("relations", [])}:
                continue
            return True
    return False


def propositions(view: View) -> list:
    """The contents the record holds as positions: each position in force, whole, and
    each named node of one whose content is presupposed, by handle and part, with
    whether the content holds anything presupposed."""
    out = []
    for e in view.entries.values():
        if e.kind[0] not in POSITIONS + ("summary",) or e.status != "in-force":
            continue
        presupposed = [n for n in _units(e.content) if any(
            p.get("member") == PRESUPPOSED for p in n["parts"])]
        out.append((e.handle, None, bool(presupposed)))
        for node in presupposed:
            if node.get("name") is not None:
                out.append((e.handle, node["name"], True))
    return out


def common_ground(view: View, now=None) -> list:
    """The viewing participant's common ground: each proposition with evidence of every
    other participant's acceptance meeting the declared criterion, and, for presupposed
    content, the viewing participant's own acceptance as well, since nothing enters it
    by accommodation (specification/discourse.md#common-ground)."""
    out = []
    for handle, part, presupposing in propositions(view):
        others = sorted(view.participants - {view.participant})
        needed = others + ([view.participant] if presupposing else [])
        evidence = {p: acceptance(view, p, handle, part, now) for p in needed}
        if needed and all(evidence.values()):
            out.append({"entry": handle, "part": part, "presupposed": presupposing,
                        "evidence": evidence})
    return out


# ---------------------------------------------------------------- standing raised

def sources(entry) -> set:
    """What a position rests on: the sources its assertions name, and its author."""
    keys = {("party", entry.handle[0])}
    for c in entry.content:
        if c.get("kind") != "assertion":
            continue
        for p in c["parts"]:
            if p.get("kind") == "filler" and p["role"] == SOURCE:
                keys.add(_source_key(p["filler"]))
    return keys


def _source_key(node) -> tuple:
    if node.get("kind") == "ref":
        return ("entry", node["author"], node["number"])
    if node.get("kind") == "term":
        parties = [p["number"] for p in node["parts"] if p.get("kind") == "party"]
        if parties:
            return ("party", parties[0])
    return ("content", Printer().node(_named_free(node)))


def _named_free(node):
    if isinstance(node, dict):
        return {k: _named_free(v) for k, v in node.items() if k != "name"}
    if isinstance(node, list):
        return [_named_free(x) for x in node]
    return node


def corroboration(view: View, handle: tuple) -> list:
    """The confirmations that raise a position's standing: each restates it, states
    that it is independent and the source it rests on, and comes from a lineage and a
    source none counted before it has, the position's author's included. A confirmation
    by a fork or another instance of one model is recorded with its lineage and raises
    nothing (`inv.independent-confirmation`)."""
    target = view.entries[handle]
    lineage_of = lineages(view)
    seen_lineages = {lineage_of.get(handle[0], handle[0])}
    seen_sources = sources(target)
    counted = []
    for e in view.entries.values():
        if e.kind[0] != "asserted-position" or e.status != "in-force":
            continue
        if not any(named == handle and part is None for named, part in head_names(e)):
            continue
        if [short(c) for c in e.move["change"]] != ["none"] or not restates_entry(e, target):
            continue
        assertions = [c for c in e.content if c.get("kind") == "assertion"]
        independent = assertions and all(any(p.get("member") == INDEPENDENT
                                             for p in c["parts"]) for c in assertions)
        mine = sources(e) - {("party", e.handle[0])}
        lineage = lineage_of.get(e.handle[0], e.handle[0])
        if not independent or not mine or lineage in seen_lineages or mine & seen_sources:
            continue
        counted.append({"entry": e.handle, "lineage": lineage,
                        "sources": sorted(map(list, mine))})
        seen_lineages.add(lineage)
        seen_sources |= mine
    return counted


def confirmations(view: View, handle: tuple) -> list:
    """Every confirmation of a position on record, counted or not, with its lineage."""
    target = view.entries[handle]
    lineage_of = lineages(view)
    out = []
    for e in view.entries.values():
        if e.kind[0] == "asserted-position" and any(
                named == handle and part is None for named, part in head_names(e)) and \
                [short(c) for c in e.move["change"]] == ["none"] and \
                restates_entry(e, target):
            out.append({"entry": e.handle,
                        "lineage": lineage_of.get(e.handle[0], e.handle[0])})
    return out


# ---------------------------------------------------------------- the record's structure

def threads(view: View) -> dict:
    """Each thread by the entry it starts from, with its entries in the order the view
    applied them; a move that names several entries, as a summary does, joins each of
    their threads (specification/discourse.md#threads-and-other-derived-structures)."""
    roots = {}

    def roots_of(h, path=()):
        if h in roots:
            return roots[h]
        e = view.entries.get(h)
        parents = [n for n, _ in head_names(e)] if e is not None else []
        parents = [p for p in parents if p in view.entries and p not in path]
        out = set()
        for p in parents:
            out |= roots_of(p, path + (h,))
        roots[h] = out or {h}
        return roots[h]
    out = {}
    for h in view.entries:
        for r in sorted(roots_of(h)):
            out.setdefault(r, []).append(h)
    return out


def replies(view: View) -> dict:
    out = {}
    for e in view.entries.values():
        for named, _ in head_names(e):
            out.setdefault(named, []).append(e.handle)
    return out


def open_issues(view: View) -> list:
    """The questions, requests, proposals and challenges not yet resolved."""
    return [{"entry": e.handle, "kind": e.kind[1], "author": e.handle[0],
             "addressed to": list(e.recipients)}
            for e in view.entries.values() if e.kind[0] == "issue" and e.status == "open"]


def action_items(view: View) -> list:
    """The task ledger's entries in force: each normative entry with the party
    responsible for its content, the actor of its action where one is named and its
    author otherwise, and its deadline."""
    out = []
    for e in view.entries.values():
        if e.kind[0] != "normative-entry" or e.kind[1] not in NORMATIVE or \
                e.status != "in-force":
            continue
        actor = None
        for c in e.content:
            for p in c.get("parts", []):
                if p.get("kind") == "filler" and short(p["role"]) == "actor":
                    parties = [q["number"] for q in p["filler"].get("parts", [])
                               if q.get("kind") == "party"]
                    selves = [q for q in p["filler"].get("parts", [])
                              if q.get("member") == "g.reference.person.self"]
                    actor = parties[0] if parties else (e.handle[0] if selves else actor)
        out.append({"entry": e.handle, "kind": e.kind[1], "author": e.handle[0],
                    "responsible": actor or e.handle[0],
                    "deadline": e.normal.get("deadline") if e.normal else None})
    return out


def positions(view: View) -> dict:
    """Each participant's public positions in force, with the standing it gave them and
    the independent confirmations that raise it."""
    lang = load()
    out = {}
    for e in view.entries.values():
        if e.kind[0] not in POSITIONS or e.status != "in-force":
            continue
        out.setdefault(e.handle[0], []).append({
            "entry": e.handle, "kind": e.kind[0],
            "standing": [_standing_record(s) for s in standings_of(e.content, lang,
                                                                     e.handle[0])],
            "corroboration": corroboration(view, e.handle)})
    return out


def _standing_record(s) -> dict:
    return {"bases": sorted(s.bases),
            "strengths": sorted((x.calibration, str(x.lower), str(x.upper), x.lower_open,
                                 x.level or x.text) for x in s.strengths)}


def relations(view: View) -> list:
    """The moves that bear on others without changing them: elaborating, restating,
    contrasting, supporting and digressing, words of the lexicon
    (specification/discourse.md#threads-and-other-derived-structures)."""
    lang = load()
    out = []
    for e in view.entries.values():
        for r in e.move.get("relations", []):
            out.append({"entry": e.handle, "relation": lang.entries[r]["key"],
                        "bears on": [n for n, _ in head_names(e)]})
    return out


def topics(view: View) -> dict:
    """For each thread, the referents its moves mark as topic, in order."""
    printer = Printer()
    out = {}
    for root, members in threads(view).items():
        for h in members:
            for node in _units(view.entries[h].content):
                if node["kind"] == "term" and any(p.get("member") == TOPIC
                                                  for p in node["parts"]):
                    out.setdefault(root, []).append(
                        {"entry": h, "topic": printer.node(_named_free(node))})
    return out


def conclusions(view: View) -> list:
    """Positions drawn by inference from entries they name as premises."""
    out = []
    for e in view.entries.values():
        if e.kind[0] not in POSITIONS + ("summary",):
            continue
        for c in e.content:
            if c.get("kind") != "assertion" or not any(
                    p.get("member") == "g.standing.basis.inference" for p in c["parts"]):
                continue
            premises = sorted(((p["filler"]["author"], p["filler"]["number"])
                               for p in c["parts"] if p.get("kind") == "filler"
                               and short(p["role"]) == "premise"
                               and p["filler"].get("kind") == "ref"),
                              key=lambda h: (int(h[0]), int(h[1])))
            if premises:
                out.append({"entry": e.handle, "premises": premises})
    return out


def summaries(view: View) -> list:
    lang = load()
    return [{"entry": e.handle, "summarises": [n for n, _ in head_names(e)],
             "standing": [_standing_record(s) for s in standings_of(e.content, lang,
                                                                      e.handle[0])]}
            for e in view.entries.values() if e.kind[0] == "summary"]


def structure(view: View, now=None) -> dict:
    """Everything the view derives, as plain data."""
    return _jsonable({
        "participant": view.participant,
        "threads": threads(view), "replies": replies(view),
        "open issues": open_issues(view), "action items": action_items(view),
        "positions": positions(view), "common ground": common_ground(view, now),
        "relations": relations(view), "topics": topics(view),
        "conclusions": conclusions(view), "summaries": summaries(view),
        "held": [{"sender": x.sender, "move": entry_kind(x.t["adds"])} for x in view.held],
        "inferences": [{"holder": i.holder, "premises": i.premises, "kind": i.kind}
                       for i in view.inferences],
    })


def _units(node):
    if isinstance(node, dict):
        if node.get("kind") in ("assertion", "situation", "term"):
            yield node
        for k, v in node.items():
            if not k.startswith("_"):
                yield from _units(v)
    elif isinstance(node, list):
        for x in node:
            yield from _units(x)


def _jsonable(x):
    if isinstance(x, tuple) and len(x) == 2 and all(isinstance(y, str) for y in x):
        return handle_text(x)
    if isinstance(x, dict):
        return {(handle_text(k) if isinstance(k, tuple) else k): _jsonable(v)
                for k, v in x.items()}
    if isinstance(x, (list, tuple, set)):
        return [_jsonable(y) for y in x]
    return x
