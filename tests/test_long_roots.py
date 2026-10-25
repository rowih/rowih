"""The long root of version 1.0
(specification/sounds-and-words.md#how-a-words-opening-fixes-its-length): seven symbols
opened by the syllable nu, whose last consonant the four symbols before it fix; a first
syllable that fixes the length its onset alone does not, so that a reader divides a
content word, and a hearer a stream of speech, at a long root as at a short one
(`inv.speech-decodable`)."""
from rowih import api, data, speech
from rowih.generator import Generator
from rowih.lexer import segment
from rowih.notation import Reader

LANG = data.load()
INDEX = {s["letter"]: s["index"] for s in LANG.phonology["symbols"]}


def long_roots():
    return [e for e in LANG.entries.values() if e["version"]["introduced"] == "1.0"
            and e["grammatical category"] in ("predicate root", "nominal root",
                                              "unit of measure", "discourse relation")]


def form(key):
    return next(e["orthographic form"] for e in LANG.entries.values() if e["key"] == key)


def item(key):
    return LANG.by_form[form(key)]


def test_every_root_of_lexicon_1_is_a_word_of_the_long_code():
    roots = long_roots()
    assert len(roots) == 394
    for e in roots:
        w = e["orthographic form"]
        assert len(w) == 7 and w[:2] == "nu"
        assert [c in LANG.consonants for c in w] == [True, False] * 3 + [True]
        c2, v2, c3, v3, c4 = (INDEX[w[2]], INDEX[w[3]] - 14, INDEX[w[4]],
                              INDEX[w[5]] - 14, INDEX[w[6]])
        assert c4 == (7 + c2 + 2 * v2 + 3 * c3 + 4 * v3) % 14, w


def test_the_first_syllable_fixes_the_length_where_the_onset_does_not():
    assert LANG.length_at(form("think")) == 7
    assert LANG.length_at(LANG.form_of("g.numbers.numeral.zero")) == 4
    assert LANG.length_at("noba") == 4
    assert LANG.length_at(form("run")) == 5
    assert LANG.length_at("a") is None


def test_a_long_root_divides_alone_with_suffixes_and_after_the_linker():
    think, run = item("think"), item("run")
    agent = next(s for s in LANG.suffixes.values() if s.name == "agent")
    assert segment(think.form, LANG) == [think]
    assert segment(think.form + agent.form, LANG) == [think, agent]
    assert segment(run.form + "i" + think.form, LANG) == [run, "linker", think]
    assert segment(think.form + "i" + run.form + agent.form, LANG) == [
        think, "linker", run, agent]
    assert segment(think.form + "i" + item("bird").form, LANG) == [think, "linker",
                                                                     item("bird")]


def test_a_stream_with_long_roots_divides_into_its_words():
    agent = next(s for s in LANG.suffixes.values() if s.name == "agent")
    words = [LANG.form_of("g.numbers.numeral.zero"), form("think"),
             form("think") + agent.form, form("run"), form("run") + "i" + form("bird"),
             form("bird") + "i" + form("run"), LANG.form_of("g.numbers.numeral.two")]
    assert speech.decode("".join(words), LANG) == words


def test_a_message_of_long_roots_parses_without_a_diagnostic():
    notation = ("(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation fly "
                "(UNDERGOER (term bird DEFINITE)))))")
    text = Generator().message(Reader(LANG).moves(notation), "full explicitness")
    a = api.parse(text)
    assert a.diagnostics == []
    forms = {w.form for w in a.words}
    assert {form("fly"), form("bird")} <= forms
