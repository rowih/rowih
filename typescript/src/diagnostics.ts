// Diagnostics as values: every rejection carries the six fields the specification
// requires (specification/conformance.md#the-diagnostics) and a code that is its
// identifier. No stage raises an exception for any input; each returns its diagnostics.

export class Span {
  encoding: string;
  start: number; // offset of the first character, in code points
  end: number; // offset after the last character
  line: number;
  column: number;

  constructor(encoding: string, start: number, end: number, line: number, column: number) {
    this.encoding = encoding;
    this.start = start;
    this.end = end;
    this.line = line;
    this.column = column;
  }

  asText(): string {
    return this.line + ":" + this.column;
  }
}

export interface DiagnosticFields {
  expected?: string[];
  detected?: string[];
  ambiguity?: string[];
  confidence?: string;
  recoverability?: string;
  note?: string;
}

export class Diagnostic {
  code: string; // d.<stage>.<name>
  location: Span | null;
  expected: string[];
  detected: string[];
  ambiguity: string[];
  confidence: string;
  recoverability: string;
  note: string;

  constructor(code: string, location: Span | null, fields: DiagnosticFields = {}) {
    this.code = code;
    this.location = location;
    this.expected = fields.expected ?? [];
    this.detected = fields.detected ?? [];
    this.ambiguity = fields.ambiguity ?? [];
    this.confidence = fields.confidence ?? "certain";
    this.recoverability = fields.recoverability ?? "rejected";
    this.note = fields.note ?? "";
  }

  asText(): string {
    const where = this.location !== null ? this.location.asText() : "-";
    const parts = [this.code + " at " + where];
    if (this.expected.length) parts.push("expected " + this.expected.join(", "));
    if (this.detected.length) parts.push("found " + this.detected.join(", "));
    if (this.note) parts.push(this.note);
    return parts.join("; ");
  }
}

/** Thrown inside a stage and caught at its boundary, where it becomes a diagnostic.
 * Never escapes the API. */
export class Reject extends Error {
  diagnostic: Diagnostic;

  constructor(diagnostic: Diagnostic) {
    super(diagnostic.code);
    this.diagnostic = diagnostic;
  }
}
