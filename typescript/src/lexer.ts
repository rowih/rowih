// The tokenizer, the lexer and the morphological analyzer: text to symbols and
// separators, symbols to words, and content words to their entries by the lexicon's
// uniquely decodable code. Offsets count code points, as the canonical implementation's
// do.

import { type Item, type Language } from "./data.ts";
import { Diagnostic, Span } from "./diagnostics.ts";
import { codePointLabel, codePointLength } from "./pyformat.ts";

const SEPARATORS = " \t\n\r";
const PAYLOAD_CHARS = "abcdefghijklmnopqrstuvwxyz234567";
const LINKER = "i";
const SUFFIX_FIRST = "aeou";

export class Token {
  text: string; // the symbols as letters, or the raw characters of a payload
  raw: string;
  span: Span;
  native: boolean;
  asciiLetters: boolean;

  constructor(text: string, raw: string, span: Span, native: boolean, asciiLetters: boolean) {
    this.text = text;
    this.raw = raw;
    this.span = span;
    this.native = native;
    this.asciiLetters = asciiLetters;
  }
}

/** A morpheme of a content word: an item, or the linker of a compound. */
export type Morpheme = Item | "linker";

export class Word {
  form: string;
  span: Span;
  item: Item | null;
  kind: string; // word, formation, unknown, payload
  morphemes: Morpheme[];
  payload: Uint8Array;

  constructor(form: string, span: Span, item: Item | null, kind = "word",
    morphemes: Morpheme[] = [], payload: Uint8Array = new Uint8Array(0)) {
    this.form = form;
    this.span = span;
    this.item = item;
    this.kind = kind;
    this.morphemes = morphemes;
    this.payload = payload;
  }

  get identifier(): string {
    return this.item !== null ? this.item.identifier : "";
  }

  get classId(): string {
    return this.item !== null ? this.item.classId : "";
  }
}

export function detectEncoding(text: string, lang: Language): string {
  for (const ch of text) if (lang.lettersOf.has(ch)) return "native";
  return "transliteration";
}

// As long as the canonical implementation's `tokenize`, which it follows statement for
// statement so that the two can be read side by side.
/** Split text into tokens at separators. */
export function tokenize(text: string, lang: Language, encoding: string | null = null):
  [Token[], Diagnostic[], string] {
  const enc = encoding ?? detectEncoding(text, lang);
  const tokens: Token[] = [];
  const diags: Diagnostic[] = [];
  let line = 1;
  let col = 1;
  let start: number | null = null;
  let buf: string[] = [];
  let raw: string[] = [];
  let native = false;
  let asc = false;
  let startLine = 0;
  let startCol = 0;
  // the block the writing-system specification declares
  // (specification/writing-system.md#the-native-digital-form)
  const block: string[] = lang.writing["code point block"];
  const puaLo = parseInt(block[0].slice(2), 16);
  const puaHi = parseInt(block[1].slice(2), 16) + 1;

  const flush = (end: number): void => {
    if (start !== null) {
      tokens.push(new Token(buf.join(""), raw.join(""),
        new Span(enc, start, end, startLine, startCol), native, asc));
    }
    buf = [];
    raw = [];
    native = false;
    asc = false;
    start = null;
  };

  let i = 0;
  for (const ch of text) {
    if (SEPARATORS.includes(ch)) {
      flush(i);
    } else {
      if (start === null) {
        start = i;
        startLine = line;
        startCol = col;
      }
      raw.push(ch);
      const letter = lang.lettersOf.get(ch);
      const cp = ch.codePointAt(0) ?? 0;
      if (letter !== undefined) {
        buf.push(letter);
        native = true;
      } else if (PAYLOAD_CHARS.includes(ch)) {
        buf.push(ch);
        if (ch >= "a" && ch <= "z") asc = true;
      } else if (puaLo <= cp && cp < puaHi) {
        diags.push(new Diagnostic("d.tokenizer.foreign-use-of-the-range",
          new Span(enc, i, i + 1, line, col), { detected: [codePointLabel(ch)] }));
        buf.push("?");
      } else {
        diags.push(new Diagnostic("d.tokenizer.outside-the-alphabet",
          new Span(enc, i, i + 1, line, col),
          { expected: ["a symbol or a separator"], detected: [codePointLabel(ch)] }));
        buf.push("?");
      }
    }
    if (ch === "\n") {
      line += 1;
      col = 1;
    } else {
      col += 1;
    }
    i += 1;
  }
  flush(i);
  return [tokens, diags, enc];
}

/** The morphemes of a content word, or null. A content word is a root or a closed-class
 * member followed by suffixes, with the linker opening each further root of a compound;
 * the shapes make the division unique (`language/phonology.json`). */
export function segment(form: string, lang: Language): Morpheme[] | null {
  // the root opening at i, of the length its first syllable fixes: five symbols or,
  // opened by the long root's syllable, seven
  // (specification/sounds-and-words.md#how-a-words-opening-fixes-its-length)
  const rootAt = (i: number): Item | null => {
    const n = lang.lengthAt(form, i);
    const item = n === undefined ? undefined : lang.byForm.get(form.slice(i, i + n));
    if (item !== undefined && item.kind === "root") return item;
    return null;
  };
  const morphemes: Morpheme[] = [];
  let i: number;
  const first = rootAt(0);
  if (first !== null) {
    morphemes.push(first);
    i = first.form.length;
  } else {
    const head = lang.byForm.get(form.slice(0, 4));
    if (head === undefined || head.kind !== "member" || form.length <= 4) return null;
    morphemes.push(head);
    i = 4;
  }
  while (i < form.length) {
    const ch = form.charAt(i);
    if (ch === LINKER) {
      const next = rootAt(i + 1);
      if (next === null) return null;
      morphemes.push("linker");
      morphemes.push(next);
      i += 1 + next.form.length;
    } else if (SUFFIX_FIRST.includes(ch)) {
      const suf = lang.suffixes.get(form.slice(i, i + 4));
      if (suf === undefined) return null;
      morphemes.push(suf);
      i += 4;
    } else {
      return null;
    }
  }
  return morphemes;
}

function payloadLength(nbytes: bigint): bigint {
  return (8n * nbytes + 4n) / 5n;
}

const BASE32 = "abcdefghijklmnopqrstuvwxyz234567";

/** RFC 4648 § 6 base 32 in lower case without padding. */
export function encodePayload(data: Uint8Array): string {
  let out = "";
  let bits = 0;
  let value = 0;
  for (const byte of data) {
    value = (value << 8) | byte;
    bits += 8;
    while (bits >= 5) {
      out += BASE32[(value >>> (bits - 5)) & 31];
      bits -= 5;
    }
    value &= (1 << bits) - 1;
  }
  if (bits > 0) out += BASE32[(value << (5 - bits)) & 31];
  return out;
}

/** The bytes of a payload, or null unless it is canonical base 32. */
export function decodePayload(chars: string): Uint8Array | null {
  for (const c of chars) if (!PAYLOAD_CHARS.includes(c)) return null;
  const out = new Uint8Array(Math.floor((chars.length * 5) / 8));
  let bits = 0;
  let value = 0;
  let k = 0;
  for (const c of chars) {
    value = (value << 5) | BASE32.indexOf(c);
    bits += 5;
    if (bits >= 8) {
      if (k < out.length) out[k] = (value >>> (bits - 8)) & 255;
      k += 1;
      bits -= 8;
    }
    value &= (1 << bits) - 1;
  }
  // A length no encoding produces, or trailing bits that are not zero, fails here.
  return encodePayload(out) === chars ? out : null;
}

const DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"];

// what is still to read: "number" for a payload's length, "scheme" for the number of an
// authentication scheme, which states no length, or a length
type Need = "number" | "scheme" | bigint;

class Lexer {
  tokens: Token[];
  lang: Language;
  words: Word[] = [];
  diags: Diagnostic[] = [];
  wall: string;
  declaredData: string;
  // the authentication field, whose signature is a payload after the numbers of its
  // scheme and its length (protocol 0.3); absent from a release before it
  authentication: string | null;

  constructor(tokens: Token[], lang: Language) {
    this.tokens = tokens;
    this.lang = lang;
    this.wall = lang.formOf("g.structure.wall");
    this.declaredData = lang.formOf("g.message.embedded-material.declared-data");
    this.authentication = lang.items.has("g.message.message-field.authentication")
      ? lang.formOf("g.message.message-field.authentication") : null;
  }

  wordOf(tok: Token): Word {
    const lang = this.lang;
    if (tok.asciiLetters && tok.native) {
      this.diags.push(new Diagnostic("d.tokenizer.mixed-encodings", tok.span,
        { detected: [tok.raw] }));
    }
    const item = lang.byForm.get(tok.text);
    if (item !== undefined) return new Word(tok.text, tok.span, item);
    for (const c of tok.text) {
      if (!lang.letters.includes(c)) {
        this.diags.push(new Diagnostic("d.lexer.letter-outside-a-payload", tok.span,
          { expected: ["a word"], detected: [tok.raw] }));
        return new Word(tok.text, tok.span, null, "unknown");
      }
    }
    const parts = segment(tok.text, lang);
    if (parts !== null) return new Word(tok.text, tok.span, null, "formation", parts);
    // Kept opaque and reported as unknown in the named version; the integrity check
    // value, where present, tells an unknown word from a corrupted one.
    this.diags.push(new Diagnostic("d.lexer.unknown-word", tok.span, {
      expected: ["a word of lexicon " + lang.version], detected: [tok.raw],
      recoverability: "kept opaque",
    }));
    return new Word(tok.text, tok.span, null, "unknown");
  }

// As long as the canonical implementation's `_Lexer.run`, which it follows statement for
  // statement so that the two can be read side by side.
  run(): [Word[], Diagnostic[]] {
    const toks = this.tokens;
    let i = 0;
    let numberState: string[] = []; // the numerals of a payload's length
    let need: Need[] = []; // lengths still to read
    while (i < toks.length) {
      const tok = toks[i];
      if (need.length && typeof need[0] === "bigint") {
        const n = need.shift() as bigint;
        let chars = "";
        let j = i;
        while (BigInt(codePointLength(chars)) < n && j < toks.length) {
          chars += toks[j].raw;
          j += 1;
        }
        const first = tok.span;
        const last = (toks.at(j - 1) as Token).span;
        const span = new Span(first.encoding, first.start, last.end, first.line, first.column);
        const length = BigInt(codePointLength(chars));
        if (length !== n) {
          // Short: the tokens ran out, or a further token was needed and did not end
          // where the length does. Long: one token exceeds the length.
          const code = j - i === 1 && length > n ? "d.lexer.payload-long" :
            "d.lexer.payload-short";
          this.diags.push(new Diagnostic(code, span, {
            expected: [n + " characters"], detected: [length + " characters"],
          }));
          this.words.push(new Word(chars, span, null, "payload"));
          need = [];
          i = j;
          continue;
        }
        let data = decodePayload(chars);
        if (data === null) {
          this.diags.push(new Diagnostic("d.lexer.payload-character", span,
            { expected: ["canonical base 32"], detected: [chars] }));
          data = new Uint8Array(0);
        }
        this.words.push(new Word(chars, span, null, "payload", [], data));
        i = j;
        continue;
      }
      const word = this.wordOf(tok);
      this.words.push(word);
      i += 1;
      // Track `WALL DECLARED-DATA number payload number payload`.
      const words = this.words;
      if (words.length >= 2 && words[words.length - 2].form === this.wall &&
        word.form === this.declaredData) {
        need = ["number", "number"];
        numberState = [];
        continue;
      }
      // Track `AUTHENTICATION number number payload`: the scheme, then the length.
      if (this.authentication !== null && word.form === this.authentication) {
        need = ["scheme", "number"];
        numberState = [];
        continue;
      }
      if (need.length && (need[0] === "number" || need[0] === "scheme")) {
        if (word.item !== null && word.classId === "g.numbers.numeral") {
          numberState.push(word.item.name);
        } else if (word.item !== null && word.classId === "g.numbers.check-word") {
          if (need[0] === "scheme") {
            need.shift();
            numberState = [];
            continue;
          }
          const digits = numberState.filter((x) => DIGITS.includes(x))
            .map((x) => String(DIGITS.indexOf(x))).join("");
          need.shift();
          const count = digits && digits.length === numberState.length ? BigInt(digits) : 0n;
          need.unshift(payloadLength(count));
          // after the first payload, the second length follows
          if (need.length === 2) need = [need[0], "number"];
          numberState = [];
        } else {
          need = [];
        }
      }
    }
    return [this.words, this.diags];
  }
}

export function lex(tokens: Token[], lang: Language): [Word[], Diagnostic[]] {
  return new Lexer(tokens, lang).run();
}
