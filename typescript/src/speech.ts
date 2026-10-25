// The spoken form (specification/sounds-and-words.md#the-spoken-form), the canonical
// implementation's `speech.spoken`: each line of a message as it is spoken, in the
// prosody its register's setting names, its words in the IPA and as espeak-ng input.
// Embedded material is not in the language and is not spoken; its place is marked by a
// pause. Synthesis itself needs espeak-ng, which a page does not have.

import { type Language } from "./data.ts";
import { type Word } from "./lexer.ts";
import { type Message } from "./syntax.ts";
import { type Tree } from "./tree.ts";

const STRESS = "ˈ";
export const EMBEDDED = "(embedded material)";

/** What the spoken form reads of an analysis. */
export interface Speakable {
  message: Message | null;
  social: Tree[];
}

export interface SpokenLine {
  prosody: string;
  ipa: string;
  espeak: string;
}

/** The syllables of a word: consonant and vowel, the last closed by a final consonant. */
export function syllables(form: string, lang: Language): string[] {
  const out: string[] = [];
  let i = 0;
  while (i < form.length) {
    let syl = form.slice(i, i + 2);
    i += 2;
    if (i === form.length - 1 && lang.consonants.includes(form[i])) {
      syl += form[i];
      i += 1;
    }
    out.push(syl);
  }
  return out;
}

function table(lang: Language, field: string): Map<string, string> {
  return new Map((lang.phonology.symbols as Record<string, string>[]).map(
    (s) => [s.letter, s[field]]));
}

/** A word in the IPA, stressed on its first syllable, its syllables divided by dots. */
export function ipa(form: string, lang: Language): string {
  const t = table(lang, "ipa");
  return STRESS + syllables(form, lang).map((syl) =>
    Array.from(syl, (c) => t.get(c)).join("")).join(".");
}

/** A word as espeak-ng phoneme input, its first syllable stressed. */
export function espeak(form: string, lang: Language): string {
  const t = table(lang, "espeak");
  return "'" + Array.from(form, (c) => t.get(c)).join("");
}

function speakable(w: Word, lang: Language): boolean {
  return w.kind !== "payload" && w.form !== "" &&
    Array.from(w.form).every((c) => lang.codePoints.has(c));
}

/** Each line of a parsed message as it is spoken. */
export function spoken(analysis: Speakable, lang: Language): SpokenLine[] {
  if (analysis.message === null) return [];
  const registers = new Map<number, string | null>();
  const moves = analysis.message.moves;
  for (let i = 0; i < Math.min(moves.length, analysis.social.length); i++) {
    registers.set(moves[i].index - 1, analysis.social[i]["register"] ?? null);
  }
  const lines: [string, Word[]][] = [["flat", analysis.message.envelope.words]];
  analysis.message.lines.forEach((words, i) => {
    const code = registers.get(i) || "R2";
    lines.push([lang.registers.get(code).settings.prosody, words]);
  });
  return lines.map(([prosody, words]) => {
    const said: string[] = [];
    const phonemes: string[] = [];
    for (const w of words) {
      if (speakable(w, lang)) {
        said.push(ipa(w.form, lang));
        phonemes.push(espeak(w.form, lang));
      } else {
        said.push(EMBEDDED);
        phonemes.push("_:");
      }
    }
    return { prosody, ipa: said.join(" "), espeak: "[[" + phonemes.join(" ") + "]]" };
  });
}
