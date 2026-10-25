// Idioms larger than a word
// (specification/lexicon.md#conventional-expressions-and-idioms), as the canonical
// implementation's `idioms` module selects and expands them, statement for statement: a
// marked constituent selects the entry whose literal structure it matches, the slots
// aside, once both are normalised alike, and the core holds the entry's expansion with
// its slots filled.

import { type Language } from "./data.ts";
import { stripPrivate, type Tree } from "./tree.ts";

export const MARK = "g.ambiguity-and-figures.idiom-selection.idiom-entry";
const UNITS = ["assertion", "situation", "term"];
const SIBLINGS = ["parts", "constituents", "readings"];

/** What a normaliser offers resolution: its language and its node rule. */
export interface NodeNormaliser {
  lang: Language;
  node(t: Tree, world: string, top?: boolean, confirmation?: boolean, mentioned?: boolean): Tree;
}

function isObject(x: unknown): x is Tree {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}

/** Python's `==` over the JSON values a tree holds. */
export function deepEqual(a: unknown, b: unknown): boolean {
  if (Array.isArray(a)) {
    return Array.isArray(b) && a.length === b.length && a.every((x, i) => deepEqual(x, b[i]));
  }
  if (isObject(a)) {
    if (!isObject(b)) return false;
    const ka = Object.keys(a);
    const kb = Object.keys(b);
    return ka.length === kb.length && ka.every((k) => k in b && deepEqual(a[k], b[k]));
  }
  return a === b;
}

export function marked(t: Tree): boolean {
  return UNITS.includes(t.kind) && (t.parts as Tree[]).some((p) =>
    p.kind === "value" && p.member === MARK);
}

/** The unit without its mark, and without the spans a written tree carries. */
export function unmarked(t: Tree): Tree {
  const u = stripPrivate(t) as Tree;
  u.parts = (u.parts as Tree[]).filter((p) => !(p.kind === "value" && p.member === MARK));
  return u;
}

export function literal(lang: Language, entry: string): any {
  return structuredClone(lang.semantic.get(entry)["literal structure"]);
}

export function expansion(lang: Language, entry: string): Tree {
  return structuredClone(lang.semantic.get(entry).expansion);
}

export function grammatical(lang: Language): string[] {
  return lang.idioms.filter((i) => !Array.isArray(lang.semantic.get(i)["literal structure"]));
}

/** Whether `actual` is `pattern` with its slots filled, binding each slot. */
export function match(pattern: unknown, actual: unknown, bindings: Map<number, unknown>): boolean {
  if (isObject(pattern) && pattern.kind === "slot") {
    const n = pattern.slot as number;
    if (bindings.has(n)) return deepEqual(bindings.get(n), actual);
    bindings.set(n, actual);
    return true;
  }
  if (isObject(pattern)) {
    if (!isObject(actual)) return false;
    const kp = Object.keys(pattern);
    const ka = Object.keys(actual);
    if (kp.length !== ka.length || !kp.every((k) => k in actual)) return false;
    for (const key of kp) {
      if (SIBLINGS.includes(key)) {
        if (!matchMultiset(pattern[key], actual[key], bindings)) return false;
      } else if (!match(pattern[key], actual[key], bindings)) {
        return false;
      }
    }
    return true;
  }
  if (Array.isArray(pattern)) {
    return Array.isArray(actual) && pattern.length === actual.length &&
      pattern.every((p, i) => match(p, actual[i], bindings));
  }
  return pattern === actual;
}

function matchMultiset(patterns: unknown[], actuals: unknown[],
  bindings: Map<number, unknown>): boolean {
  if (patterns.length !== actuals.length) return false;
  if (!patterns.length) return true;
  const [first, ...rest] = patterns;
  for (let i = 0; i < actuals.length; i++) {
    const trial = new Map(bindings);
    if (match(first, actuals[i], trial) &&
      matchMultiset(rest, [...actuals.slice(0, i), ...actuals.slice(i + 1)], trial)) {
      bindings.clear();
      for (const [k, v] of trial) bindings.set(k, v);
      return true;
    }
  }
  return false;
}

/** The pattern with each slot replaced by what it was bound to. */
export function fill(pattern: unknown, bindings: Map<number, unknown>): any {
  if (isObject(pattern)) {
    if (pattern.kind === "slot") return structuredClone(bindings.get(pattern.slot as number));
    const out: Tree = {};
    for (const [k, v] of Object.entries(pattern)) out[k] = fill(v, bindings);
    return out;
  }
  if (Array.isArray(pattern)) return pattern.map((x) => fill(x, bindings));
  return pattern;
}

/** The entry a marked unit selects and the bindings of its slots, or [null, null]. */
export function resolve(unit: Tree, normaliser: NodeNormaliser, world = "actual",
  mentioned = false): [string | null, Map<number, unknown> | null] {
  const lang = normaliser.lang;
  const actual = normaliser.node(unmarked(unit), world, false, false, mentioned);
  for (const entry of grammatical(lang)) {
    const bindings = new Map<number, unknown>();
    const pattern = normaliser.node(literal(lang, entry), world, false, false, mentioned);
    if (match(pattern, actual, bindings)) return [entry, bindings];
  }
  return [null, null];
}
