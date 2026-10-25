// Write what `version` gives and what `lookup` gives for each term, as one JSON object,
// for the comparison of the two implementations' interfaces:
// `node --experimental-strip-types tools/interface.ts TERMS.json`.

import { readFileSync } from "node:fs";

import { lookup, version } from "../src/api.ts";
import { loadLanguage } from "../src/node.ts";

const terms = JSON.parse(readFileSync(process.argv[2], "utf-8")) as string[];
const lang = loadLanguage();
const lookups: Record<string, unknown[]> = {};
for (const term of terms) {
  lookups[term] = lookup(term, lang).map((it) => ({
    kind: it.kind, identifier: it.identifier, form: it.form, gloss: it.gloss,
    class: it.classId, name: it.name, sort: it.sort, category: it.category,
  }));
}
process.stdout.write(JSON.stringify({ version: version(lang), lookups }) + "\n");
