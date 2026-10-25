// Dialects (specification/dialects.md#compressed-forms), as the canonical
// implementation's `dialects` reads them: the digest of a release's canonical text, and a
// compressed form written in the normal form as the term it compresses.

import { type Language, type Source } from "./data.ts";
import { hex, sha256Text } from "./sha256.ts";
import { type Tree } from "./tree.ts";

export const DIGEST_WIDTH = 9;

export function canonicalText(release: Source): string {
  const lines = ["rowih dialect " + release.number + " " + release.dialect + " " +
    release.version + " lexicon " + release["formed from lexicon"]];
  for (const t of release.terms) {
    lines.push("term " + t["orthographic form"] + " " + (t.version.deprecated ?? "-"));
  }
  for (const f of release.forms ?? []) {
    lines.push("form " + f["orthographic form"] + " " + f.expansion.form + " " +
      (f.version.deprecated ?? "-"));
  }
  return lines.join("\n") + "\n";
}

/** The release's digest, nine numerals. */
export function digest(release: Source): string {
  const value = BigInt("0x" + hex(sha256Text(canonicalText(release))));
  return (value % 10n ** BigInt(DIGEST_WIDTH)).toString().padStart(DIGEST_WIDTH, "0");
}

/** A word part with a compressed form of a named dialect written as the term it
 * compresses: the entry the term's form spells where the lexicon lists it, and otherwise
 * the formation, read by its composition. */
export function expansionWord(p: Tree, lang: Language): Tree {
  const record = p.entry ? lang.dialectForms.get(p.entry as string) : undefined;
  if (record === undefined) return p;
  const form = record.expansion.form as string;
  const item = lang.byForm.get(form);
  if (item !== undefined && (item.kind === "root" || item.kind === "derivation")) {
    return { kind: "word", form, entry: item.identifier, status: "known" };
  }
  return { kind: "word", form, entry: null, status: "formation" };
}

/** Every compressed form within `node` written as its expansion, in place. */
export function expand(node: unknown, lang: Language): void {
  if (lang.dialectForms.size === 0) return;
  if (Array.isArray(node)) {
    node.forEach((v, i) => {
      if (v !== null && typeof v === "object" && !Array.isArray(v) && v.kind === "word") {
        node[i] = expansionWord(v as Tree, lang);
      } else expand(v, lang);
    });
  } else if (node !== null && typeof node === "object") {
    const record = node as Record<string, unknown>;
    for (const [k, v] of Object.entries(record)) {
      if (v !== null && typeof v === "object" && !Array.isArray(v) &&
        (v as Tree).kind === "word") {
        record[k] = expansionWord(v as Tree, lang);
      } else expand(v, lang);
    }
  }
}
