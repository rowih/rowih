// The normal form (specification/meaning.md#the-normal-form): every default stated, every
// value stated on every unit that bears it, the siblings of every unit in canonical
// order, and the shared nodes numbered in the normal form's traversal. Normalisation
// reads the move, the grammar and the lexicon release, and nothing any participant holds.

import { type Language } from "./data.ts";
import * as dialects from "./dialects.ts";
import { entryKind, pyShort } from "./checker.ts";
import { regularWord, wordSort } from "./formation.ts";
import * as idioms from "./idioms.ts";
import { compareCodePoints } from "./pyformat.ts";
import { compareVersions } from "./versions.ts";
import * as registers from "./registers.ts";
import { hex, sha256Text } from "./sha256.ts";
import { get, Spell, stripPrivate, type Tree, truthy } from "./tree.ts";

export const ASPECT_OF_SORT = new Map([["s.sort.event", "perfective"], ["s.sort.state", "stative"],
  ["s.sort.process", "progressive"]]);
const EXISTENCE_OF_WORLD = new Map([["actual", "asserted-to-exist"],
  ["within-a-supposition", "within-a-supposition"],
  ["within-a-fiction", "within-a-declared-fiction"],
  ["counterfactual", "mentioned-without-existence-asserted"]]);
const AIMS = new Set(["desire", "goal", "intention", "preference"]);
// Persons fixed by the exchange itself: the speaker, its hearer, and the two together.
const GIVEN_PERSONS = new Set(["g.reference.person.self", "g.reference.person.interlocutor",
  "g.reference.person.inclusive-collective"]);
const UNIT_KINDS = new Set(["assertion", "situation", "term"]);
const SIBLING_KEYS = ["parts", "constituents", "readings"];
const WALK_KEYS = ["authority_term", "constituents", "parts", "filler", "readings"];

function value(member: string): Tree {
  return { kind: "value", member };
}

function values(parts: Tree[], classId: string): Tree[] {
  return parts.filter((p) => p.kind === "value" && (p.member as string).startsWith(classId + "."));
}

function isUnit(t: Tree): boolean {
  return UNIT_KINDS.has(get(t, "kind") as string);
}

function isObject(x: unknown): x is Tree {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}

/** `identifier.rsplit(".", 1)[0]`. */
function classOf(identifier: string): string {
  const i = identifier.lastIndexOf(".");
  return i < 0 ? identifier : identifier.slice(0, i);
}

type Rank = number[];

function compareRanks(a: Rank, b: Rank): number {
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
  }
  return a.length === b.length ? 0 : a.length < b.length ? -1 : 1;
}

export class Normaliser {
  lang: Language;
  spell: Spell;
  classIndex = new Map<string, number>();
  memberIndex = new Map<string, number>();
  resolved: string[] = []; // the idioms the last move read by their entries

  constructor(lang: Language) {
    this.lang = lang;
    this.spell = new Spell(lang);
    (lang.grammar.classes as Tree[]).forEach((c, i) => {
      this.classIndex.set(c.identifier, i);
      (c.members as Tree[]).forEach((m, j) => this.memberIndex.set(m.identifier, j));
    });
  }

  // ------------------------------------------------------------ defaults
  move(input: Tree): Tree {
    const t = stripPrivate(input) as Tree;
    // the act word, the declared loss, the politeness word, the diction and the register
    // are the social and textual component's, which the normal form sets aside
    // (specification/lexicon.md#registers)
    for (const key of registers.SOCIAL_KEYS) delete t[key];
    this.resolved = [];
    // a compressed form of a named dialect is written as the term it compresses, before
    // any default is read from a word's sort (specification/dialects.md#compressed-forms)
    dialects.expand(t, this.lang);
    const [adds, sub] = entryKind(t.adds);
    const world = adds === "supposition" ? "within-a-supposition" : "actual";
    let confirmation = false;
    const named = get(t, "named") as Tree | null;
    if (truthy(named) && named!.ref === "names" &&
      !(t.change as string[]).some((c) => pyShort(c) !== "none")) {
      const namedAdds = entryKind(named!.expected)[0];
      confirmation = adds === "asserted-position" &&
        (namedAdds === "asserted-position" || namedAdds === "conceded-position");
    }
    const also = (get(t, "also_named") ?? []) as Tree[];
    if (also.length) {
      // the entries a summary names are a set, in canonical order
      const refs = [t.named as Tree, ...also].sort(compareReferences);
      t.named = refs[0];
      t.also_named = refs.slice(1);
    }
    // A situation that is an action stands directly in a move that adds an issue other
    // than a question or a normative entry, or that restates one it names.
    const namedKind = truthy(named) && truthy(get(named, "expected")) ?
      entryKind(named!.expected) : [null, null];
    const actionMove = ((adds === "issue" || adds === "normative-entry") &&
      sub !== "question" && sub !== "challenge") ||
      ((namedKind[0] === "issue" || namedKind[0] === "normative-entry") &&
        namedKind[1] !== "question" && namedKind[1] !== "challenge");
    t.constituents = (t.constituents as Tree[]).map((c) =>
      this.node(c, world, actionMove, confirmation));
    if (truthy(get(t, "authority_term"))) t.authority_term = this.node(t.authority_term, world);
    // Order to a fixed point: a sibling's key reads the digests of the shared nodes it
    // names, which ordering their own parts may change; the graph is acyclic, so the
    // passes settle within its depth.
    if (!cyclic(t)) {
      for (let pass = 0; pass < 64; pass++) if (!this.orderAll(t)) break;
    }
    this.renumber(t);
    return t;
  }

  /** `mentioned` holds inside the source content of a figure, which is mentioned and not
   * asserted; a figure's target content is asserted under the standing of its assertion,
   * and so is the referent a metonym stands for, which its predication is about, so the
   * flag ends at either relation
   * (specification/lexicon.md#figurative-senses-and-conceptual-mappings). */
  node(t: Tree, world: string, top = false, confirmation = false, mentioned = false): Tree {
    const k = t.kind;
    if (k === "idiom") {
      // an extragrammatical idiom, recognised by its words: the core holds its expansion
      // (specification/lexicon.md#conventional-expressions-and-idioms)
      this.resolved.push(t.entry);
      return this.node(idioms.expansion(this.lang, t.entry), world, top, confirmation, mentioned);
    }
    if (idioms.marked(t)) {
      const [entry, bindings] = idioms.resolve(t, this, world, mentioned);
      if (entry === null) {
        // no entry of the release has this literal structure; the checker refuses it,
        // and the literal reading stands with the mark
        const u = this.node(idioms.unmarked(t), world, top, confirmation, mentioned);
        (u.parts as Tree[]).push(value(idioms.MARK));
        return u;
      }
      this.resolved.push(entry);
      return this.node(idioms.fill(idioms.expansion(this.lang, entry), bindings!), world, top,
        confirmation, mentioned);
    }
    if (UNIT_KINDS.has(k) && (t.parts as Tree[]).some((p) => p.kind === "value" &&
      (p.member as string).startsWith("g.ambiguity-and-figures.figurative-type."))) {
      mentioned = true;
    }
    if (k === "assertion") return this.assertion(t, world, confirmation, mentioned);
    if (k === "situation") return this.situation(t, world, top, mentioned);
    if (k === "term") return this.term(t, world, mentioned);
    if (k === "readings") {
      t.readings = (t.readings as Tree[]).map((r) => this.node(r, world, false, false, mentioned));
      return t;
    }
    return t;
  }

  assertion(t: Tree, world: string, confirmation: boolean, mentioned = false): Tree {
    const parts = t.parts as Tree[];
    if (!values(parts, "g.standing.basis").length) parts.push(value("g.standing.basis.unstated"));
    if (!values(parts, "g.standing.strength").length && !parts.some((p) => p.kind === "quantity")) {
      parts.push(value("g.standing.strength.unstated"));
    }
    if (confirmation && !values(parts, "g.standing.independence-of-a-confirmation").length) {
      parts.push(value("g.standing.independence-of-a-confirmation.same-source"));
    }
    t.parts = parts.map((p) => this.part(p, world, mentioned));
    return t;
  }

// As long as the canonical implementation's `Normaliser.situation`, which it follows statement for
  // statement so that the two can be read side by side.
  situation(t: Tree, world: string, top: boolean, mentioned = false): Tree {
    const parts = t.parts as Tree[];
    const written = values(parts, "g.situations-and-contents.world-of-evaluation");
    if (written.length) {
      world = pyShort(written[0].member) as string;
    } else {
      parts.push(value("g.situations-and-contents.world-of-evaluation." + world));
    }
    if (!values(parts, "g.situations-and-contents.polarity").length) {
      parts.push(value("g.situations-and-contents.polarity.affirmative"));
    }
    if (!values(parts, "g.situations-and-contents.status-of-content").length) {
      parts.push(value("g.situations-and-contents.status-of-content.at-issue"));
    }
    const attitude = values(parts, "g.attitudes-and-aims.kind-of-attitude");
    const report = values(parts, "g.force.kind-of-normative-entry");
    const connective = values(parts, "g.situations-and-contents.connective").length > 0 ||
      parts.some((p) => p.kind === "filler" && pyShort(p.role) === "condition");
    if (!values(parts, "g.situations-and-contents.aspect").length) {
      let aspect: string | null = null;
      for (const p of parts) {
        if (p.kind === "word" && (truthy(get(p, "entry")) || p.status === "formation")) {
          aspect = ASPECT_OF_SORT.get(wordSort(p, this.lang) ?? "") ?? null;
          break;
        }
      }
      if (aspect === null && (attitude.length || report.length)) aspect = "stative";
      if (aspect !== null && !connective) {
        parts.push(value("g.situations-and-contents.aspect." + aspect));
      }
    }
    if (attitude.length) {
      if (!values(parts, "g.standing.basis").length) parts.push(value("g.standing.basis.unstated"));
      if (!values(parts, "g.standing.strength").length &&
        !parts.some((p) => p.kind === "quantity")) {
        parts.push(value("g.standing.strength.unstated"));
      }
    }
    if ((attitude.length && AIMS.has(pyShort(attitude[0].member) as string)) || report.length) {
      if (!values(parts, "g.attitudes-and-aims.origin-of-an-aim").length) {
        parts.push(value("g.attitudes-and-aims.origin-of-an-aim.unstated"));
      }
    }
    if (top && !attitude.length && !report.length && !connective) {
      if (!values(parts, "g.attitudes-and-aims.execution-phase").length) {
        parts.push(value("g.attitudes-and-aims.execution-phase.unstated"));
      }
    }
    // from language 1.0 each content a connective joins is an action as the whole would
    // be, and takes its default phase, so that a part restated alone has the normal form
    // it has within the whole (specification/meaning.md#the-normal-form)
    const joined = top && !attitude.length && !report.length &&
      values(parts, "g.situations-and-contents.connective").length > 0 &&
      compareVersions(this.lang.language, "1.0") >= 0;
    t.parts = parts.map((p) => joined && p.kind === "filler" && pyShort(p.role) === "content"
      ? this.conjunct(p, world, mentioned) : this.part(p, world, mentioned));
    return t;
  }

  conjunct(p: Tree, world: string, mentioned: boolean): Tree {
    p.filler = this.node(p.filler, world, true, false, mentioned);
    return p;
  }

  term(t: Tree, world: string, mentioned = false): Tree {
    const parts = t.parts as Tree[];
    const referent = parts.some((p) => p.kind === "word" || p.kind === "party" ||
      p.kind === "dialect" ||
      p.kind === "ref" || (p.kind === "value" && (p.member as string).startsWith("g.reference.person.")));
    if (referent) {
      if (!values(parts, "g.reference.existence-commitment").length) {
        const existence = mentioned ? "mentioned-without-existence-asserted" :
          EXISTENCE_OF_WORLD.get(world);
        if (existence === undefined) throw new Error("KeyError: " + world);
        parts.push(value("g.reference.existence-commitment." + existence));
      }
      if (!values(parts, "g.reference.discourse-status").length) {
        // new where first written and given after (specification/meaning.md#reference): a
        // referent reached through a reference was written first in the entry it names,
        // and a participant was introduced when the exchange opened
        const given = parts.some((p) => p.kind === "ref" || p.kind === "party" ||
          p.kind === "dialect" ||
          (p.kind === "value" && GIVEN_PERSONS.has(p.member as string)));
        parts.push(value("g.reference.discourse-status." + (given ? "given" : "new")));
      }
      const external = parts.some((p) => p.kind === "value" &&
        (p.member === "g.reference.access.external" ||
          p.member === "g.reference.person.external-source"));
      if (external && !values(parts, "g.reference.verification").length) {
        parts.push(value("g.reference.verification.unverified"));
      }
    }
    t.parts = parts.map((p) => this.part(p, world, mentioned));
    return t;
  }

  part(p: Tree, world: string, mentioned = false): Tree {
    const k = p.kind;
    // a register-marked word is written as its base (specification/lexicon.md#registers),
    // and an irregular word as its regular form
    if (k === "word") return regularWord(registers.baseWord(p, this.lang), this.lang) as Tree;
    if (k === "filler") {
      const inner = mentioned && !(p.role as string).endsWith(".target-content") &&
        !(p.role as string).endsWith(".stands-for");
      p.filler = this.node(p.filler, world, false, false, inner);
    } else if (k === "quantity" && !truthy(get(p, "comparator"))) {
      p.comparator = "g.situations-and-contents.comparator.unstated";
    } else if (UNIT_KINDS.has(k) || k === "readings" || k === "idiom") {
      return this.node(p, world, false, false, mentioned);
    }
    return p;
  }

  // ------------------------------------------------------------ order
  rank(p: Tree): Rank {
    const k = p.kind;
    const cls = (id: string): number => this.classIndex.get(classOf(id)) ?? 99;
    const mem = (id: string): number => this.memberIndex.get(id) ?? 99;
    if (k === "word") return [0];
    if (k === "value") return [1, cls(p.member), mem(p.member)];
    if (k === "time") return [2, mem(p.index)];
    if (k === "quantity") return [3];
    if (k === "party") return [4];
    if (k === "dialect") return [4, 1];
    if (k === "ref") return [5];
    if (k === "filler") return [6, cls(p.role), mem(p.role)];
    const order: Record<string, number> = { assertion: 0, situation: 1, term: 2, readings: 3,
      wall: 4, same: 5 };
    return [7, Object.hasOwn(order, k) ? order[k] : 9];
  }

  /** One pass of canonical ordering over the move, deepest lists first. Returns whether
   * anything moved. */
  orderAll(t: Tree): boolean {
    const named = new Map<number, Tree>();
    collectNamed(t, named);
    let changed = false;
    const visit = (node: unknown): void => {
      if (Array.isArray(node)) {
        for (const x of node) visit(x);
      } else if (isObject(node)) {
        for (const v of Object.values(node)) visit(v);
        for (const key of SIBLING_KEYS) {
          const list = node[key];
          if (Array.isArray(list)) {
            const keyed = list.map((p: Tree) => ({ p, rank: this.rank(p),
              key: nameFreeKey(p, named, this.spell) }));
            keyed.sort((a, b) => compareRanks(a.rank, b.rank) || compareCodePoints(a.key, b.key));
            const sorted = keyed.map((x) => x.p);
            // A stable sort moves no two siblings with equal keys, and siblings with
            // equal keys are equal, so a change of order is a change of value.
            if (sorted.some((x, i) => x !== list[i])) {
              node[key] = sorted;
              changed = true;
            }
          }
        }
      }
    };
    visit(t);
    return changed;
  }

  // ------------------------------------------------------------ names
  /** Number the shared nodes in the order the normal form's traversal reaches them. */
  renumber(t: Tree): void {
    const order: number[] = [];
    const walk = (node: unknown): void => {
      if (Array.isArray(node)) {
        for (const x of node) walk(x);
      } else if (isObject(node)) {
        if (isUnit(node) && get(node, "name") !== null) order.push(node.name);
        for (const key of WALK_KEYS) {
          if (key in node && node[key] !== null) walk(node[key]);
        }
      }
    };
    walk(t);
    const mapping = new Map<number, number>();
    order.forEach((old, i) => mapping.set(old, i + 1));
    const apply = (node: unknown): void => {
      if (Array.isArray(node)) {
        for (const x of node) apply(x);
      } else if (isObject(node)) {
        if (isUnit(node) && get(node, "name") !== null) {
          const n = mapping.get(node.name);
          if (n === undefined) throw new Error("KeyError: " + node.name);
          node.name = n;
        }
        if (get(node, "kind") === "same" && mapping.has(get(node, "name") as number)) {
          node.name = mapping.get(node.name);
        }
        for (const v of Object.values(node)) apply(v);
      }
    };
    apply(t);
  }
}

/** The canonical order of references: by author, number, a serial's recipients and part,
 * as numbers. */
export function compareReferences(a: Tree, b: Tree): number {
  const target = compareCodePoints(a.target as string, b.target as string);
  if (target !== 0) return target;
  for (const key of ["author", "number"]) {
    const x = BigInt(a[key] as string);
    const y = BigInt(b[key] as string);
    if (x !== y) return x < y ? -1 : 1;
  }
  const ra = ((a.recipients ?? []) as string[]).map(BigInt);
  const rb = ((b.recipients ?? []) as string[]).map(BigInt);
  for (let i = 0; i < Math.min(ra.length, rb.length); i++) {
    if (ra[i] !== rb[i]) return ra[i] < rb[i] ? -1 : 1;
  }
  if (ra.length !== rb.length) return ra.length < rb.length ? -1 : 1;
  const pa = a.part === null || a.part === undefined ? -1 : a.part as number;
  const pb = b.part === null || b.part === undefined ? -1 : b.part as number;
  if (pa !== pb) return pa < pb ? -1 : 1;
  return compareCodePoints(a.ref as string, b.ref as string);
}

/** Whether a tree's shared names form a cycle; such a tree is ill-formed, which the
 * parser reports, and it is left unordered rather than recursed on. */
export function cyclic(t: Tree): boolean {
  const named = new Map<number, Tree>();
  collectNamed(t, named);
  const reach = new Map<number, Set<number>>();
  for (const [n, node] of named) {
    const inner = new Set<number>();
    refs(node.parts, inner);
    reach.set(n, inner);
  }
  const state = new Map<number, number>();
  const visit = (n: number): boolean => {
    state.set(n, 1);
    for (const m of reach.get(n) ?? []) {
      if (state.get(m) === 1 || (!state.has(m) && visit(m))) return true;
    }
    state.set(n, 2);
    return false;
  };
  return [...reach.keys()].sort((a, b) => a - b).some((n) => !state.has(n) && visit(n));
}

function refs(node: unknown, out: Set<number>): void {
  if (Array.isArray(node)) {
    for (const x of node) refs(x, out);
  } else if (isObject(node)) {
    if (get(node, "kind") === "same") out.add(node.name);
    if (isUnit(node) && get(node, "name") !== null) {
      out.add(node.name);
      return;
    }
    for (const v of Object.values(node)) refs(v, out);
  }
}

export function collectNamed(node: unknown, named: Map<number, Tree>): void {
  if (Array.isArray(node)) {
    for (const x of node) collectNamed(x, named);
  } else if (isObject(node)) {
    if (isUnit(node) && get(node, "name") !== null) named.set(node.name, node);
    for (const v of Object.values(node)) collectNamed(v, named);
  }
}

/** The name-free serialisation of a node: its words with its own name left out, every
 * shared node it contains standing as its digest, and every SAME as the digest of the
 * node it names. */
export function nameFreeKey(node: Tree, named: Map<number, Tree>, spell: Spell): string {
  if (get(node, "kind") === "filler") {
    // a role with its constituent: the constituent's name, too, stands as its digest, so
    // that the order never depends on numbering
    // (specification/meaning.md#the-normal-form)
    return nfPart(node, named, spell).join(" ");
  }
  return nfWords(node, named, spell, true).join(" ");
}

function digest(node: Tree, named: Map<number, Tree>, spell: Spell): string {
  return "#" + hex(sha256Text(nameFreeKey(node, named, spell)));
}

function nfWords(node: Tree, named: Map<number, Tree>, spell: Spell, top = false): string[] {
  const k = get(node, "kind") as string;
  if (UNIT_KINDS.has(k)) {
    if (get(node, "name") !== null && !top) return [digest(node, named, spell)];
    const out = [spell.f("g.structure." + k)];
    for (const p of node.parts) out.push(...nfPart(p, named, spell));
    out.push(spell.f("g.structure.end-" + k));
    return out;
  }
  if (k === "same") {
    const target = named.get(node.name);
    return [target !== undefined ? digest(target, named, spell) : "#" + node.name];
  }
  if (k === "readings") {
    const out = [spell.f("g.structure.readings"), spell.f(node.ambiguity)];
    for (const r of node.readings) out.push(...nfWords(r, named, spell));
    out.push(spell.f("g.structure.end-readings"));
    return out;
  }
  return k !== "ref" ? spell.part(node) : spell.ref(node);
}

function nfPart(p: Tree, named: Map<number, Tree>, spell: Spell): string[] {
  const k = p.kind;
  if (k === "filler") return [spell.f(p.role), ...nfWords(p.filler, named, spell)];
  if (UNIT_KINDS.has(k) || k === "same" || k === "readings") return nfWords(p, named, spell);
  if (k === "time") {
    // a time reference to a named unit stands as that unit's digest
    return spell.part(p, (name: number) => nfWords({ kind: "same", name }, named, spell));
  }
  return spell.part(p);
}
