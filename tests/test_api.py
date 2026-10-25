"""The API's functions beyond parsing (specification/conformance.md#the-python-package):
render, gloss, analyze, translate and generate, each returning its result with its
diagnostics and raising for no input."""
import pytest

from rowih import api

from corpus import messages

TEXT = messages()[0][3]


@pytest.mark.parametrize("fmt,start", [("svg", "<svg "), ("html", '<figure class="rowih">'),
                                       ("terminal", "")])
def test_render_draws_each_format(fmt, start):
    out, diags = api.render(TEXT, fmt)
    assert diags == [] and out.startswith(start)
    if fmt == "terminal":
        assert out == api.parse(TEXT).canonical


def test_render_with_the_font_writes_the_native_digital_form():
    out, _ = api.render(TEXT, "terminal", has_font=True)
    assert out == api.convert(TEXT, "native")[0]


def test_render_of_no_message_raises_nothing():
    for fmt in ("svg", "html", "terminal"):
        out, diags = api.render("", fmt, has_font=True)
        assert [d.code for d in diags] == ["d.parser.empty"]
    assert api.render("", "terminal", has_font=True)[0] == ""


def test_render_refuses_an_unknown_format():
    out, diags = api.render(TEXT, "pdf")
    assert out == "" and [d.code for d in diags] == ["d.parser.unexpected-word"]


def test_gloss_gives_five_lines_a_move():
    out, diags = api.gloss(TEXT)
    labels = [line.split("  ")[0] for line in out.split("\n") if line]
    assert diags == [] and labels == ["NATIVE", "TRANSLITERATION", "MORPHEME GLOSS",
                                      "LITERAL SEMANTIC FORM", "NATURAL ENGLISH"]


def test_analyze_measures_the_analysis():
    result = api.analyze(TEXT)
    a = result["analysis"]
    assert result["measurements"] == {"words": len(a.words), "moves": 1, "diagnostics": 0}


def test_translate_to_english_is_a_view_and_unknown_targets_are_refused():
    out, changes, diags = api.translate(TEXT, "English")
    assert diags == [] and changes == [] and out.endswith("a view, not the language)\n")
    out, changes, diags = api.translate(TEXT, "R9")
    assert out == "" and [d.code for d in diags] == ["d.parser.unexpected-word"]


def test_translate_to_a_register_keeps_the_core_and_declares_its_changes():
    out, changes, diags = api.translate(TEXT, "ceremonial")
    assert diags == [] and api.parse(out).normal_text == api.parse(TEXT).normal_text
    assert changes == [["register", "relation between participants", "wording"]]


def test_generate_gives_the_six_outputs():
    out = api.generate("(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation run "
                       "(UNDERGOER (term service)))))")
    for key in ("canonical form", "standard form", "compressed form", "human-readable gloss",
                "transliteration", "native-script rendering"):
        assert out[key]
    assert api.parse(out["standard form"]).diagnostics == []


def test_analyze_states_each_moves_dependencies():
    from corpus import messages
    text = next(t for i, k, _, t in messages() if i == "e2-conversational-memory" and k == 5)
    deps = api.analyze(text)["dependencies"]
    assert deps == [[["entry", "1", "1"], ["entry", "1", "2"], ["entry", "2", "1"]]]


def test_discourse_is_one_participants_view():
    from corpus import messages
    texts = [t for i, k, _, t in messages() if i == "e2-discourse-architecture"]
    out = api.discourse(texts, "2")
    assert out["diagnostics"] == []
    assert out["structure"]["participant"] == "2"
    assert [i["entry"] for i in out["structure"]["open issues"]] == ["3.2"]
