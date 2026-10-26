"""What a writer composes from, generated from the canonical data alone: the grammar
summary, which lists every grammatical class with its members as the notation writes
them, the act words and the closed sets of function words; and the lexicon listing,
which gives every word a writer can name with its form and meaning. The server offers
both as resources and the skill carries both as references; the reference specification
states the rules they summarise (specification/notation.md, specification/grammar.md)."""
from __future__ import annotations

from .data import Language, in_force
from .notation import Printer

# the groups of classes the generator writes and a writer never names
GENERATED_GROUPS = ("numbers", "message", "protocol")
# the categories of the lexicon whose words are a closed set of function words, listed
# in full in the grammar summary, in this order
FUNCTION_CATEGORIES = ("unit of measure", "discourse relation", "politeness word", "diction")
# the categories of the lexicon listing, in this order, each with its heading
LISTING = (("predicate root", "Predicate roots"), ("nominal root", "Nominal roots"),
           ("derivation", "Derivations"), ("compound", "Compounds"),
           ("unit of measure", "Units of measure"), ("discourse relation", "Discourse relations"),
           ("politeness word", "Politeness words"), ("diction", "Dictions"),
           ("idiom", "Idioms"))


def _releases(lang: Language) -> str:
    return "language %s, lexicon %s, protocol %s" % (
        lang.grammar["version"], lang.release["version"], lang.protocol["version"])


def _status(c: dict) -> str:
    status = c["status"]
    if status["kind"] == "default":
        return "default: %s" % status["default"]
    return status["kind"]


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def grammar(lang: Language) -> str:
    """The grammar summary, as Markdown."""
    printer = Printer(lang)
    out = ["# Rowih: the grammar summary", "",
           "Generated from the data of %s. A writer states each move in the notation and "
           "the generator writes the message; this summary lists what the notation names. "
           "The notation itself is stated in the specification's chapter on the notation, "
           "and a content word is found with `lookup` or in the lexicon listing."
           % _releases(lang), "",
           "## The grammatical classes", "",
           "Each class is listed with when it must be stated or what it defaults to, the "
           "unit it belongs to (move, assertion, situation or term), what it applies to, "
           "and its members as the notation writes them. A member may always be written "
           "with its class's name before it, in capitals, as `POLARITY.NEGATIVE`.", ""]
    generated = []
    group = None
    for c in lang.grammar["classes"]:
        if c["group"] in GENERATED_GROUPS and c["identifier"] != "g.message.embedded-material":
            generated.append(c["name"])
            continue
        if c["group"] != group:
            group = c["group"]
            out += ([""] if out[-1] else []) + ["### %s" % group.capitalize(), ""]
        members = [printer.atom_of(lang.items[m["identifier"]]) for m in c["members"]]
        out.append("- **%s** (%s; %s; applies to %s): %s" % (
            c["name"], _status(c), c["scope"], c["applies to"],
            ", ".join("`%s`" % m for m in members)))
    out += ["", "### Written by the generator", "",
            "The generator writes these classes from the envelope's values and the moves, "
            "and a writer never names them: %s." % ", ".join(generated), "",
            "## The act words", "",
            "An act word stands in a move's head for the force members it expands to.", "",
            "| Written | Stands for | Meaning |", "|---|---|---|"]
    acts = sorted((e for e in lang.entries.values() if e["grammatical category"] == "act word"),
                  key=lambda e: e["key"])
    for e in acts:
        item = lang.items[e["machine identifier"]]
        stands = " ".join(lang.items[m].gloss for m in e["expansion"])
        out.append("| `%s` | `%s` | %s |" % (item.gloss, stands, _cell(e["definition"])))
    out += ["", "## The function words", "",
            "These closed sets are written by their keys: a unit of measure in a quantity, "
            "a discourse relation, a politeness word or a diction in a move's head.", ""]
    for category in FUNCTION_CATEGORIES:
        entries = sorted((e for e in lang.entries.values()
                          if e["grammatical category"] == category and in_force(lang, e)),
                         key=lambda e: e["key"])
        out += ["### %ss" % category.capitalize(), "", "| Written | Meaning |", "|---|---|"]
        out += ["| `%s` | %s |" % (printer.atom_of(lang.items[e["machine identifier"]]),
                                    _cell(e["definition"])) for e in entries]
        out.append("")
    return "\n".join(out)


def lexicon(lang: Language) -> str:
    """The lexicon listing, as Markdown: every word a writer can name, by category, with
    how the notation writes it, its form and its meaning."""
    printer = Printer(lang)
    out = ["# Rowih: the lexicon listing", "",
           "Generated from the data of %s. Every word a writer can name in the notation, "
           "by category: how the notation writes it, the word's form and its meaning. A "
           "conventional sense is not listed, since the root is written and the frame it "
           "stands in selects the sense; a deprecated word is not listed, since the "
           "notation names the entry in force. An idiom that takes constituents the "
           "speaker supplies is written as its unit marked IDIOM-ENTRY, each `(slot N)` "
           "replaced by a constituent; `(idiom KEY)` writes the others." % _releases(lang),
           ""]
    for category, heading in LISTING:
        entries = sorted((e for e in lang.entries.values()
                          if e["grammatical category"] == category and in_force(lang, e)),
                         key=lambda e: e["key"])
        if not entries:
            continue
        out += ["## %s" % heading, "", "| Written | Form | Meaning |", "|---|---|---|"]
        for e in entries:
            item = lang.items[e["machine identifier"]]
            out.append("| `%s` | %s | %s |" % (printer.atom_of(item), item.form,
                                              _cell(e["definition"])))
        out.append("")
    return "\n".join(out)
