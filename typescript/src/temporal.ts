// The temporal network of a move (specification/meaning.md#time), the mirror of
// python/rowih/temporal.py: every time the move writes, as a start and an end on one
// line, under the constraints its clock values, relations, durations, aspects and bases
// impose, checked for consistency. A weight is [seconds, -strict]; a cycle is negative
// when its weight is below [0, 0]. Bounds are added in the order the move writes its
// times, with all-pairs shortest paths kept current: O(n^2) for each bound, O(c * n^2)
// for c bounds over n endpoints. The arithmetic is IEEE double in the Python order.

import { type Language } from "./data.ts";
import { wordSort } from "./formation.ts";
import { ASPECT_OF_SORT } from "./normal.ts";
import { pyFloat } from "./pyformat.ts";
import { get, type Tree, truthy } from "./tree.ts";

const UNIT_SECONDS = new Map([["second", 1.0], ["minute", 60.0], ["hour", 3600.0],
  ["day", 86400.0], ["week", 604800.0], ["month", 2629746.0], ["year", 31556952.0]]);

type Bound = [string, string, boolean];
const RELATIONS = new Map<string, Bound[]>([
  ["before", [["xe", "ys", true]]],
  ["after", [["ye", "xs", true]]],
  ["meets", [["xe", "ys", false], ["ys", "xe", false]]],
  ["met-by", [["ye", "xs", false], ["xs", "ye", false]]],
  ["overlaps", [["xs", "ys", true], ["ys", "xe", true], ["xe", "ye", true]]],
  ["overlapped-by", [["ys", "xs", true], ["xs", "ye", true], ["ye", "xe", true]]],
  ["starts", [["xs", "ys", false], ["ys", "xs", false], ["xe", "ye", true]]],
  ["started-by", [["xs", "ys", false], ["ys", "xs", false], ["ye", "xe", true]]],
  ["during", [["ys", "xs", true], ["xe", "ye", true]]],
  ["contains", [["xs", "ys", true], ["ye", "xe", true]]],
  ["finishes", [["xe", "ye", false], ["ye", "xe", false], ["ys", "xs", true]]],
  ["finished-by", [["xe", "ye", false], ["ye", "xe", false], ["xs", "ys", true]]],
  ["equals", [["xs", "ys", false], ["ys", "xs", false], ["xe", "ye", false],
    ["ye", "xe", false]]],
]);

const ASPECT_BOUNDS = new Map<string, [string, string][]>([
  ["stative", [["es", "rs"], ["re", "ee"]]],
  ["progressive", [["es", "rs"], ["re", "ee"]]],
  ["continuative", [["es", "rs"], ["re", "ee"]]],
  ["perfective", [["rs", "es"], ["ee", "re"]]],
  ["completive", [["rs", "ee"], ["ee", "re"]]],
  ["interrupted", [["rs", "ee"], ["ee", "re"]]],
  ["inceptive", [["rs", "es"], ["es", "re"]]],
]);

const ASSERTION_TIMES = new Set(["observation-time", "inference-time", "validity-interval"]);
const SITUATION_TIMES = new Set(["event-time", "reference-time", "execution-time"]);
type Weight = [number, number];
const ZERO: Weight = [0.0, 0];

function short(identifier: string | null | undefined): string | null {
  if (identifier === null || identifier === undefined) return null;
  const i = identifier.lastIndexOf(".");
  return i < 0 ? identifier : identifier.slice(i + 1);
}

function lt(a: Weight, b: Weight): boolean {
  return a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]);
}

function le(a: Weight, b: Weight): boolean {
  return lt(a, b) || (a[0] === b[0] && a[1] === b[1]);
}

function addWeights(a: Weight, b: Weight): Weight {
  return [a[0] + b[0], a[1] + b[1]];
}

/** A number's value as [low, high], or null where it has none. */
function seconds(number: string): [number, number] | null {
  if (number.includes("~")) {
    const i = number.indexOf("~");
    const low = pyFloat(number.slice(0, i));
    const high = pyFloat(number.slice(i + 1));
    return low === null || high === null ? null : [low, high];
  }
  if (number.includes("/")) {
    const i = number.indexOf("/");
    const num = pyFloat(number.slice(0, i));
    const den = pyFloat(number.slice(i + 1));
    if (num === null || den === null || den === 0) return null;
    const v = num / den;
    return [v, v];
  }
  const v = pyFloat(number);
  return v === null ? null : [v, v];
}

class Network {
  nodes: string[] = [];
  dist = new Map<string, Map<string, Weight>>();

  node(key: string): string {
    if (!this.dist.has(key)) {
      this.dist.set(key, new Map([[key, ZERO]]));
      this.nodes.push(key);
    }
    return key;
  }

  get(u: string, v: string): Weight | null {
    return this.dist.get(u)!.get(v) ?? null;
  }

  bound(u: string, v: string, c: number, strict: boolean): boolean {
    const w: Weight = [c, strict ? -1 : 0];
    const back = this.get(v, u);
    if (back !== null && lt(addWeights(w, back), ZERO)) return false;
    const current = this.get(u, v);
    if (current !== null && le(current, w)) return true;
    const intoU: [string, Weight][] = [];
    for (const i of this.nodes) {
      const d = this.dist.get(i)!.get(u);
      if (d !== undefined) intoU.push([i, d]);
    }
    const fromV = [...this.dist.get(v)!.entries()];
    for (const [i, du] of intoU) {
      const row = this.dist.get(i)!;
      for (const [j, dv] of fromV) {
        const cand = addWeights(addWeights(du, w), dv);
        const old = row.get(j);
        if (old === undefined || lt(cand, old)) row.set(j, cand);
      }
    }
    return true;
  }
}

export class Temporal {
  lang: Language;
  net = new Network();
  comm: string;
  epoch: string | null = null;
  communicationTime: number | null;
  named = new Map<number, Tree>();
  parents = new Map<Tree, Tree | null>();
  ids = new Map<object, number>();
  failure: Tree | null = null;
  failed = false;
  deadline: [string, string] | null = null;
  illTyped: [Tree, string, string][] = [];

  constructor(lang: Language, communicationTime: number | null) {
    this.lang = lang;
    this.comm = this.net.node("comm");
    this.communicationTime = communicationTime;
  }

  id(x: object): number {
    if (!this.ids.has(x)) this.ids.set(x, this.ids.size + 1);
    return this.ids.get(x)!;
  }

  /** Whether some time closed a contradiction; `failure` is the part it was written on. */
  build(t: Tree): boolean {
    for (const c of t.constituents as Tree[]) this.index(c, null);
    if (truthy(get(t, "deadline"))) {
      const [ds, de] = this.endpoints("deadline");
      this.point(ds, de, t.deadline, t);
      this.deadline = [ds, de];
    }
    const world = moveWorld(t);
    for (const c of t.constituents as Tree[]) {
      this.unit(c, world);
      if (this.failed) return true;
    }
    return this.failed;
  }

  index(node: Tree, parent: Tree | null): void {
    if (node === null || typeof node !== "object") return;
    const k = get(node, "kind");
    if (k === "assertion" || k === "situation" || k === "term") {
      this.parents.set(node, parent);
      if (get(node, "name") !== null) this.named.set(node.name as number, node);
      for (const p of node.parts as Tree[]) {
        if (p.kind === "filler") this.index(p.filler, node);
        else if (["assertion", "situation", "term", "readings"].includes(p.kind)) this.index(p, node);
      }
    } else if (k === "readings") {
      for (const r of node.readings as Tree[]) this.index(r, parent);
    }
  }

  endpoints(key: string): [string, string] {
    return [this.net.node(key + "|start"), this.net.node(key + "|end")];
  }

  unitTimes(unit: Tree, index: string): [string, string] {
    const [s, e] = this.endpoints("u" + this.id(unit) + "|" + index);
    this.before(s, e, false, unit);
    return [s, e];
  }

  require(u: string, v: string, c: number, strict: boolean, blame: Tree | null): void {
    if (!this.failed && !this.net.bound(u, v, c, strict)) {
      this.failed = true;
      this.failure = blame;
    }
  }

  before(a: string, b: string, strict: boolean, blame: Tree | null): void {
    this.require(b, a, 0.0, strict, blame);
  }

  equal(u: string, v: string, c: number, blame: Tree | null): void {
    this.require(u, v, c, false, blame);
    this.require(v, u, -c, false, blame);
  }

  unit(node: Tree, world: string): void {
    const k = get(node, "kind");
    if (k === "readings") {
      for (const r of node.readings as Tree[]) this.unit(r, world);
      return;
    }
    if (k !== "assertion" && k !== "situation" && k !== "term") return;
    world = worldOf(node, world);
    for (const p of node.parts as Tree[]) {
      if (p.kind === "time") {
        const [s, e] = this.unitTimes(node, short(p.index)!);
        this.spec(s, e, p.spec, node, p);
      }
    }
    if (k === "assertion") this.assertion(node, world);
    if (k === "situation") this.aspect(node);
    for (const p of node.parts as Tree[]) {
      if (p.kind === "filler") this.unit(p.filler, world);
      else if (["assertion", "situation", "term", "readings"].includes(p.kind)) this.unit(p, world);
    }
  }

  spec(s: string, e: string, spec: Tree, unit: Tree, blame: Tree): void {
    const k = spec.kind;
    if (k === "now" || k === "absolute" || k === "offset") this.point(s, e, spec, blame);
    else if (k === "relation") this.relation(s, e, spec, unit, blame);
    else if (k === "interval") {
      this.endpoint(s, spec.from, unit, blame);
      this.endpoint(e, spec.until, unit, blame);
    } else if (k === "duration") this.duration(s, e, spec, blame);
  }

  clock(spec: Tree): [string, number] | null {
    const k = spec.kind;
    if (k === "now") return [this.comm, 0.0];
    if (k === "absolute") {
      const v = seconds(spec.number);
      if (v === null || v[0] !== v[1]) return null;
      return [this.epochNode(), v[0]];
    }
    if (k === "offset") {
      const v = seconds(spec.number);
      if (v === null || v[0] !== v[1]) return null;
      const d = v[0] * UNIT_SECONDS.get(short(spec.unit)!)!;
      return [this.comm, short(spec.anchor) === "ago" ? -d : d];
    }
    return null;
  }

  epochNode(): string {
    if (this.epoch === null) {
      this.epoch = this.net.node("epoch");
      if (this.communicationTime !== null) {
        this.equal(this.epoch, this.comm, this.communicationTime, null);
      }
    }
    return this.epoch;
  }

  point(s: string, e: string, spec: Tree, blame: Tree | null): void {
    const placed = this.clock(spec);
    this.equal(s, e, 0.0, blame);
    if (placed !== null) this.equal(placed[0], s, placed[1], blame);
  }

  endpoint(p: string, spec: Tree, unit: Tree, blame: Tree): void {
    if (spec.kind === "relation") this.relation(p, p, spec, unit, blame);
    else this.point(p, p, spec, blame);
  }

  reference(ref: Tree, unit: Tree, blame: Tree): [string, string] {
    if (ref.kind === "index") {
      const index = short(ref.index)!;
      if (get(ref, "unit") !== null) {
        const target = this.named.get(ref.unit.name as number);
        if (target === undefined) return this.endpoints("unnamed|" + ref.unit.name + "|" + index);
        const bears = target.kind === "assertion" ? ASSERTION_TIMES :
          target.kind === "situation" ? SITUATION_TIMES : new Set<string>();
        if (!bears.has(index)) this.illTyped.push([blame, target.kind, index]);
        return this.unitTimes(target, index);
      }
      return this.bare(index, unit);
    }
    const [s, e] = this.endpoints("r" + this.id(ref));
    this.point(s, e, ref, blame);
    return [s, e];
  }

  /** A bare index names that index of the nearest unit that bears it
   * (specification/notation.md#times). */
  bare(index: string, unit: Tree): [string, string] {
    if (index === "communication-time") return [this.comm, this.comm];
    if (index === "deadline") return this.deadline ?? this.endpoints("deadline");
    let node: Tree | null | undefined = unit;
    while (node !== null && node !== undefined) {
      const kind = node.kind;
      if ((kind === "assertion" && ASSERTION_TIMES.has(index)) ||
          (kind === "situation" && SITUATION_TIMES.has(index))) {
        return this.unitTimes(node, index);
      }
      node = this.parents.get(node);
    }
    return this.endpoints("unplaced|" + this.id(unit) + "|" + index);
  }

  relation(xs: string, xe: string, spec: Tree, unit: Tree, blame: Tree): void {
    const [ys, ye] = this.reference(spec.reference, unit, blame);
    const ends: Record<string, string> = { xs, xe, ys, ye };
    for (const [left, right, strict] of RELATIONS.get(short(spec.relation)!)!) {
      this.before(ends[left], ends[right], strict, blame);
    }
  }

  duration(s: string, e: string, spec: Tree, blame: Tree): void {
    const v = seconds(spec.number);
    if (v === null) return;
    const unit = UNIT_SECONDS.get(short(spec.unit)!)!;
    const low = v[0] * unit;
    const high = v[1] * unit;
    const comparator = short(get(spec, "comparator") as string | null) ?? "exactly";
    if (comparator === "exactly" || comparator === "at-least") this.require(e, s, -low, false, blame);
    if (comparator === "exactly" || comparator === "at-most") this.require(s, e, high, false, blame);
  }

  written(unit: Tree, index: string): boolean {
    return (unit.parts as Tree[]).some((p) => p.kind === "time" && short(p.index) === index);
  }

  /** The ordered times (specification/meaning.md#time), and observation after the start
   * of what is observed. */
  assertion(node: Tree, world: string): void {
    const hasObs = this.written(node, "observation-time");
    const hasInf = this.written(node, "inference-time");
    let os = "", oe = "", is = "";
    if (hasObs) {
      [os, oe] = this.unitTimes(node, "observation-time");
      this.before(os, this.comm, false, node);
    }
    if (hasInf) {
      [is] = this.unitTimes(node, "inference-time");
      this.before(is, this.comm, false, node);
    }
    if (hasObs && hasInf) this.before(os, is, false, node);
    const basis = (node.parts as Tree[]).filter((p) => p.kind === "value" &&
      (p.member as string).startsWith("g.standing.basis.")).map((p) => short(p.member));
    if (basis.length !== 1 || basis[0] !== "observation" || world !== "actual") return;
    const seen = hasObs ? oe : this.comm;
    for (const p of node.parts as Tree[]) {
      const target = p.kind === "situation" ? p : p.kind === "same" ? this.named.get(p.name) : undefined;
      if (target === undefined || get(target, "kind") !== "situation") continue;
      if (worldOf(target, world) !== "actual" || !this.written(target, "event-time")) continue;
      const [es] = this.unitTimes(target, "event-time");
      const blame = (target.parts as Tree[]).find((q) => q.kind === "time" &&
        short(q.index) === "event-time")!;
      this.before(es, seen, false, blame);
    }
  }

  aspect(node: Tree): void {
    if (!(this.written(node, "event-time") && this.written(node, "reference-time"))) return;
    const aspect = situationAspect(node, this.lang);
    const bounds = aspect === null ? undefined : ASPECT_BOUNDS.get(aspect);
    if (bounds === undefined) return;
    const [es, ee] = this.unitTimes(node, "event-time");
    const [rs, re] = this.unitTimes(node, "reference-time");
    const ends: Record<string, string> = { es, ee, rs, re };
    const blame = (node.parts as Tree[]).find((q) => q.kind === "time" &&
      short(q.index) === "reference-time")!;
    for (const [left, right] of bounds) this.before(ends[left], ends[right], false, blame);
  }
}

function worldOf(node: Tree, inherited: string): string {
  const written = (node.parts as Tree[]).filter((p) => p.kind === "value" &&
    (p.member as string).startsWith("g.situations-and-contents.world-of-evaluation."));
  return written.length ? short(written[0].member)! : inherited;
}

/** The world a move's content is evaluated in, as the normal form gives it. */
function moveWorld(t: Tree): string {
  const adds = (t.adds as string[]).length ? short((t.adds as string[])[0]) : null;
  return adds === "supposition" ? "within-a-supposition" : "actual";
}

/** The aspect written, or the default the normal form gives. */
export function situationAspect(node: Tree, lang: Language): string | null {
  const parts = node.parts as Tree[];
  for (const p of parts) {
    if (p.kind === "value" && (p.member as string).startsWith("g.situations-and-contents.aspect.")) {
      return short(p.member);
    }
  }
  if (parts.some((p) => (p.kind === "value" && (p.member as string).startsWith(
    "g.situations-and-contents.connective.")) || (p.kind === "filler" && short(p.role) === "condition"))) {
    return null;
  }
  for (const p of parts) {
    if (p.kind === "word" && (truthy(get(p, "entry")) || p.status === "formation")) {
      // a formation's sort is the one its parts give (`inv.word-formation`)
      const sort = wordSort(p, lang);
      if (sort !== null && ASPECT_OF_SORT.has(sort)) return ASPECT_OF_SORT.get(sort)!;
      break;
    }
  }
  if (parts.some((p) => p.kind === "value" && ((p.member as string).startsWith(
    "g.attitudes-and-aims.kind-of-attitude.") || (p.member as string).startsWith(
    "g.force.kind-of-normative-entry.")))) {
    return "stative";
  }
  return null;
}
