// The checker: the class of a move computed from its force
// (specification/grammar.md#the-class-of-a-move), the placement of every value at the
// unit it applies to, and the rules of the frozen decisions that a single message can be
// checked against. Each finding is a diagnostic. Longer than 500 lines only by
// TypeScript's spelling of the canonical `checker.py`, which it follows statement for
// statement; the rules of conventional language are in `conventionRules.ts`, as the
// canonical ones are in their own module.

import { type Language } from "./data.ts";
import { Diagnostic, Span } from "./diagnostics.ts";
import { type Envelope } from "./syntax.ts";
import { nameFreeKey } from "./normal.ts";
import { pyFloat, pyStr, sortedStrings } from "./pyformat.ts";
import { situationAspect, Temporal } from "./temporal.ts";
import { get, Spell, type Tree, truthy } from "./tree.ts";
import * as conventions from "./conventionRules.ts";
import * as figureRules from "./figureRules.ts";
import * as registerRules from "./registerRules.ts";
import * as registers from "./registers.ts";
import * as rules from "./discourseRules.ts";
import { Normaliser } from "./normal.ts";

type Kind = [string | null, string | null];

function key(k: Kind): string {
  return JSON.stringify(k);
}

const IN_FORCE_KINDS = new Set<string>([
  ["issue", "request"], ["normative-entry", "commitment"], ["normative-entry", "obligation"],
  ["normative-entry", "permission"], ["normative-entry", "assignment"],
  ["setting", "definition"], ["setting", "version"], ["setting", "role"],
].map((k) => key(k as Kind)));
const OPEN_STATUSES = new Set(["open", "in-force"]);

const SITUATION_CLASSES = new Set([
  "g.situations-and-contents.aspect", "g.situations-and-contents.polarity",
  "g.situations-and-contents.world-of-evaluation", "g.situations-and-contents.status-of-content",
  "g.situations-and-contents.information-structure", "g.situations-and-contents.kind-of-question",
  "g.attitudes-and-aims.kind-of-attitude", "g.attitudes-and-aims.origin-of-an-aim",
  "g.force.kind-of-normative-entry", "g.force.bindingness",
  "g.attitudes-and-aims.status-of-a-normative-state", "g.attitudes-and-aims.execution-phase",
  "g.situations-and-contents.structural-relation", "g.situations-and-contents.connective",
  "g.standing.basis", "g.standing.strength", "g.ambiguity-and-figures.figurative-type",
  "g.ambiguity-and-figures.idiom-selection",
]);
// The idiom mark stands on whatever constituent an idiom's literal structure is, as the
// figurative type does (specification/lexicon.md#conventional-expressions-and-idioms).
const ASSERTION_CLASSES = new Set([
  "g.standing.basis", "g.standing.strength", "g.standing.independence-of-a-confirmation",
  "g.situations-and-contents.information-structure", "g.situations-and-contents.status-of-content",
  "g.ambiguity-and-figures.figurative-type", "g.ambiguity-and-figures.idiom-selection",
]);
const TERM_CLASSES = new Set([
  "g.reference.person", "g.situations-and-contents.quantifier",
  "g.reference.existence-commitment", "g.reference.access", "g.reference.verification",
  "g.reference.discourse-status", "g.reference.specificity",
  "g.reference.reading-of-a-collective", "g.situations-and-contents.information-structure",
  "g.ambiguity-and-figures.figurative-type", "g.ambiguity-and-figures.idiom-selection",
]);
const ALLOWED = new Map<string, Set<string>>([["assertion", ASSERTION_CLASSES],
  ["situation", SITUATION_CLASSES], ["term", TERM_CLASSES]]);
const TIME_AT = new Map<string, Set<string>>([
  ["assertion", new Set(["observation-time", "inference-time", "validity-interval"])],
  ["situation", new Set(["event-time", "reference-time", "execution-time"])],
  ["term", new Set()],
]);
const FILLER_AT = new Map<string, Set<string>>([
  ["assertion", new Set(["g.standing.provenance-link", "g.ambiguity-and-figures.figures-relation"])],
  ["situation", new Set(["g.situations-and-contents.participation",
    "g.attitudes-and-aims.counterparty", "g.situations-and-contents.connective",
    "g.ambiguity-and-figures.figures-relation"])],
  ["term", new Set(["g.ambiguity-and-figures.figures-relation",
    "g.situations-and-contents.participation", "g.standing.provenance-link"])],
]);

// The kinds an act may name, by its change and outcome
// (specification/discourse.md#what-a-change-may-name). A delegation is accepted or
// rejected as an offer is, and a challenge is answered by grounds
// (specification/discourse.md#negotiation).
const NAMEABLE = new Map<string, Kind[]>([
  ["answer", [["issue", "question"], ["issue", "challenge"]]],
  ["acceptance", [["issue", "request"], ["issue", "proposal"], ["normative-entry", "commitment"],
    ["normative-entry", "assignment"]]],
  ["rejection", [["issue", "request"], ["issue", "proposal"], ["normative-entry", "commitment"],
    ["normative-entry", "assignment"]]],
  ["settlement", [["normative-entry", "obligation"], ["normative-entry", "assignment"]]],
  ["failure", [["normative-entry", "obligation"], ["normative-entry", "assignment"],
    ["issue", "request"]]],
]);
const OWN_ENTRY_LOWERINGS = new Set<string>([
  ["asserted-position", null], ["conceded-position", null], ["normative-entry", "commitment"],
  ["normative-entry", "assignment"], ["normative-entry", "permission"], ["supposition", null],
  ["summary", null], ["issue", "proposal"],
].map((k) => key(k as Kind)));

const UNIT_SECONDS = new Map([["second", 1], ["minute", 60], ["hour", 3600], ["day", 86400],
  ["week", 604800], ["month", 2629746], ["year", 31556952]]);

/** The last part of an identifier, or null for none (`checker.short`). */
export function pyShort(identifier: string | null | undefined): string | null {
  if (!identifier) return null;
  const i = identifier.lastIndexOf(".");
  return i < 0 ? identifier : identifier.slice(i + 1);
}

function classOf(identifier: string): string {
  const i = identifier.lastIndexOf(".");
  return i < 0 ? identifier : identifier.slice(0, i);
}

export function entryKind(ids: string[]): Kind {
  const names = ids.map(pyShort);
  const adds = names.length ? names[0] : null;
  const sub = names.length > 1 && (adds === "issue" || adds === "normative-entry" ||
    adds === "setting") ? names[1] : null;
  return [adds, sub];
}

export interface MoveClass {
  "operative": boolean;
  "pending": boolean;
  "de-escalating": boolean;
  "inert": boolean;
}

/** Whether the move is operative, pending and de-escalating, computed from what it adds
 * and what it changes, never read from a name
 * (specification/grammar.md#the-class-of-a-move). */
export function moveClass(t: Tree): MoveClass {
  const [adds, sub] = entryKind(t.adds);
  const change = (t.change as string[]).map(pyShort);
  const k = key([adds, sub]);
  const addsInForce = IN_FORCE_KINDS.has(k) && k !== key(["issue", "request"]);
  const addsPending = adds === "issue" && (sub === "request" || sub === "proposal");
  const named = get(t, "named") as Tree | null;
  let namedInForce = false;
  if (truthy(named) && named!.ref === "names" && named!.target === "entry") {
    const nk = entryKind(named!.expected);
    namedInForce = IN_FORCE_KINDS.has(key(nk)) && OPEN_STATUSES.has(pyStr(pyShort(named!.status)));
  }
  const c = change.length ? change[0] : null;
  const outcome = c === "resolution" && change.length > 1 ? change[1] : null;
  const when = c === "resolution" || c === "lowering" || c === "acknowledgement" ?
    change[change.length - 1] : null;
  const changing = c === "resolution" || c === "lowering";
  const operative = addsInForce || (namedInForce && changing && when === "on-the-move");
  const pending = !operative && (addsPending || (namedInForce && changing &&
    when === "on-acceptance"));
  const deEscalating = namedInForce && when === "on-the-move" && !addsInForce &&
    (c === "lowering" || (c === "resolution" && (outcome === "rejection" ||
      outcome === "settlement")));
  return { "operative": operative, "pending": pending, "de-escalating": deEscalating,
    "inert": !operative && !pending };
}

/** Whether a move is precision-bound, by any of three routes: its computed class, the
 * speaker's declaration, or a register that carries the class by default
 * (specification/grammar.md#precision-bound-moves). */
export function precisionBound(t: Tree): boolean {
  const cls = moveClass(t);
  return cls.operative || cls.pending || truthy(get(t, "precision_bound")) ||
    registers.boundByRegister(t);
}

export class Checker {
  lang: Language;
  envelope: Envelope | null;
  spell: Spell;
  diags: Diagnostic[] = [];

  private normaliserCache: Normaliser | null = null;
  named = new Map<number, Tree>(); // the named units of the move being checked

  constructor(lang: Language, envelope: Envelope | null = null) {
    this.lang = lang;
    this.envelope = envelope;
    this.spell = new Spell(lang);
  }

  /** A normaliser of this release, for resolving the idioms a move marks. */
  normaliser(): Normaliser {
    if (this.normaliserCache === null) this.normaliserCache = new Normaliser(this.lang);
    return this.normaliserCache;
  }

  add(code: string, node: Tree, expected: string[] = [], detected: string[] = [], note = ""): void {
    const span = get(node, "_span") as Span | null;
    this.diags.push(new Diagnostic(code, span, { expected: [...expected],
      detected: [...detected], note }));
  }

  checkMove(t: Tree, sender: string | null = null): void {
    const start = this.diags.length;
    const cls = moveClass(t);
    const named = get(t, "named") as Tree | null;
    const [adds, sub] = entryKind(t.adds);
    const namesEntry = truthy(named) && named!.ref === "names";
    if (truthy(t.change) !== namesEntry) {
      this.add("d.checker.change-without-entry", t, [], [], "change " +
        (truthy(t.change) ? "present" : "absent") + " with " +
        (namesEntry ? "an entry named" : "no entry named"));
    }
    if (truthy(named) && named!.ref === "mentions") {
      this.add("d.checker.expectation", named!, [], [],
        "what a move acts on is named, not mentioned");
    }
    rules.checkSummary(this, t, adds);
    const needsAuthority = cls.operative || cls.pending;
    if (needsAuthority !== truthy(get(t, "authority"))) {
      this.add("d.checker.authority", t, [needsAuthority ? "authority" : "no authority"]);
    }
    if (namesEntry && named!.target === "entry" && truthy(t.change)) {
      this.checkFit(t, named!, sender, adds, sub);
    }
    if (cls["de-escalating"] && !truthy(t.constituents)) {
      this.add("d.checker.stop-restatement", t, [], [],
        "a stop restates the content of what it withdraws");
    }
    const bound = precisionBound(t);
    this.named = figureRules.namedUnits(t.constituents, new Map());
    for (const c of t.constituents) {
      this.node(c, bound, cls, adds === "summary");
      if (c.kind === "assertion") rules.checkConfirmation(this, t, c);
    }
    if (truthy(get(t, "authority_term"))) this.node(t.authority_term, bound, cls);
    if (truthy(get(t, "deadline"))) this.spec(t.deadline, t);
    conventions.checkConventions(this, t);
    registerRules.checkRegister(this, t);
    if (adds === "setting" && sub === "definition") conventions.checkDefinition(this, t);
    this.temporal(t, start);
  }

  /** Every time of the move on one network (specification/meaning.md#time); a
   * contradiction the ordered times already reported is not reported again. */
  temporal(t: Tree, start: number): void {
    const net = new Temporal(this.lang, this.communicationTime());
    const failed = net.build(t);
    for (const [part, kind, index] of net.illTyped) {
      this.add("d.checker.ill-typed", part, ["a time a " + kind + " bears"], [index]);
    }
    if (failed && net.failure !== null &&
        !this.diags.slice(start).some((d) => d.code === "d.checker.ordered-times")) {
      this.add("d.checker.times-inconsistent", net.failure);
    }
  }

  checkFit(t: Tree, named: Tree, sender: string | null, adds: string | null,
    sub: string | null): void {
    const change = (t.change as string[]).map(pyShort);
    const nk = entryKind(named.expected);
    const c = change[0];
    const outcome = c === "resolution" ? (change.length > 1 ? change[1] : undefined) : null;
    if (outcome === undefined) throw new Error("IndexError: a resolution without an outcome");
    const own = sender !== null && named.author === sender;
    if (c === "resolution") {
      const allowed = NAMEABLE.get(pyStr(outcome)) ?? [];
      if (!allowed.some((k) => key(k) === key(nk))) {
        this.add("d.checker.fit", named, sortedStrings(allowed.map((k) => k[0] + " " + k[1])),
          [pyStr(nk[0]) + " " + pyStr(nk[1])]);
      } else if ((outcome === "answer" || outcome === "acceptance" || outcome === "rejection") &&
        own) {
        this.add("d.checker.fit", named, [], [],
          "an issue is resolved by the participant it is addressed to");
      }
    }
    if (c === "lowering" && OWN_ENTRY_LOWERINGS.has(key(nk)) && sender !== null && !own) {
      this.add("d.checker.fit", named, [], [],
        "a participant lowers only its own " + pyStr(nk[1] || nk[0]));
    }
    if (c === "acknowledgement" && own) {
      this.add("d.checker.fit", named, [], [], "an acknowledgement names another's move");
    }
    if (adds === "issue" && sub === "challenge" && own) {
      this.add("d.checker.fit", named, [], [], "a challenge names another's position");
    }
    if (adds === "issue" && sub === "proposal" &&
      !(change[0] === "resolution" && change[1] === "rejection")) {
      // a counterproposal declines what it answers
      // (specification/discourse.md#negotiation)
      this.add("d.checker.fit", named, [], [], "a counterproposal declines what it answers");
    }
    if (c === "resolution" && (outcome === "settlement" || outcome === "failure") &&
      key(nk) === key(["normative-entry", "assignment"]) && sender !== null && !own) {
      // an action performed at another's request is recorded under the requester's
      // authority, never the performer's
      // (specification/discourse.md#requests-offers-commitments-and-delegation)
      const principal = (truthy(get(t, "authority_term")) ? t.authority_term : {}) as Tree;
      const parties = ((get(principal, "parts") ?? []) as Tree[])
        .filter((p) => get(p, "kind") === "party").map((p) => get(p, "number"));
      if (pyShort(get(t, "authority") as string | null) !== "on-behalf-of-a-named-principal" ||
        parties.length !== 1 || parties[0] !== named.author) {
        this.add("d.checker.authority-attenuates", t, ["on behalf of agent " + named.author],
          [pyShort(get(t, "authority") as string | null) || "none"]);
      }
    }
  }

  // ------------------------------------------------------------ units
  node(t: Tree, bound: boolean, cls: MoveClass, top = false): void {
    const k = t.kind;
    if (k === "assertion" || k === "situation" || k === "term") {
      // `top` holds for a constituent of a summary, whose assertions state a standing
      // that is a set (specification/discourse.md#summaries-and-confirmations)
      this.unit(t, bound, cls, top && k === "assertion");
    } else if (k === "readings") {
      if (t.readings.length < 2) this.add("d.checker.readings", t, ["two or more readings"]);
      if (bound && pyShort(t.ambiguity) === "accidental" && (cls.operative || cls.pending)) {
        this.add("d.checker.accidental-in-operative", t);
      } else if (bound) {
        this.add("d.checker.precision-bound", t, [], [],
          "a precision-bound move has exactly one reading");
      }
      for (const r of t.readings) this.node(r, bound, cls);
    }
  }

// As long as the canonical implementation's `Checker.unit`, which it follows statement for
  // statement so that the two can be read side by side.
  unit(t: Tree, bound: boolean, cls: MoveClass, summary = false): void {
    const kind = t.kind as string;
    const allowed = ALLOWED.get(kind) as Set<string>;
    const parts = t.parts as Tree[];
    const vals = parts.filter((p) => p.kind === "value");
    const isAttitude = vals.some((p) =>
      (p.member as string).startsWith("g.attitudes-and-aims.kind-of-attitude"));
    const seenClasses = new Set<string>();
    for (const p of parts) {
      const pk = p.kind;
      if (pk === "value") {
        const c = classOf(p.member);
        if (!allowed.has(c) || (c.startsWith("g.standing.") && kind === "situation" &&
          !isAttitude)) {
          this.add("d.checker.ill-typed", p, ["a value of a " + kind], [p.member]);
        }
        const several = c === "g.situations-and-contents.connective" ||
          (summary && (c === "g.standing.basis" || c === "g.standing.strength"));
        if (seenClasses.has(c) && !several) {
          this.add("d.checker.ill-typed", p, [], [], "two values of one class");
        }
        seenClasses.add(c);
      } else if (pk === "time") {
        const at = TIME_AT.get(kind) as Set<string>;
        if (!at.has(pyStr(pyShort(p.index)))) {
          this.add("d.checker.ill-typed", p, sortedStrings(at), [p.index]);
        }
        if (p.spec.kind === "rate" &&
            !["iterative", "habitual"].includes(situationAspect(t, this.lang) ?? "")) {
          this.add("d.checker.ill-typed", p, ["a rate on an iterative or habitual situation"]);
        }
        this.spec(p.spec, p);
      } else if (pk === "filler") {
        const c = classOf(p.role);
        const at = FILLER_AT.get(kind) as Set<string>;
        if ((!at.has(c) && !(c.startsWith("g.standing.") && kind === "situation" && isAttitude)) ||
          (kind === "term" && c === "g.standing.provenance-link" &&
            p.role !== "g.standing.provenance-link.source")) {
          this.add("d.checker.ill-typed", p, sortedStrings(at), [p.role]);
        }
        this.node(p.filler, bound, cls);
      } else if (pk === "quantity") {
        if (kind === "assertion" || (kind === "situation" && isAttitude)) {
          this.strength(p);
        } else if (kind !== "term") {
          this.add("d.checker.ill-typed", p, ["a quantity in a term"]);
        }
        if (truthy(get(p, "calibration")) !== summary && (summary || kind !== "term")) {
          // a summary restates others' numbers, so whose calibration each is under is
          // said there, and only there
          this.add("d.checker.ill-typed", p, [summary ? "the calibrating participant" :
            "no calibrating participant"]);
        }
        if (bound && !fixedBounds(p)) {
          this.add("d.checker.precision-bound", p, [], [], "a vague value without fixed bounds");
        }
      } else if (pk === "word") {
        if (p.status === "unknown" && bound) {
          this.add("d.checker.unknown-in-precision-bound", p, [], [p.form]);
        }
      } else if (pk === "party" && kind !== "term") {
        this.add("d.checker.ill-typed", p, ["a participant in a term"]);
      } else if (pk === "dialect" && kind !== "term") {
        this.add("d.checker.ill-typed", p, ["a dialect in a term"]);
      } else if (["assertion", "situation", "term", "readings", "wall", "same", "ref"].includes(pk)) {
        if (pk === "situation" && kind !== "assertion") {
          this.add("d.checker.ill-typed", p, [], [],
            "a situation stands in an assertion or after a role");
        }
        if (pk === "assertion" || pk === "term") {
          this.add("d.checker.ill-typed", p, [], [], "a " + pk + " stands after a role");
        }
        this.node(p, bound, cls);
      }
    }
    if (kind === "assertion" && !parts.some((p) => p.kind === "situation" || p.kind === "same" ||
      p.kind === "readings" || p.kind === "idiom")) {
      this.add("d.checker.ill-typed", t, ["a situation in the assertion"]);
    }
    if (summary) rules.checkSummaryStanding(this, t);
    if (kind === "term") rules.checkReferent(this, t);
    if (kind === "situation") rules.checkCollectives(this, t);
    figureRules.checkUnit(this, t, bound, this.named);
    if (isAttitude) this.ownAction(t);
    if (kind === "assertion") {
      this.orderedTimes(t);
      const links = parts.filter((p) => p.kind === "filler" &&
        (p.role as string).startsWith("g.standing.provenance-link."));
      const limit = (this.lang.protocol.maxima ?? {})["provenance links"];
      if (limit !== undefined && limit !== null && links.length > limit) {
        this.add("d.parser.maximum", t, ["at most " + limit + " provenance links"],
          [String(links.length)]);
      }
    }
  }

  strength(p: Tree): void {
    const text = p.number as string;
    const pieces = text.includes("~") ? text.replace(/~/g, "/").split("/") : [text];
    for (const piece of pieces) {
      const v = pyFloat(piece) ?? -1.0;
      if (!(0.0 <= v && v <= 1.0) || truthy(get(p, "unit"))) {
        this.add("d.checker.strength-range", p, ["a number within 0 and 1"], [text]);
        return;
      }
    }
  }

  ownAction(t: Tree): void {
    const parts = t.parts as Tree[];
    const vals = new Set(parts.filter((p) => p.kind === "value").map((p) => pyShort(p.member)));
    if (!vals.has("intention")) return;
    const holder = parts.filter((p) => p.kind === "filler" && pyShort(p.role) === "holder")
      .map((p) => p.filler as Tree);
    const content = parts.filter((p) => p.kind === "filler" && pyShort(p.role) === "content")
      .map((p) => p.filler as Tree);
    if (!holder.length || !content.length || content[0].kind !== "situation") {
      this.add("d.checker.own-action", t, [], [], "an intention needs a holder and an action");
      return;
    }
    if (!this.actionsOf(content[0], holder[0])) this.add("d.checker.own-action", t);
  }

  /** Whether a content is an action by the holder, or a plan: a structure of such
   * actions joined by a connective (specification/meaning.md#attitudes-and-aims). */
  actionsOf(situation: Tree, holder: Tree): boolean {
    if (get(situation, "kind") !== "situation") return false;
    const parts = situation.parts as Tree[];
    const joined = parts.some((p) => p.kind === "value" &&
      (p.member as string).startsWith("g.situations-and-contents.connective."));
    if (joined) {
      const subs = parts.filter((p) => p.kind === "filler" && pyShort(p.role) === "content")
        .map((p) => p.filler as Tree);
      return subs.length > 0 && subs.every((x) => this.actionsOf(x, holder));
    }
    const actors = parts.filter((p) => p.kind === "filler" && pyShort(p.role) === "actor")
      .map((p) => p.filler as Tree);
    return actors.length > 0 && sameReferent(actors[0], holder, this.spell);
  }

  // ------------------------------------------------------------ times
  spec(s: Tree, node: Tree): void {
    if (s.kind === "interval") {
      this.spec(s.from, node);
      this.spec(s.until, node);
    }
  }

  /** Observation before inference before communication (specification/meaning.md#time),
   * wherever the times can be placed on the clock or ordered by relation. */
  orderedTimes(t: Tree): void {
    const times = new Map<string, Tree>();
    for (const p of t.parts as Tree[]) if (p.kind === "time") times.set(pyStr(pyShort(p.index)), p);
    const comm = this.communicationTime();
    const points = new Map<string, number>();
    for (const [name, p] of times) {
      const pt = this.point(p.spec, comm);
      if (pt !== null) points.set(name, pt);
    }
    if (comm !== null) points.set("communication-time", comm);
    const order = ["observation-time", "inference-time", "communication-time"];
    order.forEach((a, i) => {
      for (const b of order.slice(i + 1)) {
        if (points.has(a) && points.has(b) && (points.get(a) as number) > (points.get(b) as number)) {
          this.add("d.checker.ordered-times", times.get(a) ?? t, [], [], a + " after " + b);
        }
      }
    });
    for (const [name, p] of times) {
      const s = p.spec as Tree;
      if (s.kind === "relation" && s.reference.kind === "index") {
        const other = pyStr(pyShort(s.reference.index));
        const rel = pyStr(pyShort(s.relation));
        if (order.includes(name) && order.includes(other)) {
          const earlier = order.indexOf(name) < order.indexOf(other);
          const wrong = (earlier && (rel === "after" || rel === "met-by")) ||
            (!earlier && (rel === "before" || rel === "meets"));
          if (wrong) this.add("d.checker.ordered-times", p, [], [], name + " " + rel + " " + other);
        }
      }
    }
  }

  communicationTime(): number | null {
    if (this.envelope === null) return null;
    return pyFloat(this.envelope.time.text);
  }

  point(s: Tree, comm: number | null): number | null {
    if (s.kind === "absolute") return pyFloat(s.number);
    if (comm === null) return null;
    if (s.kind === "now") return comm;
    if (s.kind === "offset") {
      const n = pyFloat(s.number);
      if (n === null) return null;
      const unit = UNIT_SECONDS.get(pyStr(pyShort(s.unit)));
      if (unit === undefined) throw new Error("KeyError: " + s.unit);
      const d = n * unit;
      return pyShort(s.anchor) === "ago" ? comm - d : comm + d;
    }
    return null;
  }
}

/** A quantity whose bounds are fixed: an interval, or a number with a comparator that
 * states its precision (invariants, `inv.precision-bound-one-reading`). */
export function fixedBounds(q: Tree): boolean {
  if ((q.number as string).includes("~")) return true;
  const c = pyShort(get(q, "comparator") as string | null);
  return c === "exactly" || c === "at-least" || c === "at-most";
}

/** Two fillers denote the same referent when one stands for the other's name or both
 * are the same term written alike. */
export function sameReferent(a: Tree, b: Tree, spell: Spell): boolean {
  if (get(a, "kind") === "same" && get(b, "name") === get(a, "name")) return true;
  if (get(b, "kind") === "same" && get(a, "name") === get(b, "name")) return true;
  if (get(a, "kind") === "same" && get(b, "kind") === "same") return a.name === b.name;
  return nameFreeKey(a, new Map(), spell) === nameFreeKey(b, new Map(), spell);
}
