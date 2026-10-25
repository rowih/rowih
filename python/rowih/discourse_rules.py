"""The checker's rules for reference and discourse
(specification/discourse.md#summaries-and-confirmations): what a summary names and the
standing it states, the independence of a confirmation, and the statuses of a referent
where they apply. Each takes the checker whose diagnostics it adds to; `checker.py` calls
them."""
from __future__ import annotations

from . import checker as base
from .standing import LEXICON, tier

EXTERNAL = {"g.reference.access.external", "g.reference.person.external-source"}
COLLECTIVE_PERSONS = {"g.reference.person.inclusive-collective",
                      "g.reference.person.exclusive-collective"}
COLLECTIVE = COLLECTIVE_PERSONS | {"g.situations-and-contents.quantifier.collective"}


def check_summary(checker, t: dict, adds: str):
    """A summary names every entry it summarises, by NAMES with its expectation and
    the change NONE, and only a summary names more than one entry
    (specification/discourse.md#summaries-and-confirmations)."""
    more = t.get("also_named") or []
    change = [base.short(c) for c in t["change"]]
    if adds == "summary" and (not t.get("named") or change != ["none"]):
        checker.add("d.checker.force", t, expected=["the entries summarised, with NONE"],
                    note="a summary names what it summarises and changes none of it")
    if more and adds != "summary":
        checker.add("d.checker.force", more[0], expected=["one entry named"],
                    note="only a summary names more than one entry")
    for r in more:      # the first reference is held to this by `check_move`
        if r["ref"] != "names" or r["target"] != "entry":
            checker.add("d.checker.expectation", r,
                        note="a summary names entries, each with what it expects of it")


def check_confirmation(checker, t: dict, assertion: dict):
    """The independence of a confirmation is stated on a confirmation alone, an
    asserted position naming a position with the change NONE, and an independent
    one states the source it rests on (`inv.independent-confirmation`)."""
    values = [p for p in assertion["parts"] if p["kind"] == "value"
              and p["member"].startswith("g.standing.independence-of-a-confirmation.")]
    if not values:
        return
    named = t.get("named")
    adds, _ = base.entry_kind(t["adds"])
    confirming = (adds == "asserted-position" and named is not None
                  and named["ref"] == "names" and named["target"] == "entry"
                  and [base.short(c) for c in t["change"]] == ["none"]
                  and base.entry_kind(named["expected"])[0] in ("asserted-position",
                                                           "conceded-position"))
    if not confirming:
        checker.add("d.checker.ill-typed", values[0], expected=["a confirmation"],
                    detected=[values[0]["member"]])
    elif base.short(values[0]["member"]) == "independent" and not any(
            p["kind"] == "filler" and p["role"] == "g.standing.provenance-link.source"
            for p in assertion["parts"]):
        checker.add("d.checker.confirmation-source", values[0],
                    expected=["the independent source it rests on"])


def check_summary_standing(checker, t: dict):
    """The standing of an assertion of a summary: bases all of one tier, the unstated
    basis and the unstated strength each alone, and one strength for each
    calibration (`inv.summary-keeps-lowest`)."""
    bases = [p for p in t["parts"] if p["kind"] == "value"
             and p["member"].startswith("g.standing.basis.")]
    if len({tier(checker.lang, p["member"]) for p in bases}) > 1:
        checker.add("d.checker.ill-typed", bases[1], expected=["bases of one tier"])
    if len(bases) != len({p["member"] for p in bases}):
        checker.add("d.checker.ill-typed", bases[-1], note="a basis stated twice")
    calibrations = [LEXICON for p in t["parts"] if p["kind"] == "value"
                    and p["member"].startswith("g.standing.strength.")]
    calibrations += [p.get("calibration") for p in t["parts"] if p["kind"] == "quantity"]
    if len(calibrations) != len(set(calibrations)):
        checker.add("d.checker.ill-typed", t, note="two strengths under one calibration")
    unstated = any(p["kind"] == "value" and p["member"] == "g.standing.strength.unstated"
                   for p in t["parts"])
    if unstated and len(calibrations) > 1:
        checker.add("d.checker.ill-typed", t, note="the unstated strength stands alone")


def check_referent(checker, t: dict):
    """The statuses of a referent where they apply (specification/grammar.md#reference):
    verification, and a source, only on an external referent, a named third party's
    verification with the source that verified it, the reading of a collective on a
    collective, and no referent reached through a reference written as new."""
    values = {p["member"] for p in t["parts"] if p["kind"] == "value"}
    sources = [p for p in t["parts"] if p["kind"] == "filler"
               and p["role"] == "g.standing.provenance-link.source"]
    external = bool(values & EXTERNAL)
    verification = sorted(v for v in values if v.startswith("g.reference.verification."))
    if (verification or sources) and not external:
        checker.add("d.checker.ill-typed", t, expected=["an external referent"],
                    detected=verification or ["a source"])
    if "g.reference.verification.verified-by-a-named-third-party" in values and \
            not sources:
        checker.add("d.checker.ill-typed", t, expected=["the source that verified it"])
    if any(v.startswith("g.reference.reading-of-a-collective.") for v in values) and \
            not values & COLLECTIVE:
        checker.add("d.checker.ill-typed", t, expected=["a collective referent"])
    if "g.reference.discourse-status.new" in values and any(
            p["kind"] == "ref" for p in t["parts"]):
        checker.add("d.checker.ill-typed", t, note="a referent reached through a "
                    "reference was introduced where it was first written")


def check_collectives(checker, t: dict):
    """A collective agent that acts, or that holds a normative state, states whether
    it does so jointly or each member for itself (specification/grammar.md#reference); a
    plural referent read collectively may state it, and need not."""
    normative = any(p["kind"] == "value" and p["member"].startswith(
        "g.force.kind-of-normative-entry.") for p in t["parts"])
    for p in t["parts"]:
        if p["kind"] != "filler" or p["filler"].get("kind") != "term":
            continue
        role = base.short(p["role"])
        if role != "actor" and not (role == "holder" and normative):
            continue
        values = {q["member"] for q in p["filler"]["parts"] if q["kind"] == "value"}
        if values & COLLECTIVE_PERSONS and not any(
                v.startswith("g.reference.reading-of-a-collective.") for v in values):
            checker.add("d.checker.collective-reading", p["filler"],
                        expected=["joint or distributive"])
