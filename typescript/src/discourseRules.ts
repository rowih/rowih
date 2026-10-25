// The checker's rules for reference and discourse
// (specification/discourse.md#summaries-and-confirmations): what a summary names and the
// standing it states, the independence of a confirmation, and the statuses of a referent
// where they apply. Each takes the checker whose diagnostics it adds to, as the canonical
// implementation's `discourse_rules.py` does, statement for statement.

import { type Checker, entryKind, pyShort } from "./checker.ts";
import { sortedStrings } from "./pyformat.ts";
import { get, type Tree, truthy } from "./tree.ts";

const EXTERNAL = new Set(["g.reference.access.external", "g.reference.person.external-source"]);
export const COLLECTIVE_PERSONS = new Set(["g.reference.person.inclusive-collective",
  "g.reference.person.exclusive-collective"]);
export const COLLECTIVE = new Set([...COLLECTIVE_PERSONS,
  "g.situations-and-contents.quantifier.collective"]);
const LEXICON = "lexicon";

/** A summary names every entry it summarises, by NAMES with its expectation and the
 * change NONE, and only a summary names more than one entry. */
export function checkSummary(checker: Checker, t: Tree, adds: string | null): void {
  const more = (get(t, "also_named") ?? []) as Tree[];
  const change = (t.change as string[]).map((c) => pyShort(c));
  if (adds === "summary" && (!truthy(get(t, "named")) ||
    !(change.length === 1 && change[0] === "none"))) {
    checker.add("d.checker.force", t, ["the entries summarised, with NONE"], [],
      "a summary names what it summarises and changes none of it");
  }
  if (more.length && adds !== "summary") {
    checker.add("d.checker.force", more[0], ["one entry named"], [],
      "only a summary names more than one entry");
  }
  for (const r of more) { // the first reference is held to this by `checkMove`
    if (r.ref !== "names" || r.target !== "entry") {
      checker.add("d.checker.expectation", r, [], [],
        "a summary names entries, each with what it expects of it");
    }
  }
}

/** The independence of a confirmation is stated on a confirmation alone, and an
 * independent one states the source it rests on. */
export function checkConfirmation(checker: Checker, t: Tree, assertion: Tree): void {
  const values = (assertion.parts as Tree[]).filter((p) => p.kind === "value" &&
    (p.member as string).startsWith("g.standing.independence-of-a-confirmation."));
  if (!values.length) return;
  const named = get(t, "named") as Tree | null;
  const [adds] = entryKind(t.adds);
  const change = (t.change as string[]).map((c) => pyShort(c));
  const namedAdds = named !== null ? entryKind(named.expected)[0] : null;
  const confirming = adds === "asserted-position" && named !== null &&
    named.ref === "names" && named.target === "entry" &&
    change.length === 1 && change[0] === "none" &&
    (namedAdds === "asserted-position" || namedAdds === "conceded-position");
  if (!confirming) {
    checker.add("d.checker.ill-typed", values[0], ["a confirmation"], [values[0].member]);
  } else if (pyShort(values[0].member) === "independent" && !(assertion.parts as Tree[]).some(
    (p) => p.kind === "filler" && p.role === "g.standing.provenance-link.source")) {
    checker.add("d.checker.confirmation-source", values[0],
      ["the independent source it rests on"]);
  }
}

function tier(checker: Checker, basis: string): number {
  const cls = checker.lang.classes.get("g.standing.basis");
  const member = (cls.members as Tree[]).find((m) => m.identifier === basis);
  if (member === undefined) throw new Error("KeyError: " + basis);
  return member.tier as number;
}

/** The standing of an assertion of a summary: bases all of one tier, the unstated basis
 * and the unstated strength each alone, and one strength for each calibration. */
export function checkSummaryStanding(checker: Checker, t: Tree): void {
  const parts = t.parts as Tree[];
  const bases = parts.filter((p) => p.kind === "value" &&
    (p.member as string).startsWith("g.standing.basis."));
  if (new Set(bases.map((p) => tier(checker, p.member))).size > 1) {
    checker.add("d.checker.ill-typed", bases[1], ["bases of one tier"]);
  }
  if (bases.length !== new Set(bases.map((p) => p.member)).size) {
    checker.add("d.checker.ill-typed", bases[bases.length - 1], [], [], "a basis stated twice");
  }
  const calibrations: (string | null)[] = parts.filter((p) => p.kind === "value" &&
    (p.member as string).startsWith("g.standing.strength.")).map(() => LEXICON);
  for (const p of parts) {
    if (p.kind === "quantity") calibrations.push((get(p, "calibration") ?? null) as string | null);
  }
  if (calibrations.length !== new Set(calibrations).size) {
    checker.add("d.checker.ill-typed", t, [], [], "two strengths under one calibration");
  }
  const unstated = parts.some((p) => p.kind === "value" &&
    p.member === "g.standing.strength.unstated");
  if (unstated && calibrations.length > 1) {
    checker.add("d.checker.ill-typed", t, [], [], "the unstated strength stands alone");
  }
}

/** The statuses of a referent where they apply: verification, and a source, only on an
 * external referent, a named third party's verification with the source that verified
 * it, the reading of a collective on a collective, and no referent reached through a
 * reference written as new. */
export function checkReferent(checker: Checker, t: Tree): void {
  const parts = t.parts as Tree[];
  const values = new Set(parts.filter((p) => p.kind === "value").map((p) => p.member as string));
  const sources = parts.filter((p) => p.kind === "filler" &&
    p.role === "g.standing.provenance-link.source");
  const external = [...values].some((v) => EXTERNAL.has(v));
  const verification = sortedStrings([...values].filter((v) =>
    v.startsWith("g.reference.verification.")));
  if ((verification.length || sources.length) && !external) {
    checker.add("d.checker.ill-typed", t, ["an external referent"],
      verification.length ? verification : ["a source"]);
  }
  if (values.has("g.reference.verification.verified-by-a-named-third-party") &&
    !sources.length) {
    checker.add("d.checker.ill-typed", t, ["the source that verified it"]);
  }
  if ([...values].some((v) => v.startsWith("g.reference.reading-of-a-collective.")) &&
    ![...values].some((v) => COLLECTIVE.has(v))) {
    checker.add("d.checker.ill-typed", t, ["a collective referent"]);
  }
  if (values.has("g.reference.discourse-status.new") && parts.some((p) => p.kind === "ref")) {
    checker.add("d.checker.ill-typed", t, [], [],
      "a referent reached through a reference was introduced where it was first written");
  }
}

/** A collective agent that acts, or that holds a normative state, states whether it does
 * so jointly or each member for itself; a plural referent read collectively may state
 * it, and need not. */
export function checkCollectives(checker: Checker, t: Tree): void {
  const parts = t.parts as Tree[];
  const normative = parts.some((p) => p.kind === "value" &&
    (p.member as string).startsWith("g.force.kind-of-normative-entry."));
  for (const p of parts) {
    if (p.kind !== "filler" || get(p.filler, "kind") !== "term") continue;
    const role = pyShort(p.role);
    if (role !== "actor" && !(role === "holder" && normative)) continue;
    const values = (p.filler.parts as Tree[]).filter((q) => q.kind === "value")
      .map((q) => q.member as string);
    if (values.some((v) => COLLECTIVE_PERSONS.has(v)) &&
      !values.some((v) => v.startsWith("g.reference.reading-of-a-collective."))) {
      checker.add("d.checker.collective-reading", p.filler, ["joint or distributive"]);
    }
  }
}
