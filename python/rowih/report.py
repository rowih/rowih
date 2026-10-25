"""Diagnostics rendered in the language (specification/conformance.md#the-diagnostics): a
report of failure is an asserted position, on the basis of computation, that the reader
detected a fault in the message it names, with the diagnostic's fields as roles drawn from
the metalinguistic vocabulary of the lexicon, and its code carried as declared data for
machines."""
from __future__ import annotations

from .diagnostics import Diagnostic
from .generator import Generator
from .notation import Reader

STAGE_ROOT = {"tokenizer": "corrupt", "lexer": "unknown", "parser": "expect",
              "checker": "problem", "check-values": "corrupt", "view": "problem"}


def notation_of(diagnostic: Diagnostic, sender: str, identifier: str) -> str:
    """The report of one diagnostic about message `identifier` of agent `sender`, in the
    literal semantic notation."""
    stage = diagnostic.code.split(".")[1]
    root = STAGE_ROOT.get(stage, "problem")
    where = diagnostic.location.start if diagnostic.location else 0
    code = diagnostic.code.replace('"', "")
    return ('(move ASSERTED-POSITION (assertion COMPUTATION CERTAIN (situation detect '
            '(ACTOR (term SELF)) (UNDERGOER (term (mentions 1 1))) (CONTENT (situation %s '
            '(UNDERGOER (term fault (CONTENT (term position (q EXACTLY %d))))) '
            '(CONTENT (data "text/plain" "%s %s %s")))))))'
            % (root, where, code, sender, identifier))


def render(diagnostic: Diagnostic, about_sender: str = "1", about_identifier: str = "1",
           sender: int = 2, recipients=(1,)) -> str:
    """The report as a message in the language, written by the generator."""
    gen = Generator()
    moves = Reader(gen.lang).moves(notation_of(diagnostic, about_sender, about_identifier))
    return gen.message(moves, sender=sender, recipients=recipients)
