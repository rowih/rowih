// Word formation (specification/lexicon.md#word-formation): the meaning a derivation or a
// compound has from its parts, as the canonical implementation's `formation` module
// computes it, statement for statement. A suffix is a function of the stem it follows; a
// compound's first stem is its head and each further stem a modifier of everything before
// it; wherever the form built so far is a word the release lists, the listed entry
// governs (`inv.word-formation`).

import { type Item, type Language, type Source } from "./data.ts";
import { segment } from "./lexer.ts";

export type Meaning = Record<string, any>;

const PREDICATE_SORTS = ["s.sort.event", "s.sort.state", "s.sort.process"];
const CONNECTIVE = "g.situations-and-contents.connective.";
const MODIFIER_ROLES = ["undergoer", "content"];
const KEEPS_ROLES = ["result", "privative", "reversative", "repetitive"];
// suffixes whose formation keeps its base's sort as well: the honorific, which adds only
// the deference the ceremonial register shows (specification/lexicon.md#registers)
const KEEPS_BASE = ["honorific"];
// suffixes whose formation adds the actor that brings its base about and keeps the base's
// other roles: the causative of lexicon 1.0
const ADDS_ACTOR = ["causative"];
// suffixes whose formation has one role, its base's undergoer: the potential
const TAKES_UNDERGOER = ["potential"];
const ROLE_OF: Record<string, string> = { agent: "actor", undergoer: "undergoer" };

function copyArguments(args: Source[]): Source[] {
  return args.map((a) => ({ ...a }));
}

export function category(meaning: Meaning): string {
  if (meaning.connective) return "connective";
  return PREDICATE_SORTS.includes(meaning.sort) ? "predicate" : "nominal";
}

/** The meaning of a word the release lists: what its entry states. */
export function ofEntry(entry: Source): Meaning {
  return {
    entry: entry["machine identifier"], sort: entry.sort,
    arguments: copyArguments(entry["argument structure"]), definition: entry.definition,
  };
}

/** The meaning of a closed-class member as the base of a formation. */
export function ofMember(identifier: string, name: string): Meaning {
  return {
    entry: identifier, sort: null, arguments: [], definition: name,
    connective: identifier.startsWith(CONNECTIVE),
  };
}

/** The formation of a suffix, by its entry, on `base`; null where the suffix does not
 * take a stem of the base's kind or names a role the base lacks. */
export function derive(base: Meaning | null, suffix: Source): Meaning | null {
  if (base === null || category(base) !== suffix.base) return null;
  const key: string = suffix.key;
  let sort = suffix.sort;
  let args: Source[];
  if (key in ROLE_OF) {
    const role = (base.arguments as Source[]).find((a) => a.role === ROLE_OF[key]);
    if (role === undefined) return null;
    sort = role.sort;
    args = [];
  } else if (KEEPS_BASE.includes(key)) {
    sort = base.sort;
    args = copyArguments(base.arguments);
  } else if (KEEPS_ROLES.includes(key)) {
    args = copyArguments(base.arguments);
  } else if (ADDS_ACTOR.includes(key)) {
    args = [...copyArguments(suffix["argument structure"]),
      ...copyArguments((base.arguments as Source[]).filter((a) => a.role !== "actor"))];
  } else if (TAKES_UNDERGOER.includes(key)) {
    const role = (base.arguments as Source[]).find((a) => a.role === "undergoer");
    if (role === undefined) return null;
    args = [{ ...role }];
  } else {
    args = copyArguments(suffix["argument structure"]);
  }
  return {
    mechanism: key, parts: [base, suffix["machine identifier"]], sort, arguments: args,
    definition: (suffix.definition as string).split("the base").join(
      "[" + base.definition + "]"),
  };
}

/** The compound of `head` and `modifier`; null where the head is a predicate with no
 * role a modifier takes, or a connective. */
export function compound(head: Meaning | null, modifier: Meaning | null): Meaning | null {
  if (head === null || modifier === null) return null;
  const kind = category(head);
  let args: Source[];
  let definition: string;
  if (kind === "predicate") {
    const role = MODIFIER_ROLES.find((r) => (head.arguments as Source[]).some((a) => a.role === r));
    if (role === undefined) return null;
    args = copyArguments((head.arguments as Source[]).filter((a) => a.role !== role));
    definition = "[" + head.definition + "], with [" + modifier.definition + "] as its " + role;
  } else if (kind === "nominal") {
    args = [];
    definition = "[" + head.definition + "], bearing on [" + modifier.definition + "]";
  } else {
    return null;
  }
  return { mechanism: "compound", parts: [head, modifier], sort: head.sort, arguments: args,
    definition };
}

/** The meaning of a content word from its morphemes, as the lexer segments them; null
 * where a step of its formation has no meaning. */
export function compose(morphemes: (Item | "linker")[], lang: Language): Meaning | null {
  const listed = (form: string, meaning: Meaning | null): Meaning | null => {
    const item = lang.byForm.get(form);
    if (item !== undefined && (item.kind === "root" || item.kind === "derivation")) {
      return ofEntry(lang.entries.get(item.identifier));
    }
    return meaning;
  };
  const stemStart = (m: Item): Meaning => m.kind === "member" ? ofMember(m.identifier, m.name) :
    ofEntry(lang.entries.get(m.identifier));
  const stems: Item[][] = [];
  let current: Item[] = [];
  for (const m of morphemes) {
    if (m === "linker") {
      stems.push(current);
      current = [];
    } else {
      current.push(m);
    }
  }
  stems.push(current);
  const stemMeaning = (stem: Item[]): Meaning | null => {
    let meaning: Meaning | null = null;
    let form = "";
    stem.forEach((m, i) => {
      form += m.form;
      meaning = i === 0 ? stemStart(m) : derive(meaning, lang.entries.get(m.identifier));
      meaning = listed(form, meaning);
    });
    return meaning;
  };
  let meaning = stemMeaning(stems[0]);
  let form = stems[0].map((m) => m.form).join("");
  for (const stem of stems.slice(1)) {
    meaning = compound(meaning, stemMeaning(stem));
    form += "i" + stem.map((m) => m.form).join("");
    meaning = listed(form, meaning);
  }
  return meaning;
}

/** The sort of a word part of a tree: its entry's, or for a formation the release does
 * not list, the sort its parts give; null for an unknown word. */
export function wordSort(p: Record<string, any>, lang: Language): string | null {
  if (p.entry !== null && p.entry !== undefined && p.entry !== "") {
    const entry = lang.entries.get(p.entry);
    return entry !== undefined ? entry.sort : null;
  }
  if (p.status !== "formation") return null;
  const morphemes = segment(p.form, lang);
  const meaning = morphemes !== null ? compose(morphemes, lang) : null;
  return meaning !== null ? meaning.sort : null;
}

/** A word part with an irregular word written as its regular form, the formation of the
 * root and suffix its entry is formed from, so that the word and the formation it stands
 * for have one normal form. */
export function regularWord(p: Record<string, any>, lang: Language): Record<string, any> {
  const entry = p.entry !== null && p.entry !== undefined && p.entry !== ""
    ? lang.entries.get(p.entry)
    : undefined;
  if (entry === undefined || !("irregular" in entry)) return p;
  return { ...p, form: entry.irregular["regular form"], entry: null, status: "formation" };
}
