// Version identifiers (specification/protocol.md#versions-and-features), as the canonical
// implementation's `versions` reads them: two integers, major and minor, with the decimal
// point between them and neither with a leading zero, compared as pairs of integers, so
// that 0.10 follows 0.9 and is not 0.1.

const FORM = /^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$/;

export function parseVersion(text: string): [number, number] | null {
  const m = FORM.exec(text);
  return m === null ? null : [Number(m[1]), Number(m[2])];
}

export function wellFormed(text: string): boolean {
  return parseVersion(text) !== null;
}

export function versionKey(text: string): [number, number] {
  const pair = parseVersion(text);
  if (pair === null) throw new Error("not a version: " + text);
  return pair;
}

/** Negative, zero or positive as `a` comes before, with or after `b`. */
export function compareVersions(a: string, b: string): number {
  const [x, y] = [versionKey(a), versionKey(b)];
  return x[0] !== y[0] ? x[0] - y[0] : x[1] - y[1];
}

export function ordered(texts: Iterable<string>): string[] {
  return [...texts].sort(compareVersions);
}
