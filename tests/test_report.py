"""Diagnostics expressible in the language (specification/conformance.md#the-diagnostics):
every diagnostic the negative corpus draws renders as a message that parses cleanly and
carries its code."""
import json
import os

import pytest

from rowih import api, report

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS = json.load(open(os.path.join(ROOT, "corpus", "source", "negative.json"),
                       encoding="utf-8"))["items"]


@pytest.mark.parametrize("item", ITEMS, ids=[i["id"] for i in ITEMS])
def test_diagnostic_renders_in_the_language(item):
    text = open(os.path.join(ROOT, "corpus", "negative", item["id"] + ".txt"),
                encoding="utf-8").read()
    for d in api.parse(text).diagnostics:
        message = report.render(d)
        r = api.parse(message)
        assert r.diagnostics == []
        from rowih.lexer import decode_payload
        walls = [p for t in r.moves for p in _walk(t) if p.get("kind") == "wall"]
        assert any(d.code in decode_payload(w["data"]).decode("utf-8") for w in walls)


def _walk(node):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for x in node:
            yield from _walk(x)
