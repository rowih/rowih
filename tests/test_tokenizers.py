"""The tokenizer panel (specification/conformance.md#the-invariants):
`inv.tokenizer-round-trip`, tested as the invariants state, over the transliteration of
every corpus message under every tokenizer of the named, versioned panel, with a control
that the check must find failing. The panel's files are fetched into the ignored cache
on first use and checked against their hashes (`tools/tokenizer_panel.py`)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "tools"))
import tokenizer_panel as P  # noqa: E402


@pytest.fixture(scope="module")
def panel():
    panel = P.load_panel()
    P.fetch(panel)
    return panel


@pytest.fixture(scope="module")
def texts():
    return P.corpus_texts()


def test_the_panel_is_named_versioned_and_pinned(panel):
    """The project maintains a named, versioned panel of tokenizers; each member is pinned
    to a revision and to the SHA-256 of its file."""
    assert panel["name"] and panel["version"] == 1
    assert len(panel["members"]) == 13
    for m in panel["members"] + [panel["control"]]:
        assert len(m["revision"]) == 40 and len(m["sha256"]) == 64


def test_every_tokenizer_on_the_panel_returns_every_transliteration(panel, texts):
    """`inv.tokenizer-round-trip`: for every tokenizer on the panel, decoding the encoding
    of the transliteration of every corpus message returns it byte for byte."""
    assert len(texts) > 300
    failures = P.check_panel(panel, texts)
    assert set(failures) == {m["name"] for m in panel["members"]}
    assert failures == {name: [] for name in failures}


def test_the_check_finds_the_control_failing(panel, texts):
    """The check is sound: run on the control, a tokenizer whose normaliser rewrites
    whitespace, it reports texts not returned."""
    control = P.check_panel(panel, texts, [panel["control"]])
    assert len(control[panel["control"]["name"]]) == len(texts)


def test_a_check_fails_where_a_tokenizer_changes_a_text_or_the_control_returns_one():
    texts = ["a", "b"]
    assert not P.check_failed({"one": [], "two": []}, ["a", "b"], texts)
    assert P.check_failed({"one": ["a"], "two": []}, ["a", "b"], texts)
    assert P.check_failed({"one": [], "two": []}, ["a"], texts)
