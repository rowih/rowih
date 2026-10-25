// Write the record of each text in a JSON array of strings, one line each, for the
// comparison of the two implementations: `node --experimental-strip-types
// tools/records.ts INPUTS.json [--every-view]`, the flag adding the compact,
// handwritten and high-contrast SVG and the display PNG's SHA-256.

import { readFileSync } from "node:fs";

import { loadLanguage } from "../src/node.ts";
import { recordLine } from "../src/record.ts";

const texts = JSON.parse(readFileSync(process.argv[2], "utf-8")) as string[];
const lang = loadLanguage();
const everyView = process.argv.includes("--every-view");
for (const text of texts) process.stdout.write(recordLine(text, lang, everyView) + "\n");
