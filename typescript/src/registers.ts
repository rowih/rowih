// Registers (specification/lexicon.md#registers), as the canonical implementation's
// `registers` module states them for reading: the register a move states, the precision
// bound two registers carry by default, the register-marked words the normal form writes
// as their bases, and what a realisation keeps of its head.

import { DEFAULT_REGISTER, type Language, REGISTER_CLASS, type Source } from "./data.ts";
import { segment } from "./lexer.ts";
import { get, type Tree, truthy } from "./tree.ts";

/** The two registers precision-bound by default
 * (specification/grammar.md#precision-bound-moves). */
export const BOUND = [REGISTER_CLASS + ".protocol", REGISTER_CLASS + ".formal"];
const HONORIFIC = "honorific";
/** The head's records of the social and textual component, which the normal form sets
 * aside. */
export const SOCIAL_KEYS = ["act", "losses", "politeness", "diction", "register"];

/** The register of a move: the one its head states, or the standard register. */
export function code(t: Tree, lang: Language): string {
  const member = get(t, "register") as string | null;
  return truthy(member) ? lang.registerCode.get(member!)! : DEFAULT_REGISTER;
}

export function record(t: Tree, lang: Language): Source {
  return lang.registers.get(code(t, lang));
}

export function boundByRegister(t: Tree): boolean {
  return BOUND.includes(get(t, "register") as string);
}

/** Whether an entry is register-marked: a synonym, or the honorific suffix. */
export function marked(entry: Source | undefined): boolean {
  if (entry === undefined) return false;
  return "synonym of" in entry || (entry.key === HONORIFIC &&
    entry["grammatical category"] === "derivational suffix");
}

/** The normal form `n` of move `t` with the register, politeness word and diction `t`
 * states written back in its head, and the losses they incur. */
export function carry(t: Tree, n: Tree): Tree {
  const out: Tree = { ...n };
  const incurred: string[] = [];
  if (truthy(get(t, "register"))) {
    out.register = t.register;
    incurred.push("register");
  }
  for (const [key, loss] of [["politeness", "relation between participants"],
    ["diction", "diction"]]) {
    if (truthy(get(t, key))) {
      out[key] = t[key];
      incurred.push(loss);
    }
  }
  const losses = ((get(t, "losses") ?? []) as string[]).filter((x) =>
    incurred.includes(x.slice(x.lastIndexOf(".") + 1).split("-").join(" ")));
  if (losses.length) out.losses = losses;
  return out;
}

/** A word part with every register-marked morpheme written as its base. */
export function baseWord(p: Tree, lang: Language): Tree {
  const entry = truthy(get(p, "entry")) ? lang.entries.get(p.entry) : undefined;
  if (entry !== undefined && "synonym of" in entry) {
    const base: string = entry["synonym of"];
    return { ...p, form: lang.item(base).form, entry: base, status: "known" };
  }
  if (get(p, "status") !== "formation") return p;
  const morphemes = segment(p.form, lang);
  if (morphemes === null) return p;
  let form = "";
  let changed = false;
  for (const m of morphemes) {
    if (m === "linker") {
      form += "i";
      continue;
    }
    const e = lang.entries.get(m.identifier);
    if (e !== undefined && "synonym of" in e) {
      form += lang.item(e["synonym of"]).form;
      changed = true;
    } else if (e !== undefined && marked(e)) {
      changed = true;
    } else {
      form += m.form;
    }
  }
  if (!changed) return p;
  const item = lang.byForm.get(form);
  if (item !== undefined && (item.kind === "root" || item.kind === "derivation")) {
    return { kind: "word", form, entry: item.identifier, status: "known" };
  }
  return { kind: "word", form, entry: null, status: "formation" };
}

function* walk(node: unknown): Generator<Tree> {
  if (Array.isArray(node)) {
    for (const x of node) yield* walk(x);
  } else if (node !== null && typeof node === "object") {
    yield node as Tree;
    for (const v of Object.values(node)) yield* walk(v);
  }
}

/** The register-marked words a move writes, in the order it writes them. */
export function markedWords(t: Tree, lang: Language): string[] {
  const out: string[] = [];
  for (const node of walk(get(t, "constituents") ?? [])) {
    if (node.kind !== "word") continue;
    const entry = truthy(get(node, "entry")) ? lang.entries.get(node.entry) : undefined;
    if (entry !== undefined && marked(entry)) {
      out.push(node.form);
    } else if (node.status === "formation") {
      const morphemes = segment(node.form, lang) ?? [];
      if (morphemes.some((m) => m !== "linker" && marked(lang.entries.get(m.identifier)))) {
        out.push(node.form);
      }
    }
  }
  return out;
}
