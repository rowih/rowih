// Write the collocations and examples of every entry the TypeScript reader holds, as one
// JSON object by identifier, for the comparison of the two readers of the usage
// (specification/lexicon.md#entries-and-their-identifiers): `node
// --experimental-strip-types tools/usage.ts VERSION [NUMBER:VERSION ...]`, the further
// arguments the dialects to name.

import { loadLanguage } from "../src/node.ts";

const [version, ...named] = process.argv.slice(2);
const dialects = named.map((d): [number, string] => {
  const [number, release] = d.split(":");
  return [Number(number), release];
});
const lang = loadLanguage(version, undefined, null, dialects);
const out: Record<string, unknown> = {};
for (const [ident, entry] of lang.entries) {
  out[ident] = { collocations: entry.collocations ?? null, examples: entry.examples ?? null };
}
process.stdout.write(JSON.stringify(out) + "\n");
