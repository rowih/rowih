// The checker's rules for figures
// (specification/lexicon.md#figurative-senses-and-conceptual-mappings), as the canonical
// implementation's `figure_rules` module states them, statement for statement: a target
// content stands only on a metaphor, an irony or a hyperbole, and is a situation or a
// constituent of the figure's own kind; what a term stands for stands only on a metonym,
// and is a term; a metonymy stands only on a term; a figure takes one relation; and in a
// precision-bound move each figure states the relation its type requires.

import { type RuleChecker } from "./conventionRules.ts";
import { sortedStrings } from "./pyformat.ts";
import { type Tree } from "./tree.ts";

const FIGURE = "g.ambiguity-and-figures.figurative-type.";
const RELATION = "g.ambiguity-and-figures.figures-relation.";
const TARGET = RELATION + "target-content";
const STANDS_FOR = RELATION + "stands-for";
/** The relation each type requires in a precision-bound move
 * (specification/grammar.md#precision-bound-moves). */
const REQUIRED: Record<string, string> = {
  metaphor: TARGET, irony: TARGET, hyperbole: TARGET, metonymy: STANDS_FOR,
};
const RELATION_NAME: Record<string, string> = {
  [TARGET]: "a target content", [STANDS_FOR]: "what it stands for",
};
const UNITS = ["assertion", "situation", "term"];

function namedFigure(figure: string): string {
  return ("aeiou".includes(figure[0]) ? "an " : "a ") + figure;
}

/** The kind of constituent a role is filled by: a shared node by the kind of the node it
 * names, and a set of readings by the kind its readings share (`senses.filler_kind`). */
export function fillerKind(filler: Tree, named: Map<number, Tree>): string {
  const kind = filler.kind as string;
  if (kind === "same" && named.has(filler.name)) return (named.get(filler.name)!.kind as string);
  if (kind === "readings") {
    const kinds = new Set<string>((filler.readings as Tree[]).map((r) => fillerKind(r, named)));
    return kinds.size === 1 ? [...kinds][0] : kind;
  }
  return kind;
}

/** The figurative type a unit's mark states, or null for a literal unit. */
export function figureType(unit: Tree): string | null {
  for (const p of (unit.parts ?? []) as Tree[]) {
    if (p.kind === "value" && (p.member as string).startsWith(FIGURE)) {
      return (p.member as string).slice(FIGURE.length);
    }
  }
  return null;
}

function relations(unit: Tree): Tree[] {
  return ((unit.parts ?? []) as Tree[]).filter((p) => p.kind === "filler" &&
    (p.role as string).startsWith(RELATION));
}

/** Every unit of a move that carries a name, by its name. */
export function namedUnits(node: unknown, out: Map<number, Tree>): Map<number, Tree> {
  if (Array.isArray(node)) {
    for (const x of node) namedUnits(x, out);
  } else if (node !== null && typeof node === "object") {
    const t = node as Tree;
    if (UNITS.includes(t.kind) && t.name !== null && t.name !== undefined) out.set(t.name, t);
    for (const v of Object.values(t)) namedUnits(v, out);
  }
  return out;
}

export function checkUnit(checker: RuleChecker, t: Tree, bound: boolean,
  named: Map<number, Tree>): void {
  const kind = t.kind as string;
  const figure = figureType(t);
  const found = relations(t);
  if (figure === "metonymy" && kind !== "term") {
    checker.add("d.checker.figure-relation", t, ["a term"], [kind],
      "a metonymy stands on the term that stands for something else");
  }
  if (found.length > 1) {
    checker.add("d.checker.figure-relation", found[1], [], [], "a figure takes one relation");
  }
  for (const p of found) {
    if (figure === null) {
      checker.add("d.checker.figure-relation", p, [], [p.role],
        "a figure's relation on a constituent no figurative mark stands on");
      continue;
    }
    if (p.role !== REQUIRED[figure]) {
      checker.add("d.checker.figure-relation", p, [REQUIRED[figure]], [p.role],
        namedFigure(figure) + " takes " + RELATION_NAME[REQUIRED[figure]]);
      continue;
    }
    const filled = fillerKind(p.filler, named);
    const allowed = p.role === STANDS_FOR ? ["term"] : [kind, "situation"];
    if (!allowed.includes(filled) && filled !== "same") {
      checker.add("d.checker.figure-relation", p, sortedStrings(new Set(allowed)), [filled],
        RELATION_NAME[p.role] + " of another kind");
    }
  }
  if (figure !== null && bound && !found.some((p) => p.role === REQUIRED[figure])) {
    checker.add("d.checker.figure-without-target", t, [REQUIRED[figure]], [],
      namedFigure(figure) + " in a precision-bound move states " +
      RELATION_NAME[REQUIRED[figure]]);
  }
}
