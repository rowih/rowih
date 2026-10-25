// The renderer of the native writing system
// (specification/writing-system.md#the-renderings): SVG, PNG, HTML and the terminal. The
// SVG and the PNG are both written from one drawing (`drawing.ts`), in the display,
// compact or handwritten form, with the ceremonial variant for moves in the ceremonial
// register. Every rendering is a view made by its receiver, and its text alternative is
// the transliteration. The high-contrast rendering draws black on white with strokes half
// as heavy again; no distinction depends on colour or on ornament.

import { type Language } from "./data.ts";
import { type Drawable, type Drawing, draw, type Path } from "./drawing.ts";
import { encode } from "./png.ts";
import { htmlEscape } from "./pyformat.ts";
import { rasterise } from "./raster.ts";
import { toNative } from "./serialise.ts";

export const CONTRASTS = ["normal", "high"];
const HEAVIER = 1.5;

/** What the renderer reads of an analysis. */
export interface Rendered extends Drawable {
  canonical: string;
}

// Python's `repr` of the widths the forms use (1.5, 0.75 and their halves and
// multiples by 1.5) is JavaScript's `String`; whole widths are written as integers.
const width = (value: number): string => String(value);

function points(path: Path): string {
  return path.points.map(([x, y]) => x + "," + y).join(" ");
}

function heavier(d: Drawing): Drawing {
  return { ...d, stroke: d.stroke * HEAVIER, hairline: d.hairline * HEAVIER };
}

function svgOf(d: Drawing, alt: string, contrast: string): string {
  if (contrast === "high") d = heavier(d);
  const ink = contrast === "high" ? "#000000" : "currentColor";
  const parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + d.width + " " +
    d.height + '" width="' + d.width + '" height="' + d.height + '" role="img" aria-label="' +
    alt + '"><title>' + alt + "</title><desc>A view of the native written form, made by " +
    "this receiver.</desc>"];
  if (contrast === "high") {
    parts.push('<rect width="' + d.width + '" height="' + d.height + '" fill="#ffffff"/>');
  }
  for (const [weight, w] of [["stroke", d.stroke], ["hairline", d.hairline]] as const) {
    const paths = d.paths.filter((p) => p.weight === weight);
    if (paths.length) {
      parts.push('<g fill="none" stroke="' + ink + '" stroke-width="' + width(w) +
        '" stroke-linecap="round" stroke-linejoin="round">');
      for (const p of paths) parts.push('<polyline points="' + points(p) + '"/>');
      parts.push("</g>");
    }
  }
  if (d.texts.length) {
    parts.push('<g fill="' + ink + '" font-family="monospace">');
    for (const t of d.texts) {
      parts.push('<text x="' + t.x + '" y="' + t.y + '" font-size="' + t.size + '">' +
        htmlEscape(t.text) + "</text>");
    }
    parts.push("</g>");
  }
  parts.push("</svg>\n");
  return parts.join("");
}

/** The native written form of a parsed message as SVG, a view. */
export function svg(analysis: Rendered, lang: Language, form = "display",
  contrast = "normal"): string {
  if (analysis.message === null) return "";
  return svgOf(draw(analysis, form, lang), htmlEscape(analysis.canonical), contrast);
}

/** The native written form of a parsed message as a greyscale PNG, a view, with the
 * transliteration as its description. */
export function png(analysis: Rendered, lang: Language, form = "display",
  contrast = "normal"): Uint8Array {
  if (analysis.message === null) return new Uint8Array(0);
  let d = draw(analysis, form, lang);
  if (contrast === "high") d = heavier(d);
  const [w, h, greys] = rasterise(d, lang.writing["pixels per unit"]);
  if (contrast === "high") {
    for (let i = 0; i < greys.length; i++) greys[i] = greys[i] < 128 ? 0 : 255;
  }
  return encode(w, h, greys, analysis.canonical);
}

/** The native digital form where the terminal has the font, else the transliteration,
 * never a box or a substitute glyph. */
export function terminal(analysis: Rendered, lang: Language, hasFont = false): string {
  if (!hasFont) return analysis.canonical;
  if (analysis.message === null) return "";
  return toNative([analysis.message.envelope.words, ...analysis.message.lines], lang);
}

/** The SVG in a figure whose caption is the transliteration, marked as text in an
 * artificial language (BCP 47 `art`), and, where one is given, the linear semantic
 * description. */
export function html(analysis: Rendered, lang: Language, form = "display", contrast = "normal",
  description: string | null = null): string {
  let caption = '<code lang="art">' + htmlEscape(analysis.canonical) + "</code>";
  if (description) caption += '<p class="description">' + htmlEscape(description) + "</p>";
  return '<figure class="rowih">' + svg(analysis, lang, form, contrast) + "<figcaption>" +
    caption + "</figcaption></figure>\n";
}
