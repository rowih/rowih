// The API of the parser and the renderer: parse, render, validate, lookup, normalise,
// convert, checkValues, tokenize and version. No function throws for any input: each
// returns its result together with its diagnostics.

import { Item, type Language, type Releases, type Source } from "./data.ts";
import { Diagnostic } from "./diagnostics.ts";
import { lex, tokenize as tokenizeText, type Word } from "./lexer.ts";
import { Checker, type MoveClass, moveClass, precisionBound } from "./checker.ts";
import { compose, type Meaning } from "./formation.ts";
import { Normaliser } from "./normal.ts";
import { parseWords } from "./parser.ts";
import * as registers from "./registers.ts";
import { dumps, type Json, zeroPad } from "./pyformat.ts";
import { FORMS } from "./drawing.ts";
import { CONTRASTS, html, png, svg, terminal } from "./render.ts";
import { canonicalLines, checkValue, toNative } from "./serialise.ts";
import { type Envelope, type Message, type StatementPart } from "./syntax.ts";
import { compareVersions } from "./versions.ts";
import { fromAstMove, Spell, stripPrivate, type Tree } from "./tree.ts";

export class Analysis {
  text: string;
  encoding: string;
  words: Word[];
  message: Message | null = null;
  moves: Tree[] = []; // move trees
  normal: Tree[] = []; // normal-form move trees
  classes: MoveClass[] = []; // the computed class of each move
  diagnostics: Diagnostic[];
  canonical = "";
  normalText = "";
  // the social and textual component of each move: the act word and the idioms its
  // realisation chose, the losses it declares, and its register, diction, politeness word
  // and register-marked words (specification/lexicon.md#registers)
  social: Tree[] = [];
  // the meaning each formation the release does not list has from its parts
  formations: Tree[] = [];
  // the statement of a protocol message, which carries no moves
  // (specification/protocol.md#protocol-messages): what it states and its parts, each a
  // channel with serials or entries
  statement: Tree | null = null;
  // how far what was parsed is vouched for in transit
  // (specification/protocol.md#the-check-values): verified, lowered or unchecked
  confidence = "unchecked";

  constructor(text: string, encoding: string, words: Word[], diagnostics: Diagnostic[]) {
    this.text = text;
    this.encoding = encoding;
    this.words = words;
    this.diagnostics = diagnostics;
  }

  get ok(): boolean {
    return this.diagnostics.length === 0;
  }
}

export function version(lang: Language): Record<string, unknown> {
  const reads = readsOf(lang);
  const dialects: Record<string, string> = {};
  for (const [name, release] of newestDialects(lang)) dialects[name] = release.version;
  return { language: lang.grammar.version, lexicon: lang.release.version,
    protocol: lang.protocol.version, dialects,
    reads: { language: reads.language, lexicon: reads.lexicon, protocol: reads.protocol,
      dialects: reads.dialects } };
}

/** The newest release of each dialect this implementation holds, by name, as the
 * canonical implementation's `data.dialects` gives them: none where the loader supplies
 * no releases, as a page that bundles one release does not. */
export function newestDialects(lang: Language): Map<string, Source> {
  const out = new Map<string, Source>();
  if (lang.releases === null) return out;
  for (const [number, v] of lang.releases.reads().dialects) {
    const release = lang.releases.dialectRelease(number, v);
    if (release !== undefined) out.set(release.dialect as string, release);
  }
  return out;
}

/** What a reader reads: the releases its loader supplies, or its own release alone. */
function readsOf(lang: Language): ReturnType<Releases["reads"]> {
  if (lang.releases !== null) return lang.releases.reads();
  return { language: [lang.language], lexicon: [lang.version],
    protocol: [lang.protocol.version], dialects: [] };
}

type Lacking = { language?: string[]; lexicon?: string[]; protocol?: string[];
  dialects?: [number, string, string][] };

/** What a message names, and either the release it is read under or what the reader
 * lacks of it, as the canonical implementation's `releases.resolve` gives them. */
function resolve(env: Envelope, lang: Language): { lacking: Lacking; pairing: string[];
  load: [string, string, [number, string][]] | null } {
  const named: Record<string, string> = { language: env.version[0].text,
    lexicon: env.version[1].text, protocol: env.version[2].text };
  const dialects = env.dialects.map(([n, v, d]) =>
    [Number(n.integer()), v.text, d.text] as [number, string, string]);
  const reads = readsOf(lang);
  const lacking: Lacking = {};
  for (const kind of ["language", "lexicon", "protocol"] as const) {
    if (!reads[kind].includes(named[kind])) (lacking[kind] ??= []).push(named[kind]);
  }
  for (const [number, version, digest] of dialects) {
    const release = lang.releases?.dialectRelease(number, version);
    if (!reads.dialects.some(([n, v]) => n === number && v === version) ||
      release === undefined || release.digest !== digest) {
      (lacking.dialects ??= []).push([number, version, digest]);
    }
  }
  const pairing: string[] = [];
  if (Object.keys(lacking).length) return { lacking, pairing, load: null };
  const records = lang.releases !== null ? lang.releases.languageReleases.language as Source[]
    : [];
  const record = records.find((r) => r.language === named.language) ??
    { lexicon: lang.version };
  const least = record["least lexicon"] ?? record.lexicon;
  if (compareVersions(named.lexicon, least) < 0) {
    pairing.push("language " + named.language + " names a lexicon from " + least);
  }
  for (const [number, version] of dialects) {
    const formed = lang.releases?.dialectRelease(number, version)["formed from lexicon"];
    if (compareVersions(named.lexicon, formed) < 0) {
      pairing.push("dialect " + number + " " + version + " is formed from lexicon " + formed);
    }
  }
  return { lacking, pairing, load: pairing.length ? null : [named.lexicon, named.language,
    dialects.map(([n, v]) => [n, v] as [number, string])] };
}

function readsText(reads: ReturnType<Releases["reads"]>, lacking: Lacking): string[] {
  const out: string[] = [];
  for (const kind of ["language", "lexicon", "protocol"] as const) {
    if (lacking[kind] !== undefined) out.push(kind + " " + reads[kind].join(" "));
  }
  if (lacking.dialects !== undefined) {
    out.push("dialects " + (reads.dialects.map(([n, v]) => n + " " + v).join(" ") || "none"));
  }
  return out;
}

function lackingText(lacking: Lacking): string[] {
  const out: string[] = [];
  for (const kind of ["language", "lexicon", "protocol"] as const) {
    for (const v of lacking[kind] ?? []) out.push(kind + " " + v);
  }
  for (const [n, v, d] of lacking.dialects ?? []) out.push("dialect " + n + " " + v + " " + d);
  return out;
}

/** The pairs of forms a message's resources would confuse: a compressed form of a named
 * dialect within one edit of a word of the named lexicon release or of another named
 * dialect's form. */
function conflicts(lang: Language): string[] {
  const forms = [...lang.dialectForms.values()].map(
    (f) => [f["orthographic form"] as string, f["machine identifier"] as string]);
  const out: string[] = [];
  forms.forEach(([form, ident], i) => {
    for (const [other, item] of lang.byForm) {
      if (item.identifier !== ident && item.kind !== "move-check" &&
        other.length === form.length && levenshtein(form, other) < 2) {
        out.push(ident + " " + item.identifier);
      }
    }
    for (const [form2, ident2] of forms.slice(i + 1)) {
      if (form2 === form) out.push(ident + " " + ident2);
    }
  });
  return out;
}

function levenshtein(a: string, b: string): number {
  let row = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const next = [i];
    for (let j = 1; j <= b.length; j++) {
      next.push(Math.min(row[j] + 1, next[j - 1] + 1, row[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1)));
    }
    row = next;
  }
  return row[b.length];
}

function read(text: string, lang: Language, encoding: string | null): Analysis {
  const [tokens, diags, enc] = tokenizeText(text, lang, encoding);
  const [words, ldiags] = lex(tokens, lang);
  const a = new Analysis(text, enc, words, [...diags, ...ldiags]);
  const [message, pdiags] = parseWords(words, lang);
  a.diagnostics.push(...pdiags);
  a.message = message;
  if (message !== null) a.canonical = canonicalLines(message.envelope.words, message.lines);
  return a;
}

// As long as the canonical implementation's `parse`, which it follows statement for
// statement so that the two can be read side by side.
export function parse(text: string, own: Language, encoding: string | null = null): Analysis {
  let a = read(text, own, encoding);
  if (a.message === null) return a;
  let env = a.message.envelope;
  if (env.isProtocol) {
    // a protocol message is read whatever version it states, since every word it can
    // hold is a fixed form (specification/protocol.md#versions-and-features)
    if (a.message.statement !== null) {
      a.statement = { kind: a.message.statement.kind,
        parts: a.message.statement.parts.map((p) => statementPartJson(p)) };
      a.diagnostics.push(...checkValuesOf(a, own));
    }
    return a;
  }
  // Normalisation reads only what the message names
  // (specification/conformance.md#what-a-conformant-implementation-must-do): what the
  // reader lacks of it is reported, with what the reader reads, and the moves are not
  // interpreted under anything else.
  const res = resolve(env, own);
  const span = env.version[0].words[0].span;
  if (Object.keys(res.lacking).length) {
    // the words the reader lacks for want of what the message names are the lack this
    // diagnostic reports, not each a word of its own
    a.diagnostics = a.diagnostics.filter((d) => d.code !== "d.lexer.unknown-word");
    a.diagnostics.push(new Diagnostic("d.parser.version-unknown", span, {
      expected: readsText(readsOf(own), res.lacking), detected: lackingText(res.lacking),
      recoverability: "restate in what the reader reads" }));
    return a;
  }
  if (res.pairing.length) {
    a.diagnostics.push(new Diagnostic("d.parser.version-pairing", span,
      { detected: res.pairing }));
    return a;
  }
  const [version, language, named] = res.load as [string, string, [number, string][]];
  const lang = own.releases !== null ? own.releases.load(version, language, named) : own;
  if (lang.version !== own.version || lang.language !== own.language ||
    JSON.stringify(lang.dialects) !== JSON.stringify(own.dialects)) {
    a = read(text, lang, encoding);
    if (a.message === null) return a;
    env = a.message.envelope;
  }
  const message = a.message as Message;
  const clashes = lang.dialectForms.size ? conflicts(lang) : [];
  if (clashes.length) {
    a.diagnostics.push(new Diagnostic("d.parser.dialect-conflict", span, { detected: clashes }));
    return a;
  }
  const sender = env.sender.text;
  const checker = new Checker(lang, env);
  const norm = new Normaliser(lang);
  const spell = new Spell(lang);
  const lines: string[] = [];
  for (const m of message.moves) {
    const t = fromAstMove(m);
    a.moves.push(t);
    a.classes.push(moveClass(t));
    checker.checkMove(t, sender);
    const n = norm.move(t);
    a.normal.push(n);
    a.social.push({ act: t.act ?? null, idioms: [...norm.resolved],
      losses: [...(t.losses ?? [])], register: registers.code(t, lang),
      diction: t.diction ?? null, politeness: t.politeness ?? null,
      marked: registers.markedWords(t, lang) });
    if (norm.resolved.length) {
      // the expansion must fit where the idiom stands
      // (specification/lexicon.md#conventional-expressions-and-idioms)
      const known = new Set(checker.diags.map((d) => d.code));
      const inner = new Checker(lang, env);
      // in the move's own register, which the normal form sets aside
      inner.checkMove(registers.carry(t, n), sender);
      for (const d of inner.diags) {
        if (known.has(d.code)) continue;
        d.location = t._span ?? null;
        checker.diags.push(d);
      }
    }
    lines.push(spell.move(n).join(" "));
  }
  a.diagnostics.push(...checker.diags);
  a.formations = a.words.filter((w) => w.kind === "formation").map((w) => ({
    form: w.form, meaning: compose(w.morphemes, lang) as Meaning | null }));
  a.normalText = lines.map((line) => line + "\n").join("");
  a.diagnostics.push(...checkValuesOf(a, lang));
  return a;
}

/** A statement part as the canonical implementation's JSON writes it: numbers as numbers,
 * versions and digests as strings. */
function statementPartJson(p: StatementPart): Json[] {
  return p.map((x) => typeof x === "string" ? x : typeof x === "bigint" ? Number(x) :
    (x as (bigint | string)[]).map((y) => typeof y === "bigint" ? Number(y) : y)) as Json[];
}

function checkValuesOf(a: Analysis, lang: Language): Diagnostic[] {
  const message = a.message as Message;
  const env = message.envelope;
  const out: Diagnostic[] = [];
  // every precision-bound move, by any of three routes, needs the value
  // (`inv.integrity-value-required`; specification/grammar.md#precision-bound-moves), and
  // so does every protocol message (protocol 0.3)
  const width = lang.protocol["check value width"];
  const needs = env.isProtocol || a.moves.some((t) => precisionBound(t));
  if (needs && env.integrity === null) {
    out.push(new Diagnostic("d.checker.integrity-value-required",
      env.words.length ? env.words[0].span : null, { expected: ["an integrity check value"] }));
  }
  let integrityOk = true;
  if (env.integrity !== null && message.lines.length > 0) {
    const computed = checkValue(canonicalLines(env.words, message.lines, env.integrityWords),
      width);
    a.confidence = "verified";
    if (BigInt(computed) !== env.integrity.integer()) {
      integrityOk = false;
      a.confidence = "lowered";
      out.push(new Diagnostic("d.check-values.integrity-mismatch", env.integrity.words[0].span,
        { expected: [zeroPad(computed, width)], detected: [env.integrity.text],
          recoverability: "send again" }));
    }
  }
  if (env.semantic !== null && integrityOk) {
    const computed = checkValue(a.normalText, width);
    if (BigInt(computed) !== env.semantic.integer()) {
      out.push(new Diagnostic("d.check-values.semantic-mismatch", env.semantic.words[0].span,
        { expected: [zeroPad(computed, width)], detected: [env.semantic.text] }));
    }
  }
  return out;
}

export function validate(text: string, lang: Language, encoding: string | null = null):
  Diagnostic[] {
  return parse(text, lang, encoding).diagnostics;
}

export function normalise(text: string, lang: Language): [string, Diagnostic[]] {
  const a = parse(text, lang);
  return [a.normalText, a.diagnostics];
}

export interface CheckValues {
  diagnostics: Diagnostic[];
  integrity?: { stated: string | null; computed: string };
  semantic?: { stated: string | null; computed: string };
}

export function checkValues(text: string, lang: Language): CheckValues {
  const a = parse(text, lang);
  const result: CheckValues = { diagnostics: a.diagnostics };
  if (a.message !== null) {
    const env = a.message.envelope;
    const width = lang.protocol["check value width"];
    result.integrity = {
      stated: env.integrity !== null ? env.integrity.text : null,
      computed: zeroPad(checkValue(canonicalLines(env.words, a.message.lines,
        env.integrityWords), width), width),
    };
    result.semantic = { stated: env.semantic !== null ? env.semantic.text : null,
      computed: zeroPad(checkValue(a.normalText, width), width) };
  }
  return result;
}

/** To the transliteration (canonical layout), the native digital form, the canonical
 * serialisation, or a JSON export marked as a view. */
export function convert(text: string, to: string, lang: Language): [string, Diagnostic[]] {
  const a = parse(text, lang);
  if (a.message === null) return ["", a.diagnostics];
  const env = a.message.envelope;
  const lines = [env.words, ...a.message.lines];
  if (to === "transliteration" || to === "canonical") return [a.canonical, a.diagnostics];
  if (to === "native") return [toNative(lines, lang), a.diagnostics];
  if (to === "json") {
    const view: { [key: string]: Json } = {
      "view": "export", "made from": a.encoding,
      "note": "an export of the analysis; never parsed as the language",
      "envelope": {
        "sender": env.sender.text, "recipients": env.recipients.map((r) => r.text),
        "communication time": env.time.text, "version": env.version.map((v) => v.text),
        "identifier": env.identifier.text, "first entry": env.firstEntry.text,
      },
      "moves": a.moves.map((t) => stripPrivate(t) as Json),
    };
    if (a.statement !== null) view["statement"] = a.statement as Json;
    return [dumps(view, 1) + "\n", a.diagnostics];
  }
  return ["", [new Diagnostic("d.parser.unexpected-word", null, {
    expected: ["transliteration", "native", "canonical", "json"], detected: [to],
  })]];
}

/** The rendering of a message in a format the specification names: SVG, PNG (bytes),
 * HTML, or the terminal representation, in the display, compact or handwritten form, at
 * normal or high contrast (specification/writing-system.md#the-renderings). */
export function render(text: string, format: "png", lang: Language, hasFont?: boolean,
  form?: string, contrast?: string): [Uint8Array, Diagnostic[]];
export function render(text: string, format: string, lang: Language, hasFont?: boolean,
  form?: string, contrast?: string): [string, Diagnostic[]];
export function render(text: string, format: string, lang: Language, hasFont = false,
  form = "display", contrast = "normal"): [string | Uint8Array, Diagnostic[]] {
  const a = parse(text, lang);
  if (!FORMS.includes(form) || !CONTRASTS.includes(contrast)) {
    return ["", [new Diagnostic("d.parser.unexpected-word", null, {
      expected: [...FORMS, ...CONTRASTS], detected: [form, contrast],
    })]];
  }
  if (format === "svg") return [svg(a, lang, form, contrast), a.diagnostics];
  if (format === "png") return [png(a, lang, form, contrast), a.diagnostics];
  if (format === "html") return [html(a, lang, form, contrast), a.diagnostics];
  if (format === "terminal") return [terminal(a, lang, hasFont), a.diagnostics];
  return ["", [new Diagnostic("d.parser.unexpected-word", null, {
    expected: ["svg", "png", "html", "terminal"], detected: [format],
  })]];
}

export function tokenize(text: string, lang: Language): [Word[], Diagnostic[]] {
  const [tokens, diags] = tokenizeText(text, lang);
  const [words, ldiags] = lex(tokens, lang);
  return [words, [...diags, ...ldiags]];
}

export function lookup(term: string, lang: Language): Item[] {
  const t = term.toLowerCase();
  const out: Item[] = [];
  for (const item of lang.items.values()) {
    if (t === item.form || t === item.identifier.toLowerCase() || t === item.name.toLowerCase() ||
      item.gloss.toLowerCase().replace(/-/g, " ").split(/\s+/).filter((x) => x).includes(t)) {
      out.push(item);
    }
  }
  // the terms of each dialect's newest release, and its compressed forms
  // (specification/dialects.md#dialects-registers-and-technical-terms;
  // specification/dialects.md#compressed-forms)
  for (const d of newestDialects(lang).values()) {
    for (const x of (d.terms ?? []) as Source[]) {
      if ([x["orthographic form"], x["machine identifier"].toLowerCase(),
        x.term.toLowerCase()].includes(t)) {
        out.push(new Item("jargon", x["machine identifier"], x["orthographic form"],
          (x.term as string).toUpperCase().replace(/ /g, "-"),
          { name: x.term, sort: x.sort, category: "jargon" }));
      }
    }
    for (const f of (d.forms ?? []) as Source[]) {
      if ([f["orthographic form"], f["machine identifier"].toLowerCase(),
        f.term.toLowerCase()].includes(t)) {
        out.push(new Item("dialect", f["machine identifier"], f["orthographic form"],
          (f.key as string).toUpperCase().replace(/ /g, "-"),
          { name: f.key, sort: f.sort, category: "dialect form" }));
      }
    }
  }
  return out;
}
