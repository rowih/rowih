// The few behaviours of Python's standard library that the canonical implementation's
// output depends on, written out so that the two implementations agree byte for byte
// (`compare_implementations`; specification/conformance.md#the-two-implementations):
// fixed-point formatting, which rounds a tie to the even digit; `float()` over the
// numeral alphabet; `json.dumps` with `ensure_ascii=False`; `html.escape`; and strings
// measured in code points.

/** A JSON value as the records hold it; integers beyond 2^53 are bigints. */
export type Json = null | boolean | number | bigint | string | Json[] | { [key: string]: Json };

/** The number of code points in a string, Python's `len`. */
export function codePointLength(s: string): number {
  let n = 0;
  for (const _ of s) n += 1;
  return n;
}

/** Python's `"%.<digits>f" % x`: correctly rounded, a tie going to the even digit. */
export function fixed(x: number, digits: number): string {
  if (Number.isNaN(x)) return "nan";
  if (!Number.isFinite(x)) return x > 0 ? "inf" : "-inf";
  const negative = x < 0 || Object.is(x, -0);
  const m = Math.abs(x);
  const scale = 10 ** digits;
  // A tie is a value exactly halfway between two outputs: m * 10^d + 1/2 an integer.
  // Doubles are dyadic, so for one digit a tie is an odd multiple of 1/4, and for none
  // an odd multiple of 1/2; both products below are exact.
  const tieUnit = digits === 0 ? 2 : digits === 1 ? 4 : 0;
  let body: string;
  if (tieUnit !== 0 && Number.isInteger(m * tieUnit) && (m * tieUnit) % 2 === 1) {
    let n = BigInt(Math.floor(m * scale));
    if (n % 2n === 1n) n += 1n;
    body = withPoint(n, digits);
  } else if (m >= 1e21) {
    body = withPoint(BigInt(m) * BigInt(scale), digits);
  } else {
    body = m.toFixed(digits);
  }
  return (negative ? "-" : "") + body;
}

function withPoint(n: bigint, digits: number): string {
  if (digits === 0) return n.toString();
  const s = n.toString().padStart(digits + 1, "0");
  return s.slice(0, s.length - digits) + "." + s.slice(s.length - digits);
}

const PY_FLOAT = /^-?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:e-?[0-9]+)?$/;

/** Python's `float(text)` over the numerals' symbols (digits, '.', '-', '/', 'e', '~'):
 * the value, or null where Python raises `ValueError`. */
export function pyFloat(text: string): number | null {
  return PY_FLOAT.test(text) ? Number(text) : null;
}

/** Python's `str()` of a string or None. */
export function pyStr(x: string | null | undefined): string {
  return x === null || x === undefined ? "None" : x;
}

/** Python's `html.escape(s, quote=True)`. */
export function htmlEscape(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#x27;");
}

/** Python's `str.zfill(width)`. */
export function zfill(s: string, width: number): string {
  const len = codePointLength(s);
  if (len >= width) return s;
  const pad = "0".repeat(width - len);
  if (s.startsWith("-") || s.startsWith("+")) return s[0] + pad + s.slice(1);
  return pad + s;
}

/** Python's `"%06d" % n` and the like: an integer padded with zeros. */
export function zeroPad(n: number | bigint, width: number): string {
  const s = n.toString();
  return s.startsWith("-") ? "-" + s.slice(1).padStart(width - 1, "0") : s.padStart(width, "0");
}

/** Python's `"U+%04X" % ord(ch)`. */
export function codePointLabel(ch: string): string {
  return "U+" + (ch.codePointAt(0) ?? 0).toString(16).toUpperCase().padStart(4, "0");
}

/** Compare two strings by code point, as Python orders them. */
export function compareCodePoints(a: string, b: string): number {
  const ia = a[Symbol.iterator]();
  const ib = b[Symbol.iterator]();
  for (;;) {
    const x = ia.next();
    const y = ib.next();
    if (x.done || y.done) return x.done && y.done ? 0 : x.done ? -1 : 1;
    const cx = x.value.codePointAt(0) ?? 0;
    const cy = y.value.codePointAt(0) ?? 0;
    if (cx !== cy) return cx < cy ? -1 : 1;
  }
}

/** Python's `sorted()` of strings. */
export function sortedStrings(xs: Iterable<string>): string[] {
  return Array.from(xs).sort(compareCodePoints);
}

function escapeString(s: string): string {
  let out = '"';
  for (const ch of s) {
    const c = ch.codePointAt(0) ?? 0;
    if (ch === '"') out += '\\"';
    else if (ch === "\\") out += "\\\\";
    else if (ch === "\n") out += "\\n";
    else if (ch === "\r") out += "\\r";
    else if (ch === "\t") out += "\\t";
    else if (ch === "\b") out += "\\b";
    else if (ch === "\f") out += "\\f";
    else if (c < 0x20) out += "\\u" + c.toString(16).padStart(4, "0");
    else out += ch;
  }
  return out + '"';
}

/** Python's `json.dumps(value, ensure_ascii=False, indent=indent)`, keys in insertion
 * order. Floats are refused: no record holds one. */
export function dumps(value: Json, indent: number | null = null): string {
  return dump(value, indent, 0);
}

function dump(value: Json, indent: number | null, level: number): string {
  if (value === null) return "null";
  if (value === true) return "true";
  if (value === false) return "false";
  if (typeof value === "bigint") return value.toString();
  if (typeof value === "number") {
    if (!Number.isInteger(value)) throw new TypeError("a float in a record: " + value);
    return Object.is(value, -0) ? "0" : value.toString();
  }
  if (typeof value === "string") return escapeString(value);
  const open = indent === null ? "" : "\n" + " ".repeat(indent * (level + 1));
  const close = indent === null ? "" : "\n" + " ".repeat(indent * level);
  const sep = indent === null ? ", " : "," + open;
  if (Array.isArray(value)) {
    if (value.length === 0) return "[]";
    return "[" + open + value.map((v) => dump(v, indent, level + 1)).join(sep) + close + "]";
  }
  const keys = Object.keys(value);
  if (keys.length === 0) return "{}";
  return "{" + open + keys.map((k) => escapeString(k) + ": " +
    dump(value[k] as Json, indent, level + 1)).join(sep) + close + "}";
}
