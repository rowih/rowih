// Reading the canonical sources from a checkout, for Node: `language/` and `lexicon/`
// under the repository root, each release entry from `lexicon/roots/`,
// `lexicon/formation/`, `lexicon/idioms/` or `lexicon/senses/`, and each idiom's trees
// from `lexicon/semantic/`, as the canonical implementation reads them.

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { buildLanguage, CURRENT, type Language, type Releases, type Source } from "./data.ts";
import { compareVersions, ordered } from "./versions.ts";

/** The repository root: two directories above this file. */
export const REPOSITORY = join(dirname(fileURLToPath(import.meta.url)), "..", "..");

function read(...parts: string[]): Source {
  return JSON.parse(readFileSync(join(...parts), "utf-8"));
}

const loaded = new Map<string, Language>();

/** Release `version` of the lexicon from the checkout at `root`, read under language
 * release `language` (the grammar's own where it is null) with the named `dialects`, each
 * (number, version), loaded once; it carries the loader of the other releases. */
export function loadLanguage(version: string = CURRENT, root: string = REPOSITORY,
  language: string | null = null, dialects: [number, string][] = []): Language {
  const key = [root, version, language ?? "", JSON.stringify(dialects)].join("\u0000");
  const cached = loaded.get(key);
  if (cached !== undefined) return cached;
  const release = read(root, "lexicon", "releases", version + ".json");
  const entries: Record<string, Source> = {};
  const semantic: Record<string, Source> = {};
  for (const ident of release.entries as string[]) {
    const dir = ["roots", "formation", "idioms", "senses"].find((d) =>
      existsSync(join(root, "lexicon", d, ident + ".json")));
    if (dir === undefined) throw new Error("the release names an absent entry: " + ident);
    entries[ident] = read(root, "lexicon", dir, ident + ".json");
    if (dir === "idioms" && existsSync(join(root, "lexicon", "semantic", ident + ".json"))) {
      semantic[ident] = read(root, "lexicon", "semantic", ident + ".json");
    }
  }
  // the fields each release up to this one states for entries an earlier release wrote,
  // and the collocations and examples the corpus gives every entry, read over the entries
  // in release order; the usage of an entry outside the release, a dialect's compressed
  // form, waits for the dialect to be named
  const usage: Record<string, Source> = {};
  for (const directory of ["fields", "usage"]) {
    const statedDir = join(root, "lexicon", directory);
    if (!existsSync(statedDir)) continue;
    const stated = ordered(readdirSync(statedDir).filter((n) => n.endsWith(".json"))
      .map((n) => n.slice(0, -5))).filter((v) => compareVersions(v, version) <= 0);
    for (const v of stated) {
      for (const [ident, fields] of Object.entries(read(statedDir, v + ".json"))) {
        if (entries[ident] !== undefined) entries[ident] = { ...entries[ident], ...(fields as Source) };
        else if (directory === "usage") usage[ident] = { ...usage[ident], ...(fields as Source) };
      }
    }
  }
  const releases = nodeReleases(root);
  const lang = buildLanguage({
    grammar: read(root, "language", "grammar.json"),
    phonology: read(root, "language", "phonology.json"),
    writing: read(root, "language", "writing.json"),
    protocol: read(root, "language", "protocol.json"),
    semantics: read(root, "language", "semantics.json"),
    release,
    entries,
    semantic,
    usage,
    registers: Object.fromEntries(["R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7"].map(
      (code) => [code, read(root, "lexicon", "registers", code.toLowerCase() + ".json")])),
    dialects: [...dialects].sort((a, b) => a[0] - b[0] || compareVersions(a[1], b[1]))
      .map(([n, v]) => releases.dialectRelease(n, v)),
  }, version, language);
  lang.releases = releases;
  loaded.set(key, lang);
  return lang;
}

const releasesAt = new Map<string, Releases>();

/** The releases of the checkout at `root`, as the canonical implementation's `releases`
 * and `data` read them
 * (specification/conformance.md#what-a-conformant-implementation-must-do). */
export function nodeReleases(root: string = REPOSITORY): Releases {
  const cached = releasesAt.get(root);
  if (cached !== undefined) return cached;
  const dialects = new Map<string, Source>();
  const jargon = join(root, "lexicon", "jargon");
  for (const name of readdirSync(jargon).sort()) {
    if (!statSync(join(jargon, name)).isDirectory()) continue;
    for (const file of readdirSync(join(jargon, name)).sort()) {
      if (!file.endsWith(".json")) continue;
      const d = read(jargon, name, file);
      dialects.set(d.number + " " + d.version, d);
    }
  }
  const languageReleases = read(root, "language", "releases.json");
  const lexicons = ordered(readdirSync(join(root, "lexicon", "releases"))
    .filter((f) => f.endsWith(".json")).map((f) => f.slice(0, -5)));
  const record = (v: string): Source =>
    (languageReleases.language as Source[]).find((r) => r.language === v);
  const releases: Releases = {
    load: (version, language, named) => loadLanguage(version, root, language, named),
    dialectRelease: (number, version) => dialects.get(number + " " + version),
    languageReleases,
    reads() {
      const grammar = read(root, "language", "grammar.json");
      const protocol = read(root, "language", "protocol.json");
      const language = ordered(record(grammar.version).reads as string[]);
      const least = language.map((v) => (record(v)["least lexicon"] ?? v) as string)
        .sort(compareVersions)[0];
      return {
        language,
        lexicon: lexicons.filter((v) => compareVersions(least, v) <= 0),
        protocol: ((languageReleases.protocol as Source[]).find(
          (p) => p.protocol === protocol.version).reads as string[]),
        dialects: [...dialects.values()].map((d) => [d.number, d.version] as [number, string])
          .sort((a, b) => a[0] - b[0] || compareVersions(a[1], b[1])),
      };
    },
  };
  releasesAt.set(root, releases);
  return releases;
}
