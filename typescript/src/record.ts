// The record both implementations write of an analysis, compared byte for byte by
// `compare_implementations` (specification/conformance.md#the-two-implementations): every
// stage's output, every diagnostic with its six fields, the check values, the conversions
// and the renderings, as one line of JSON.

import { checkValues, convert, parse, render } from "./api.ts";
import { type Language } from "./data.ts";
import { type Diagnostic, type Span } from "./diagnostics.ts";
import { type Word } from "./lexer.ts";
import { dumps, type Json } from "./pyformat.ts";
import { png, svg } from "./render.ts";
import { hex, sha256 } from "./sha256.ts";
import { spoken } from "./speech.ts";
import { stripPrivate } from "./tree.ts";

function spanRecord(s: Span | null): Json {
  return s === null ? null : [s.encoding, s.start, s.end, s.line, s.column];
}

function wordRecord(w: Word): Json {
  return {
    "form": w.form, "kind": w.kind, "entry": w.item !== null ? w.item.identifier : null,
    "morphemes": w.morphemes.map((m) => m === "linker" ? "linker" : m.identifier),
    "payload": hex(w.payload), "span": spanRecord(w.span),
  };
}

function diagnosticRecord(d: Diagnostic): Json {
  return {
    "code": d.code, "location": spanRecord(d.location), "expected": d.expected,
    "detected": d.detected, "ambiguity": d.ambiguity, "confidence": d.confidence,
    "recoverability": d.recoverability, "note": d.note, "text": d.asText(),
  };
}

/** The record of a text; with `everyView`, it also holds the compact, handwritten and
 * high-contrast SVG and the SHA-256 of the display PNG, which the records of sampled
 * edits leave out. */
export function record(text: string, lang: Language, everyView = false): Json {
  const a = parse(text, lang);
  const values = checkValues(text, lang);
  const out: { [key: string]: Json } = {
    "encoding": a.encoding,
    "words": a.words.map(wordRecord),
    "canonical": a.canonical,
    "moves": a.moves.map((t) => stripPrivate(t) as Json),
    "classes": a.classes.map((c) => ({ ...c })),
    "normal": a.normal as Json[],
    "normal text": a.normalText,
    "social": a.social as Json[],
    "formations": a.formations as Json[],
    "diagnostics": a.diagnostics.map(diagnosticRecord),
    "statement": a.statement as Json,
    "confidence": a.confidence,
    "integrity": (values.integrity ?? null) as Json,
    "semantic": (values.semantic ?? null) as Json,
    "native": convert(text, "native", lang)[0],
    "export": convert(text, "json", lang)[0],
    "svg": render(text, "svg", lang)[0],
    "html": render(text, "html", lang)[0],
    "terminal": render(text, "terminal", lang, true)[0],
    "spoken": spoken(a, lang).map((line) => ({ ...line })),
  };
  if (everyView) {
    out["compact"] = svg(a, lang, "compact");
    out["handwritten"] = svg(a, lang, "handwritten");
    out["high contrast"] = svg(a, lang, "display", "high");
    out["png"] = hex(sha256(png(a, lang)));
  }
  return out;
}

export function recordLine(text: string, lang: Language, everyView = false): string {
  return dumps(record(text, lang, everyView));
}
