// The drawing of a message in the native written form
// (specification/writing-system.md#drawing-a-word-and-a-line and 2.4): a display list of
// paths in integer units, from which the SVG and the PNG are both written, so that the
// two cannot draw differently. The canonical implementation's `drawing.draw`, which this
// follows statement for statement; its `drawing.read`, the inverse the tests use, has no
// counterpart here.

import { type Language } from "./data.ts";
import { type Word } from "./lexer.ts";
import { codePointLabel, codePointLength } from "./pyformat.ts";
import { type Message } from "./syntax.ts";
import { type Tree } from "./tree.ts";
import { freeEnds, penStrokes, type Point } from "./writing.ts";

export const FORMS = ["display", "compact", "handwritten"];
const CEREMONIAL = "R7";

export interface Path {
  points: Point[]; // in units, x to the right and y downward
  weight: "stroke" | "hairline"; // a hairline is a join of the handwritten form
}

export interface Text {
  x: number;
  y: number; // the baseline
  width: number;
  size: number; // the height of the text, and of its outline in the PNG
  text: string;
}

export interface Drawing {
  form: string;
  width: number;
  height: number;
  paths: Path[];
  texts: Text[];
  stroke: number;
  hairline: number;
  lines: number[]; // the top of each line's text, in order
}

/** What the drawing reads of an analysis. */
export interface Drawable {
  message: Message | null;
  social: Tree[];
}

const floorDiv = (a: number, b: number): number => Math.floor(a / b);

const stroke = (points: Point[]): Path => ({ points, weight: "stroke" });

function markBase(mark: number[][]): number {
  const base = mark.filter((p) => p[1] === 0).map((p) => p[0]);
  return floorDiv(Math.min(...base) + Math.max(...base), 2);
}

/** The layout of one line, in its own coordinates: the line's text from y 0 to the
 * box's height, its marks above and its rules below. */
class Line {
  lang: Language;
  spec: any; // the parsed `language/writing.json`
  m: Record<string, number>;
  box: [number, number];
  ceremonial: boolean;
  envelope: boolean;
  paths: Path[] = [];
  texts: Text[] = [];
  x: number;
  opens = new Map<string, string>();
  closes = new Map<string, string>();
  stack: [string, number, number][] = []; // open units: unit, side x, highest level inside
  units: [string, number, number, number][] = []; // unit, opening x, closing x, level
  lone: [string, number, boolean][] = []; // unit, side x, opens; without a partner
  walls: [number, boolean][] = [];
  levels = 0;

  constructor(lang: Language, ceremonial: boolean, envelope: boolean) {
    this.lang = lang;
    this.spec = lang.writing;
    this.m = this.spec.metrics;
    this.box = this.spec.lattice.box;
    this.ceremonial = ceremonial;
    this.envelope = envelope;
    this.x = this.m["margin"];
    for (const [unit, sign] of Object.entries(this.spec.units as Record<string, any>)) {
      this.opens.set(sign.opens, unit);
      this.closes.set(sign.closes, unit);
    }
  }

  side(unit: string, opens: boolean): void {
    const x = this.x + floorDiv(this.m["side"], 2);
    const top = this.stack[this.stack.length - 1];
    if (opens) {
      this.stack.push([unit, x, 0]);
    } else if (top !== undefined && top[0] === unit) {
      this.stack.pop();
      const level = top[2] + 1;
      this.units.push([unit, top[1], x, level]);
      this.levels = Math.max(this.levels, level);
      const outer = this.stack[this.stack.length - 1];
      if (outer !== undefined) outer[2] = Math.max(outer[2], level);
    } else {
      this.lone.push([unit, x, false]);
    }
    this.x += this.m["side"] + this.m["word gap"];
  }

  wall(opens: boolean): void {
    this.walls.push([this.x, opens]);
    this.x += this.m["side"] + this.m["word gap"];
  }

  payload(text: string): void {
    const width = this.m["character"] * codePointLength(text);
    this.texts.push({ x: this.x, y: this.box[1] - 2, width, size: this.m["text size"], text });
    this.x += width + this.m["word gap"];
  }

  cluster(form: string, isProtected: boolean, handwritten: boolean): [number, number] {
    const start = this.x;
    const w = this.box[0];
    const gap = this.m["gap"];
    let previousEnd: Point | null = null;
    for (const ch of form) {
      if (!this.lang.codePoints.has(ch)) {
        // a character outside the alphabet has no component; it is shown as itself
        // where it is printable ASCII and otherwise by its code point
        const c = ch.codePointAt(0) ?? 0;
        const label = 0x20 < c && c < 0x7F ? ch : codePointLabel(ch);
        const width = this.m["character"] * label.length;
        this.texts.push({ x: this.x, y: this.box[1] - 2, width, size: this.m["text size"],
          text: label });
        this.x += width + gap;
        previousEnd = null;
        continue;
      }
      const pens = penStrokes(ch, this.lang);
      for (const path of pens) {
        this.paths.push(stroke(path.map(([px, py]): Point => [this.x + px, py])));
      }
      if (handwritten && pens.length) {
        const first: Point = [this.x + pens[0][0][0], pens[0][0][1]];
        if (previousEnd !== null) this.paths.push({ points: [previousEnd, first], weight: "hairline" });
        const last = pens[pens.length - 1];
        previousEnd = [this.x + last[last.length - 1][0], last[last.length - 1][1]];
      }
      if (this.ceremonial) {
        const s: number = this.spec.serif;
        for (const [px, py] of freeEnds(ch, this.lang)) {
          this.paths.push(stroke([[this.x + px, py - s], [this.x + px, py + s]]));
        }
      }
      this.x += w + gap;
    }
    const end = this.x - gap;
    if (isProtected) {
      let y = -this.m["overline"];
      this.paths.push(stroke([[start, y], [end, y]]));
      if (this.ceremonial) {
        y -= this.spec.double;
        this.paths.push(stroke([[start, y], [end, y]]));
      }
    }
    this.x = end + this.m["word gap"];
    return [start, end];
  }

  frame(start: number, end: number): void {
    const h = floorDiv(this.box[1], 2);
    const half = this.m["frame"];
    const a = start - floorDiv(this.m["frame space"], 2);
    const b = end + floorDiv(this.m["frame space"], 2);
    const tip = floorDiv(half, 3);
    this.paths.push(stroke([[a, h - half], [b, h - half], [b + tip, h], [b, h + half],
      [a, h + half], [a - tip, h], [a, h - half]]));
  }

  ruleY(level: number): number {
    return this.box[1] + this.m["rule depth"] + (level - 1) * this.m["rule step"];
  }

  /** Draw the sides, rules, marks, walls and strip, and return the line's width with
   * its extent above and below its own origin. */
  finish(): [number, number, number] {
    for (const [unit, x] of this.stack) this.lone.push([unit, x, true]);
    const top = -2;
    for (const [unit, ox, cx, level] of this.units) {
      const y = this.ruleY(level);
      for (const x of [ox, cx]) {
        this.paths.push(stroke([[x, top], [x, y]]));
        this.mark(unit, x);
      }
      this.paths.push(stroke([[ox, y], [cx, y]]));
      if (this.ceremonial) {
        const d: number = this.spec.double;
        this.paths.push(stroke([[ox, y + d], [cx, y + d]]));
      }
    }
    for (const [unit, x, opens] of this.lone) {
      const y = this.ruleY(1);
      const foot = opens ? 4 : -4;
      this.paths.push(stroke([[x, top], [x, y], [x + foot, y]]));
      this.mark(unit, x);
    }
    const bottom = this.levels
      ? this.ruleY(this.levels) + (this.ceremonial ? this.spec.double as number : 0)
      : this.box[1] + this.m["rule depth"];
    for (const [x, opens] of this.walls) {
      for (const dx of [2, 6]) this.paths.push(stroke([[x + dx, top], [x + dx, bottom]]));
      // a tick at the top turned inward, so that the two walls differ
      this.paths.push(stroke(opens ? [[x + 6, top], [x + 10, top]] : [[x - 2, top], [x + 2, top]]));
    }
    const width = this.x - this.m["word gap"] + this.m["margin"];
    const h = floorDiv(this.box[1], 2);
    const above = this.m["above"];
    let below = Math.max(bottom, h + this.m["frame"]) + this.m["below"];
    if (this.envelope) {
      const s = this.m["strip"];
      for (const y of [-s, this.box[1] + s]) {
        this.paths.push(stroke([[floorDiv(this.m["margin"], 2), y],
          [width - floorDiv(this.m["margin"], 2), y]]));
      }
      below = Math.max(below, this.box[1] + s + this.m["below"]);
    }
    return [width, above, below];
  }

  mark(unit: string, x: number): void {
    const mark: number[][] = this.spec.units[unit].mark;
    const dx = x - markBase(mark);
    this.paths.push(stroke(mark.map(([px, py]): Point => [dx + px, py - 2])));
  }
}

/** The register of each move line, by its place among the lines. */
function lineRegisters(analysis: Drawable): Map<number, unknown> {
  const out = new Map<number, unknown>();
  if (analysis.message === null) return out;
  const moves = analysis.message.moves;
  for (let i = 0; i < Math.min(moves.length, analysis.social.length); i++) {
    out.set(moves[i].index - 1, analysis.social[i]["register"]);
  }
  return out;
}

function isNumeral(w: Word | undefined, numeral: string): boolean {
  return w !== undefined && w.item !== null && w.item.classId === numeral;
}

/** The drawing of a parsed message in one of the forms. */
export function draw(analysis: Drawable, form: string, lang: Language): Drawing {
  if (!FORMS.includes(form)) throw new Error("no form " + form);
  const m: Record<string, number> = lang.writing.metrics;
  const out: Drawing = { form, width: 0, height: 0, paths: [], texts: [], stroke: m["stroke"],
    hairline: m["hairline"], lines: [] };
  if (analysis.message === null) return out;
  const registers = lineRegisters(analysis);
  const lines: [Word[], boolean, boolean][] = [[analysis.message.envelope.words, false, true],
    ...analysis.message.lines.map((words, i): [Word[], boolean, boolean] =>
      [words, registers.get(i) === CEREMONIAL, false])];
  let y = 0;
  for (const [words, ceremonial, envelope] of lines) {
    const line = new Line(lang, ceremonial, envelope);
    write(line, words, form === "handwritten");
    const [width, above, below] = line.finish();
    const offset = y + above;
    for (const p of line.paths) {
      out.paths.push({ points: p.points.map(([px, py]): Point => [px, py + offset]),
        weight: p.weight });
    }
    for (const t of line.texts) out.texts.push({ ...t, y: t.y + offset });
    out.width = Math.max(out.width, width);
    out.lines.push(offset);
    y = offset + below + m["line gap"];
  }
  out.height = y;
  return form === "compact" ? halve(out) : out;
}

/** Each word of a line in turn: a side, a wall, embedded material or a cluster, and a
 * frame round each run of numerals. */
function write(line: Line, words: Word[], handwritten: boolean): void {
  const spec = line.spec;
  const numeral: string = spec.numbers.class;
  const wallOpens: string = spec.walls.opens;
  const wallCloses: string = spec.walls.closes;
  let run: [number, number] | null = null;
  words.forEach((w, i) => {
    const ident = w.item !== null ? w.item.identifier : "";
    const numeralWord = isNumeral(w, numeral);
    if (numeralWord && run === null) line.x += line.m["frame space"];
    const opens = line.opens.get(ident);
    const closes = line.closes.get(ident);
    if (opens !== undefined) {
      line.side(opens, true);
    } else if (closes !== undefined) {
      line.side(closes, false);
    } else if (ident === wallOpens || ident === wallCloses) {
      line.wall(ident === wallOpens);
    } else if (w.kind === "payload") {
      line.payload(w.form);
    } else {
      const [start, end] = line.cluster(w.form, w.item !== null && w.item.protected,
        handwritten);
      if (numeralWord) run = [run !== null ? run[0] : start, end];
    }
    if (run !== null && !isNumeral(words[i + 1], numeral)) {
      line.frame(run[0], run[1]);
      line.x += line.m["frame space"];
      run = null;
    }
  });
}

function halve(d: Drawing): Drawing {
  const h = (v: number): number => floorDiv(v, 2);
  return {
    form: "compact", width: h(d.width), height: h(d.height),
    paths: d.paths.map((p) => ({ points: p.points.map(([x, y]): Point => [h(x), h(y)]),
      weight: p.weight })),
    texts: d.texts.map((t) => ({ x: h(t.x), y: h(t.y), width: h(t.width), size: h(t.size),
      text: t.text })),
    stroke: d.stroke / 2, hairline: d.hairline / 2, lines: d.lines.map(h),
  };
}
