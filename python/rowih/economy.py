"""Movement toward economy (specification/lexicon.md#conventional-expressions-and-idioms):
the devices of conventional expression and idiom applied to a meaning, which is a choice
where normalisation is a function. The choice is fixed so that the generator stays
deterministic: every device the mode admits is applied wherever it applies, the longest
act word first and the release's earlier idiom first, and a device is applied only where
the result normalises to the meaning it was given.

Normal expression admits the conventional expressions, the act words and the formulas
(specification/lexicon.md#conventional-expressions-and-idioms); the mode of idiom admits
the decoding idioms as well, and the mode of compression the device of shared context
(specification/lexicon.md#registers), which is applied only for a hearer the speaker knows
to hold the entry it names. The marked figures and creative ambiguity of creative
expression are the speaker's to write in the meaning, and movement toward economy adds
none."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from functools import lru_cache

from . import idioms, registers
from .moves import resolve_deixis, restates, strip_name
from .normal import Normaliser
from .register_rules import NORMATIVE, RESOLUTION, ACCEPTANCE

WORLDS = ("actual", "within-a-supposition", "within-a-fiction", "counterfactual")
DEVICES = {
    "full explicitness": (),
    "normal expression": ("conventional expressions",),
    "compression": ("conventional expressions", "shared context", "dialect forms"),
    "idiom": ("conventional expressions", "idioms"),
    "creative expression": ("conventional expressions",),
}


@dataclass
class Holdings:
    """What a hearer holds, as its speaker knows it: the lexicon versions the hearer's
    messages state or it has acknowledged, the entries it holds or has been sent, an entry
    sent counting as held for the device of shared context (`inv.devices-admissible`),
    each by its handle with its content and its author's recipients, and the dialects its
    messages state or it has stated it understands, each (number, version, digest).
    `speaker` and `recipients` are the speaker's own, which the deixis of what it writes
    is read under."""
    speaker: str = "1"
    recipients: tuple = ("2",)
    lexicon: tuple = ()
    entries: dict = field(default_factory=dict)   # (author, number) -> (content, recipients)
    dialects: tuple = ()

    @classmethod
    def from_view(cls, view, speaker: str, hearer: str, lexicon: tuple = ()) -> "Holdings":
        """The holdings of `hearer` as `speaker`'s view shows them: every entry the hearer
        authored or was sent, and the lexicon releases and dialects its messages stated or
        it stated it understands
        (specification/dialects.md#settling-the-dialects-two-agents-share), each dialect
        by its number, version and digest."""
        entries = {h: (e.content, e.recipients) for h, e in view.entries.items()
                   if h[0] == hearer or hearer in e.recipients}
        stated = view.stated.get(hearer, {})
        understood = view.understood.get(hearer, {})
        lexicons = set(lexicon) | set(stated.get("lexicon", ())) | set(
            understood.get("lexicon", ()))
        dialects = set(stated.get("dialects", ())) | set(
            tuple(d) for d in understood.get("dialects", ()))
        return cls(speaker, (hearer,), tuple(sorted(lexicons)), entries,
                   tuple(sorted(dialects)))


def _shared(t: dict, n: dict, holdings: Holdings | None):
    """The move with the device of shared context applied: an acceptance that adds a
    normative entry and restates the entry it names, which the hearer holds, written
    without its restatement; or None where the device does not apply."""
    named = t.get("named")
    if holdings is None or not named or named["ref"] != "names" or \
            named["target"] != "entry" or not t["adds"] or t["adds"][0] != NORMATIVE or \
            t["change"][:2] != [RESOLUTION, ACCEPTANCE] or not n["constituents"]:
        return None
    held = holdings.entries.get((str(named["author"]), str(named["number"])))
    if held is None:
        return None
    content, recipients = held
    if named.get("part") is not None:
        from .moves import find_named
        content = [strip_name(find_named(content, named["part"]))]
    mine = resolve_deixis([strip_name(c) for c in n["constituents"]], holdings.speaker,
                          holdings.recipients)
    if not restates(mine, resolve_deixis(content, str(named["author"]), recipients)):
        return None
    return dict(t, constituents=[])


def admitted(entry: dict, devices: tuple, record: dict | None = None) -> bool:
    """Whether an idiom's entry is a device the mode admits: a formula is a conventional
    expression, any other idiom an idiom; and, given a register's record, whether the
    register lists the entry and, for a formula, admits formulas
    (specification/lexicon.md#registers)."""
    kind = "conventional expressions" if entry["route"] == "formula" else "idioms"
    if record is not None and (record["code"] not in entry["register"] or (
            entry["route"] == "formula" and not record["formulas admitted"])):
        return False
    return kind in devices


def act_word(t: dict, lang) -> str | None:
    """The act word whose expansion is the longest beginning of the move's force values,
    the release's earlier one where two are as long."""
    force = list(t["adds"]) + list(t["change"])
    best = None
    for ident, e in lang.entries.items():
        if e["grammatical category"] != "act word":
            continue
        n = len(e["expansion"])
        if force[:n] == e["expansion"] and (best is None or n > best[0]):
            best = (n, ident)
    return best[1] if best else None


def _contexts():
    for world in WORLDS:
        for top in (False, True):
            for mentioned in (False, True):
                yield world, top, mentioned


@lru_cache(maxsize=None)
def _normal_expansions(lexicon: str, language: str) -> dict:
    """The normal forms of a release's idiom expansions, by entry and context, filled in
    as they are first needed. They depend on the release alone, as the trees they are made
    from do (`idioms._semantic`), so every move economised under the release shares them:
    normalising each expansion in each context for each unit made the search grow with the
    idioms times the units, which lexicon 1.0's 269 idioms made the cost of the generator.
    Matching reads a pattern and never changes it."""
    return {}


def _normal_expansion(lang, norm: Normaliser, entry: str, world: str, top: bool,
                      mentioned: bool) -> dict:
    cache = _normal_expansions(lang.version, lang.grammar.get("version"))
    key = (entry, world, top, mentioned)
    if key not in cache:
        cache[key] = norm.node(idioms.expansion(lang, entry), world, top, mentioned=mentioned)
    return cache[key]


def _replacement(unit: dict, lang, norm: Normaliser, devices: tuple, record=None):
    """The idiomatic constituent for a unit of a normal form, or None: the first idiom
    the mode and the register admit whose expansion, normalised in some context, is the
    unit."""
    for entry in lang.idioms:
        e = lang.entries[entry]
        if not admitted(e, devices, record):
            continue
        for world, top, mentioned in _contexts():
            bindings = {}
            pattern = _normal_expansion(lang, norm, entry, world, top, mentioned)
            if not idioms.match(pattern, unit, bindings):
                continue
            literal = idioms.literal(lang, entry)
            if isinstance(literal, list):
                return {"kind": "idiom", "entry": entry}
            filled = idioms.fill(literal, bindings)
            filled["parts"].append({"kind": "value", "member": idioms.MARK})
            return filled
    return None


def _idiomatise(node, lang, norm, devices, record=None):
    if isinstance(node, list):
        return [_idiomatise(x, lang, norm, devices, record) for x in node]
    if not isinstance(node, dict):
        return node
    if node.get("kind") in idioms.UNITS:
        found = _replacement(node, lang, norm, devices, record)
        if found is not None:
            return found
    return {k: _idiomatise(v, lang, norm, devices, record) for k, v in node.items()}


def economy(t: dict, lang, mode: str, holdings: Holdings | None = None) -> dict:
    """The move with the devices of `mode` applied to its meaning. A device is kept only
    where the move still normalises to the same normal form, so that the choice never
    changes what is said (`inv.realisations-normalise`), except the device of shared
    context, which puts the reference in place of the restated content and is applied
    only where `holdings` show the hearer to hold the entry it names."""
    # the devices of the mode that the move's register admits: a register that does not
    # admit a mode's device moves the realisation toward explicitness
    # (specification/lexicon.md#registers)
    record = registers.record(t, lang)
    devices = tuple(d for d in DEVICES[mode] if d in record["devices admitted"])
    norm = Normaliser(lang)
    target = norm.move(t)
    out = registers.carry(t, copy.deepcopy(target))
    if "idioms" in devices or "conventional expressions" in devices:
        trial = dict(out, constituents=_idiomatise(out["constituents"], lang, norm, devices,
                                                   record))
        if norm.move(trial) == target:
            out = trial
    if "conventional expressions" in devices:
        act = act_word(out, lang)
        if act is not None:
            out["act"] = act
    if "shared context" in devices:
        shared = _shared(out, target, holdings)
        if shared is not None:
            out = shared
    if "dialect forms" in devices and holdings is not None and lang.dialect_forms:
        compressed = copy.deepcopy(out)
        _compress(compressed["constituents"], lang, held_dialects(holdings))
        if norm.move(compressed) == target:
            out = compressed
    return out


def held_dialects(holdings: Holdings) -> set:
    """The dialects a hearer holds, by (number, version), each under the digest of the
    release this implementation holds: a dialect the hearer holds under another digest is
    another release, whose forms it would read otherwise
    (specification/dialects.md#settling-the-dialects-two-agents-share)."""
    from .releases import digest_of
    return {(n, v) for n, v, d in holdings.dialects if digest_of(n, v) == d}


def _compress(node, lang, held: set):
    """Each word that spells the term a compressed form of a held dialect compresses,
    written as that form, in place (the device of dialect forms)."""
    by_expansion = {}
    for ident, f in lang.dialect_forms.items():
        if (f["dialect"], f["release"]) in held:
            by_expansion.setdefault(f["expansion"]["form"], (ident, f))
    if not by_expansion:
        return

    def visit(x):
        if isinstance(x, list):
            for i, v in enumerate(x):
                if isinstance(v, dict) and v.get("kind") == "word" and \
                        v.get("form") in by_expansion:
                    ident, f = by_expansion[v["form"]]
                    x[i] = {"kind": "word", "form": f["orthographic form"], "entry": ident,
                            "status": "known"}
                else:
                    visit(v)
        elif isinstance(x, dict):
            for v in x.values():
                visit(v)
    visit(node)
