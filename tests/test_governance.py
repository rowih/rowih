"""How Rowih changes (governance/): the registry of dialect numbers agrees with every
dialect release and is what the build reads; the data are what the sources build, and the
check of that finds a planted difference; the proposal format's check admits a proposal
in the format and refuses each way out of it, and agrees with the document that states
the format; and the governance's documents cite nothing outside the public repository and
name only commands and anchors that exist."""
import datetime
import json
import os
import re
import sys

import pytest

from rowih import api, data

from test_specification import CITED_PATH, LINK, anchors, cites_a_section

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import check_proposal  # noqa: E402
import check_rebuild  # noqa: E402

with open(os.path.join(ROOT, "governance", "dialects.json"), encoding="utf-8") as f:
    REGISTRY = json.load(f)
DOCUMENTS = ["governance/README.md", "governance/proposals.md", "proposals/README.md",
             "proposals/TEMPLATE.md"]


def read(path: str) -> str:
    with open(os.path.join(ROOT, path), encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------- the registry
def test_the_registry_assigns_each_number_once_in_order():
    numbers = [d["number"] for d in REGISTRY["dialects"]]
    assert numbers == list(range(1, len(numbers) + 1))
    assert REGISTRY["next"] == len(numbers) + 1
    names = [d["name"] for d in REGISTRY["dialects"]]
    assert len(set(names)) == len(names)
    for d in REGISTRY["dialects"]:
        assert set(d) == {"number", "name", "community", "assigned"}
        assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", d["name"])
        datetime.date.fromisoformat(d["assigned"])
    assert "never reused" in REGISTRY["rule"]


def test_every_dialect_release_states_its_registered_number_and_name():
    registered = {d["number"]: d for d in REGISTRY["dialects"]}
    releases = data.dialect_releases()
    assert releases
    for (number, _version), release in releases.items():
        entry = registered[number]
        assert (release["dialect"], release["community"]) == (entry["name"],
                                                              entry["community"]), number
    # a number assigned before its dialect's first release is the only one without one
    assert {n for n, _ in releases} == set(registered)


def test_the_build_takes_the_numbers_from_the_registry():
    import dialect_source
    assert dialect_source.DIALECT_NUMBERS == {d["name"]: d["number"]
                                              for d in REGISTRY["dialects"]}


def test_the_specification_s_dialects_are_the_registered_ones():
    newest = data.dialects()
    assert sorted((d["number"], name) for name, d in newest.items()) == \
        [(d["number"], d["name"]) for d in REGISTRY["dialects"]]


# ------------------------------------------------------------------ the rebuild
def test_the_data_are_what_the_sources_build():
    assert check_rebuild.rebuild() == {"added": [], "changed": [], "removed": []}


def test_the_rebuild_check_finds_a_planted_difference():
    def definition(root):
        path = os.path.join(root, "tools", "language_source.py")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace('"be under way as a process"',
                                 '"be under way as a process, planted"'))
    found = check_rebuild.rebuild(steps=("build_language",), plant=definition)
    assert "lexicon/roots/lx.000004.json" in found["changed"]

    def number(root):
        path = os.path.join(root, "governance", "dialects.json")
        registry = json.loads(open(path, encoding="utf-8").read())
        registry["dialects"][-1]["number"] = 13
        with open(path, "w", encoding="utf-8") as f:
            json.dump(registry, f)
    found = check_rebuild.rebuild(steps=("build_language",), plant=number)
    assert "lexicon/jargon/conversation/0.1.json" in found["changed"]


def test_a_failing_step_is_reported_and_not_taken_for_a_difference():
    def broken(root):
        with open(os.path.join(root, "tools", "language_source.py"), "a",
                  encoding="utf-8") as f:
            f.write("\nraise RuntimeError('planted')\n")
    with pytest.raises(check_rebuild.StepFailed, match="build_language"):
        check_rebuild.rebuild(steps=("build_language",), plant=broken)


def test_the_governance_states_the_rebuild_order_the_check_runs():
    order = " ".join("`tools/%s.py`" % step for step in check_rebuild.ORDER)
    stated = re.findall(r"`tools/([a-z_]+)\.py`", read("governance/README.md").split(
        "## The regenerated data")[1].split("in that order")[0])
    assert stated == list(check_rebuild.ORDER), order


# ------------------------------------------------------------------ proposals
FILLED = {"Author": "an agent (a language model), run by the operator Example",
          "Date": "2026-10-25"}


def proposal(kind="lexicon", releases="lexicon 1.1", compatibility="compatible",
             architectural="no", answers=("no", "no", "no", "no"), reader="a reviewer agent",
             sections=check_proposal.SECTIONS, number="0001", fields=None, review=True):
    """A proposal in the format, from the template, which each test bends one way."""
    values = {"Kind": kind, "Releases": releases, "Compatibility": compatibility,
              "Architectural": architectural, **FILLED}
    lines = ["# %s: A root for forecasting" % number, ""]
    lines += ["- **%s:** %s" % (f, values[f]) for f in (fields or check_proposal.FIELDS)]
    for section in sections:
        lines += ["", "## %s" % section, ""]
        if section == "Review":
            if review:
                lines.append("- **Reader:** %s" % reader)
                lines += ["- **%s** %s" % (q, a) for q, a in zip(check_proposal.QUESTIONS,
                                                                  answers, strict=True)]
        else:
            lines.append("What the section states.")
    return "\n".join(lines) + "\n"


IN_FORCE = {"language": (1, 0), "lexicon": (1, 0), "protocol": (0, 5),
            "dialect mathematics": (0, 3)}
NAME = "0001-a-root-for-forecasting.md"
GOOD_ANSWERS = ("yes, the evidence", "no, the evidence", "in part, the evidence", "no")


def problems(text, name=NAME, merge=False):
    return check_proposal.check(text, name, merge, IN_FORCE)


def test_a_proposal_in_the_format_is_admitted():
    assert problems(proposal(answers=GOOD_ANSWERS), merge=True) == []
    assert problems(proposal(answers=("pending",) * 4, reader="pending")) == []
    assert problems(proposal(kind="dialect", releases="dialect weather 0.1",
                             answers=("pending",) * 4, reader="not required"),
                    merge=True) == []
    assert problems(proposal(kind="grammar", releases="language 2.0, lexicon 2.0",
                             compatibility="breaking", architectural="yes",
                             answers=GOOD_ANSWERS), merge=True) == []


@pytest.mark.parametrize("text,name,says", [
    (proposal(), "1-root.md", "the file is named"),
    (proposal(number="0002"), NAME, "not the file's"),
    (proposal().replace("# 0001: A root", "A root"), NAME, "the first line is the title"),
    (proposal(fields=("Releases", "Kind", "Compatibility", "Architectural", "Author",
                      "Date")), NAME, "in that order"),
    (proposal(kind="vocabulary"), NAME, "Kind is one of"),
    (proposal(compatibility="mostly"), NAME, "Compatibility is"),
    (proposal(architectural="perhaps"), NAME, "Architectural is"),
    (proposal(releases="the next one"), NAME, "names no release"),
    (proposal(releases="lexicon 1.0"), NAME, "not later than"),
    (proposal(releases="grammar 1.1"), NAME, "names no release"),
    (proposal(releases="lexicon 1.1", compatibility="breaking"), NAME, "raises a major"),
    (proposal(releases="lexicon 2.0"), NAME, "keeps the major version"),
    (proposal(kind="dialect", releases="dialect mathematics 1.0", compatibility="breaking"),
     NAME, "a dialect release is compatible"),
    (proposal(sections=check_proposal.SECTIONS[1:]), NAME, "the sections are"),
    (proposal(sections=check_proposal.SECTIONS[::-1]), NAME, "the sections are"),
    (proposal().replace("What the section states.", "<!-- guidance -->", 1), NAME,
     "is empty"),
    (proposal(review=False), NAME, "does not state the reviewer's answer"),
    (proposal().replace("- **Author:** an agent", "- **Author:**").replace(
        "(a language model), run by the operator Example", ""), NAME, "Author names"),
    (proposal().replace("2026-10-25", "25 October"), NAME, "Date is a date"),
])
def test_a_proposal_out_of_the_format_is_refused_with_the_reason(text, name, says):
    found = problems(text, name)
    assert found and any(says in p for p in found), found


@pytest.mark.parametrize("answers,says", [
    (("pending",) * 4, "is pending"),
    (("no",) + GOOD_ANSWERS[1:], "a departure"),
    (GOOD_ANSWERS[:2] + ("yes",) + GOOD_ANSWERS[3:], "a departure"),
    (("perhaps",) + GOOD_ANSWERS[1:], "yes, no or in part"),
])
def test_a_proposal_needing_a_reading_is_merged_only_with_one_without_a_departure(
        answers, says):
    found = problems(proposal(answers=answers), merge=True)
    assert any(says in p for p in found), found
    # an architectural change needs the reading whatever its kind
    found = problems(proposal(kind="dialect", releases="dialect weather 0.1",
                              architectural="yes", answers=answers), merge=True)
    assert found


def test_the_template_is_refused_until_it_is_filled():
    found = problems(read("proposals/TEMPLATE.md"), "0001-template.md")
    assert any("Author" in p for p in found) and any("Date" in p for p in found)
    assert any("is empty" in p for p in found)


def test_every_merged_proposal_is_in_the_format():
    directory = os.path.join(ROOT, "proposals")
    names = [n for n in os.listdir(directory) if n not in ("README.md", "TEMPLATE.md")]
    for name in names:
        with open(os.path.join(directory, name), encoding="utf-8") as f:
            assert check_proposal.check(f.read(), name, merge=True) == [], name


def test_the_check_reads_the_releases_in_force():
    in_force = check_proposal._in_force()
    v = api.version()
    assert in_force["lexicon"] == tuple(int(x) for x in v["lexicon"].split("."))
    assert in_force["dialect mathematics"] == tuple(
        int(x) for x in v["dialects"]["mathematics"].split("."))


def test_the_command_exits_with_its_finding(tmp_path, capsys):
    good = tmp_path / NAME
    good.write_text(proposal(answers=GOOD_ANSWERS), encoding="utf-8")
    assert check_proposal.main(["--merge", str(good)]) == 0
    bad = tmp_path / NAME
    bad.write_text(proposal(kind="vocabulary"), encoding="utf-8")
    assert check_proposal.main([str(bad)]) == 1
    assert "Kind is one of" in capsys.readouterr().out
    assert check_proposal.main([]) == 2


def test_the_format_s_document_states_what_the_check_checks():
    text = read("governance/proposals.md")
    table = text.split("## The fields")[1].split("## The sections")[0]
    rows = re.findall(r"^\| ([A-Z][a-z]+) \|", table, re.M)
    assert rows[0] == "Field" and rows[1:] == list(check_proposal.FIELDS)
    for kind in check_proposal.KINDS:
        assert "`%s`" % kind in table
    sections = re.findall(r"^\d\. \*\*([^*]+)\.\*\*", text, re.M)
    assert sections == list(check_proposal.SECTIONS)
    template = read("proposals/TEMPLATE.md")
    assert re.findall(r"^## (.+)$", template, re.M) == list(check_proposal.SECTIONS)
    assert re.findall(r"^- \*\*([A-Za-z]+):\*\*", template, re.M)[:6] == list(
        check_proposal.FIELDS)


def test_the_four_questions_are_the_reviewer_s_own():
    import review_linguisticity
    assert check_proposal.QUESTIONS == review_linguisticity.QUESTIONS
    assert check_proposal.DEPARTURE == review_linguisticity.DEPARTURE
    for document in ("governance/README.md", "governance/proposals.md"):
        for question in check_proposal.QUESTIONS:
            assert question in read(document), (document, question)


# ------------------------------------------------------------------ documents
def test_the_governance_cites_no_section_but_a_standard_s():
    for path in DOCUMENTS:
        assert not cites_a_section(read(path)), path


def test_every_path_and_link_the_governance_cites_exists():
    for path in DOCUMENTS:
        text = read(path)
        for cited in CITED_PATH.findall(text) + re.findall(
                r"`((?:governance|proposals)/[^`\s]*)`", text):
            assert os.path.exists(os.path.join(ROOT, cited.rstrip(".,;:"))), (path, cited)
        here = os.path.dirname(os.path.join(ROOT, path))
        for link in LINK.findall(text):
            if re.match(r"[a-z]+:", link):
                continue
            target, _, anchor = link.partition("#")
            target = os.path.normpath(os.path.join(here, target)) if target else \
                os.path.join(ROOT, path)
            assert os.path.exists(target), (path, link)
            if anchor:
                with open(target, encoding="utf-8") as f:
                    assert anchor in anchors(f.read()), (path, link)


def test_every_command_of_the_gate_exists():
    table = read("governance/README.md").split("## The gate")[1].split("\n\n")[2]
    tools = re.findall(r"`python3 (tools/[a-z_]+\.py)", table)
    assert len(tools) >= 9
    for tool in tools:
        assert os.path.isfile(os.path.join(ROOT, tool)), tool
