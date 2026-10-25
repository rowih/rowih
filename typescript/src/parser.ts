// One module, as long as the canonical implementation's `parser.py`, which it follows
// production for production so that the two can be read side by side.
//
// The parser words to the AST by the productions of `language/grammar.json`, with the
// count, the move check word, every number's check word and the widths verified. Each
// rejection is a diagnostic; parsing resumes at the next move when a move's count is
// intact.

import { type Language } from "./data.ts";
import { Diagnostic, Reject, Span } from "./diagnostics.ts";
import { type Word } from "./lexer.ts";
import { compareVersions, ordered, wellFormed } from "./versions.ts";
import {
  Authentication, type Constituent, ContentWord, DialectName, Envelope, Filler, Head, Idiom, IndexOf,
  Message, Move, NumberNode,
  Party, type Part, Quantity, ReadingSet, Reference, Same, Statement, type StatementPart,
  TimeSpec, TimeValue, Unit, Value, Wall,
} from "./syntax.ts";

// RFC 6838 § 4.2: type "/" subtype, each a restricted name.
const MEDIA_TYPE = /^[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}\/[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}$/;
const FIELD = "g.message.message-field.";
const UNIT_OPEN = new Map<string, [string, string]>([
  ["g.structure.assertion", ["assertion", "g.structure.end-assertion"]],
  ["g.structure.situation", ["situation", "g.structure.end-situation"]],
  ["g.structure.term", ["term", "g.structure.end-term"]],
]);
const FILLER_ROLES = new Set(["g.situations-and-contents.participation",
  "g.attitudes-and-aims.counterparty", "g.standing.provenance-link",
  "g.ambiguity-and-figures.figures-relation"]);
const CONDITION = "g.situations-and-contents.connective.condition";
const LOSS = "g.ambiguity-and-figures.declared-loss";
const REGISTER = "g.ambiguity-and-figures.register";
const NUMERAL = "g.numbers.numeral";
const CHECK = "g.numbers.check-word";
const COMPARATOR = "g.situations-and-contents.comparator";
const UNTIL = "g.structure.until";
const DIALECT = "g.structure.dialect";
const PART = "g.protocol.statement-part.";
const VERSION_PARTS = new Map<string, "language" | "lexicon" | "protocol">([
  [PART + "language-version", "language"], [PART + "lexicon-version", "lexicon"],
  [PART + "protocol-version", "protocol"]]);
// The times that may last, and those that may also be stated by their length alone
// (specification/notation.md#times).
const SPANNING_TIMES = new Set(["observation-time", "event-time", "reference-time", "execution-time"]);
const MEASURED_TIMES = new Set(["event-time", "reference-time", "execution-time"]);
const SUBCLASS = new Map<string, string>([
  ["issue", "g.force.kind-of-issue"],
  ["normative-entry", "g.force.kind-of-normative-entry"],
  ["setting", "g.force.kind-of-setting"],
]);

/** Each digit times (i mod 10) + 1, i counting from 0 at the left, summed mod 11. */
export function numberCheck(digits: string): number {
  let total = 0;
  for (let i = 0; i < digits.length; i++) total += Number(digits[i]) * ((i % 10) + 1);
  return total % 11;
}

/** The move check word's value over the words between the count and the check word
 * (specification/protocol.md#the-move-check-word). */
export function moveCheck(bodyWords: { item: { criticalCode: number } | null }[],
  lang: Language): number {
  const p = lang.modulus;
  let total = 0;
  bodyWords.forEach((w, k) => {
    const code = w.item !== null ? w.item.criticalCode : 0;
    total += code * (((k + 1) % (p - 1)) + 1);
  });
  return total % p;
}

/** The unit check word's value over the words between the count of an envelope or a
 * statement and its check word (specification/protocol.md#the-unit-check-word): a fixed
 * rule over fixed codes, so that a reader of any version checks it alike. */
export function unitCheck(bodyWords: { identifier: string; classId: string;
  item: unknown }[], lang: Language): number {
  const rule = lang.protocol["unit check word"];
  const codes: Record<string, number> = rule.codes;
  let total = 0;
  bodyWords.forEach((w, i) => {
    let code = 0;
    if (w.item !== null) code = codes[w.identifier] ?? codes[w.classId] ?? 0;
    total += code * ((i % 10) + 1);
  });
  return total % rule.modulus;
}

/** What makes a statement ill-formed, or an empty string: each channel named once by its
 * recipients in ascending order, entries asked for once; in an acknowledgement, the
 * serials beyond the first ascending and each above the serial after the first, which is
 * the first missing; elsewhere every serial and entry ascending from one. */
export function statementForm(statement: Statement): string {
  // their readers check their order (`Parser.understood`, `Parser.lacked`)
  if (statement.kind === "understands" || statement.kind === "lacks") return "";
  const seen = new Set<string>();
  const ascending = (xs: bigint[]) => xs.every((x, i) => i === 0 || xs[i - 1] < x);
  for (const part of statement.parts) {
    if (part[0] === "channel") {
      const [, recipients, serials] = part;
      const key = recipients.join(" ");
      if (!ascending(recipients) || seen.has(key)) {
        return "a channel's recipients out of order, repeated or named twice";
      }
      seen.add(key);
      if (statement.kind === "holds") {
        const beyond = serials.slice(1);
        if (!ascending(beyond) || beyond.some((x) => x <= serials[0] + 1n)) {
          return "serials held beyond the first missing out of order";
        }
      } else if (!ascending(serials) || serials[0] < 1n) {
        return "serials asked for out of order or below one";
      }
    } else {
      const numbers = part[1] as bigint[];
      if (seen.has("entries") || !ascending(numbers) || numbers[0] < 1n) {
        return "entries asked for out of order, below one or twice";
      }
      seen.add("entries");
    }
  }
  return "";
}

function spanOf(words: Word[]): Span | null {
  if (!words.length) return null;
  const a = words[0].span;
  const b = words[words.length - 1].span;
  return new Span(a.encoding, a.start, b.end, a.line, a.column);
}

function isDigits(s: string): boolean {
  return /^[0-9]+$/.test(s);
}

export class Parser {
  words: Word[];
  lang: Language;
  pos = 0;
  end: number;
  names = new Set<number>();
  nameRefs: Same[] = [];
  depth = 0;
  maxima: Record<string, number | undefined>;
  queued: Value[] = []; // the force values an act word stands for, unread
  namedDialects: [NumberNode, NumberNode, NumberNode][] = [];

  constructor(words: Word[], lang: Language) {
    this.words = words;
    this.lang = lang;
    this.end = words.length;
    this.maxima = lang.protocol.maxima ?? {};
  }

  // ------------------------------------------------------------ primitives
  peek(k = 0): Word | null {
    const i = this.pos + k;
    return i < this.end ? this.words[i] : null;
  }

  ident(k = 0): string {
    const w = this.peek(k);
    return w !== null ? w.identifier : "";
  }

  cls(k = 0): string {
    const w = this.peek(k);
    return w !== null && w.item !== null ? w.classId : "";
  }

  take(): Word {
    const w = this.peek();
    if (w === null) {
      const last = this.end ? this.words[this.end - 1] : null;
      throw new Reject(new Diagnostic("d.parser.end-of-input", last !== null ? last.span : null,
        { expected: ["more words"] }));
    }
    this.pos += 1;
    return w;
  }

  fail(code: string, expected: string[], word: Word | null = null, note = ""): never {
    const w = word !== null ? word : this.peek();
    throw new Reject(new Diagnostic(code, w !== null ? w.span : null, {
      expected: [...expected], detected: w !== null ? [w.form] : [], note,
    }));
  }

  expect(identifier: string): Word {
    if (this.ident() !== identifier) this.fail("d.parser.unexpected-word", [identifier]);
    return this.take();
  }

  value(): Value {
    const w = this.take();
    return new Value(w.identifier, w);
  }

  protocolWidth(key: string): number {
    return this.lang.protocol[key];
  }

  // ------------------------------------------------------------ numbers
  number(width: number | null = null, integer = false): NumberNode {
    const words: Word[] = [];
    const names: string[] = [];
    while (this.cls() === NUMERAL) {
      const w = this.take();
      words.push(w);
      names.push((w.item as { name: string }).name);
    }
    if (!names.length) this.fail("d.parser.unexpected-word", ["a numeral"]);
    if (this.cls() !== CHECK) this.fail("d.parser.unexpected-word", ["a number's check word"]);
    const cw = this.take();
    words.push(cw);
    const checkName = (cw.item as { name: string }).name.split(/\s+/);
    const check = Number(checkName[checkName.length - 1]);
    const num = new NumberNode(names, check, words);
    this.numberForm(num, integer, width);
    if (width !== null && (num.numerals.length !== width || num.text !== num.digits)) {
      throw new Reject(new Diagnostic("d.parser.width", spanOf(words),
        { expected: [width + " digits"], detected: [num.text] }));
    }
    if (numberCheck(num.digits) !== check) {
      throw new Reject(new Diagnostic("d.parser.number-check-mismatch", spanOf(words), {
        expected: ["check " + numberCheck(num.digits)], detected: ["check " + check],
      }));
    }
    return num;
  }

  /** A number is [-]digits[.digits][e[-]digits], optionally a ratio or an interval of
   * two; no whole part has a leading zero except at a fixed width. */
  numberForm(num: NumberNode, integer: boolean, width: number | null): void {
    const text = num.text;
    const pieces = splitAny(text, "/~");
    let ok = pieces.length <= 2 && pieces.every(decimalOk);
    if (integer) ok = ok && isDigits(text);
    if (ok && width === null) {
      for (const piece of pieces) {
        const whole = piece.replace(/^-+/, "").split(".")[0].split("e")[0];
        if (whole.length > 1 && whole.startsWith("0")) ok = false;
      }
    }
    if (!ok) {
      throw new Reject(new Diagnostic("d.parser.number-form", spanOf(num.words),
        { expected: ["a well-formed number"], detected: [text] }));
    }
  }

  // ------------------------------------------------------------ message
  envelope(): Envelope {
    const start = this.pos;
    // the envelope is a counted unit with its own check word (protocol 0.3)
    const [fields] = this.counted(() => this.envelopeBody());
    const [sender, recipients, time, version, identifier, firstEntry, forwarded, semantic] =
      fields;
    let integrity: NumberNode | null = null;
    let integrityWords: Word[] = [];
    let authentication: Authentication | null = null;
    if (this.ident() === FIELD + "authentication") authentication = this.authentication();
    if (this.ident() === FIELD + "integrity-check-value") {
      const iw = this.take();
      integrity = this.number(this.protocolWidth("check value width"), true);
      integrityWords = [iw, ...integrity.words];
    }
    if (this.cls() === "g.message.message-field") {
      this.fail("d.parser.envelope", ["a move"], null, "a field repeated or out of order");
    }
    const env = new Envelope(sender, recipients, time, version, identifier, firstEntry,
      forwarded, semantic, integrity, this.words.slice(start, this.pos), integrityWords,
      authentication, this.namedDialects);
    if (env.isProtocol && (firstEntry.integer() !== 0n || recipients.length !== 1 ||
      forwarded !== null)) {
      throw new Reject(new Diagnostic("d.parser.protocol-message", spanOf(identifier.words), {
        expected: ["first entry zero, one recipient, not forwarded"],
        note: "a message whose identifier is zero is a protocol message",
      }));
    }
    return env;
  }

  /** A counted unit, an envelope or a statement (protocol 0.3): WORD-COUNT, its count,
   * what `read` reads within the count, and a check word computed by the unit check
   * word's rule. Returns what `read` returned, with the count and the check word. */
  counted<T>(read: () => T): [T, NumberNode, Word] {
    this.expect("g.message.word-count.word-count");
    const count = this.number(null, true);
    const n = Number(count.integer());
    const bodyStart = this.pos;
    if (n < 2 || bodyStart + n > this.end) {
      throw new Reject(new Diagnostic("d.parser.count-mismatch", spanOf(count.words), {
        expected: [n + " words"], detected: [(this.end - bodyStart) + " words"],
      }));
    }
    const checkWord = this.words[bodyStart + n - 1];
    if (checkWord.item === null || checkWord.classId !== CHECK) {
      throw new Reject(new Diagnostic("d.parser.count-mismatch", checkWord.span, {
        expected: ["a check word as word " + n], detected: [checkWord.form],
      }));
    }
    const end = this.end;
    this.end = bodyStart + n - 1;
    let result: T;
    try {
      result = read();
    } finally {
      this.end = end;
    }
    const computed = unitCheck(this.words.slice(bodyStart, bodyStart + n - 1), this.lang);
    const checkName = (checkWord.item as { name: string }).name.split(/\s+/);
    const stated = Number(checkName[checkName.length - 1]);
    if (stated !== computed) {
      throw new Reject(new Diagnostic("d.parser.unit-check-mismatch", checkWord.span, {
        expected: ["check " + computed], detected: ["check " + stated],
      }));
    }
    this.pos = bodyStart + n;
    return [result, count, checkWord];
  }

  envelopeBody(): ReturnType<Parser["envelopeFields"]> {
    const fields = this.envelopeFields();
    if (this.pos < this.end) {
      this.fail("d.parser.envelope", ["the envelope's check word"], null,
        "a field repeated or out of order");
    }
    return fields;
  }

  /** The fields inside the envelope's count, from the sender to the semantic check
   * value. */
  envelopeFields(): [NumberNode, NumberNode[], NumberNode, NumberNode[], NumberNode,
    NumberNode, Value | null, NumberNode | null] {
    this.field("sender");
    const sender = this.number(null, true);
    this.field("recipients");
    const recipients = [this.number(null, true)];
    while (this.cls() === NUMERAL) recipients.push(this.number(null, true));
    this.field("communication-time");
    const time = this.number();
    this.field("version");
    const version = [this.versionNumber(), this.versionNumber(), this.versionNumber()];
    this.namedDialects = this.dialects();
    this.field("identifier");
    const identifier = this.number(this.protocolWidth("identifier width"), true);
    this.field("first-entry");
    const firstEntry = this.number(null, true);
    if (firstEntry.integer() < 1n && identifier.integer() !== 0n) {
      throw new Reject(new Diagnostic("d.parser.number-form", spanOf(firstEntry.words),
        { expected: ["an entry number from 1"], detected: [firstEntry.text] }));
    }
    let forwarded: Value | null = null;
    if (this.ident() === "g.message.forwarded.forwarded") forwarded = this.value();
    let semantic: NumberNode | null = null;
    if (this.ident() === FIELD + "semantic-check-value") {
      this.take();
      semantic = this.number(this.protocolWidth("check value width"), true);
    }
    return [sender, recipients, time, version, identifier, firstEntry, forwarded, semantic];
  }

  /** A version: two integers with the decimal point between them, neither with a leading
   * zero (specification/protocol.md#versions-and-features). */
  versionNumber(): NumberNode {
    const v = this.number();
    if (!wellFormed(v.text)) {
      throw new Reject(new Diagnostic("d.parser.number-form", spanOf(v.words),
        { expected: ["major . minor"], detected: [v.text] }));
    }
    return v;
  }

  /** `DIALECT number version digest`: a dialect by its number, its version and the digest
   * of its release (language 0.10). */
  dialectNamed(): [NumberNode, NumberNode, NumberNode] {
    this.expect(DIALECT);
    const number = this.number(null, true);
    const version = this.versionNumber();
    const digest = this.number(this.protocolWidth("check value width"), true);
    return [number, version, digest];
  }

  /** The dialects a version field or a statement names, in ascending order of number and
   * then of version, none twice. */
  dialects(code = "d.parser.envelope"): [NumberNode, NumberNode, NumberNode][] {
    const out: [NumberNode, NumberNode, NumberNode][] = [];
    while (this.ident() === DIALECT) out.push(this.dialectNamed());
    for (let i = 1; i < out.length; i++) {
      const [a, b] = [out[i - 1], out[i]];
      const order = a[0].integer() !== b[0].integer() ? (a[0].integer() < b[0].integer() ? -1 : 1)
        : compareVersions(a[1].text, b[1].text);
      if (order >= 0) {
        throw new Reject(new Diagnostic(code, spanOf(out[0][0].words), {
          expected: ["dialects in ascending order, none twice"],
          detected: out.map(([n, v]) => n.integer() + " " + v.text) }));
      }
    }
    return out;
  }

  /** `AUTHENTICATION number number payload`: the scheme, the signature's length in bytes
   * and the signature (protocol 0.3). */
  authentication(): Authentication {
    const start = this.pos;
    this.take();
    const scheme = this.number(null, true);
    const length = this.number(null, true);
    const w = this.peek();
    if (w === null || w.kind !== "payload") {
      this.fail("d.parser.authentication-form", ["a signature"]);
    }
    this.take();
    const schemes = this.lang.protocol["authentication schemes"] ?? {};
    const known = schemes[String(scheme.integer())];
    const payload = (w as Word).payload;
    if (known === undefined || BigInt(known["signature bytes"]) !== length.integer() ||
      BigInt(payload.length) !== length.integer()) {
      throw new Reject(new Diagnostic("d.parser.authentication-form",
        spanOf(this.words.slice(start, this.pos)), {
          expected: ["a known scheme and a signature of its length"],
          detected: ["scheme " + scheme.text + ", " + payload.length + " bytes"],
        }));
    }
    return new Authentication(scheme, length, payload, this.words.slice(start, this.pos));
  }

  // ------------------------------------------------------------ protocol statement
  /** The statement of a protocol message (specification/protocol.md#protocol-messages):
   * its count, what it states, its parts and its check word, every word a fixed form. */
  statement(): Statement {
    const start = this.pos;
    const [[kind, parts], count, checkWord] = this.counted(() => this.statementBody());
    const statement = new Statement(kind, parts, count, checkWord,
      this.words.slice(start, this.pos));
    const failure = statementForm(statement);
    if (failure) {
      throw new Reject(new Diagnostic("d.parser.statement-form", spanOf(statement.words),
        { note: failure }));
    }
    return statement;
  }

  statementBody(): [string, StatementPart[]] {
    if (this.cls() !== "g.protocol.protocol-statement") {
      this.fail("d.parser.unexpected-word", ["g.protocol.protocol-statement"]);
    }
    const kind = ((this.take().item as { name: string }).name).replace(/ /g, "-");
    if (kind === "understands") return [kind, this.understood()];
    if (kind === "lacks") return [kind, this.lacked()];
    const parts: StatementPart[] = [];
    while (this.pos < this.end) parts.push(this.statementPart(kind));
    if (!parts.length) this.fail("d.parser.end-of-input", ["a channel or entries"]);
    return [kind, parts];
  }

  /** A statement part of versions: its word and the versions that follow it, one or
   * several in ascending order. */
  versionsPart(ident: string, one = false): StatementPart {
    this.expect(ident);
    const found = [this.versionNumber()];
    while (!one && this.cls() === NUMERAL) found.push(this.versionNumber());
    const texts = found.map((v) => v.text);
    const sorted = ordered(new Set(texts));
    if (texts.length !== sorted.length || texts.some((t, i) => t !== sorted[i])) {
      throw new Reject(new Diagnostic("d.parser.statement-form", spanOf(found[0].words),
        { note: "versions out of order or repeated" }));
    }
    return [VERSION_PARTS.get(ident) as "language", texts];
  }

  dialectParts(): StatementPart[] {
    return this.dialects("d.parser.statement-form").map(([n, v, d]) =>
      ["dialect", n.integer(), v.text, d.text] as StatementPart);
  }

  lackingPart(): StatementPart {
    const word = this.expect(PART + "lacking-features");
    const found = [this.number(null, true)];
    while (this.cls() === NUMERAL) found.push(this.number(null, true));
    const numbers = found.map((n) => n.integer());
    if (numbers.some((x, i) => i > 0 && numbers[i - 1] >= x) || numbers[0] < 1n) {
      throw new Reject(new Diagnostic("d.parser.statement-form",
        spanOf([word, ...found[found.length - 1].words]),
        { note: "features out of order, repeated or below one" }));
    }
    return ["lacking", numbers];
  }

  /** What `UNDERSTANDS` states (protocol 0.4): the language, lexicon and protocol versions
   * its sender reads, the dialects it holds and the features it lacks. */
  understood(): StatementPart[] {
    const parts = [...VERSION_PARTS.keys()].map((ident) => this.versionsPart(ident));
    parts.push(...this.dialectParts());
    if (this.pos < this.end) parts.push(this.lackingPart());
    if (this.pos < this.end) this.fail("d.parser.unexpected-word", ["the statement's check word"]);
    return parts;
  }

  /** What `LACKS` states (protocol 0.4): a message of the addressee's by its channel and
   * serial, and the versions, dialects and features of it its sender lacks, in the order
   * the production writes them. */
  lacked(): StatementPart[] {
    const start = this.pos;
    const channel = this.statementPart("lacks");
    if (channel[0] !== "channel" || (channel[2] as bigint[]).length !== 1) {
      throw new Reject(new Diagnostic("d.parser.statement-form",
        spanOf(this.words.slice(start, this.pos)),
        { note: "one message, by its channel and one serial" }));
    }
    const parts: StatementPart[] = [channel];
    for (const ident of VERSION_PARTS.keys()) {
      if (this.ident() === ident) parts.push(this.versionsPart(ident, true));
    }
    parts.push(...this.dialectParts());
    if (this.ident() === PART + "lacking-features") parts.push(this.lackingPart());
    if (this.pos < this.end) this.fail("d.parser.unexpected-word", ["the statement's check word"]);
    if (parts.length === 1) this.fail("d.parser.end-of-input", ["what the message lacks"]);
    return parts;
  }

  statementPart(kind: string): StatementPart {
    if (this.ident() === "g.protocol.statement-part.channel") {
      this.take();
      const recipients = [this.number(null, true).integer()];
      while (this.cls() === NUMERAL) recipients.push(this.number(null, true).integer());
      this.expect("g.protocol.statement-part.serials");
      const serials = [this.number(null, true).integer()];
      while (this.cls() === NUMERAL) serials.push(this.number(null, true).integer());
      return ["channel", recipients, serials];
    }
    if (kind !== "holds" && kind !== "lacks" &&
      this.ident() === "g.protocol.statement-part.entries") {
      this.take();
      const numbers = [this.number(null, true).integer()];
      while (this.cls() === NUMERAL) numbers.push(this.number(null, true).integer());
      return ["entries", numbers];
    }
    return this.fail("d.parser.unexpected-word", ["g.protocol.statement-part.channel"]
      .concat(kind !== "holds" && kind !== "lacks" ? ["g.protocol.statement-part.entries"]
        : []));
  }

  field(name: string): void {
    if (this.ident() !== FIELD + name) this.fail("d.parser.envelope", [FIELD + name]);
    this.take();
  }

  // ------------------------------------------------------------ moves
  // As long as the canonical implementation's `Parser.move`, which it follows statement for
  // statement so that the two can be read side by side.
  move(index: number): Move {
    const start = this.pos;
    this.expect("g.message.word-count.word-count");
    const count = this.number(null, true);
    const n = count.integer();
    const bodyStart = this.pos;
    if (n < 2n || BigInt(bodyStart) + n > BigInt(this.end)) {
      const avail = this.end - bodyStart;
      throw new Reject(new Diagnostic("d.parser.count-mismatch", spanOf(count.words),
        { expected: [n + " words"], detected: [avail + " words"] }));
    }
    const size = Number(n);
    const body = this.words.slice(bodyStart, bodyStart + size);
    const checkWord = body[body.length - 1];
    if (checkWord.item === null || checkWord.item.kind !== "move-check") {
      throw new Reject(new Diagnostic("d.parser.count-mismatch", checkWord.span, {
        expected: ["a move check word as word " + size], detected: [checkWord.form],
      }));
    }
    const computed = moveCheck(body.slice(0, -1), this.lang);
    const stated = this.lang.moveCheckValue.get(checkWord.form) as number;
    if (computed !== stated) {
      throw new Reject(new Diagnostic("d.parser.move-check-mismatch", checkWord.span,
        { expected: ["CHK" + computed], detected: ["CHK" + stated] }));
    }
    const savedEnd = this.end;
    this.end = bodyStart + size - 1;
    this.names = new Set();
    this.nameRefs = [];
    let head: Head;
    const constituents: Constituent[] = [];
    try {
      head = this.head();
      while (this.pos < this.end) constituents.push(this.constituent());
    } finally {
      this.end = savedEnd;
    }
    for (const ref of this.nameRefs) {
      if (!this.names.has(Number(ref.name.integer()))) {
        throw new Reject(new Diagnostic("d.parser.name-undefined", spanOf(ref.words),
          { expected: ["a defined name"], detected: [ref.name.text] }));
      }
    }
    const cycle = nameCycle(constituents);
    if (cycle !== null) {
      throw new Reject(new Diagnostic("d.parser.name-cycle", spanOf(body), {
        expected: ["a rooted acyclic graph"], detected: ["name " + cycle + " reaches itself"],
      }));
    }
    this.pos = bodyStart + size;
    return new Move(index, count, head, constituents, checkWord, body,
      this.words.slice(start, this.pos));
  }

  // As long as the canonical implementation's `Parser.head`, which it follows statement
  // for statement so that the two can be read side by side. An act word stands for the
  // force values its entry expands to, read in their place and spanning the act word
  // (specification/lexicon.md#act-words).
  head(): Head {
    const h = new Head();
    const w = this.peek();
    if (w !== null && w.item !== null && w.item.kind === "act") {
      h.act = this.take();
      const act = h.act;
      this.queued = (this.lang.entries.get(act.identifier).expansion as string[]).map(
        (m) => new Value(m, act));
    }
    let left: Value[];
    try {
      this.force(h);
    } finally {
      left = this.queued;
      this.queued = [];
    }
    if (left.length) this.fail("d.parser.unexpected-word", [left[0].classId], h.act);
    if (this.cls() === "g.force.authority-claimed") {
      h.authority = this.value();
      if (h.authority.name !== "speakers-own") {
        if (this.ident() !== "g.structure.term") {
          this.fail("d.parser.unexpected-word", ["g.structure.term"]);
        }
        h.authorityTerm = this.unit();
      }
    }
    if (this.ident() === "g.time.time-index.deadline") {
      this.take();
      h.deadline = this.timeSpec();
    }
    if (this.cls() === "g.reference.kind-of-reference") {
      h.named = this.reference();
      // a summary names every entry it summarises
      // (specification/discourse.md#summaries-and-confirmations); whether a further
      // reference is admitted is the checker's to say
      while (this.cls() === "g.reference.kind-of-reference") h.alsoNamed.push(this.reference());
    }
    for (;;) {
      const r = this.peek();
      if (r === null || r.item === null || r.item.category !== "discourse relation") break;
      h.relations.push(new ContentWord(this.take()));
    }
    let w2 = this.peek();
    if (w2 !== null && w2.item !== null && w2.item.category === "politeness word") {
      h.politeness = this.take();
    }
    w2 = this.peek();
    if (w2 !== null && w2.item !== null && w2.item.category === "diction") {
      h.diction = this.take();
    }
    while (this.cls() === LOSS) h.losses.push(this.value());
    if (this.cls() === REGISTER) h.register = this.value();
    if (this.ident() === "g.ambiguity-and-figures.precision-bound-declaration.precision-bound") {
      h.precisionBound = this.value();
    }
    return h;
  }

  hcls(): string {
    return this.queued.length ? this.queued[0].classId : this.cls();
  }

  hvalue(): Value {
    return this.queued.length ? this.queued.shift() as Value : this.value();
  }

  /** The force values, from what the move adds to when its change takes effect. */
  force(h: Head): void {
    if (this.hcls() !== "g.force.what-the-move-adds") {
      this.fail("d.parser.unexpected-word", ["g.force.what-the-move-adds"]);
    }
    const adds = this.hvalue();
    h.adds.push(adds);
    const sub = SUBCLASS.get(adds.name);
    for (const c of sub !== undefined ? [sub] : []) {
      if (this.hcls() !== c) this.fail("d.parser.unexpected-word", [c]);
      h.adds.push(this.hvalue());
    }
    if (adds.name === "normative-entry" && h.adds[h.adds.length - 1].name !== "recommendation") {
      if (this.hcls() !== "g.force.bindingness") {
        this.fail("d.parser.unexpected-word", ["g.force.bindingness"]);
      }
      h.adds.push(this.hvalue());
    }
    if (this.hcls() === "g.force.change-made") {
      const change = this.hvalue();
      h.change.push(change);
      if (change.name === "resolution") {
        if (this.hcls() !== "g.force.outcome-of-a-resolution") {
          this.fail("d.parser.unexpected-word", ["g.force.outcome-of-a-resolution"]);
        }
        h.change.push(this.hvalue());
      }
      if (change.name !== "none") {
        for (const c of ["g.force.extent", "g.force.when-the-change-takes-effect"]) {
          if (this.hcls() !== c) this.fail("d.parser.unexpected-word", [c]);
          h.change.push(this.hvalue());
        }
      }
    }
  }

  /** An extragrammatical idiom whose words begin here, the longest the release lists, or
   * null. Its first word is a content word where a constituent stands, which no
   * production admits, so that it is recognised by form and never ambiguous
   * (specification/lexicon.md#conventional-expressions-and-idioms). */
  idiom(): Idiom | null {
    let best: [string[], string] | null = null;
    for (const [key, entry] of this.lang.extragrammatical) {
      const words = key.split(",");
      const n = words.length;
      if (this.pos + n <= this.end && words.every((w, k) => this.ident(k) === w) &&
        (best === null || n > best[0].length)) {
        best = [words, entry];
      }
    }
    if (best === null) return null;
    const taken: Word[] = [];
    for (let i = 0; i < best[0].length; i++) taken.push(this.take());
    return new Idiom(best[1], taken);
  }

  // ------------------------------------------------------------ constituents
  constituent(): Constituent {
    const ident = this.ident();
    const found = this.idiom();
    if (found !== null) return found;
    if (UNIT_OPEN.has(ident)) return this.unit();
    if (ident === "g.structure.wall") return this.wall();
    if (ident === "g.structure.readings") return this.readings();
    if (ident === "g.structure.same") return this.same();
    return this.fail("d.parser.unexpected-word", ["a unit", "a wall", "a set of readings",
      "g.structure.same"]);
  }

  filler(): Constituent {
    const ident = this.ident();
    if (this.cls() === "g.reference.kind-of-reference") return this.reference();
    return ident ? this.constituent() : this.fail("d.parser.end-of-input", ["a constituent"]);
  }

  same(): Same {
    const w = this.take();
    const name = this.number(this.protocolWidth("name width"), true);
    const s = new Same(name, [w, ...name.words]);
    this.nameRefs.push(s);
    return s;
  }

  unit(): Unit {
    const openWord = this.take();
    const [kind, closer] = UNIT_OPEN.get(openWord.identifier) as [string, string];
    this.depth += 1;
    try {
      const limit = this.maxima["nesting"];
      if (limit !== undefined && this.depth > limit) {
        // rejected where the depth is reached, before the rest is read
        throw new Reject(new Diagnostic("d.parser.maximum", openWord.span, {
          expected: ["nesting at most " + limit], detected: ["nesting " + this.depth],
        }));
      }
      return this.unitBody(openWord, kind, closer);
    } finally {
      this.depth -= 1;
    }
  }

  unitBody(openWord: Word, kind: string, closer: string): Unit {
    let name: NumberNode | null = null;
    if (this.ident() === "g.structure.name") {
      this.take();
      name = this.number(this.protocolWidth("name width"), true);
      const value = Number(name.integer());
      if (this.names.has(value)) {
        throw new Reject(new Diagnostic("d.parser.name-repeated", spanOf(name.words),
          { detected: [name.text] }));
      }
      this.names.add(value);
    }
    const parts: Part[] = [];
    for (;;) {
      const w = this.peek();
      if (w === null) {
        throw new Reject(new Diagnostic("d.parser.unclosed-unit", openWord.span,
          { expected: [closer] }));
      }
      if (w.identifier === closer) {
        const close = this.take();
        return new Unit(kind, name, parts, openWord, close);
      }
      parts.push(this.unitPart(kind));
    }
  }

  unitPart(kind: string): Part {
    if (kind === "assertion") {
      const found = this.idiom();
      if (found !== null) return found;
    }
    const w = this.peek() as Word;
    const ident = w.identifier;
    const c = this.cls();
    if (w.item === null) {
      this.take();
      return new ContentWord(w); // a formation or an unknown word, kept opaque
    }
    const k = w.item.kind;
    if (k === "dialect") {
      this.take();
      return new ContentWord(w); // a compressed form of a named dialect
    }
    if (k === "root" || k === "derivation") {
      this.take();
      return new ContentWord(w);
    }
    if (k === "structural") {
      if (UNIT_OPEN.has(ident) || ident === "g.structure.wall" ||
        ident === "g.structure.readings" || ident === "g.structure.same") {
        return this.constituent();
      }
      if (ident === "g.structure.party") {
        this.take();
        return new Party(this.number(null, true));
      }
      if (ident === DIALECT) {
        this.take();
        return new DialectName(this.number(null, true));
      }
      this.fail("d.parser.unexpected-word", ["a part of a " + kind]);
    }
    if (k !== "member") this.fail("d.parser.unexpected-word", ["a part of a " + kind]);
    if (FILLER_ROLES.has(c) || ident === CONDITION) {
      const role = this.value();
      return new Filler(role, this.filler());
    }
    if (c === "g.time.time-index") {
      const index = this.value();
      return new TimeValue(index, this.timeSpec(index));
    }
    if (c === "g.reference.kind-of-reference") return this.reference();
    if (c === "g.situations-and-contents.comparator" || c === NUMERAL) return this.quantity(kind);
    return this.value();
  }

  quantity(kind = "term"): Quantity {
    const comparator = this.cls() === "g.situations-and-contents.comparator" ? this.value() :
      null;
    const num = this.number();
    let unit: Value | ContentWord | null = null;
    let per: Value | null = null;
    const w = this.peek();
    if (this.cls() === "g.time.time-unit") {
      unit = this.value();
    } else if (w !== null && w.item !== null && w.item.category === "unit of measure") {
      unit = new ContentWord(this.take());
    }
    if (this.ident() === "g.time.time-anchor.per") {
      this.take();
      if (this.cls() !== "g.time.time-unit") this.fail("d.parser.unexpected-word",
        ["g.time.time-unit"]);
      per = this.value();
    }
    let calibration: NumberNode | null = null;
    if (kind !== "term" && unit === null && per === null && this.ident() === "g.structure.party") {
      // a numeric strength's calibration, the participant whose numbers it is in
      // (specification/discourse.md#summaries-and-confirmations); in a term PARTY is a
      // part of its own
      this.take();
      calibration = this.number(null, true);
    }
    return new Quantity(comparator, num, unit, per, calibration);
  }

  reference(): Reference {
    const start = this.pos;
    const kind = this.value().name;
    let ref: Reference;
    if (this.ident() === "g.structure.message-target") {
      this.take();
      const author = this.number(null, true);
      const num = this.number(null, true);
      ref = new Reference(kind, "message", author, num);
    } else if (this.ident() === "g.structure.message-serial") {
      // a message by its sender, its serial and its channel's recipients, which names a
      // message its speaker does not hold
      // (specification/discourse.md#naming-entries-and-messages)
      this.take();
      const author = this.number(null, true);
      const num = this.number(this.protocolWidth("identifier width"), true);
      ref = new Reference(kind, "serial", author, num);
      ref.recipients = [this.number(null, true)];
      while (this.cls() === NUMERAL) ref.recipients.push(this.number(null, true));
    } else {
      const author = this.number(null, true);
      const num = this.number(null, true);
      ref = new Reference(kind, "entry", author, num);
      if (kind === "names") {
        ref.expected = this.expectedKind();
        if (this.cls() !== "g.reference.expected-status-of-an-entry") {
          this.fail("d.parser.unexpected-word", ["g.reference.expected-status-of-an-entry"]);
        }
        ref.status = this.value();
      }
    }
    if (this.ident() === "g.structure.part") {
      this.take();
      ref.part = this.number(this.protocolWidth("name width"), true);
    }
    ref.words = this.words.slice(start, this.pos);
    return ref;
  }

  expectedKind(): Value[] {
    if (this.cls() !== "g.force.what-the-move-adds") {
      this.fail("d.parser.unexpected-word", ["g.force.what-the-move-adds"]);
    }
    const out = [this.value()];
    const sub = SUBCLASS.get(out[0].name);
    if (sub !== undefined) {
      if (this.cls() !== sub) this.fail("d.parser.unexpected-word", [sub]);
      out.push(this.value());
    }
    return out;
  }

  /** A time (specification/notation.md#times): a point, an interval, a duration or a
   * rate, as the index it describes admits. */
  timeSpec(index: Value | null = null): TimeSpec {
    const name = index !== null ? index.name : null;
    if (name !== null && MEASURED_TIMES.has(name) && this.cls() === COMPARATOR) {
      const comparator = this.value();
      return this.simpleTime(name, comparator);
    }
    const spec = this.point(name);
    if (spec.kind === "duration" || spec.kind === "rate") return spec;
    if (name === "validity-interval") {
      return new TimeSpec("interval", { reference: spec, until: this.point() });
    }
    if (name !== null && SPANNING_TIMES.has(name) && this.ident() === UNTIL) {
      this.take();
      return new TimeSpec("interval", { reference: spec, until: this.point() });
    }
    return spec;
  }

  point(name: string | null = null): TimeSpec {
    if (this.ident() === "g.time.time-anchor.now") {
      this.take();
      return new TimeSpec("now");
    }
    if (this.cls() === "g.time.time-relation") {
      const relation = this.value();
      return new TimeSpec("relation", { relation, reference: this.timeReference() });
    }
    if (this.cls() === NUMERAL) return this.simpleTime(name);
    return this.fail("d.parser.unexpected-word", ["a time"]);
  }

  timeReference(): TimeSpec | Value | IndexOf {
    if (this.cls() === "g.time.time-index") return this.value();
    if (this.ident() === "g.structure.same") {
      const same = this.same();
      if (this.cls() !== "g.time.time-index") {
        this.fail("d.parser.unexpected-word", ["g.time.time-index"]);
      }
      return new IndexOf(same, this.value());
    }
    return this.simpleTime();
  }

  /** A clock value; after a measured index, also a duration or a rate. */
  simpleTime(name: string | null = null, comparator: Value | null = null): TimeSpec {
    if (comparator === null && this.ident() === "g.time.time-anchor.now") {
      this.take();
      return new TimeSpec("now");
    }
    const num = this.number();
    if (name === "event-time" && this.ident() === "g.time.time-anchor.per") {
      this.take();
      if (this.cls() !== "g.time.time-unit") this.fail("d.parser.unexpected-word", ["g.time.time-unit"]);
      return new TimeSpec("rate", { number: num, unit: this.value(), comparator });
    }
    if (this.cls() === "g.time.time-unit") {
      const unit = this.value();
      if (comparator === null && (this.ident() === "g.time.time-anchor.ago" ||
          this.ident() === "g.time.time-anchor.hence")) {
        return new TimeSpec("offset", { number: num, unit, anchor: this.value() });
      }
      if (name !== null && MEASURED_TIMES.has(name)) {
        return new TimeSpec("duration", { number: num, unit, comparator });
      }
      this.fail("d.parser.unexpected-word", ["g.time.time-anchor.ago",
        "g.time.time-anchor.hence"]);
    }
    if (comparator !== null) this.fail("d.parser.unexpected-word", ["g.time.time-unit"]);
    return new TimeSpec("absolute", { number: num });
  }

  wall(): Wall {
    this.take();
    if (this.cls() !== "g.message.embedded-material") {
      this.fail("d.parser.unexpected-word", ["g.message.embedded-material"]);
    }
    const kind = this.value();
    if (kind.name === "declared-data") {
      const w = new Wall(kind);
      w.typeLength = this.number(null, true);
      w.typePayload = this.payload();
      w.length = this.number(null, true);
      w.payload = this.payload();
      for (const [num, pay] of [[w.typeLength, w.typePayload], [w.length, w.payload]] as
        [NumberNode, Word][]) {
        if (BigInt(pay.payload.length) !== num.integer()) {
          throw new Reject(new Diagnostic("d.lexer.payload-short", pay.span, {
            expected: [num.integer() + " bytes"], detected: [pay.payload.length + " bytes"],
          }));
        }
      }
      let declared = "";
      for (const byte of w.typePayload.payload) declared += String.fromCharCode(byte);
      if (!MEDIA_TYPE.test(declared)) {
        throw new Reject(new Diagnostic("d.parser.media-type", w.typePayload.span, {
          expected: ["a media type (RFC 6838 § 4.2)"], detected: [w.typePayload.form],
        }));
      }
      this.expect("g.structure.end-wall");
      return w;
    }
    const w = new Wall(kind);
    while (this.ident() !== "g.structure.end-wall") {
      if (this.peek() === null) {
        throw new Reject(new Diagnostic("d.parser.unclosed-unit", kind.word.span,
          { expected: ["g.structure.end-wall"] }));
      }
      w.words.push(this.take());
    }
    this.take();
    return w;
  }

  payload(): Word {
    const w = this.peek();
    if (w === null || w.kind !== "payload") this.fail("d.parser.unexpected-word", ["a payload"]);
    return this.take();
  }

  readings(): ReadingSet {
    this.take();
    if (this.cls() !== "g.ambiguity-and-figures.kind-of-ambiguity") {
      this.fail("d.parser.unexpected-word", ["g.ambiguity-and-figures.kind-of-ambiguity"]);
    }
    const kind = this.value();
    const readings: Constituent[] = [];
    const limit = this.maxima["readings"];
    while (this.ident() !== "g.structure.end-readings") {
      if (limit !== undefined && readings.length >= limit) {
        this.fail("d.parser.maximum", ["at most " + limit + " readings"]);
      }
      if (this.peek() === null) {
        throw new Reject(new Diagnostic("d.parser.unclosed-unit", kind.word.span,
          { expected: ["g.structure.end-readings"] }));
      }
      readings.push(this.filler());
    }
    this.take();
    return new ReadingSet(kind, readings);
  }
}

/** A name whose unit reaches itself through the units and SAMEs inside it, or null
 * (the structure is a rooted directed acyclic graph). */
function nameCycle(constituents: Constituent[]): number | null {
  const reaches = new Map<number, Set<number>>();
  const collect = (node: unknown, out: Set<number>): void => {
    if (node instanceof Unit) {
      if (node.name !== null) {
        out.add(Number(node.name.integer()));
        return;
      }
      for (const p of node.parts) collect(p, out);
    } else if (node instanceof Same) {
      out.add(Number(node.name.integer()));
    } else if (node instanceof TimeValue) {
      // a time reference is an edge of the graph (specification/notation.md#times)
      for (const same of specSames(node.spec)) out.add(Number(same.name.integer()));
    } else if (node instanceof Filler) {
      collect(node.filler, out);
    } else if (node instanceof ReadingSet) {
      for (const r of node.readings) collect(r, out);
    }
  };
  const named = (node: unknown): void => {
    if (node instanceof Unit) {
      if (node.name !== null) {
        const inner = new Set<number>();
        for (const p of node.parts) collect(p, inner);
        reaches.set(Number(node.name.integer()), inner);
      }
      for (const p of node.parts) named(p);
    } else if (node instanceof Filler) {
      named(node.filler);
    } else if (node instanceof ReadingSet) {
      for (const r of node.readings) named(r);
    }
  };
  for (const c of constituents) named(c);
  const state = new Map<number, number>();
  const visit = (n: number): number | null => {
    state.set(n, 1);
    for (const m of reaches.get(n) ?? []) {
      if (state.get(m) === 1) return m;
      if (!state.has(m)) {
        const found = visit(m);
        if (found !== null) return found;
      }
    }
    state.set(n, 2);
    return null;
  };
  for (const n of [...reaches.keys()].sort((a, b) => a - b)) {
    if (!state.has(n)) {
      const found = visit(n);
      if (found !== null) return found;
    }
  }
  return null;
}

function splitAny(text: string, seps: string): string[] {
  const out: string[] = [];
  let cur = "";
  for (const ch of text) {
    if (seps.includes(ch)) {
      out.push(cur);
      cur = "";
    } else {
      cur += ch;
    }
  }
  out.push(cur);
  return out;
}

/** [-]digits[.digits][e[-]digits] */
function decimalOk(piece: string): boolean {
  let mant: string;
  const e = piece.indexOf("e");
  if (e >= 0) {
    mant = piece.slice(0, e);
    let exp = piece.slice(e + 1);
    exp = exp.startsWith("-") ? exp.slice(1) : exp;
    if (!isDigits(exp)) return false;
  } else {
    mant = piece;
  }
  mant = mant.startsWith("-") ? mant.slice(1) : mant;
  const dot = mant.indexOf(".");
  const whole = dot >= 0 ? mant.slice(0, dot) : mant;
  const frac = dot >= 0 ? mant.slice(dot + 1) : "";
  if (!isDigits(whole)) return false;
  if (dot >= 0 && !isDigits(frac)) return false;
  return true;
}

/** Parse a whole message. A rejected move is reported and parsing resumes after its
 * counted body; a rejection elsewhere ends it. */
/** A protocol message: its envelope and one statement, nothing after it. */
function protocolMessage(p: Parser, env: Envelope, words: Word[]): [Message, Diagnostic[]] {
  const start = p.pos;
  let statement: Statement;
  try {
    statement = p.statement();
    if (p.pos < p.end) p.fail("d.parser.unexpected-word", ["the end of a protocol message"]);
  } catch (r) {
    if (!(r instanceof Reject)) throw r;
    return [new Message(env, [], [words.slice(start)]), [r.diagnostic]];
  }
  return [new Message(env, [], [words.slice(start, p.pos)], statement), []];
}

export function parseWords(words: Word[], lang: Language): [Message | null, Diagnostic[]] {
  const p = new Parser(words, lang);
  const diags: Diagnostic[] = [];
  const limit = p.maxima["message words"];
  if (limit !== undefined && words.length > limit) {
    return [null, [new Diagnostic("d.parser.maximum", words[limit].span, {
      expected: ["at most " + limit + " words"], detected: [words.length + " words"],
    })]];
  }
  let env: Envelope;
  try {
    if (!words.length) {
      throw new Reject(new Diagnostic("d.parser.empty", null, { expected: ["a message"] }));
    }
    env = p.envelope();
  } catch (r) {
    if (r instanceof Reject) return [null, [r.diagnostic]];
    throw r;
  }
  if (env.isProtocol) return protocolMessage(p, env, words);
  const moves: Move[] = [];
  const lines: Word[][] = [];
  let index = 0;
  while (p.pos < p.end) {
    index += 1;
    const start = p.pos;
    try {
      moves.push(p.move(index));
    } catch (r) {
      if (!(r instanceof Reject)) throw r;
      diags.push(r.diagnostic);
      // resume after the counted body when the count can be read; otherwise the rest of
      // the words stand as one line
      p.pos = start;
      p.end = words.length;
      try {
        p.expect("g.message.word-count.word-count");
        const n = p.number(null, true).integer();
        const next = BigInt(p.pos) + n;
        p.pos = next < BigInt(words.length) ? Number(next) : words.length;
      } catch (inner) {
        if (!(inner instanceof Reject)) throw inner;
        lines.push(words.slice(start));
        break;
      }
    }
    lines.push(words.slice(start, p.pos));
  }
  if (!moves.length && !diags.length) {
    diags.push(new Diagnostic("d.parser.end-of-input", spanOf(env.words),
      { expected: ["a move"] }));
  }
  return [new Message(env, moves, lines), diags];
}

/** The SAMEs a time names through its references. */
function specSames(spec: TimeSpec | null): Same[] {
  if (spec === null) return [];
  const out: Same[] = [];
  if (spec.reference instanceof IndexOf) out.push(spec.reference.same);
  else if (spec.reference instanceof TimeSpec) out.push(...specSames(spec.reference));
  out.push(...specSames(spec.until));
  return out;
}
