"""The reading of the writing system
(specification/writing-system.md#what-the-writing-system-has-been-tested-on): the strings
come again from the seed, the sheets are drawn, and a reading is scored by size and by the
confusions it makes against the measure of the components' distance."""
import json
import os
import sys

from rowih import data, writing

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import read_writing  # noqa: E402

LANG = data.load()


def reading_of(sheets: dict) -> dict:
    return {"reader": "a test", "read": "2026-10-18", "sheets": sheets}


def test_the_strings_come_again_from_the_seed():
    first, second = read_writing.strings(LANG), read_writing.strings(LANG)
    assert first == second
    assert sorted(first) == sorted(read_writing.SIZES)
    for items in first.values():
        assert len(items) == read_writing.ITEMS
        assert all(len(s) == read_writing.LENGTH and set(s) <= set(LANG.letters)
                   for s in items)


def test_the_sheets_are_drawn_at_each_size(tmp_path):
    read_writing.sheets(str(tmp_path))
    names = sorted(os.listdir(tmp_path))
    assert names == ["key.png", "sheet-12.png", "sheet-24.png", "sheet-48.png"]
    for name in names:
        assert (tmp_path / name).read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_a_reading_is_scored_by_size_and_by_its_confusions():
    truth = {str(12 * size): items for size, items in read_writing.strings(LANG).items()}
    perfect = read_writing.evaluate(reading_of(truth), LANG)
    assert all(s["share"] == 1.0 and s["is legible"] for s in perfect["sizes"].values())
    assert perfect["confusions"] == [] and "is borne out" not in perfect["measure"]
    # one component misread and one left unread at the smallest size
    planted = dict(truth)
    first = planted["12"][0]
    other = next(c for c in LANG.letters if c != first[0])
    planted["12"] = [other + first[1:4] + "?"] + planted["12"][1:]
    scored = read_writing.evaluate(reading_of(planted), LANG)
    components = read_writing.ITEMS * read_writing.LENGTH
    assert scored["sizes"]["12"]["read correctly"] == components - 2
    assert scored["sizes"]["12"]["unread"] == 1
    assert scored["confusions"] == [{"drawn": first[0], "read": other, "times": 1,
                                     "distance": round(writing.distance(first[0], other,
                                                                        LANG), 3)}]


def test_the_report_is_what_the_reading_scores():
    with open(read_writing.OUT, encoding="utf-8") as f:
        report = json.load(f)
    reading = {"reader": report["reader"], "read": report["read"],
               "sheets": report["reading"], "remarks": report["remarks"]}
    assert read_writing.evaluate(reading, LANG) == report
