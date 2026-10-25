// The canonical serialisation, the native digital form and the check values
// (specification/protocol.md#the-check-values).

import { type Language } from "./data.ts";
import { type Word } from "./lexer.ts";
import { hex, sha256Text } from "./sha256.ts";

/** The envelope as the first line and each move a line of its own, words separated by
 * one space and every line ended by one line feed. Words in `drop` (by identity) are
 * left out, which is how the integrity check value's field is removed. */
export function canonicalLines(envelopeWords: Word[], movesWords: Word[][],
  drop: Word[] = []): string {
  const dropped = new Set(drop);
  const lines = [envelopeWords.filter((w) => !dropped.has(w)).map((w) => w.form).join(" ")];
  for (const words of movesWords) lines.push(words.map((w) => w.form).join(" "));
  return lines.map((line) => line + "\n").join("");
}

/** SHA-256 (FIPS 180-4 § 6.2) of the text's UTF-8 bytes, as an integer, modulo ten to the
 * check value width of the protocol schema (nine numerals from protocol 0.3,
 * specification/protocol.md#the-check-values). */
export function checkValue(text: string, width: number): number {
  return Number(BigInt("0x" + hex(sha256Text(text))) % (10n ** BigInt(width)));
}

/** The bytes an authentication covers (specification/protocol.md#authentication): the
 * canonical serialisation of the whole message, `envelope` its first line without the
 * authentication and integrity check value fields and `body` its moves, each line ended
 * by a line feed. */
export function covered(envelope: string, body: string): string {
  return envelope + "\n" + body;
}

/** The native digital form: each symbol as its code point, payloads as written. */
export function toNative(wordsByLine: Word[][], lang: Language): string {
  const lines = wordsByLine.map((words) => words.map((w) => {
    if (w.kind === "payload") return w.form;
    let out = "";
    for (const ch of w.form) out += lang.codePoints.get(ch) ?? ch;
    return out;
  }).join(" "));
  return lines.map((line) => line + "\n").join("");
}
