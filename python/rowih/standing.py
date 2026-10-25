"""The order of standings (specification/meaning.md#standing-and-provenance): bases in
three tiers by what a hearer can check, strengths as intervals on the scale from zero to
one under a calibration, and the standing a summary keeps, the weakest basis and the
lowest strength of what it summarises (`inv.summary-keeps-lowest`)."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from .data import Language

# The calibration of the named levels, whose intervals the lexicon fixes. A number is
# under the calibration of the participant whose number it is (the language does not
# calibrate one agent's numbers against another's).
LEXICON = "lexicon"
BASIS = "g.standing.basis"
STRENGTH = "g.standing.strength"
UNSTATED_BASIS = "g.standing.basis.unstated"
UNSTATED_STRENGTH = "g.standing.strength.unstated"
COMPARATOR = "g.situations-and-contents.comparator."
UNSTATED_COMPARATOR = COMPARATOR + "unstated"
# Comparators under which a number names its point: exactly, and those that leave its
# precision unstated or approximate, which a summary restates as written.
AT_THE_POINT = {UNSTATED_COMPARATOR, COMPARATOR + "approximately",
                COMPARATOR + "as-a-representative-quantity", COMPARATOR + "exactly"}


@dataclass(frozen=True)
class Strength:
    """A strength as an interval under a calibration. A named level keeps its member;
    a number keeps its comparator and its numerals as written."""
    calibration: str
    lower: Decimal
    upper: Decimal
    lower_open: bool = False
    level: str | None = None
    comparator: str | None = None
    text: str = field(default="", compare=False)

    @property
    def key(self) -> tuple:
        """The order of lower ends: a closed end claims less than an open one at the
        same value."""
        return (self.lower, self.lower_open)


@dataclass(frozen=True)
class Standing:
    bases: frozenset
    strengths: frozenset


def tier(lang: Language, basis: str) -> int:
    for m in lang.classes[BASIS]["members"]:
        if m["identifier"] == basis:
            return m["tier"]
    raise KeyError(basis)


def named(lang: Language, member: str) -> Strength:
    for m in lang.classes[STRENGTH]["members"]:
        if m["identifier"] == member:
            iv = m["interval"]
            return Strength(LEXICON, Decimal(iv["lower"]), Decimal(iv["upper"]),
                            iv["lower open"], level=member)
    raise KeyError(member)


def numeric(number: str, comparator: str | None, calibration: str) -> Strength | None:
    """A numeric strength as an interval: an interval written with its two ends, at
    least a number up to one, at most a number from zero, and any other number as the
    point it names. None when the numerals are no decimal number."""
    try:
        if "~" in number:
            lo, hi = (Decimal(x) for x in number.split("~", 1))
        else:
            lo = hi = Decimal(number)
    except InvalidOperation:
        return None
    comparator = comparator or UNSTATED_COMPARATOR
    if comparator == COMPARATOR + "at-least":
        hi = Decimal(1)
    elif comparator == COMPARATOR + "at-most":
        lo = Decimal(0)
    elif comparator not in AT_THE_POINT:
        return None
    return Strength(calibration, lo, hi, comparator=comparator, text=number)


def standing_of(assertion: dict, lang: Language, speaker: str) -> Standing:
    """The standing an assertion states, in its normal form: its bases and its
    strengths, a number under the calibration it names or else its speaker's."""
    bases, strengths = set(), set()
    for p in assertion["parts"]:
        if p["kind"] == "value" and p["member"].startswith(BASIS + "."):
            bases.add(p["member"])
        elif p["kind"] == "value" and p["member"].startswith(STRENGTH + "."):
            strengths.add(named(lang, p["member"]))
        elif p["kind"] == "quantity":
            s = numeric(p["number"], p.get("comparator"), p.get("calibration") or speaker)
            if s is not None:
                strengths.add(s)
    if not bases:
        bases.add(UNSTATED_BASIS)
    if not strengths:
        strengths.add(named(lang, UNSTATED_STRENGTH))
    return Standing(frozenset(bases), frozenset(strengths))


def standings_of(content: list, lang: Language, speaker: str) -> list:
    """The standings an entry's speaker states: those of the assertions its move adds,
    not of what they report or suppose inside them."""
    return [standing_of(c, lang, speaker) for c in content if c.get("kind") == "assertion"]


def lowest(standings: list, lang: Language) -> Standing:
    """The standing a summary of these keeps. Of bases, the set of those in the lowest
    tier present, all of them, since bases within a tier are incomparable. Of strengths,
    under each calibration apart, the one with the least lower end, or where several
    share it the smallest interval containing them; and the unstated strength alone
    where any is unstated, since it is lower than every other. Nothing summarised has
    the lowest standing of all."""
    unstated = named(lang, UNSTATED_STRENGTH)
    if not standings:
        return Standing(frozenset({UNSTATED_BASIS}), frozenset({unstated}))
    bases = set().union(*(s.bases for s in standings))
    floor = max(tier(lang, b) for b in bases)
    kept_bases = frozenset(b for b in bases if tier(lang, b) == floor)
    strengths = set().union(*(s.strengths for s in standings))
    if unstated in strengths:
        return Standing(kept_bases, frozenset({unstated}))
    kept = set()
    for cal in sorted({s.calibration for s in strengths}):
        group = [s for s in strengths if s.calibration == cal]
        least = min(s.key for s in group)
        tied = {s for s in group if s.key == least}
        if len(tied) == 1:
            kept |= tied
        else:
            lo = least[0]
            hi = max(s.upper for s in tied)
            kept.add(Strength(cal, lo, hi, least[1], comparator=UNSTATED_COMPARATOR,
                              text="%s~%s" % (lo, hi)))
    return Standing(kept_bases, frozenset(kept))


def standing_parts(standing: Standing) -> list:
    """The parts that state a standing in an assertion of a summary, in the order the
    normal form puts them: the bases, the named strength, then each number with the
    participant whose calibration it is under."""
    parts = [{"kind": "value", "member": b} for b in sorted(standing.bases)]
    for s in sorted(standing.strengths, key=lambda x: (x.calibration != LEXICON,
                                                       x.calibration, x.key)):
        if s.level is not None:
            parts.append({"kind": "value", "member": s.level})
        else:
            parts.append({"kind": "quantity", "comparator": s.comparator,
                          "number": s.text, "unit": None, "per": None,
                          "calibration": s.calibration})
    return parts
