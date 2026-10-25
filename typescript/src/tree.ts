// The semantic representation's tree: each move as plain data, identifiers in place of
// forms, so that it is both what normalisation and checking work on and what an export
// writes. `fromAstMove` reads the AST; `Spell` writes a move tree back as words, which is
// the normal form's serialisation. Keys beginning with an underscore carry spans for
// diagnostics and are never written. The trees are objects whose keys keep the order the
// canonical implementation's dictionaries have, since exports and digests are made from
// them in that order.

import { type Language } from "./data.ts";
import { decodePayload } from "./lexer.ts";
import {
  ContentWord, DialectName, Filler, Idiom, IndexOf, type Move, Party, type Part, Quantity, ReadingSet,
  Reference, Same, TimeSpec, TimeValue, Unit, Value, Wall,
} from "./syntax.ts";
import { Writer } from "./writer.ts";

/** A node of a move tree: a JSON object, with `_span` where the AST had a span. */
// The tree is the canonical implementation's dictionary, read and written by key.
export type Tree = Record<string, any>;

/** Python's truthiness, for the values a tree holds. */
export function truthy(x: unknown): boolean {
  if (x === null || x === undefined || x === false || x === 0 || x === "") return false;
  if (Array.isArray(x)) return x.length > 0;
  if (typeof x === "object") return Object.keys(x as object).length > 0;
  return true;
}

/** `dict.get(key)`: the value, or null where the key is absent. */
export function get(t: Tree | null | undefined, key: string): unknown {
  if (t === null || t === undefined) return null;
  const v = t[key];
  return v === undefined ? null : v;
}

// ---------------------------------------------------------------- AST to tree

export function fromAstMove(move: Move): Tree {
  const h = move.head;
  const t: Tree = {
    kind: "move",
    adds: h.adds.map((v) => v.member),
    change: h.change.map((v) => v.member),
    authority: h.authority !== null ? h.authority.member : null,
    authority_term: h.authorityTerm !== null ? unitTree(h.authorityTerm) : null,
    deadline: h.deadline !== null ? specTree(h.deadline) : null,
    named: h.named !== null ? refTree(h.named) : null,
    also_named: h.alsoNamed.map(refTree),
    relations: h.relations.map((cw) => cw.word.identifier),
    precision_bound: h.precisionBound !== null,
    constituents: move.constituents.map(nodeTree),
    _span: move.words.length ? move.words[0].span : null,
  };
  // the social and textual component's choices, kept only where made, so that a move
  // without them carries no such keys
  // (specification/lexicon.md#conventional-expressions-and-idioms)
  if (h.act !== null) t.act = h.act.identifier;
  if (h.losses.length) t.losses = h.losses.map((v) => v.member);
  // and the register's choices, kept in the same way (specification/lexicon.md#registers)
  if (h.politeness !== null) t.politeness = h.politeness.identifier;
  if (h.diction !== null) t.diction = h.diction.identifier;
  if (h.register !== null) t.register = h.register.member;
  return t;
}

export function nodeTree(node: unknown): Tree {
  if (node instanceof Unit) return unitTree(node);
  if (node instanceof Same) return { kind: "same", name: Number(node.name.integer()) };
  if (node instanceof Wall) return wallTree(node);
  if (node instanceof ReadingSet) {
    return {
      kind: "readings", ambiguity: node.kind.member, readings: node.readings.map(nodeTree),
      _span: node.kind.word.span,
    };
  }
  if (node instanceof Reference) return refTree(node);
  if (node instanceof Idiom) return { kind: "idiom", entry: node.entry, _span: node.words[0].span };
  throw new TypeError(String((node as object)?.constructor?.name));
}

function unitTree(u: Unit): Tree {
  return {
    kind: u.kind, name: u.name !== null ? Number(u.name.integer()) : null,
    parts: u.parts.map(partTree), _span: u.openWord.span,
  };
}

function partTree(p: Part): Tree {
  if (p instanceof Value) return { kind: "value", member: p.member, _span: p.word.span };
  if (p instanceof ContentWord) {
    const w = p.word;
    const status = w.item !== null ? "known" : w.kind;
    return {
      kind: "word", form: w.form, entry: w.item !== null ? w.item.identifier : null, status,
      _span: w.span,
    };
  }
  if (p instanceof Filler) {
    return { kind: "filler", role: p.role.member, filler: nodeTree(p.filler), _span: p.role.word.span };
  }
  if (p instanceof TimeValue) {
    return { kind: "time", index: p.index.member, spec: specTree(p.spec), _span: p.index.word.span };
  }
  if (p instanceof Quantity) {
    let unit: string | null = null;
    if (p.unit instanceof Value) unit = p.unit.member;
    else if (p.unit instanceof ContentWord) unit = p.unit.word.identifier;
    return {
      kind: "quantity", comparator: p.comparator !== null ? p.comparator.member : null,
      number: p.number.text, unit, per: p.per !== null ? p.per.member : null,
      calibration: p.calibration !== null ? p.calibration.text : null,
      _span: p.number.words[0].span,
    };
  }
  if (p instanceof Party) return { kind: "party", number: p.number.text };
  if (p instanceof DialectName) return { kind: "dialect", number: p.number.text };
  if (p instanceof Reference) return refTree(p);
  return nodeTree(p);
}

function refTree(r: Reference): Tree {
  const tree: Tree = {
    kind: "ref", ref: r.kind, target: r.target, author: r.author.text, number: r.number.text,
    expected: r.expected.map((v) => v.member), status: r.status !== null ? r.status.member : null,
    part: r.part !== null ? Number(r.part.integer()) : null,
    _span: r.words.length ? r.words[0].span : null,
  };
  if (r.target === "serial") {
    // a message by its serial on the channel its recipients name, the serial written
    // without the zeros of its fixed width
    // (specification/discourse.md#naming-entries-and-messages)
    tree.number = String(r.number.integer());
    tree.recipients = r.recipients.map((n) => n.text);
  }
  return tree;
}

function specTree(s: TimeSpec): Tree {
  if (s.kind === "now") return { kind: "now" };
  if (s.kind === "absolute") return { kind: "absolute", number: s.number!.text };
  if (s.kind === "offset") {
    return { kind: "offset", number: s.number!.text, unit: s.unit!.member, anchor: s.anchor!.member };
  }
  if (s.kind === "relation") {
    const ref = s.reference;
    let refT: Tree;
    if (ref instanceof Value) refT = { kind: "index", index: ref.member };
    else if (ref instanceof IndexOf) {
      refT = { kind: "index", index: ref.index.member,
        unit: { kind: "same", name: Number(ref.same.name.integer()) } };
    } else refT = specTree(ref as TimeSpec);
    return { kind: "relation", relation: s.relation!.member, reference: refT };
  }
  if (s.kind === "interval") {
    return { kind: "interval", from: specTree(s.reference as TimeSpec), until: specTree(s.until!) };
  }
  if (s.kind === "duration" || s.kind === "rate") {
    return { kind: s.kind, comparator: s.comparator !== null ? s.comparator.member : null,
      number: s.number!.text, unit: s.unit!.member };
  }
  throw new Error("ValueError: " + s.kind);
}

function wallTree(w: Wall): Tree {
  if (w.kind.name === "declared-data") {
    let type = "";
    for (const byte of w.typePayload!.payload) {
      if (byte > 127) throw new Error("UnicodeDecodeError: a declared type outside ASCII");
      type += String.fromCharCode(byte);
    }
    return {
      kind: "wall", material: w.kind.member, type, data: w.payload!.form,
      _span: w.kind.word.span,
    };
  }
  return {
    kind: "wall", material: w.kind.member, words: w.words.map((x) => x.form),
    _span: w.kind.word.span,
  };
}

// ---------------------------------------------------------------- tree to words

/** Writes trees as word forms. */
export class Spell {
  lang: Language;
  wr: Writer;

  constructor(lang: Language) {
    this.lang = lang;
    this.wr = new Writer(lang);
  }

  f(identifier: string): string {
    return this.lang.item(identifier).form;
  }

  moveBody(t: Tree): string[] {
    const force: string[] = [...t.adds, ...t.change];
    const out: string[] = [];
    if (truthy(get(t, "act"))) {
      // the act word stands for the force values its entry expands to
      const covered = this.lang.entries.get(t.act).expansion as string[];
      out.push(this.f(t.act), ...force.slice(covered.length).map((i) => this.f(i)));
    } else {
      out.push(...force.map((i) => this.f(i)));
    }
    if (truthy(get(t, "authority"))) {
      out.push(this.f(t.authority));
      if (truthy(get(t, "authority_term"))) out.push(...this.node(t.authority_term));
    }
    if (truthy(get(t, "deadline"))) {
      out.push(this.f("g.time.time-index.deadline"));
      out.push(...this.spec(t.deadline));
    }
    if (truthy(get(t, "named"))) out.push(...this.ref(t.named));
    for (const r of (get(t, "also_named") ?? []) as Tree[]) out.push(...this.ref(r));
    for (const i of (get(t, "relations") ?? []) as string[]) out.push(this.f(i));
    for (const key of ["politeness", "diction"]) {
      if (truthy(get(t, key))) out.push(this.f(t[key]));
    }
    for (const i of (get(t, "losses") ?? []) as string[]) out.push(this.f(i));
    if (truthy(get(t, "register"))) out.push(this.f(t.register));
    if (truthy(get(t, "precision_bound"))) {
      out.push(this.f("g.ambiguity-and-figures.precision-bound-declaration.precision-bound"));
    }
    for (const c of t.constituents) out.push(...this.node(c));
    return out;
  }

  move(t: Tree): string[] {
    return this.wr.move(this.moveBody(t));
  }

  node(t: Tree): string[] {
    const k = t.kind;
    if (k === "assertion" || k === "situation" || k === "term") {
      const out = [this.f("g.structure." + k)];
      if (get(t, "name") !== null) out.push(this.f("g.structure.name"), ...this.wr.name(t.name));
      for (const p of t.parts) out.push(...this.part(p));
      out.push(this.f("g.structure.end-" + k));
      return out;
    }
    if (k === "same") return [this.f("g.structure.same"), ...this.wr.name(t.name)];
    if (k === "wall") {
      const out = [this.f("g.structure.wall"), this.f(t.material)];
      if ("data" in t) {
        const typeBytes = Uint8Array.from(t.type as string, (c) => c.charCodeAt(0));
        const data = decodePayload(t.data) ?? new Uint8Array(0);
        out.push(...this.wr.payload(typeBytes), ...this.wr.number(String(data.length)), t.data);
      } else {
        out.push(...t.words);
      }
      out.push(this.f("g.structure.end-wall"));
      return out;
    }
    if (k === "readings") {
      const out = [this.f("g.structure.readings"), this.f(t.ambiguity)];
      for (const r of t.readings) out.push(...this.node(r));
      out.push(this.f("g.structure.end-readings"));
      return out;
    }
    if (k === "ref") return this.ref(t);
    if (k === "idiom") {
      const words = this.lang.semantic.get(t.entry)["literal structure"] as string[];
      return words.map((w) => this.f(w));
    }
    throw new Error("ValueError: " + k);
  }

  /** `same`, where given, writes the SAME of a time reference in place of its name (the
   * name-free key of the normal form). */
  part(p: Tree, same: ((name: number) => string[]) | null = null): string[] {
    const k = p.kind;
    if (k === "value") return [this.f(p.member)];
    if (k === "word") return [p.form];
    if (k === "filler") return [this.f(p.role), ...this.node(p.filler)];
    if (k === "time") return [this.f(p.index), ...this.spec(p.spec, p.index, same)];
    if (k === "quantity") {
      const out = truthy(get(p, "comparator")) ? [this.f(p.comparator)] : [];
      out.push(...this.wr.number(p.number));
      if (truthy(get(p, "unit"))) out.push(this.f(p.unit));
      if (truthy(get(p, "per"))) out.push(this.f("g.time.time-anchor.per"), this.f(p.per));
      if (truthy(get(p, "calibration"))) {
        out.push(this.f("g.structure.party"), ...this.wr.number(p.calibration));
      }
      return out;
    }
    if (k === "party") return [this.f("g.structure.party"), ...this.wr.number(p.number)];
    if (k === "dialect") return [this.f("g.structure.dialect"), ...this.wr.number(p.number)];
    return this.node(p);
  }

  ref(r: Tree): string[] {
    const out = [this.f("g.reference.kind-of-reference." + r.ref)];
    if (r.target === "message") {
      out.push(this.f("g.structure.message-target"), ...this.wr.number(r.author));
      // a message is named by its sender and the first entry its envelope states
      out.push(...this.wr.number(r.number));
    } else if (r.target === "serial") {
      out.push(this.f("g.structure.message-serial"), ...this.wr.number(r.author));
      out.push(...this.wr.number(r.number, this.lang.protocol["identifier width"]));
      for (const recipient of r.recipients as string[]) out.push(...this.wr.number(recipient));
    } else {
      out.push(...this.wr.number(r.author), ...this.wr.number(r.number));
      for (const i of (get(r, "expected") ?? []) as string[]) out.push(this.f(i));
      if (truthy(get(r, "status"))) out.push(this.f(r.status));
    }
    if (get(r, "part") !== null) out.push(this.f("g.structure.part"), ...this.wr.name(r.part));
    return out;
  }

  spec(s: Tree, index: string | null = null, same: ((name: number) => string[]) | null = null): string[] {
    const k = s.kind;
    if (k === "now") return [this.f("g.time.time-anchor.now")];
    if (k === "absolute") return this.wr.number(s.number);
    if (k === "offset") return [...this.wr.number(s.number), this.f(s.unit), this.f(s.anchor)];
    if (k === "relation") {
      const ref = s.reference;
      let tail: string[];
      if (ref.kind !== "index") tail = this.spec(ref);
      else if (get(ref, "unit") === null) tail = [this.f(ref.index)];
      else {
        const name = ref.unit.name as number;
        tail = [...(same !== null ? same(name) : [this.f("g.structure.same"), ...this.wr.name(name)]),
          this.f(ref.index)];
      }
      return [this.f(s.relation), ...tail];
    }
    if (k === "interval") {
      // the validity interval is always one and writes its pair unmarked; any other index
      // marks its end with UNTIL (specification/notation.md#times)
      const marker = index === "g.time.time-index.validity-interval" ? [] : [this.f("g.structure.until")];
      return [...this.spec(s.from, null, same), ...marker, ...this.spec(s.until, null, same)];
    }
    if (k === "duration" || k === "rate") {
      const out = truthy(get(s, "comparator")) ? [this.f(s.comparator)] : [];
      out.push(...this.wr.number(s.number));
      if (k === "rate") out.push(this.f("g.time.time-anchor.per"));
      return [...out, this.f(s.unit)];
    }
    throw new Error("ValueError: " + k);
  }
}

/** The tree without its underscore keys, as an export writes it: a fresh copy. */
export function stripPrivate(t: unknown): unknown {
  if (Array.isArray(t)) return t.map(stripPrivate);
  if (t !== null && typeof t === "object") {
    const out: Tree = {};
    for (const [k, v] of Object.entries(t)) if (!k.startsWith("_")) out[k] = stripPrivate(v);
    return out;
  }
  return t;
}
