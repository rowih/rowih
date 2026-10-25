"""The checker's rules for figures (specification/meaning.md#figures): each figure's
relation fitted to its type. A target content stands only on a metaphor, an irony or a
hyperbole, and is a situation or a constituent of the figure's own kind; what a term
stands for stands only on a metonym, and is a term; a metonymy stands only on a term; and
a figure takes one relation (`d.checker.figure-relation`). In a precision-bound move each
figure states the relation its type requires (`d.checker.figure-without-target`)."""
from __future__ import annotations

from .senses import filler_kind

FIGURE = "g.ambiguity-and-figures.figurative-type."
RELATION = "g.ambiguity-and-figures.figures-relation."
TARGET = RELATION + "target-content"
STANDS_FOR = RELATION + "stands-for"
# the relation each type requires in a precision-bound move
# (specification/meaning.md#figures)
REQUIRED = {"metaphor": TARGET, "irony": TARGET, "hyperbole": TARGET,
            "metonymy": STANDS_FOR}
RELATION_NAME = {TARGET: "a target content", STANDS_FOR: "what it stands for"}


def named_figure(figure: str) -> str:
    return ("an " if figure[0] in "aeiou" else "a ") + figure


def figure_type(unit: dict) -> str | None:
    """The figurative type a unit's mark states, or None for a literal unit."""
    for p in unit.get("parts", []):
        if p.get("kind") == "value" and p["member"].startswith(FIGURE):
            return p["member"][len(FIGURE):]
    return None


def relations(unit: dict) -> list:
    return [p for p in unit.get("parts", []) if p.get("kind") == "filler"
            and p["role"].startswith(RELATION)]


def named_units(node, out: dict) -> dict:
    """Every unit of a move that carries a name, by its name."""
    if isinstance(node, dict):
        if node.get("kind") in ("assertion", "situation", "term") and \
                node.get("name") is not None:
            out[node["name"]] = node
        for v in node.values():
            named_units(v, out)
    elif isinstance(node, list):
        for x in node:
            named_units(x, out)
    return out


def check_unit(checker, t: dict, bound: bool, named: dict):
    kind = t["kind"]
    figure = figure_type(t)
    found = relations(t)
    if figure == "metonymy" and kind != "term":
        checker.add("d.checker.figure-relation", t, expected=["a term"], detected=[kind],
                    note="a metonymy stands on the term that stands for something else")
    if len(found) > 1:
        checker.add("d.checker.figure-relation", found[1],
                    note="a figure takes one relation")
    for p in found:
        if figure is None:
            checker.add("d.checker.figure-relation", p, detected=[p["role"]],
                        note="a figure's relation on a constituent no figurative mark "
                             "stands on")
            continue
        if p["role"] != REQUIRED[figure]:
            checker.add("d.checker.figure-relation", p, expected=[REQUIRED[figure]],
                        detected=[p["role"]],
                        note="%s takes %s" % (named_figure(figure),
                                              RELATION_NAME[REQUIRED[figure]]))
            continue
        filled = filler_kind(p["filler"], named)
        allowed = ("term",) if p["role"] == STANDS_FOR else (kind, "situation")
        if filled not in allowed + ("same",):
            checker.add("d.checker.figure-relation", p, expected=sorted(set(allowed)),
                        detected=[filled],
                        note="%s of another kind" % RELATION_NAME[p["role"]])
    if figure is not None and bound and not any(p["role"] == REQUIRED[figure]
                                                for p in found):
        checker.add("d.checker.figure-without-target", t, expected=[REQUIRED[figure]],
                    note="%s in a precision-bound move states %s" % (
                        named_figure(figure), RELATION_NAME[REQUIRED[figure]]))
