// The writing-system specification as the renderer reads it (`language/writing.json`;
// specification/writing-system.md#the-components): each symbol's strokes of the pen, and
// the free ends of its unit strokes, where the ceremonial variant sets a serif. The
// canonical implementation's `writing` module also holds the declared visual measure,
// which only its tests and its build read.

import { type Language } from "./data.ts";

export type Point = [number, number];

interface Tables {
  units: Map<string, [Point, Point][]>;
  pen: Map<string, Point[][]>;
}

const TABLES = new WeakMap<Language, Tables>();

function tables(lang: Language): Tables {
  const cached = TABLES.get(lang);
  if (cached !== undefined) return cached;
  const units = new Map<string, [Point, Point][]>();
  const pen = new Map<string, Point[][]>();
  for (const c of lang.writing.components) {
    units.set(c.symbol, (c["unit strokes"] as number[][][]).map(
      ([a, b]) => [[a[0], a[1]], [b[0], b[1]]]));
    pen.set(c.symbol, (c["pen strokes"] as number[][][]).map(
      (path) => path.map((p): Point => [p[0], p[1]])));
  }
  const out = { units, pen };
  TABLES.set(lang, out);
  return out;
}

/** The strokes of the pen that write a component, in order, each from its start. */
export function penStrokes(symbol: string, lang: Language): Point[][] {
  const pen = tables(lang).pen.get(symbol);
  if (pen === undefined) throw new Error("KeyError: " + symbol);
  return pen;
}

/** The points where a component's strokes end without meeting another, in the order of
 * their coordinates (specification/writing-system.md#drawing-a-word-and-a-line). */
export function freeEnds(symbol: string, lang: Language): Point[] {
  const units = tables(lang).units.get(symbol);
  if (units === undefined) throw new Error("KeyError: " + symbol);
  const degree = new Map<string, [Point, number]>();
  for (const stroke of units) {
    for (const p of stroke) {
      const key = p[0] + "," + p[1];
      const seen = degree.get(key);
      degree.set(key, [p, seen === undefined ? 1 : seen[1] + 1]);
    }
  }
  return [...degree.values()].filter(([, d]) => d === 1).map(([p]) => p)
    .sort((a, b) => a[0] - b[0] || a[1] - b[1]);
}
