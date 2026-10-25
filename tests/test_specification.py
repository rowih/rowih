"""The reference specification, `specification/`: each table is what
`tools/build_specification.py` writes from the canonical data, the text cites no section but
a published standard's and no file the repository lacks, and every link between its
chapters resolves."""
import glob
import os
import re
import sys
import unicodedata

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import build_specification as spec  # noqa: E402

# The directories the public repository holds, so the only ones a public document may
# cite.
PUBLIC = ("language", "lexicon", "corpus", "python", "typescript", "tools", "tests",
          "specification", "skill", "governance", "proposals")
CITED_PATH = re.compile(r"`((?:%s)/[^`\s]*)`" % "|".join(PUBLIC))
# A section of a published standard, the only section a public document may cite, since
# its reader holds nothing else in which to look a section up.
SECTION_SIGN = spec.SECTION_SIGN
STANDARD_SECTION = re.compile(r"(?:RFC \d+|FIPS [\d-]+)\s+" + SECTION_SIGN + r"\s*[\d.]+")
LINK = re.compile(r"\]\(([^)\s]+)\)")
HEADING = re.compile(r"^#+ (.+)$", re.MULTILINE)


def chapters() -> dict:
    out = {}
    for path in spec.chapters():
        with open(path, encoding="utf-8") as f:
            out[os.path.basename(path)] = f.read()
    return out


def slug(heading: str) -> str:
    """The anchor GitHub gives a heading: lower case, every character that is not a
    letter, a digit, a space, a hyphen or an underscore removed, spaces made hyphens."""
    kept = "".join(ch for ch in heading.lower()
                   if ch in " -_" or unicodedata.category(ch)[0] in "LN")
    return kept.replace(" ", "-")


def anchors(text: str) -> set:
    seen, out = {}, set()
    for heading in HEADING.findall(text):
        base = slug(re.sub(r"`|\*", "", heading))
        n = seen.get(base, 0)
        out.add(base if n == 0 else "%s-%d" % (base, n))
        seen[base] = n + 1
    return out


def test_the_specification_has_its_chapters():
    assert {"README.md"} <= set(chapters())


def test_every_generated_block_is_what_the_tool_writes():
    for path in spec.chapters():
        with open(path, encoding="utf-8") as f:
            text = f.read()
        assert spec.regenerate(text, path) == text, path


def test_a_stale_block_is_found():
    text = "<!-- generated: maxima -->\n| stale |\n<!-- end generated -->\n"
    assert spec.regenerate(text, "planted") != text


def test_a_block_the_tool_does_not_write_is_refused():
    with pytest.raises(spec.UnknownBlock):
        spec.regenerate("<!-- generated: nothing -->\n<!-- end generated -->\n", "planted")


def cites_a_section(text: str) -> bool:
    """Whether `text` cites a section of anything but a published standard."""
    return SECTION_SIGN in STANDARD_SECTION.sub("", text)


def test_the_tool_refuses_a_section_of_anything_but_a_standard():
    standard = "encoded by RFC 4648 %s 6" % SECTION_SIGN
    assert spec.stated_in_full(standard) == standard
    with pytest.raises(spec.CitationLeft):
        spec.stated_in_full("as %s 3.4 decides" % SECTION_SIGN)


def test_the_specification_cites_no_section_but_a_standard_s():
    for name, text in chapters().items():
        assert not cites_a_section(text), name


def test_the_check_of_sections_finds_a_planted_one():
    assert cites_a_section("which %s 8.8 requires" % SECTION_SIGN)
    assert not cites_a_section("water freezes at 0 degrees (RFC 8032 %s 5.1)"
                               % SECTION_SIGN)
    assert not cites_a_section("the digest of FIPS 180-4 %s 6.2" % SECTION_SIGN)


def test_every_cited_path_exists_in_the_repository():
    for name, text in chapters().items():
        for path in CITED_PATH.findall(text):
            path = path.rstrip(".,;:")
            assert glob.glob(os.path.join(ROOT, path)), (name, path)


def test_every_link_between_chapters_resolves():
    texts = chapters()
    targets = {name: anchors(text) for name, text in texts.items()}
    for name, text in texts.items():
        for link in LINK.findall(text):
            if re.match(r"[a-z]+:", link):
                continue
            file, _, anchor = link.partition("#")
            file = file or name
            if file.startswith("../"):
                # a document of the public repository outside the specification
                target = os.path.normpath(os.path.join(ROOT, "specification", file))
                assert os.path.exists(target), (name, link)
                if anchor:
                    with open(target, encoding="utf-8") as f:
                        assert anchor in anchors(f.read()), (name, link)
                continue
            if not file.endswith(".md"):
                assert os.path.exists(os.path.join(ROOT, "specification", file)), (name, link)
                continue
            assert file in targets, (name, link)
            assert not anchor or anchor in targets[file], (name, link)


def test_the_check_of_links_finds_a_planted_break():
    assert slug("3. The move check word") == "3-the-move-check-word"
    assert "the-envelope" not in anchors("# The message\n\n## The body\n")
