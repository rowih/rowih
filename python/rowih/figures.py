"""What the speaker of a move answers for (specification/meaning.md#figures), computed
from the move's normal form. A marked metaphor, irony or hyperbole is replaced by its
target content, at the figure where the content is of the figure's kind and at the
situation the figure stands in where a figurative term means a situation; a metonym is
replaced by the referent it stands for; a figure that states no content leaves in its
place a target content its speaker meant and did not state; a set of readings keeps its
type, each reading computed alike; and a word read in a conventional sense is answered for
in that sense. The source of every figure is mentioned and not asserted, and `sources`
returns it apart. The result is a view of the move, never a move: its words name the
entries they are read as, and it is not parsed back."""
from __future__ import annotations

import copy

from . import senses
from .data import Language
from .figure_rules import REQUIRED, STANDS_FOR, TARGET, figure_type, named_units, relations

UNITS = ("assertion", "situation", "term")


def unstated(figure: str, kind: str) -> dict:
    """The target content a figure's speaker meant and did not state: what the speaker
    answers for, which no hearer's reading of the figure may stand in for
    (`inv.inference-not-said`)."""
    return {"kind": "unstated", "figure": "g.ambiguity-and-figures.figurative-type." + figure,
            "of": kind}


class _Lift:
    """A figurative term whose target content is a situation: the content stands for the
    situation the term stands in, which the enclosing situation replaces itself by."""

    def __init__(self, content: dict):
        self.content = content


def answers_for(constituents: list, lang: Language) -> list:
    """The content a move's speaker answers for, one node for each constituent of its
    normal form."""
    named = named_units(constituents, {})
    return [_settle(_node(copy.deepcopy(c), lang, named)) for c in constituents]


def sources(constituents: list) -> list:
    """The source of every marked figure of a move: mentioned, and not asserted."""
    out = []

    def walk(node):
        if isinstance(node, dict):
            if node.get("kind") in UNITS and figure_type(node) is not None:
                source = copy.deepcopy(node)
                source["parts"] = [p for p in source["parts"] if p not in relations(node)]
                out.append(source)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for x in node:
                walk(x)
    walk(constituents)
    return out


def _settle(node):
    return node.content if isinstance(node, _Lift) else node


def _node(t: dict, lang: Language, named: dict):
    kind = t.get("kind")
    if kind == "readings":
        t["readings"] = [_settle(_node(r, lang, named)) for r in t["readings"]]
        return t
    if kind not in UNITS:
        return t
    figure = figure_type(t)
    if figure is not None:
        return _figure(t, figure, lang, named)
    sense = senses.sense_of(t, lang, named)
    lifted = []
    parts = []
    for p in t["parts"]:
        pk = p.get("kind")
        if pk == "word" and sense is not None and p is senses.head_word(t):
            p = dict(p, entry=sense)
        elif pk == "filler":
            inner = _node(p["filler"], lang, named)
            if isinstance(inner, _Lift):
                if kind == "situation":
                    lifted.append(inner.content)
                    continue
                inner = inner.content
            p = dict(p, filler=inner)
        elif pk in UNITS or pk == "readings":
            inner = _node(p, lang, named)
            if isinstance(inner, _Lift):
                if kind == "situation":
                    lifted.append(inner.content)
                    continue
                inner = inner.content
            p = inner
        parts.append(p)
    t["parts"] = parts
    if lifted:
        # a figurative term that means a situation stands for the situation it is in;
        # two such terms in one situation each mean all of it, so both are answered for
        return lifted[0] if len(lifted) == 1 else {
            "kind": "situation", "name": None,
            "parts": [{"kind": "value",
                       "member": "g.situations-and-contents.connective.conjunction"}]
            + [{"kind": "filler", "role": "g.situations-and-contents.participation.content",
                "filler": c} for c in lifted]}
    return t


def _figure(t: dict, figure: str, lang: Language, named: dict):
    kind = t["kind"]
    found = [p for p in relations(t) if p["role"] == REQUIRED[figure]]
    if not found:
        return unstated(figure, kind)
    content = _settle(_node(found[0]["filler"], lang, named))
    filled = senses.filler_kind(content, named)
    if REQUIRED[figure] == STANDS_FOR or filled == kind:
        return content
    if kind == "term" and filled == "situation":
        return _Lift(content)
    if kind == "assertion" and filled == "situation":
        # a figurative assertion keeps its standing and answers for its target content
        standing = [p for p in t["parts"]
                    if (p.get("kind") in ("time", "quantity")
                        or (p.get("kind") == "value" and figure_type({"parts": [p]}) is None)
                        or (p.get("kind") == "filler" and p["role"] != TARGET))]
        return dict(t, parts=standing + [content])
    return content
