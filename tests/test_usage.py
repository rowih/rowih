"""The usage fields of the lexicon the corpus gives
(specification/lexicon.md#entries-and-their-identifiers): the usage lexicon 1.0 states is
what `tools/measure_usage.py` measures over the domain corpus, every root and every entry
that is not a root is used, each example is a move that uses its entry, the measure reads
the cases whose answer is known, and both readers read the usage over the entries of
lexicon 1.0 and of the dialects it names, and not over an earlier release."""
import json
import os
import shutil
import subprocess
import sys

from rowih import data
from rowih.generator import Generator
from rowih.notation import Reader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_corpus  # noqa: E402
import measure_usage  # noqa: E402

MOVES = measure_usage.occurrences()
with open(os.path.join(ROOT, "lexicon", "usage", "1.0.json"), encoding="utf-8") as f:
    STORED = json.load(f)
# the dialects whose newest releases give compressed forms
FORM_DIALECTS = tuple(sorted((d["number"], d["version"]) for d in data.dialects().values()
                             if d.get("forms")))


def test_the_usage_is_what_the_measure_gives():
    assert json.loads(json.dumps(measure_usage.measure(MOVES))) == STORED


def test_every_entry_the_corpus_is_to_use_is_used():
    expected = measure_usage.expected(data.load("1.0"))
    assert {kind: len(ids) for kind, ids in expected.items()} == {
        "roots": 500, "register synonyms": 9, "suffixes": 18, "derivations": 12,
        "act words": 25, "idioms": 277, "senses": 16, "politeness words": 3, "dictions": 12,
        "technical terms": 115, "compressed forms": 55}
    assert measure_usage.unused(STORED) == {kind: [] for kind in expected}


def test_each_example_is_a_move_that_uses_its_entry():
    used = {(item, k, j): entries for item, _, k, j, entries in MOVES}
    roots = measure_usage.roots(data.load("1.0"))
    for ident, fields in STORED.items():
        assert 1 <= len(fields["examples"]) <= measure_usage.EXAMPLES, ident
        for example in fields["examples"]:
            assert ident in used[example["item"], example["message"], example["move"]]
        for collocate in fields["collocations"]:
            assert collocate["entry"] in roots and collocate["entry"] != ident


def built(notation: str, dialects: tuple = ()) -> str:
    lang = data.load(None, None, dialects) if dialects else data.load()
    moves = Reader(lang).moves(build_corpus.substitute(notation, lang))
    return Generator(lang).message(moves, "normal expression", 1, [2], "1760000000", 1,
                                   first_entry=1)


def keys(text: str) -> set:
    lang = data.load()
    return {lang.entries[i]["key"] if i in lang.entries else i
            for i in measure_usage.Reading(text).moves[0]}


def test_the_measure_reads_the_cases_whose_answer_is_known():
    # the thanks formula's own word is the formula's; what fills its slot is the speaker's
    # use of its roots, and a formation is used as its root and its suffix
    assert keys(built(
        "(move ACT-ANSWER (names 2 1 ISSUE QUESTION OPEN) courteous EXPLANATORY (assertion "
        "INTROSPECTION CERTAIN (situation IDIOM-ENTRY benefit (CONTENT (situation examine "
        "(ACTOR (term INTERLOCUTOR)) (UNDERGOER (term (formed \"test.agent\") "
        "DEFINITE)))))))")) == {"answer", "courteous", "thanks", "examine", "test", "agent"}
    # a frame that selects a conventional sense uses the sense, not the root's basic one
    assert keys(built(
        "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE (situation take (ACTOR (term "
        "SELF)) (UNDERGOER (situation run (UNDERGOER (term service DEFINITE)))))))")) == {
        "understand", "run", "service"}
    # a formation is the dialect's term only in a message that names the dialect
    bug = "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation detect (ACTOR " \
          "(term SELF)) (UNDERGOER (term (unknown \"nupenudinuwelob\") INDEFINITE)))))"
    assert "jg.programming.007" in keys(built(bug, ((2, "0.3"),)))
    assert "jg.programming.007" not in keys(built(bug))


def test_a_reader_of_lexicon_1_reads_the_usage_and_one_of_0_7_does_not():
    for ident in ("lx.000001", "lx.000144", "lx.000584"):
        entry = data.load("1.0").entries[ident]
        assert (entry["collocations"], entry["examples"]) == (
            STORED[ident]["collocations"], STORED[ident]["examples"])
    assert data.load("0.7").entries["lx.000001"]["examples"] == []
    forms = data.load(None, None, FORM_DIALECTS)
    assert forms.entries["dl.programming.005"]["examples"] == \
        STORED["dl.programming.005"]["examples"]


def test_both_readers_read_the_same_usage():
    proc = subprocess.run(
        [shutil.which("node"), "--experimental-strip-types", "--no-warnings",
         "tools/usage.ts", "1.0"] + ["%d:%s" % d for d in FORM_DIALECTS],
        cwd=os.path.join(ROOT, "typescript"), capture_output=True, timeout=600, check=True)
    typescript = json.loads(proc.stdout)
    python = data.load(None, None, FORM_DIALECTS).entries
    assert set(typescript) == set(python)
    # each reader reads the usage, so that agreement is not two readers reading nothing
    assert typescript["lx.000001"]["examples"] == STORED["lx.000001"]["examples"]
    for ident, entry in python.items():
        assert typescript[ident] == {"collocations": entry["collocations"],
                                     "examples": entry["examples"]}, ident
