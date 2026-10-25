"""Diagnostics as values (specification/conformance.md#the-diagnostics): every rejection
carries the six fields of a diagnostic and a code that is its identifier. No stage raises
an exception for any input; each returns its diagnostics."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Span:
    encoding: str
    start: int          # offset of the first character
    end: int            # offset after the last character
    line: int
    column: int

    def as_text(self) -> str:
        return "%d:%d" % (self.line, self.column)


@dataclass
class Diagnostic:
    code: str                      # d.<stage>.<name>
    location: Span | None
    expected: list = field(default_factory=list)
    detected: list = field(default_factory=list)
    ambiguity: list = field(default_factory=list)
    confidence: str = "certain"
    recoverability: str = "rejected"
    note: str = ""

    def as_text(self) -> str:
        where = self.location.as_text() if self.location else "-"
        parts = ["%s at %s" % (self.code, where)]
        if self.expected:
            parts.append("expected %s" % ", ".join(self.expected))
        if self.detected:
            parts.append("found %s" % ", ".join(self.detected))
        if self.note:
            parts.append(self.note)
        return "; ".join(parts)


class InputError(ValueError):
    """An error of what a writer or a caller gave, which is not a message: a text that
    does not read as the notation, envelope values that cannot be written, or a
    register, mode, diction or release the language does not have. It is raised, not
    reported as a diagnostic, since diagnostics are the language's judgements of
    messages."""


class Reject(Exception):
    """Raised inside a stage and caught at its boundary, where it becomes a diagnostic.
    Never escapes the API."""

    def __init__(self, diagnostic: Diagnostic):
        super().__init__(diagnostic.code)
        self.diagnostic = diagnostic


# The codes each stage can report. The rendering of each in the language is built by the
# generator from the metalinguistic vocabulary
# (specification/conformance.md#the-diagnostics).
CODES = {
    "d.tokenizer.outside-the-alphabet": "a character outside the alphabet",
    "d.tokenizer.mixed-encodings": "letters of the transliteration and code points of the "
                                   "native digital form in one text",
    "d.tokenizer.foreign-use-of-the-range": "a code point of the declared range that is no "
                                            "symbol",
    "d.lexer.unknown-word": "a word absent from the named lexicon version",
    "d.lexer.payload-short": "a payload shorter than its stated length",
    "d.lexer.payload-long": "a payload longer than its stated length",
    "d.lexer.payload-character": "a character no payload may hold",
    "d.lexer.letter-outside-a-payload": "a letter outside the symbols, outside any payload",
    "d.parser.empty": "no message",
    "d.parser.envelope": "an envelope field missing, repeated or out of order",
    "d.parser.unexpected-word": "a word no production admits at its place",
    "d.parser.end-of-input": "the message ends before a production is complete",
    "d.parser.count-mismatch": "a move's count differs from its number of words",
    "d.parser.move-check-mismatch": "a move check word differs from the one computed",
    "d.parser.number-check-mismatch": "a number's check word differs from the one computed",
    "d.parser.number-form": "numerals that do not form a number",
    "d.parser.width": "a name, identifier or check value at the wrong width",
    "d.parser.unclosed-unit": "a unit opened and not closed within its move",
    "d.parser.name-undefined": "a reference to a node no name in the move defines",
    "d.parser.name-repeated": "a name defined twice in one move",
    "d.parser.name-cycle": "a shared node that reaches itself",
    "d.parser.maximum": "a register's maximum exceeded",
    "d.parser.version-unknown": "a language, lexicon or protocol version, a dialect or a "
                                "feature the message names that this reader lacks",
    "d.parser.version-pairing": "a lexicon release earlier than the language release or a "
                                "named dialect may be read with",
    "d.parser.dialect-conflict": "a compressed form of a named dialect within one edit of a "
                                 "word of the named lexicon release or of another named "
                                 "dialect",
    "d.checker.definition-scope": "a definition scoped to a dialect its message does not "
                                  "name",
    "d.parser.feature-lacking": "a move that uses a must-understand feature this reader "
                                "lacks",
    "d.parser.media-type": "a declared type that is not a media type",
    "d.parser.protocol-message": "a message whose identifier is zero with a first entry "
                                 "other than zero, more than one recipient or the mark of "
                                 "a forwarded message",
    "d.parser.unit-check-mismatch": "the check word of an envelope or a protocol statement "
                                    "differs from the one computed",
    "d.parser.statement-form": "a protocol statement whose channels, serials or entries are "
                               "out of order or repeated",
    "d.parser.authentication-form": "an authentication field whose scheme is unknown or "
                                    "whose signature has another length",
    "d.checker.force": "a force class missing, present where it does not apply, or "
                       "inconsistent",
    "d.checker.authority": "authority missing on an operative or pending move, or present "
                           "on another",
    "d.checker.change-without-entry": "a change made with no entry named, or an entry "
                                      "named with no change",
    "d.checker.expectation": "a reference that names an entry without the kind and status "
                             "it expects, or a mention that states them",
    "d.checker.ill-typed": "a constituent whose sort its place does not admit",
    "d.checker.ordered-times": "an observation time after an inference time, or an "
                               "inference time after the communication time",
    "d.checker.strength-range": "a numeric strength outside zero and one",
    "d.checker.accidental-in-operative": "an operative move marked as accidentally ambiguous",
    "d.checker.precision-bound": "an ambiguity in a precision-bound move other than a "
                                 "declared kind",
    "d.checker.figure-without-target": "a novel figure in a precision-bound move without "
                                       "the relation its type requires, its target "
                                       "content or what a metonym stands for",
    "d.checker.figure-relation": "a figure's relation that does not fit its type or its "
                                 "unit, a relation where no figure stands, a metonymy on "
                                 "a unit that is not a term, or a figure with two "
                                 "relations",
    "d.checker.idiom-absent": "an idiom absent from the declared lexicon version, or with "
                              "an incomplete expansion",
    "d.checker.loss-not-incurred": "a declared loss that no conventional or idiomatic form "
                                   "of the move incurs",
    "d.checker.formation-unfit": "a formation whose suffix does not take its stem, or a "
                                 "compound whose head takes no modifier",
    "d.checker.definition-form": "an act of definition that does not state its term and its "
                                 "expansion, or a term not shaped as a root",
    "d.checker.definition-reaches-the-core": "a definition of a word of the grammar, which "
                                             "no act of definition changes",
    "d.checker.definition-shadows": "a definition of a word the release already lists",
    "d.checker.definition-confusable": "a defined term within one edit of a word, or two "
                                       "of a critical word",
    "d.checker.definition-recursive": "a definition whose expansion contains its term",
    "d.checker.definition-carries-force": "a definition whose expansion carries embedded "
                                          "material or readings",
    "d.checker.stop-restatement": "a stop whose restatement differs from what it withdraws",
    "d.checker.fit": "an act that does not fit the entry it names",
    "d.checker.integrity-value-required": "a precision-bound move, operative, pending, "
                                          "declared or in a register that carries the "
                                          "class by default, in a message without the "
                                          "integrity check value",
    "d.checker.register-excludes-word": "a word, suffix, act word or idiom whose entry "
                                        "does not list the move's register",
    "d.checker.register-excludes-device": "a device of economy that none of the move's "
                                          "register's modes admits, or a formula in a "
                                          "register that admits none",
    "d.checker.register-order": "siblings out of canonical order in a register whose "
                                "syntax is canonical",
    "d.checker.own-action": "an intention whose content is not an action by its holder",
    "d.checker.authority-attenuates": "a grant that exceeds the grantor's claimed scope",
    "d.checker.readings": "a set of readings with fewer than two readings",
    "d.checker.times-inconsistent": "times that cannot all hold together",
    "d.checker.unknown-in-precision-bound": "an unknown word in a precision-bound move",
    "d.checker.confirmation-source": "an independent confirmation that does not state the "
                                     "source it rests on",
    "d.checker.collective-reading": "a collective that acts or holds a normative state "
                                    "without its reading, joint or distributive",
    "d.check-values.integrity-mismatch": "the integrity check value differs from the one "
                                         "computed",
    "d.check-values.semantic-mismatch": "the semantic check value differs from the one "
                                        "computed",
}
