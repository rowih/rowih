// The behaviours of Python's standard library the records depend on, checked against
// outputs the canonical implementation's Python produced.

import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { test } from "node:test";

import { decodePayload, encodePayload } from "../src/lexer.ts";
import { codePointLength, compareCodePoints, dumps, fixed, htmlEscape, pyFloat, zfill }
  from "../src/pyformat.ts";
import { hex, sha256 } from "../src/sha256.ts";

// [value, "%.1f" % value, "%.0f" % value], from CPython 3.12.
const FIXED: [number, string, string][] = [
  [0.25, "0.2", "0"], [0.75, "0.8", "1"], [1.25, "1.2", "1"], [2.5, "2.5", "2"],
  [-0.25, "-0.2", "-0"], [-0.0, "-0.0", "-0"], [0.0, "0.0", "0"], [13.75, "13.8", "14"],
  [16.25, "16.2", "16"], [13.25, "13.2", "13"],
  [1e21, "1000000000000000000000.0", "1000000000000000000000"],
  [1.5e22, "15000000000000000000000.0", "15000000000000000000000"], [0.05, "0.1", "0"],
  [123.456, "123.5", "123"], [2.675, "2.7", "3"], [-2.675, "-2.7", "-3"], [0.15, "0.1", "0"],
  [0.35, "0.3", "0"], [1e-7, "0.0", "0"], [-1e-7, "-0.0", "-0"], [999.95, "1000.0", "1000"],
  [999.25, "999.2", "999"], [5.0, "5.0", "5"], [7.0, "7.0", "7"], [0.5, "0.5", "0"],
  [1.5, "1.5", "2"], [-1.5, "-1.5", "-2"], [3.5, "3.5", "4"], [4.5, "4.5", "4"],
  [3.4999999, "3.5", "3"], [1234567.25, "1234567.2", "1234567"],
];

test("fixed-point formatting rounds a tie to the even digit, as Python does", () => {
  for (const [v, one, none] of FIXED) {
    assert.equal(fixed(v, 1), one, String(v));
    assert.equal(fixed(v, 0), none, String(v));
  }
});

test("SHA-256 agrees with Node's over lengths across the block boundaries", () => {
  let seed = 7;
  for (let n = 0; n < 300; n++) {
    const data = new Uint8Array(n);
    for (let i = 0; i < n; i++) {
      seed = (seed * 1103515245 + 12345) % 2147483648;
      data[i] = seed & 255;
    }
    assert.equal(hex(sha256(data)), createHash("sha256").update(data).digest("hex"), String(n));
  }
});

test("base 32 round-trips, and only canonical text decodes", () => {
  for (let n = 0; n < 40; n++) {
    const data = Uint8Array.from({ length: n }, (_, i) => (i * 37 + n) & 255);
    assert.deepEqual(decodePayload(encodePayload(data)), data);
  }
  // RFC 4648 § 10, lower case without padding, as Python's base64 writes them
  const vectors: [string, string][] = [["", ""], ["f", "my"], ["fo", "mzxq"], ["foo", "mzxw6"],
    ["foob", "mzxw6yq"], ["fooba", "mzxw6ytb"], ["foobar", "mzxw6ytboi"],
    ["text/plain", "orsxq5bpobwgc2lo"]];
  for (const [plain, coded] of vectors) {
    assert.equal(encodePayload(new TextEncoder().encode(plain)), coded);
  }
  for (const bad of ["a", "abc", "abcdef", "mz", "mzxw6ytboj", "ORSX", "a1"]) {
    assert.equal(decodePayload(bad), null, bad);
  }
});

test("float parsing accepts what Python's float() accepts over the numeral symbols", () => {
  assert.equal(pyFloat("1e5"), 100000);
  assert.equal(pyFloat("-.5"), -0.5);
  assert.equal(pyFloat("5."), 5);
  for (const bad of ["", "-", "1/2", "1~2", "e5", "1e", "1.2.3", "--1"]) {
    assert.equal(pyFloat(bad), null, bad);
  }
});

test("strings are measured and ordered by code point", () => {
  assert.equal(codePointLength("a\u{1F600}b"), 3);
  assert.ok(compareCodePoints("\u{FFFF}", "\u{10000}") < 0);
  assert.ok("\u{FFFF}" > "\u{10000}"); // what UTF-16 order would give instead
  assert.equal(zfill("-5", 3), "-05");
  assert.equal(htmlEscape(`<a href="x">'&'</a>`),
    "&lt;a href=&quot;x&quot;&gt;&#x27;&amp;&#x27;&lt;/a&gt;");
});

test("JSON is written as Python's json.dumps writes it", () => {
  assert.equal(dumps({ a: [1, "é\n\u0001"], b: {}, c: [], d: null, e: true }),
    '{"a": [1, "é\\n\\u0001"], "b": {}, "c": [], "d": null, "e": true}');
  assert.equal(dumps({ a: [1, { b: 2n }] }, 1), '{\n "a": [\n  1,\n  {\n   "b": 2\n  }\n ]\n}');
});
