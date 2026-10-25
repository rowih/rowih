// The checker's rules for conventional language
// (specification/lexicon.md#conventional-expressions-and-idioms), as the canonical
// implementation's `convention_rules` module states them, statement for statement: the
// idiom mark, the declared loss, formations read from their parts, and the act of
// definition (`inv.core-closed`).

import { type Language } from "./data.ts";
import { type Diagnostic, type Span } from "./diagnostics.ts";
import { compose } from "./formation.ts";
import * as idioms from "./idioms.ts";
import { decodePayload, segment } from "./lexer.ts";
import { markedWords } from "./registers.ts";
import { get, type Tree, truthy } from "./tree.ts";

const ROOT_ONSET = "r";
const ROOT_LENGTH = 5;
const CRITICAL_DISTANCE = 3;

/** What these rules need of the checker. */
export interface RuleChecker {
  lang: Language;
  envelope?: { dialects: { integer(): bigint }[][] } | null;
  add(code: string, node: Tree, expected?: string[], detected?: string[], note?: string): void;
  normaliser(): idioms.NodeNormaliser;
}

/** Every object of a move tree, depth first. */
export function* walk(node: unknown): Generator<Tree> {
  if (Array.isArray(node)) {
    for (const x of node) yield* walk(x);
  } else if (node !== null && typeof node === "object") {
    yield node as Tree;
    for (const v of Object.values(node)) yield* walk(v);
  }
}

/** The idioms a move reads by their entries, the losses it declares, and the formations
 * it uses. */
export function checkConventions(checker: RuleChecker, t: Tree): void {
  const lang = checker.lang;
  const norm = checker.normaliser();
  const incurred = new Set<string>();
  if (truthy(get(t, "act"))) {
    for (const l of lang.entries.get(t.act)["declared loss"]) incurred.add(l);
  }
  // a register written in the head, and a politeness word, a diction and every
  // register-marked word, incur what their entries record
  // (specification/lexicon.md#registers)
  if (truthy(get(t, "register"))) incurred.add("register");
  for (const key of ["politeness", "diction"]) {
    if (truthy(get(t, key))) {
      for (const l of lang.entries.get(t[key])["declared loss"]) incurred.add(l);
    }
  }
  if (markedWords(t, lang).length) incurred.add("register");
  for (const node of walk(t.constituents)) {
    if (node.kind === "idiom") {
      for (const l of lang.entries.get(node.entry)["declared loss"]) incurred.add(l);
    } else if (idioms.marked(node)) {
      const [entry] = idioms.resolve(node, norm);
      if (entry === null) {
        checker.add("d.checker.idiom-absent", node, ["an idiom of lexicon " + lang.version]);
      } else {
        for (const l of lang.entries.get(entry)["declared loss"]) incurred.add(l);
      }
    } else if (node.kind === "word" && node.status === "formation") {
      const morphemes = segment(node.form, lang);
      if (morphemes === null || compose(morphemes, lang) === null) {
        checker.add("d.checker.formation-unfit", node, [], [node.form],
          "a suffix that does not take its stem, or a compound whose head takes no modifier");
      }
    }
  }
  const losses = (get(t, "losses") ?? []) as string[];
  if (new Set(losses).size !== losses.length) {
    checker.add("d.checker.ill-typed", t, [], [], "a loss declared twice");
  }
  for (const loss of losses) {
    const name = lang.item(loss).name;
    if (!incurred.has(name)) {
      const expected = [...incurred].sort();
      checker.add("d.checker.loss-not-incurred", t,
        expected.length ? expected : ["no declared loss"], [name]);
    }
  }
}

/** The edit distance of two words, every edit of one symbol counting one. */
export function distance(a: string, b: string): number {
  let prev = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    for (let j = 1; j <= b.length; j++) {
      cur.push(Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] !== b[j - 1] ? 1 : 0)));
    }
    prev = cur;
  }
  return prev[prev.length - 1];
}

/** Whether a constituent states a defined word: a term holding only a declared-data wall
 * of the language's media type, which the protocol states. */
function termConstituent(c: Tree, lang: Language): boolean {
  return c.kind === "term" && (c.parts as Tree[]).length === 1 && c.parts[0].kind === "wall" &&
    c.parts[0].type === lang.protocol["media type"];
}

/** The word a definition defines, from the one constituent that states it, or null; found
 * by its form, not its place, since the normal form orders constituents canonically. */
export function definedTerm(t: Tree, lang: Language): string | null {
  const stating = (t.constituents as Tree[]).filter((c) => termConstituent(c, lang));
  if (stating.length !== 1) return null;
  const data = decodePayload(stating[0].parts[0].data);
  if (data === null || [...data].some((b) => b > 127)) return null;
  return String.fromCharCode(...data);
}

function rootShaped(word: string, lang: Language): boolean {
  return word.length === ROOT_LENGTH && word[0] === ROOT_ONSET && [...word].every((c, i) =>
    i % 2 === 0 ? lang.consonants.includes(c) : lang.vowels.includes(c));
}

/** The first word of the release a defined term could be confused with: one within one
 * edit of it, or a critical word within two. */
export function confusable(word: string, lang: Language): string | null {
  for (const form of [...lang.byForm.keys()].sort()) {
    const item = lang.byForm.get(form)!;
    const limit = item.criticalCode || item.protected ? CRITICAL_DISTANCE : 2;
    if (Math.abs(form.length - word.length) < limit && distance(word, form) < limit) return form;
  }
  return null;
}

/** An act of definition states its term, as declared data of the language's media type in
 * a term, and then its expansion, a term or a situation of the core (`inv.core-closed`).
 * */
/** Whether a constituent states a definition's scope: a term naming a dialect
 * (specification/lexicon.md#coining-a-word-by-definition). */
function scopeConstituent(c: Tree): boolean {
  return c.kind === "term" && (c.parts as Tree[]).some((p) => p.kind === "dialect");
}

export function checkDefinition(checker: RuleChecker, t: Tree): void {
  const lang = checker.lang;
  const word = definedTerm(t, lang);
  const scopes = (t.constituents as Tree[]).filter(scopeConstituent);
  const rest = (t.constituents as Tree[]).filter((c) => !termConstituent(c, lang) &&
    !scopes.includes(c));
  if (scopes.length > 1) {
    checker.add("d.checker.definition-form", t, [], [], "a definition states one scope");
    return;
  }
  if (scopes.length) {
    // a definition scoped to a dialect proposes its term to that dialect, and is written
    // in a message that names it
    const number = Number(((scopes[0].parts as Tree[]).find((p) => p.kind === "dialect") as
      Tree).number);
    const named = (checker.envelope?.dialects ?? []).map((d) => Number(d[0].integer()));
    if (!named.includes(number)) {
      checker.add("d.checker.definition-scope", t, ["a dialect the message names"],
        ["dialect " + number]);
    }
  }
  if (word === null || rest.length !== 1 || !["term", "situation"].includes(rest[0].kind)) {
    checker.add("d.checker.definition-form", t,
      ["a term holding the defined word as " + lang.protocol["media type"] +
        ", then its expansion"]);
    return;
  }
  const item = lang.byForm.get(word);
  if (item !== undefined) {
    const code = item.kind === "root" || item.kind === "derivation" ?
      "d.checker.definition-shadows" : "d.checker.definition-reaches-the-core";
    checker.add(code, t, [], [word, item.identifier]);
    return;
  }
  if (!rootShaped(word, lang)) {
    checker.add("d.checker.definition-form", t,
      ["a word of five symbols beginning " + ROOT_ONSET], [word]);
    return;
  }
  const near = confusable(word, lang);
  if (near !== null) checker.add("d.checker.definition-confusable", t, [], [word, near]);
  const expansion = rest[0];
  if ([...walk(expansion)].some((n) => n.kind === "word" && n.form === word)) {
    checker.add("d.checker.definition-recursive", t, [], [word]);
  }
  if ([...walk(expansion)].some((n) => n.kind === "wall" || n.kind === "readings")) {
    checker.add("d.checker.definition-carries-force", t, [], [],
      "a defined term may not stand for embedded material or readings");
  }
}

/** The move with its idioms expanded, checked as written; each finding is located at the
 * move. */
export function checkExpanded(diags: Diagnostic[], span: Span | null): Diagnostic[] {
  for (const d of diags) d.location = span;
  return diags;
}
