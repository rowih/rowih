// The canonical sources and the indexes every stage uses: the grammar, the phonology,
// the protocol schema, the semantic schema and a release of the lexicon. The sources are
// passed in as parsed JSON, so that a page bundles them and Node reads them from disk
// (`node.ts`); nothing here touches a platform API.

// The canonical sources are JSON documents whose shapes the Python implementation and
// `language/*.json` define; they are read here field by field.
import { compareVersions } from "./versions.ts";

export type Source = any;

export interface Sources {
  grammar: Source;
  phonology: Source;
  /** The writing-system specification (specification/writing-system.md#the-components).
   * */
  writing: Source;
  protocol: Source;
  semantics: Source;
  release: Source;
  /** Each entry of the release by its identifier, from `lexicon/roots/`,
   * `lexicon/formation/`, `lexicon/idioms/` or `lexicon/senses/`. */
  entries: Record<string, Source>;
  /** Each idiom's literal structure and expansion as trees, from `lexicon/semantic/`. */
  semantic: Record<string, Source>;
  /** The eight registers' records, by code, from `lexicon/registers/`
   * (specification/lexicon.md#registers). */
  registers: Record<string, Source>;
  /** The releases of the dialects a message names, from `lexicon/jargon/`
   * (specification/dialects.md#compressed-forms). */
  dialects?: Source[];
  /** The collocations and examples the corpus gives the entries of the named dialects,
   * from `lexicon/usage/`. */
  usage?: Record<string, Source>;
}

/** What a reader holds besides the release it was built from
 * (specification/conformance.md#what-a-conformant-implementation-must-do): the language
 * built for a lexicon release, a language release and named dialects; the releases this
 * implementation reads; the dialect releases by number and version; and the record of the
 * language releases. */
export interface Releases {
  load(version: string, language: string, dialects: [number, string][]): Language;
  reads(): { language: string[]; lexicon: string[]; protocol: string[];
    dialects: [number, string][] };
  dialectRelease(number: number, version: string): Source | undefined;
  languageReleases: Source;
}

export const REGISTER_CLASS = "g.ambiguity-and-figures.register";
export const DEFAULT_REGISTER = "R2";

/** A word of the lexicon or a bound morpheme, with what it spells. */
export class Item {
  kind: string; // member, structural, move-check, root, derivation, suffix, act, idiom,
  //               sense, dialect
  identifier: string;
  form: string;
  gloss: string;
  classId: string;
  name: string;
  protected: boolean;
  criticalCode: number;
  sort: string;
  category: string;

  constructor(kind: string, identifier: string, form: string, gloss: string,
    fields: Partial<Pick<Item, "classId" | "name" | "protected" | "criticalCode" | "sort" |
      "category">> = {}) {
    this.kind = kind;
    this.identifier = identifier;
    this.form = form;
    this.gloss = gloss;
    this.classId = fields.classId ?? "";
    this.name = fields.name ?? "";
    this.protected = fields.protected ?? false;
    this.criticalCode = fields.criticalCode ?? 0;
    this.sort = fields.sort ?? "";
    this.category = fields.category ?? "";
  }
}

export class Language {
  version: string;
  grammar: Source;
  phonology: Source;
  writing: Source;
  protocol: Source;
  semantics: Source;
  release: Source;
  entries = new Map<string, Source>();
  items = new Map<string, Item>();
  byForm = new Map<string, Item>();
  suffixes = new Map<string, Item>();
  classes = new Map<string, Source>();
  memberClass = new Map<string, string>();
  moveCheckForms: string[] = [];
  moveCheckValue = new Map<string, number>();
  modulus = 0;
  letters = "";
  consonants = "";
  vowels = "";
  codePoints = new Map<string, string>(); // letter -> code point
  lettersOf = new Map<string, string>(); // code point -> letter
  onsetLength = new Map<string, number>();
  /** A first syllable that fixes a length its onset alone does not, the long root's
   * (specification/sounds-and-words.md#how-a-words-opening-fixes-its-length). */
  syllableLength = new Map<string, number>();
  /** The idioms larger than a word, in the order of the release
   * (specification/lexicon.md#conventional-expressions-and-idioms), each with its trees,
   * and each extragrammatical one by its words. */
  idioms: string[] = [];
  semantic = new Map<string, Source>();
  extragrammatical = new Map<string, string>(); // word identifiers joined by "," -> entry
  /** The eight registers' records by code, and the code of each register member. */
  registers = new Map<string, Source>();
  registerCode = new Map<string, string>();
  /** The conventional figurative senses of each root, in the order of the release
   * (specification/lexicon.md#figurative-senses-and-conceptual-mappings); a sense shares
   * its root's form, so it has no place in `byForm`. */
  senses = new Map<string, string[]>(); // root identifier -> sense identifiers
  /** The language release a message is read under, every word introduced after it being
   * unknown; the dialects it names, each (number, version); and the compressed forms of
   * those dialects by identifier
   * (specification/conformance.md#what-a-conformant-implementation-must-do). */
  language = "";
  dialects: [number, string][] = [];
  dialectForms = new Map<string, Source>();
  /** The other releases this reader holds, where a loader supplies them. */
  releases: Releases | null = null;

  constructor(version: string, sources: Sources) {
    this.version = version;
    this.grammar = sources.grammar;
    this.phonology = sources.phonology;
    this.writing = sources.writing;
    this.protocol = sources.protocol;
    this.semantics = sources.semantics;
    this.release = sources.release;
  }

  member(identifier: string): Item {
    return this.item(identifier);
  }

  item(identifier: string): Item {
    const item = this.items.get(identifier);
    if (item === undefined) throw new Error("KeyError: " + identifier);
    return item;
  }

  formOf(identifier: string): string {
    return this.item(identifier).form;
  }

  inClass(form: string, classId: string): boolean {
    const item = this.byForm.get(form);
    return item !== undefined && item.classId === classId;
  }

  /** The length of the morpheme that opens at `i`: its first syllable's where the
   * phonology names the syllable, its onset's otherwise, undefined where neither fixes
   * one (`language/phonology.json`, word shapes). */
  lengthAt(form: string, i = 0): number | undefined {
    return this.syllableLength.get(form.slice(i, i + 2)) ?? this.onsetLength.get(form.slice(i, i + 1));
  }
}

export function short(identifier: string): string {
  const i = identifier.lastIndexOf(".");
  return i < 0 ? identifier : identifier.slice(i + 1);
}

export const CURRENT = "1.0";

/** Build release `version` of the lexicon from its sources, read under language release
 * `language` (the grammar's own where it is null) with the dialects `sources` carries. */
export function buildLanguage(sources: Sources, version: string = CURRENT,
  language: string | null = null): Language {
  const grammar = sources.grammar;
  const lang = new Language(version, sources);
  lang.language = language ?? grammar.version;
  const within = (introduced: string | undefined) =>
    compareVersions(introduced ?? "0.1", lang.language) <= 0;
  // a release's codes are the first of the list, as many as it states
  // (specification/protocol.md#the-move-check-word: the list only grows, each form
  // appended at its end)
  const count = lang.release["critical forms"] ?? grammar["critical forms"].length;
  const critical = new Map<string, number>();
  (grammar["critical forms"] as string[]).slice(0, count).forEach(
    (ident, i) => critical.set(ident, i + 1));
  for (const cls of grammar.classes) {
    lang.classes.set(cls.identifier, cls);
    for (const m of cls.members) {
      const item = new Item("member", m.identifier, m.form, m.gloss, {
        classId: cls.identifier, name: m.name, protected: cls.protected,
        criticalCode: critical.get(m.identifier) ?? 0,
      });
      lang.items.set(item.identifier, item);
      lang.memberClass.set(item.identifier, cls.identifier);
      if (within(m.introduced)) lang.byForm.set(item.form, item);
    }
  }
  for (const s of grammar["structural words"]) {
    const item = new Item("structural", s.identifier, s.form, s.gloss, {
      name: s.name, criticalCode: critical.get(s.identifier) ?? 0,
    });
    lang.items.set(item.identifier, item);
    if (within(s.introduced)) lang.byForm.set(item.form, item);
  }
  // a release's modulus is its record's, and its forms the first of the list, as many as
  // the modulus: the list only grows, each form appended at its end
  const mc = grammar["move check word"];
  lang.modulus = lang.release["move check modulus"] ?? mc.modulus;
  lang.moveCheckForms = (mc.forms as string[]).slice(0, lang.modulus);
  lang.moveCheckForms.forEach((form, value) => {
    const item = new Item("move-check", "g.move-check." + value, form, "CHK" + value);
    lang.items.set(item.identifier, item);
    lang.byForm.set(form, item);
    lang.moveCheckValue.set(form, value);
  });
  for (const ident of lang.release.entries as string[]) {
    const e = sources.entries[ident];
    if (e === undefined) throw new Error("the release names an absent entry: " + ident);
    lang.entries.set(ident, e);
    const cat: string = e["grammatical category"];
    const kinds: Record<string, string> = {
      "derivational suffix": "suffix", "derivation": "derivation", "compound": "derivation",
      "act word": "act", "idiom": "idiom", "conventional sense": "sense",
    };
    const kind = kinds[cat] ?? "root";
    const gloss = (e.key as string).toUpperCase().replace(/ /g, "-");
    const item = new Item(kind, ident, e["orthographic form"],
      kind === "act" ? "ACT-" + gloss : gloss,
      { name: e.key, sort: e.sort, category: cat, protected: kind === "act",
        criticalCode: critical.get(ident) ?? 0 });
    lang.items.set(ident, item);
    if (kind === "suffix") lang.suffixes.set(item.form, item);
    else if (kind === "idiom") lang.idioms.push(ident);
    else if (kind === "sense") {
      const of = e["sense of"] as string;
      lang.senses.set(of, [...(lang.senses.get(of) ?? []), ident]);
    } else lang.byForm.set(item.form, item);
  }
  for (const [code, record] of Object.entries(sources.registers)) {
    lang.registers.set(code, record);
    if (record.member !== undefined) lang.registerCode.set(record.member as string, code);
  }
  for (const ident of lang.idioms) {
    const trees = sources.semantic[ident];
    if (trees === undefined) throw new Error("an idiom without its trees: " + ident);
    lang.semantic.set(ident, trees);
    const literal = trees["literal structure"];
    if (Array.isArray(literal)) lang.extragrammatical.set((literal as string[]).join(","), ident);
  }
  const phon = lang.phonology;
  for (const s of phon.symbols) {
    lang.letters += s.letter;
    if (s.kind === "consonant") lang.consonants += s.letter;
    if (s.kind === "vowel") lang.vowels += s.letter;
    const cp = String.fromCodePoint(parseInt((s["code point"] as string).slice(2), 16));
    lang.codePoints.set(s.letter, cp);
    lang.lettersOf.set(cp, s.letter);
  }
  for (const [length, onsets] of Object.entries(phon["word shapes"].onsets)) {
    for (const o of onsets as string[]) lang.onsetLength.set(o, parseInt(length, 10));
  }
  for (const [length, syllables] of Object.entries(phon["word shapes"]["first syllables"] ?? {})) {
    for (const s of syllables as string[]) lang.syllableLength.set(s, parseInt(length, 10));
  }
  for (const release of sources.dialects ?? []) {
    lang.dialects.push([release.number, release.version]);
    // the compressed forms of a named dialect, each an entry of the dialect read where
    // the lexicon's entries are read (specification/dialects.md#compressed-forms)
    for (const f of release.forms ?? []) {
      const item = new Item("dialect", f["machine identifier"], f["orthographic form"],
        (f.key as string).toUpperCase().replace(/ /g, "-"),
        { name: f.key, sort: f.sort, category: "dialect form" });
      const record = { ...f, dialect: release.number, "dialect name": release.dialect,
        release: release.version, ...sources.usage?.[f["machine identifier"]] };
      lang.items.set(item.identifier, item);
      lang.byForm.set(item.form, item);
      lang.dialectForms.set(item.identifier, record);
      lang.entries.set(item.identifier, record);
    }
  }
  return lang;
}
