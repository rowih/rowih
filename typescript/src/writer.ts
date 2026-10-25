// Spelling: words by identifier, numbers with their check words, and moves with their
// counts and move check words, as the normal form's serialisation writes them.

import { type Item, type Language } from "./data.ts";
import { encodePayload } from "./lexer.ts";
import { moveCheck, numberCheck } from "./parser.ts";
import { DIGITS } from "./syntax.ts";
import { zfill } from "./pyformat.ts";

const SYMBOL_NUMERAL = new Map<string, string>([
  ...DIGITS.map((d, i): [string, string] => [String(i), d]),
  [".", "decimal-point"], ["-", "negative"], ["/", "ratio"], ["e", "exponent"],
  ["~", "interval"],
]);

export class Writer {
  lang: Language;

  constructor(lang: Language) {
    this.lang = lang;
  }

  /** The form of a member, a structural word or an entry; `identifier` may be a member's
   * identifier, `g.structure.<name>`, an `lx.` identifier or a root's key. */
  w(identifier: string): string {
    const item = this.lang.items.get(identifier);
    if (item !== undefined) return item.form;
    for (const it of this.lang.items.values()) {
      if ((it.kind === "root" || it.kind === "derivation") && it.name === identifier) {
        return it.form;
      }
    }
    throw new Error("KeyError: " + identifier);
  }

  number(text: string, width: number | null = null): string[] {
    const t = width !== null ? zfill(text, width) : text;
    const forms: string[] = [];
    let digits = "";
    for (const ch of t) {
      const name = SYMBOL_NUMERAL.get(ch);
      if (name === undefined) throw new Error("KeyError: " + ch);
      forms.push(this.w("g.numbers.numeral." + name));
      if (ch >= "0" && ch <= "9") digits += ch;
    }
    forms.push(this.w("g.numbers.check-word.check-" + numberCheck(digits)));
    return forms;
  }

  name(n: number): string[] {
    return this.number(String(n), this.lang.protocol["name width"]);
  }

  payload(data: Uint8Array): string[] {
    return [...this.number(String(data.length)), encodePayload(data)];
  }

  /** WORD-COUNT, the count, the body and the move check word. */
  move(body: string[]): string[] {
    const items = body.map((f) => ({ item: (this.lang.byForm.get(f) ?? null) as Item | null }));
    const chk = moveCheck(items, this.lang);
    return [this.w("g.message.word-count.word-count"), ...this.number(String(body.length + 1)),
      ...body, this.lang.moveCheckForms[chk]];
  }
}
