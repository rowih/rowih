"""The resemblance audit (specification/conformance.md#known-limitations): the report
compares every word of one morpheme in the open classes as the lexicon now has it, no word
keeps a close match with an offensive or related meaning, every match is classified, and
the reduction, the index, the orthographies and the classification read the cases whose
answer is known. The comparison itself needs the pinned sources and is run by
`tools/compare_roots.py`."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import compare_roots  # noqa: E402
import vocabularies as V  # noqa: E402

with open(compare_roots.OUT, encoding="utf-8") as f:
    REPORT = json.load(f)
with open(compare_roots.RULINGS, encoding="utf-8") as f:
    RULINGS = json.load(f)


def test_the_report_compares_every_word_as_the_lexicon_has_it():
    words = compare_roots.ours()
    assert len(words) == REPORT["words compared"] == 584
    assert REPORT["words"] == {form: {"entry": ident, "key": key, "phonological form": ph}
                               for ident, key, form, ph in words}


def test_no_word_keeps_an_offensive_or_related_close_match():
    for m in REPORT["matches"]:
        assert m["class"] == "accidental and retained", m
        assert m["reason"] and m["word"] in REPORT["words"]
    # a word redesigned no longer has the form that matched
    for r in RULINGS["redesigned"]:
        assert r["form"] not in REPORT["words"]
        assert REPORT["words"][r["new form"]]["entry"] == r["new entry"]


def test_the_reduction_reads_the_cases_whose_answer_is_known():
    cases = {"ç a r m e n": "çarmen", "tʰ i̯ ɛ n ⁵ ¹": "tien", "ˈw ɔː t ə": "wotə",
             "t͡ʃ a": "tʃa", "ɾ u k a w": "rukaw", "s ʲ ɪ d ə": "sidə", "ʁ e": "re",
             "ŋ ɲ ɴ m": "nnnm", "ʔ a": "ʔa", "ɡ ʎ": "gl"}
    for transcription, segments in cases.items():
        assert "".join(V.reduce(transcription.split())) == segments


def test_the_index_finds_one_edit_and_not_two():
    index = V.Index()
    language = {"name": "test", "compared by": "segments"}
    words = {w: V.Entry(w, tuple(w), None, False) for w in
             ("rukaw", "rukam", "rkaw", "rukawa", "urkaw", "rakam", "pukax")}
    index.add(language, list(words.values()))
    found = {w.spelling for _, w in index.close(tuple("rukaw"))}
    # the word itself, a substitution, a deletion and an insertion; not a transposition,
    # nor two substitutions
    assert found == {"rukaw", "rukam", "rkaw", "rukawa"}
    consonants = {"name": "roots", "compared by": "consonants"}
    index.add(consonants, [V.Entry("rkw", tuple("rkw"), None, False),
                           V.Entry("rk", tuple("rk"), None, False)])
    assert {w.spelling for lang, w in index.close(tuple("rukaw"))
            if lang["name"] == "roots"} == {"rkw"}


def test_each_orthography_transcribes_the_words_whose_sound_is_known():
    assert "".join(V.transcribe("bacru", V.LOJBAN)) == "baʃru"
    assert "".join(V.transcribe("Qapla'", V.KLINGON)) == "qχaplaʔ"
    assert "".join(V.transcribe("hyarmen", V.QUENYA)) == "çarmen"
    assert "".join(V.transcribe("ech", V.SINDARIN)) == "eχ"
    assert "".join(V.laadan_spelling("Láadan")) == "ladan"
    assert "".join(V.loglan_spelling("cersi")) == "ʃersi"
    assert "".join(V.loglan_spelling("ie")) == "je"
    assert "".join(V.transcribe("dosol", V.SOLRESOL)) == "dosol"


def test_an_offensive_or_related_match_is_redesigned_and_any_other_retained():
    match = {"word": "rukaw", "language": "English", "match": "rook", "offensive": ""}
    none = {"related": {}, "not offensive": {}}
    assert compare_roots.classify(match, none)[0] == "accidental and retained"
    marked = dict(match, offensive="vulgar")
    assert compare_roots.classify(marked, none)[0] == "redesigned"
    judged = {"related": {}, "not offensive": {("rukaw", "English", "rook"): "a bird"}}
    assert compare_roots.classify(marked, judged)[0] == "accidental and retained"
    related = {"related": {("rukaw", "English", "rook"): "a bird"}, "not offensive": {}}
    assert compare_roots.classify(match, related) == ("redesigned",
                                                      "related in meaning: a bird")


def test_a_comparison_fails_where_a_word_awaits_redesign():
    assert not compare_roots.failed(REPORT["classes"])
    assert compare_roots.failed(dict(REPORT["classes"], redesigned=1))
