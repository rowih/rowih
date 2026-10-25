// The checker's rules for registers (specification/lexicon.md#registers), as the
// canonical implementation's `register_rules` module states them, statement for
// statement: a word, suffix, act word or idiom stands only in a register its entry lists;
// a device of economy only in a register one of whose modes admits it, and a formula only
// in one that admits formulas; and siblings stand in canonical order where the register's
// syntax is canonical.

import { type RuleChecker, walk } from "./conventionRules.ts";
import * as idioms from "./idioms.ts";
import { segment } from "./lexer.ts";
import { type Normaliser } from "./normal.ts";
import * as registers from "./registers.ts";
import { get, stripPrivate, type Tree, truthy } from "./tree.ts";

const FIGURE = "g.ambiguity-and-figures.figurative-type.";
const CREATIVE = "g.ambiguity-and-figures.kind-of-ambiguity.creative";
const NORMATIVE = "g.force.what-the-move-adds.normative-entry";
const RESOLUTION = "g.force.change-made.resolution";
const ACCEPTANCE = "g.force.outcome-of-a-resolution.acceptance";

/** Whether a move uses the device of shared context: an acceptance that adds a normative
 * entry and writes no content, naming the entry it accepts in place of restating it. */
export function sharedContext(t: Tree): boolean {
  const named = get(t, "named") as Tree | null;
  const adds = t.adds as string[];
  const change = t.change as string[];
  return adds.length > 0 && adds[0] === NORMATIVE && change[0] === RESOLUTION &&
    change[1] === ACCEPTANCE && truthy(named) && named!.ref === "names" &&
    named!.target === "entry" && (t.constituents as Tree[]).length === 0;
}

function* entriesUsed(checker: RuleChecker, t: Tree): Generator<[Tree, string]> {
  const lang = checker.lang;
  for (const key of ["act", "politeness", "diction"]) {
    if (truthy(get(t, key))) yield [t, t[key]];
  }
  for (const node of walk(t.constituents)) {
    if (node.kind === "idiom") {
      yield [node, node.entry];
    } else if (idioms.marked(node)) {
      const [entry] = idioms.resolve(node, checker.normaliser());
      if (entry !== null) yield [node, entry];
    } else if (node.kind === "word") {
      if (truthy(get(node, "entry"))) {
        yield [node, node.entry];
      } else if (node.status === "formation") {
        for (const m of segment(node.form, lang) ?? []) {
          if (m !== "linker" && lang.entries.has(m.identifier)) yield [node, m.identifier];
        }
      }
    }
  }
}

export function checkRegister(checker: RuleChecker, t: Tree): void {
  const lang = checker.lang;
  const rec = registers.record(t, lang);
  const code: string = rec.code;
  const devices = new Set<string>(rec["devices admitted"]);
  for (const [node, ident] of entriesUsed(checker, t)) {
    const entry = lang.entries.get(ident);
    if (!(entry.register as string[]).includes(code)) {
      checker.add("d.checker.register-excludes-word", node, [...entry.register],
        [entry["orthographic form"], code]);
    }
    if (entry["grammatical category"] !== "idiom") continue;
    if (entry.route === "formula") {
      if (!rec["formulas admitted"]) {
        checker.add("d.checker.register-excludes-device", node, [], [code],
          "a formula, which the register does not admit");
      }
    } else if (!devices.has("idioms")) {
      checker.add("d.checker.register-excludes-device", node, [], [code],
        "an idiom, which none of the register's modes admits");
    }
  }
  for (const node of walk(t.constituents)) {
    if (node.kind === "value" && (node.member as string).startsWith(FIGURE) &&
      !devices.has("marked figures")) {
      checker.add("d.checker.register-excludes-device", node, [], [code],
        "a marked figure, which none of the register's modes admits");
    } else if (node.kind === "readings" && node.ambiguity === CREATIVE &&
      !devices.has("creative ambiguity")) {
      checker.add("d.checker.register-excludes-device", node, [], [code],
        "a creative ambiguity, which none of the register's modes admits");
    }
  }
  if (sharedContext(t) && !devices.has("shared context")) {
    checker.add("d.checker.register-excludes-device", t, [], [code],
      "an entry named in place of restating it, which none of the register's modes admits");
  }
  if (rec.order === "canonical") {
    const written = stripPrivate(t) as Tree;
    if ((checker.normaliser() as unknown as Normaliser).orderAll(written)) {
      checker.add("d.checker.register-order", t, [], [code],
        "siblings out of canonical order, which the register's syntax requires");
    }
  }
}
