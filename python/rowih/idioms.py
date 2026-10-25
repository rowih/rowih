"""Idioms larger than a word
(specification/lexicon.md#conventional-expressions-and-idioms): the selection of an entry
by a constituent's literal structure, and the expansion that enters the core in its place.

A grammatical idiom is read by its entry only where the idiom mark stands on it; its
literal structure is a pattern whose slots take the constituents the speaker supplies,
and the constituent selects the entry whose pattern it matches, the slots aside, once
both are normalised alike. An extragrammatical idiom is recognised by its words, which
the parser has already done. Either way the core holds the entry's expansion, its slots
filled with what the speaker supplied, and the wording stays in the social and textual
component, which the expansion loses."""
from __future__ import annotations

import copy
from functools import lru_cache

MARK = "g.ambiguity-and-figures.idiom-selection.idiom-entry"
UNITS = ("assertion", "situation", "term")


def marked(t: dict) -> bool:
    return t.get("kind") in UNITS and any(
        p.get("kind") == "value" and p.get("member") == MARK for p in t["parts"])


def unmarked(t: dict) -> dict:
    """The unit without its mark, and without the spans a written tree carries."""
    from .tree import strip_private
    u = strip_private(t)
    u["parts"] = [p for p in u["parts"] if not (p.get("kind") == "value"
                                                 and p.get("member") == MARK)]
    return u


@lru_cache(maxsize=None)
def _semantic(lang_version: str, entry: str) -> dict:
    """An idiom's literal structure and expansion as trees with slots, from
    `lexicon/semantic/`, which both implementations read."""
    from .data import _load
    return _load("lexicon", "semantic", entry + ".json")


def literal(lang, entry: str) -> dict:
    return copy.deepcopy(_semantic(lang.version, entry)["literal structure"])


def expansion(lang, entry: str) -> dict:
    return copy.deepcopy(_semantic(lang.version, entry)["expansion"])


def grammatical(lang) -> list:
    return [i for i in lang.idioms
            if not isinstance(lang.entries[i]["literal structure"], list)]


def match(pattern, actual, bindings: dict) -> bool:
    """Whether `actual` is `pattern` with its slots filled, binding each slot. Siblings
    are compared as multisets, since neither tree is yet in canonical order."""
    if isinstance(pattern, dict) and pattern.get("kind") == "slot":
        n = pattern["slot"]
        if n in bindings:
            return bindings[n] == actual
        bindings[n] = actual
        return True
    if isinstance(pattern, dict):
        if not isinstance(actual, dict) or set(pattern) != set(actual):
            return False
        for key in pattern:
            if key in ("parts", "constituents", "readings"):
                if not _match_multiset(pattern[key], actual[key], bindings):
                    return False
            elif not match(pattern[key], actual[key], bindings):
                return False
        return True
    if isinstance(pattern, list):
        return isinstance(actual, list) and len(pattern) == len(actual) and all(
            match(p, a, bindings) for p, a in zip(pattern, actual))
    return pattern == actual


def _match_multiset(patterns: list, actuals: list, bindings: dict) -> bool:
    if len(patterns) != len(actuals):
        return False
    if not patterns:
        return True
    first, rest = patterns[0], patterns[1:]
    for i, a in enumerate(actuals):
        trial = dict(bindings)
        if match(first, a, trial) and _match_multiset(rest, actuals[:i] + actuals[i + 1:],
                                                      trial):
            bindings.clear()
            bindings.update(trial)
            return True
    return False


def unify(p, q) -> bool:
    """Whether some constituent could match both patterns, a slot of either standing for
    anything. Conservative: a slot's repetitions are not held to one value, so two
    patterns this calls unifiable may in fact never share a constituent."""
    if (isinstance(p, dict) and p.get("kind") == "slot") or \
            (isinstance(q, dict) and q.get("kind") == "slot"):
        return True
    if isinstance(p, dict):
        if not isinstance(q, dict) or set(p) != set(q):
            return False
        return all(_unify_multiset(p[k], q[k]) if k in ("parts", "constituents", "readings")
                   else unify(p[k], q[k]) for k in p)
    if isinstance(p, list):
        return isinstance(q, list) and len(p) == len(q) and all(
            unify(a, b) for a, b in zip(p, q))
    return p == q


def _unify_multiset(ps: list, qs: list) -> bool:
    if len(ps) != len(qs):
        return False
    if not ps:
        return True
    return any(unify(ps[0], q) and _unify_multiset(ps[1:], qs[:i] + qs[i + 1:])
               for i, q in enumerate(qs))


FAR = 2   # two substitutions or more: as far as the check below need look


def substitutions(p, q, critical) -> int:
    """The fewest substitutions of one word that make a constituent of pattern `p` one of
    pattern `q`, slots of either standing for anything, counted up to FAR. A content word
    or a value replaced by another counts one, unless either is a word with a code, whose
    substitution the move check word detects; any other difference counts FAR."""
    if (isinstance(p, dict) and p.get("kind") == "slot") or \
            (isinstance(q, dict) and q.get("kind") == "slot"):
        return 0
    if isinstance(p, dict) and isinstance(q, dict):
        if p == q:
            return 0
        leaf = {"word": "entry", "value": "member"}
        if p.get("kind") in leaf and q.get("kind") in leaf:
            words = [x.get("entry") or x.get("member") for x in (p, q)]
            return FAR if any(critical(w) for w in words) else 1
        if set(p) != set(q):
            return FAR
        total = 0
        for k in p:
            total += _multiset_cost(p[k], q[k], critical) if k in (
                "parts", "constituents", "readings") else substitutions(p[k], q[k], critical)
            if total >= FAR:
                return FAR
        return total
    if isinstance(p, list) and isinstance(q, list) and len(p) == len(q):
        return min(FAR, sum(substitutions(a, b, critical) for a, b in zip(p, q)))
    return 0 if p == q else FAR


def _multiset_cost(ps, qs, critical) -> int:
    """The cheapest matching of two sets of siblings. A part identical to one of the other
    set and holding no slot is matched to it first: the count of substitutions obeys the
    triangle inequality wherever no slot stands, so no other matching does better, and a
    normal form's many identical defaults leave few parts to search (O(n²) before the
    search, which is factorial in the parts that remain)."""
    if len(ps) != len(qs):
        return FAR
    rest = list(qs)
    left = []
    for p in ps:
        if not _holds_slot(p) and p in rest:
            rest.remove(p)
        else:
            left.append(p)
    return _search(left, rest, critical)


def _search(ps, qs, critical) -> int:
    if not ps:
        return 0
    return min([FAR] + [substitutions(ps[0], q, critical) + _search(
        ps[1:], qs[:i] + qs[i + 1:], critical) for i, q in enumerate(qs)])


def _holds_slot(x) -> bool:
    if isinstance(x, dict):
        return x.get("kind") == "slot" or any(_holds_slot(v) for v in x.values())
    if isinstance(x, list):
        return any(_holds_slot(v) for v in x)
    return False


def fill(pattern, bindings: dict):
    """The pattern with each slot replaced by what it was bound to."""
    if isinstance(pattern, dict):
        if pattern.get("kind") == "slot":
            return copy.deepcopy(bindings[pattern["slot"]])
        return {k: fill(v, bindings) for k, v in pattern.items()}
    if isinstance(pattern, list):
        return [fill(x, bindings) for x in pattern]
    return pattern


def resolve(unit: dict, normaliser, world: str = "actual", mentioned: bool = False) -> tuple:
    """The entry a marked unit selects and the bindings of its slots, or (None, None).
    The unit without its mark and each literal structure are normalised in the unit's
    own context, so that the defaults either states are stated in both and what a slot
    binds is normal in that context; which entry matches does not depend on the context,
    since equal parts receive equal defaults in any one context."""
    lang = normaliser.lang
    actual = normaliser.node(unmarked(unit), world, mentioned=mentioned)
    for entry in grammatical(lang):
        bindings = {}
        pattern = normaliser.node(literal(lang, entry), world, mentioned=mentioned)
        if match(pattern, actual, bindings):
            return entry, bindings
    return None, None
