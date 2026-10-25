"""The reviewer's test of linguisticity
(specification/conformance.md#the-conformance-suite): the packet comes again from the seed
and the canonical sources, a reading is held to the four questions verbatim, and its
outcome follows from its answers under the rule fixed before it was read."""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import review_linguisticity as review  # noqa: E402


def reading_of(*answers: str) -> dict:
    return {"answers": [{"question": q, "answer": a, "grounds": ["a ground"]}
                        for q, a in zip(review.QUESTIONS, answers)], "remarks": ""}


def test_the_sample_comes_again_from_the_seed():
    first, second = review.sample(), review.sample()
    assert first == second
    text, ids = first
    assert len(ids) == len(set(ids)) == 12 * review.ITEMS_PER_DOMAIN
    domains = [i.rsplit("-", 1)[0] for i in ids]
    assert all(domains.count(d) == review.ITEMS_PER_DOMAIN for d in set(domains))
    assert text.count("## Item ") == len(ids)


def test_a_departure_is_no_to_the_first_question_or_yes_to_another():
    assert review.outcome(reading_of("yes", "no", "no", "no")) == {
        "departures": [], "findings": [], "blocks the release": False}
    partial = review.outcome(reading_of("in part", "in part", "no", "no"))
    assert partial == {"departures": [], "findings": list(review.QUESTIONS[:2]),
                       "blocks the release": False}
    assert review.outcome(reading_of("no", "no", "no", "no"))["departures"] == \
        [review.QUESTIONS[0]]
    for k in range(1, 4):
        answers = ["yes", "no", "no", "no"]
        answers[k] = "yes"
        out = review.outcome(reading_of(*answers))
        assert out["departures"] == [review.QUESTIONS[k]] and out["blocks the release"]


def test_a_reading_that_changes_a_question_or_an_answer_is_refused():
    changed = reading_of("yes", "no", "no", "no")
    changed["answers"][2]["question"] = "Is it a cipher?"
    with pytest.raises(review.ReadingRefused):
        review.outcome(changed)
    loose = reading_of("yes", "no", "no", "maybe")
    with pytest.raises(review.ReadingRefused):
        review.outcome(loose)
    with pytest.raises(review.ReadingRefused):
        review.outcome({"answers": reading_of("yes", "no", "no", "no")["answers"][:3]})


def test_the_packet_must_be_what_the_tool_writes(tmp_path):
    review.write_packet(str(tmp_path))
    with open(tmp_path / "reading.json", "w", encoding="utf-8") as f:
        json.dump(reading_of("yes", "no", "no", "no"), f)
    out = review.evaluate(str(tmp_path), "a test", "2026-10-18")
    assert out["outcome"]["departures"] == [] and out["items"] == review.sample()[1]
    with open(tmp_path / "sample.md", "a", encoding="utf-8") as f:
        f.write("\n")
    with pytest.raises(review.ReadingRefused):
        review.evaluate(str(tmp_path), "a test", "2026-10-18")


def test_the_report_is_what_its_reading_gives():
    with open(review.OUT, encoding="utf-8") as f:
        report = json.load(f)
    assert report["rule"] == review.RULE and report["seed"] == review.SEED
    assert report["questions"] == list(review.QUESTIONS)
    assert report["outcome"] == review.outcome(report["reading"])
    assert not report["outcome"]["blocks the release"]
