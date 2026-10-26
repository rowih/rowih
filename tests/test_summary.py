"""What a writer composes from (rowih.summary): the grammar summary lists every class a
writer names, with every member as the notation writes it, and every act word and
function word; the lexicon listing gives every word a writer can name and no other; each
spelling either gives reads back in the notation as the word it spells; and neither, nor
anything else the server or the skill tells an agent, cites the development record."""
import json
import re

import pytest

from rowih import data, summary
from rowih.notation import Printer, Reader, marked, sexp, takes_slots
from rowih.server import INSTRUCTIONS, Server

from test_specification import cites_a_section

LANG = data.load()
READER = Reader(LANG)
PRINTER = Printer(LANG)
GRAMMAR = summary.grammar(LANG)
LEXICON = summary.lexicon(LANG)


def test_the_summary_lists_every_class_a_writer_names_with_every_member():
    for c in LANG.grammar["classes"]:
        if c["group"] in summary.GENERATED_GROUPS and \
                c["identifier"] != "g.message.embedded-material":
            assert c["name"] in GRAMMAR.split("### Written by the generator")[1]
            continue
        line = next(x for x in GRAMMAR.splitlines() if x.startswith("- **%s**" % c["name"]))
        for m in c["members"]:
            assert "`%s`" % PRINTER.atom_of(LANG.items[m["identifier"]]) in line


def test_the_summary_lists_every_act_word_and_function_word():
    for e in LANG.entries.values():
        category = e["grammatical category"]
        if category == "act word":
            assert "| `%s` |" % LANG.items[e["machine identifier"]].gloss in GRAMMAR
        elif category in summary.FUNCTION_CATEGORIES and data.in_force(LANG, e):
            assert "| `%s` |" % e["key"].replace(" ", "-") in GRAMMAR


def test_the_listing_gives_every_word_a_writer_names_and_no_other():
    listed = set(re.findall(r"^\| `([^`]+)` \|", LEXICON, re.M))
    expected = set()
    for e in LANG.entries.values():
        if e["grammatical category"] in dict(summary.LISTING) and data.in_force(LANG, e):
            expected.add(PRINTER.atom_of(LANG.items[e["machine identifier"]]))
    assert listed == expected and len(listed) > 800
    deprecated = [f for f in LANG.deprecated]
    assert deprecated and not any("| %s |" % f in LEXICON for f in deprecated)


def _reads_as(written: str, item) -> bool:
    if " IDIOM-ENTRY " in written:
        # an idiom that takes slots, written as its marked unit
        entry = LANG.entries[item.identifier]
        return takes_slots(entry) and written == marked(entry) and \
            READER.node(sexp(re.sub(r"\(slot \d+\)", "(term thing)", written))[0])["kind"] \
            == "situation"
    if written.startswith("(idiom "):
        return READER.idiom_by_key.get(written[7:-1]) == item.identifier
    if written.startswith("(unknown "):
        return READER.part(sexp(written)[0])["status"] == "formation"
    if written.startswith("("):
        return True   # a member written as the head of a list
    if written in READER.entry_by_key:
        return READER.entry_by_key[written] == item.identifier
    return READER.by_gloss.get(written) == item.identifier


def test_every_spelling_reads_back_as_the_word_it_spells():
    count = 0
    for item in LANG.items.values():
        written = PRINTER.atom_of(item)
        if written is not None:
            assert _reads_as(written, item), (item.identifier, written)
            count += 1
    assert count > 1000


@pytest.mark.parametrize("kind", ["structural", "move-check", "suffix", "sense"])
def test_what_the_notation_never_writes_has_no_spelling(kind):
    assert all(PRINTER.atom_of(i) is None for i in LANG.items.values() if i.kind == kind)


def test_the_generators_classes_have_no_spelling():
    for c in ("g.numbers.numeral", "g.numbers.check-word", "g.message.message-field",
              "g.message.word-count", "g.protocol.protocol-statement"):
        for m in LANG.classes[c]["members"]:
            assert PRINTER.atom_of(LANG.items[m["identifier"]]) is None


def test_a_dialect_s_words_are_spelled_as_a_writer_names_them():
    from rowih import api
    for d in data.dialects().values():
        term = api.lookup(d["terms"][0]["term"])
        jargon = [i for i in term if i.kind == "jargon"][0]
        assert PRINTER.atom_of(jargon) == '(unknown "%s")' % jargon.form
        if d.get("forms"):
            form = [i for i in api.lookup(d["forms"][0]["term"]) if i.kind == "dialect"][0]
            assert PRINTER.atom_of(form) == "%s.%s" % (
                d["dialect"], d["forms"][0]["key"].replace(" ", "-"))


def test_nothing_told_to_an_agent_cites_a_section_but_a_standard_s():
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "skill", "rowih", "SKILL.md"), encoding="utf-8") as f:
        skill = f.read()
    tools = json.dumps([[t.title, t.description] for t in Server().offer.tools])
    for text in (GRAMMAR, LEXICON, skill, INSTRUCTIONS, tools):
        assert not cites_a_section(text)
