"""The ambiguity test set (specification/conformance.md#the-conformance-suite): the
parser's reading set is the stated one with the stated type, a declared precision bound
refuses it, and each explicit disambiguation parses to one reading."""
import json
import os

import pytest

from rowih import api
from rowih.generator import Generator
from rowih.notation import Reader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS = json.load(open(os.path.join(ROOT, "corpus", "source", "ambiguity.json"),
                       encoding="utf-8"))["items"]
GEN = Generator()


def reading_sets(node, out):
    if isinstance(node, dict):
        if node.get("kind") == "readings":
            out.append(node)
        for v in node.values():
            reading_sets(v, out)
    elif isinstance(node, list):
        for x in node:
            reading_sets(x, out)
    return out


def analyse(notation):
    return api.parse(GEN.message(Reader(GEN.lang).moves(notation)))


@pytest.mark.parametrize("item", ITEMS, ids=[i["id"] for i in ITEMS])
def test_reading_set_is_the_stated_one(item):
    a = analyse(item["expression"])
    codes = [d.code for d in a.diagnostics]
    if item.get("refusal"):
        assert item["refusal"] in codes
    else:
        assert codes == []
    sets = reading_sets(a.normal, [])
    if item["type"] is None:
        assert sets == []
    else:
        assert len(sets) == 1
        assert sets[0]["ambiguity"].endswith("." + item["type"])
        assert len(sets[0]["readings"]) == item["readings"]


@pytest.mark.parametrize("item", ITEMS, ids=[i["id"] for i in ITEMS])
def test_disambiguation_has_one_reading(item):
    a = analyse(item["disambiguation"])
    assert [d.code for d in a.diagnostics] == []
    assert reading_sets(a.normal, []) == []


def test_every_type_appears():
    types = {i["type"] for i in ITEMS if i["type"]}
    assert types == {"accidental", "productive", "strategic", "creative", "epistemic"}


def test_an_interval_of_standing_stays_an_interval():
    """A strength between two levels is an interval in the normal form, never a point
    (`ambiguity/interval-written-as-a-point`)."""
    item = next(i for i in ITEMS if i["id"] == "a04-vagueness")
    a = analyse(item["expression"])
    strengths = [p for n in a.normal for c in n["constituents"] for p in c["parts"]
                 if p["kind"] == "quantity"]
    assert [q["number"] for q in strengths] == ["0.6~1"]
