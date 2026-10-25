// The AST: what was written, the words where they stand, each value at the unit where it
// was written, siblings in the order written and every reference unresolved. Every node
// keeps the words it was read from.

import { type Word } from "./lexer.ts";

export const DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight",
  "nine"];
const NUMERAL_SYMBOL = new Map<string, string>([
  ...DIGITS.map((d, i): [string, string] => [d, String(i)]),
  ["decimal point", "."], ["negative", "-"], ["ratio", "/"], ["exponent", "e"],
  ["interval", "~"],
]);

function symbolOf(numeral: string): string {
  const s = NUMERAL_SYMBOL.get(numeral);
  if (s === undefined) throw new Error("KeyError: " + numeral);
  return s;
}

export class NumberNode {
  numerals: string[]; // member names, from the most significant
  check: number;
  words: Word[];

  constructor(numerals: string[], check: number, words: Word[]) {
    this.numerals = numerals;
    this.check = check;
    this.words = words;
  }

  /** The numerals as a compact string: digits, '.', '-', '/', 'e', '~'. */
  get text(): string {
    return this.numerals.map(symbolOf).join("");
  }

  get digits(): string {
    return this.numerals.filter((n) => DIGITS.includes(n)).map(symbolOf).join("");
  }

  integer(): bigint {
    const digits = this.digits;
    if (!digits) throw new Error("ValueError: a number without digits");
    return BigInt(digits);
  }
}

export class Value {
  member: string; // the member's identifier
  word: Word;

  constructor(member: string, word: Word) {
    this.member = member;
    this.word = word;
  }

  get classId(): string {
    const i = this.member.lastIndexOf(".");
    return i < 0 ? this.member : this.member.slice(0, i);
  }

  get name(): string {
    const i = this.member.lastIndexOf(".");
    if (i < 0) throw new Error("IndexError: a value without a class");
    return this.member.slice(i + 1);
  }
}

export class ContentWord {
  word: Word;

  constructor(word: Word) {
    this.word = word;
  }
}

export class Reference {
  kind: string; // names, mentions
  target: string; // entry, message, serial
  author: NumberNode;
  number: NumberNode;
  expected: Value[] = []; // the kind expected
  status: Value | null = null;
  part: NumberNode | null = null;
  words: Word[] = [];
  // the recipients of the channel a message named by its serial was sent on
  // (specification/discourse.md#naming-entries-and-messages)
  recipients: NumberNode[] = [];

  constructor(kind: string, target: string, author: NumberNode, number: NumberNode) {
    this.kind = kind;
    this.target = target;
    this.author = author;
    this.number = number;
  }
}

export class TimeSpec {
  kind: string; // now, absolute, offset, relation, interval, duration, rate
  number: NumberNode | null;
  unit: Value | null;
  anchor: Value | null;
  relation: Value | null;
  reference: TimeSpec | Value | IndexOf | null; // a TimeSpec, a Value naming a time index, or an IndexOf
  until: TimeSpec | null; // the second TimeSpec of an interval
  comparator: Value | null; // the bound of a duration or a rate

  constructor(kind: string, fields: Partial<Omit<TimeSpec, "kind">> = {}) {
    this.kind = kind;
    this.number = fields.number ?? null;
    this.unit = fields.unit ?? null;
    this.anchor = fields.anchor ?? null;
    this.relation = fields.relation ?? null;
    this.reference = fields.reference ?? null;
    this.until = fields.until ?? null;
    this.comparator = fields.comparator ?? null;
  }
}

/** A time index of a named unit: SAME name time-index (specification/notation.md#times).
 * */
export class IndexOf {
  same: Same;
  index: Value;

  constructor(same: Same, index: Value) {
    this.same = same;
    this.index = index;
  }
}

export class TimeValue {
  index: Value;
  spec: TimeSpec;

  constructor(index: Value, spec: TimeSpec) {
    this.index = index;
    this.spec = spec;
  }
}

export class Quantity {
  comparator: Value | null;
  number: NumberNode;
  unit: Value | ContentWord | null; // a time unit, or a unit root
  per: Value | null;
  calibration: NumberNode | null; // a numeric strength's calibrating participant

  constructor(comparator: Value | null, number: NumberNode, unit: Value | ContentWord | null,
    per: Value | null, calibration: NumberNode | null = null) {
    this.comparator = comparator;
    this.number = number;
    this.unit = unit;
    this.per = per;
    this.calibration = calibration;
  }
}

export class Party {
  number: NumberNode;

  constructor(number: NumberNode) {
    this.number = number;
  }
}

/** `DIALECT number` in a term: the dialect whose number follows (language 0.10). */
export class DialectName {
  number: NumberNode;

  constructor(number: NumberNode) {
    this.number = number;
  }
}

export class Same {
  name: NumberNode;
  words: Word[];

  constructor(name: NumberNode, words: Word[]) {
    this.name = name;
    this.words = words;
  }
}

/** A role, a provenance link, a figure's relation or the condition, with the constituent
 * it marks. */
export class Filler {
  role: Value;
  filler: Constituent;

  constructor(role: Value, filler: Constituent) {
    this.role = role;
    this.filler = filler;
  }
}

export class Unit {
  kind: string; // assertion, situation, term
  name: NumberNode | null;
  parts: Part[];
  openWord: Word;
  closeWord: Word | null;

  constructor(kind: string, name: NumberNode | null, parts: Part[], openWord: Word,
    closeWord: Word | null = null) {
    this.kind = kind;
    this.name = name;
    this.parts = parts;
    this.openWord = openWord;
    this.closeWord = closeWord;
  }
}

export class Wall {
  kind: Value;
  typeLength: NumberNode | null = null;
  typePayload: Word | null = null;
  length: NumberNode | null = null;
  payload: Word | null = null;
  words: Word[] = []; // quoted words

  constructor(kind: Value) {
    this.kind = kind;
  }
}

export class ReadingSet {
  kind: Value;
  readings: Constituent[];

  constructor(kind: Value, readings: Constituent[]) {
    this.kind = kind;
    this.readings = readings;
  }
}

/** What stands in a move, a reading or after a role. */
/** An extragrammatical idiom, recognised by its words where a constituent stands, which
 * no production of the grammar admits
 * (specification/lexicon.md#conventional-expressions-and-idioms). */
export class Idiom {
  entry: string;
  words: Word[];

  constructor(entry: string, words: Word[]) {
    this.entry = entry;
    this.words = words;
  }
}

export type Constituent = Unit | Wall | ReadingSet | Same | Reference | Idiom;
/** What stands in a unit. */
export type Part = Constituent | Value | ContentWord | Filler | TimeValue | Quantity | Party
  | DialectName;

export class Head {
  adds: Value[] = []; // the values of the force classes
  change: Value[] = [];
  authority: Value | null = null;
  authorityTerm: Unit | null = null;
  deadline: TimeSpec | null = null;
  named: Reference | null = null;
  alsoNamed: Reference[] = []; // a summary's further references
  relations: ContentWord[] = [];
  precisionBound: Value | null = null;
  act: Word | null = null; // the act word that wrote the force values, if one did
  losses: Value[] = []; // the values of the declared loss
  // the social and textual component the head states
  // (specification/lexicon.md#registers): the politeness word and the diction, words of
  // the lexicon, and the register
  politeness: Word | null = null;
  diction: Word | null = null;
  register: Value | null = null;
}

export class Move {
  index: number;
  count: NumberNode;
  head: Head;
  constituents: Constituent[];
  check: Word;
  body: Word[]; // the words the count states, the check word last
  words: Word[]; // every word of the move, the count's included

  constructor(index: number, count: NumberNode, head: Head, constituents: Constituent[],
    check: Word, body: Word[], words: Word[]) {
    this.index = index;
    this.count = count;
    this.head = head;
    this.constituents = constituents;
    this.check = check;
    this.body = body;
    this.words = words;
  }
}

/** The authentication field (protocol 0.3, specification/protocol.md#authentication): the
 * scheme it names, and the signature, carried as a payload. */
export class Authentication {
  scheme: NumberNode;
  length: NumberNode;
  signature: Uint8Array;
  words: Word[]; // the field's words, its own word first

  constructor(scheme: NumberNode, length: NumberNode, signature: Uint8Array, words: Word[]) {
    this.scheme = scheme;
    this.length = length;
    this.signature = signature;
    this.words = words;
  }
}

export class Envelope {
  sender: NumberNode;
  recipients: NumberNode[];
  time: NumberNode;
  version: NumberNode[];
  identifier: NumberNode;
  firstEntry: NumberNode; // the number of the entry the first move adds (protocol 0.2)
  forwarded: Value | null;
  semantic: NumberNode | null;
  integrity: NumberNode | null;
  words: Word[];
  integrityWords: Word[];
  authentication: Authentication | null;
  /** Each dialect the message names, (number, version, digest), in ascending order of
   * number (language 0.10, specification/dialects.md#naming-a-dialect-in-a-message). */
  dialects: [NumberNode, NumberNode, NumberNode][];

  constructor(sender: NumberNode, recipients: NumberNode[], time: NumberNode,
    version: NumberNode[], identifier: NumberNode, firstEntry: NumberNode,
    forwarded: Value | null, semantic: NumberNode | null, integrity: NumberNode | null,
    words: Word[], integrityWords: Word[], authentication: Authentication | null = null,
    dialects: [NumberNode, NumberNode, NumberNode][] = []) {
    this.sender = sender;
    this.recipients = recipients;
    this.time = time;
    this.version = version;
    this.identifier = identifier;
    this.firstEntry = firstEntry;
    this.forwarded = forwarded;
    this.semantic = semantic;
    this.integrity = integrity;
    this.words = words;
    this.integrityWords = integrityWords;
    this.authentication = authentication;
    this.dialects = dialects;
  }

  /** Whether the message is a protocol message, which takes no serial on its channel and
   * adds no entry (protocol 0.3). */
  get isProtocol(): boolean {
    return this.identifier.integer() === 0n;
  }
}

/** The statement of a protocol message (specification/protocol.md#protocol-messages):
 * what it states, holds, send-again, not-held, understands or lacks, and its parts, each
 * a channel by its recipients with serials, the addressee's entries by their numbers, a
 * list of versions, a dialect, or features
 * (specification/dialects.md#settling-the-dialects-two-agents-share). */
export type StatementPart = ["channel", bigint[], bigint[]] | ["entries", bigint[]]
  | ["language" | "lexicon" | "protocol", string[]] | ["dialect", bigint, string, string]
  | ["lacking", bigint[]];

export class Statement {
  kind: string;
  parts: StatementPart[];
  count: NumberNode;
  check: Word;
  words: Word[];

  constructor(kind: string, parts: StatementPart[], count: NumberNode, check: Word,
    words: Word[]) {
    this.kind = kind;
    this.parts = parts;
    this.count = count;
    this.check = check;
    this.words = words;
  }
}

export class Message {
  envelope: Envelope;
  moves: Move[];
  // The words of every move as written, rejected moves included, one list a move: what
  // the canonical serialisation, the integrity check value and conversion read; for a
  // protocol message, the words of its statement.
  lines: Word[][];
  statement: Statement | null;

  constructor(envelope: Envelope, moves: Move[], lines: Word[][] = [],
    statement: Statement | null = null) {
    this.envelope = envelope;
    this.moves = moves;
    this.lines = lines;
    this.statement = statement;
  }
}
