"""The discourse of the record (specification/discourse.md): handles fixed by their
author, every reference a dependency, normalisation that reads no view, the standing a
summary keeps, the confirmations that raise standing, the common ground and what a
hearer infers, each tested in views, over the corpus, over generated standings and over
seeded exchanges in which messages are lost, repeated and reordered."""
import copy
import random

from hypothesis import given, settings, strategies as st

from rowih import api, data
from rowih import conventions as C
from rowih import discourse as D
from rowih import standing as S
from rowih.generator import Generator
from rowih.moves import resolve_deixis
from rowih.notation import Reader
from rowih.register_rules import shared_context
from rowih.tree import strip_private
from rowih.view import View

from corpus import items, messages

GEN = Generator()
READ = Reader(GEN.lang)
LANG = data.load()
IS = "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE"
MESSAGES = messages()
TEXTS = {(i, k): t for i, k, _, t in MESSAGES}


def message(notation, sender=1, recipients=(2,), identifier=1, first=1, time=0):
    return GEN.message(READ.moves(notation), sender=sender, recipients=recipients,
                       identifier=identifier, first_entry=first,
                       time=str(1759622400 + time))


# ---------------------------------------------------------------- handles and dependencies

def test_handles_are_the_authors_whatever_arrives():
    """A hearer that receives an author's later message without its earlier one gives
    each entry the number its author gave it (protocol 0.2)."""
    first = message("(move ASSERTED-POSITION (assertion OBSERVATION (situation run "
                    "(UNDERGOER (term service DEFINITE)))))", recipients=(2, 3))
    later = message("(move ASSERTED-POSITION (assertion OBSERVATION (situation break "
                    "(UNDERGOER (term network DEFINITE)))))", recipients=(3,), first=2)
    view = View("3")
    assert view.hear(later) == []
    assert list(view.entries) == [("1", "2")]
    assert view.hear(first) == []
    assert sorted(view.entries) == [("1", "1"), ("1", "2")]


def test_a_handle_given_twice_is_refused():
    view = View("2")
    text = "(move ASSERTED-POSITION (assertion OBSERVATION (situation run (UNDERGOER (term " \
           "service DEFINITE)))))"
    assert view.hear(message(text)) == []
    codes = [d.code for d in view.hear(message(text, identifier=2))]
    assert codes == ["d.view.handle-repeated"]


def test_a_reference_in_content_is_a_dependency():
    """A move whose content names an entry the hearer lacks is held until it arrives, and
    one whose content expects another status is refused (`inv.dependencies-explicit`)."""
    position = message("(move ASSERTED-POSITION (assertion OBSERVATION (situation run "
                       "(UNDERGOER (term service DEFINITE)))))")
    premised = message("(move ASSERTED-POSITION (assertion INFERENCE (PREMISE (names 1 1 "
                       "ASSERTED-POSITION %s)) (situation break (UNDERGOER (term network "
                       "DEFINITE)))))" % IS, identifier=2, first=2)
    view = View("2")
    assert [d.code for d in view.hear(premised)] == ["d.view.held"]
    assert view.hear(position) == []
    assert view.held == [] and ("1", "2") in view.entries
    wrong = message("(move ASSERTED-POSITION (assertion INFERENCE (PREMISE (names 1 1 "
                    "ASSERTED-POSITION EXPECTED-STATUS-OF-AN-ENTRY.WITHDRAWN)) (situation "
                    "break (UNDERGOER (term network DEFINITE)))))", identifier=3, first=3)
    assert [d.code for d in view.hear(wrong)] == ["d.view.expectation-not-met"]


def test_a_mention_is_no_dependency():
    view = View("2")
    text = message("(move ASSERTED-POSITION (assertion REPORT (situation unknown (UNDERGOER "
                   "(term (mentions 3 9))))))")
    assert view.hear(text) == [] and view.held == []


# ---------------------------------------------------------------- view-independent normalisation

def _recorded(view):
    """The normal forms a view recorded, by handle."""
    return {h: e.normal for h, e in view.entries.items()}


def _expected():
    """Every corpus entry's normal form as parsing alone gives it, by item and handle."""
    out = {}
    for item_id, k, m, text in MESSAGES:
        a = api.parse(text)
        for i, n in enumerate(a.normal):
            out[(item_id, (str(m["sender"]), str(m["first entry"] + i)))] = strip_private(n)
    return out


def test_normal_forms_do_not_depend_on_the_view():
    """Every corpus message normalises to the same normal form in an empty view, in a
    view that holds its whole exchange, and in a view that heard the exchange backwards,
    and to the one parsing alone gives (`inv.view-independent-normalisation`)."""
    expected = _expected()
    for item in items():
        texts = [TEXTS[(item["id"], k)] for k in range(1, len(item["messages"]) + 1)]
        parties = sorted({str(r) for m in item["messages"] for r in m["recipients"]})
        for party in parties:
            views = []
            for order in (texts, list(reversed(texts))):
                v = View(party)
                for t in order:
                    v.hear(t)
                views.append(v)
            for t in texts:
                v = View(party)
                v.hear(t)
                views.append(v)
            for v in views:
                for h, n in _recorded(v).items():
                    assert n == expected[(item["id"], h)], (item["id"], party, h)


# ---------------------------------------------------------------- the standing a summary keeps

BASES = [m["identifier"] for m in LANG.classes["g.standing.basis"]["members"]]
LEVELS = [m["identifier"] for m in LANG.classes["g.standing.strength"]["members"]]
COMPARATORS = ["g.situations-and-contents.comparator." + c
               for c in ("exactly", "at-least", "at-most", "unstated")]


@st.composite
def standings(draw):
    bases = frozenset(draw(st.lists(st.sampled_from(BASES), min_size=1, max_size=2)))
    strengths = set()
    for _ in range(draw(st.integers(1, 2))):
        if draw(st.booleans()):
            strengths.add(S.named(LANG, draw(st.sampled_from(LEVELS))))
        else:
            n = draw(st.sampled_from(["0", "0.25", "0.5", "0.7", "0.8", "1"]))
            s = S.numeric(n, draw(st.sampled_from(COMPARATORS)), draw(st.sampled_from("12")))
            strengths.add(s)
    return S.Standing(bases, frozenset(strengths))


@settings(max_examples=400, deadline=None)
@given(st.lists(standings(), min_size=1, max_size=5))
def test_a_summary_keeps_the_lowest_standing(group):
    """For every set of standings, the summary keeps every basis of the lowest tier
    present and no other, and under each calibration apart the strength with the least
    lower end, widened to contain those that share it and never narrowed; an unstated
    strength alone where any is unstated (`inv.summary-keeps-lowest`)."""
    kept = S.lowest(group, LANG)
    bases = set().union(*(s.bases for s in group))
    floor = max(S.tier(LANG, b) for b in bases)
    assert kept.bases == {b for b in bases if S.tier(LANG, b) == floor}
    strengths = set().union(*(s.strengths for s in group))
    unstated = S.named(LANG, S.UNSTATED_STRENGTH)
    if unstated in strengths:
        assert kept.strengths == {unstated}
        return
    calibrations = {s.calibration for s in strengths}
    assert {s.calibration for s in kept.strengths} == calibrations
    for cal in calibrations:
        mine = [s for s in kept.strengths if s.calibration == cal]
        assert len(mine) == 1
        k = mine[0]
        theirs = [s for s in strengths if s.calibration == cal]
        least = min(s.key for s in theirs)
        assert k.key == least
        tied = [s for s in theirs if s.key == least]
        assert k.upper == max(s.upper for s in tied)
        assert all(s.lower >= k.lower and s.upper <= k.upper for s in tied)


def _summary_exchange(summary_grounds):
    a = message("(move ASSERTED-POSITION (assertion OBSERVATION PROBABLE (situation run "
                "POLARITY.NEGATIVE (UNDERGOER (term service DEFINITE)))))", recipients=(2, 3))
    b = message("(move ASSERTED-POSITION (assertion REPORT CERTAIN (SOURCE (term TOOL)) "
                "(situation break (UNDERGOER (term network DEFINITE)))))", sender=2,
                recipients=(1, 3))
    s = message("(move SUMMARY NONE (names 1 1 ASSERTED-POSITION %s) (names 2 1 "
                "ASSERTED-POSITION %s) (assertion %s (situation CONJUNCTION (CONTENT "
                "(situation run POLARITY.NEGATIVE (UNDERGOER (term service DEFINITE)))) "
                "(CONTENT (situation break (UNDERGOER (term network DEFINITE)))))))"
                % (IS, IS, summary_grounds), sender=3, recipients=(1, 2))
    view = View("1")
    assert view.hear(a) == [] and view.hear(b) == []
    return [d.code for d in view.hear(s)]


def test_a_summary_states_exactly_the_standing_it_keeps():
    """A summary of an observation held probable and a report held certain keeps both
    bases and the strength probable; one that raises the strength, orders the bases of
    one tier, or takes its basis from the act of summarising is refused
    (`discourse/summary-raises-standing`, `epistemic/summary-basis-from-the-act`)."""
    assert _summary_exchange("OBSERVATION REPORT PROBABLE") == []
    assert _summary_exchange("OBSERVATION REPORT CERTAIN") == ["d.view.summary-standing"]
    assert _summary_exchange("OBSERVATION PROBABLE") == ["d.view.summary-standing"]
    assert _summary_exchange("INFERENCE PROBABLE") == ["d.view.summary-standing"]


def test_the_corpus_summaries_keep_the_lowest_standing():
    for item in items():
        if any("SUMMARY" in m.get("notation", "") for m in item["messages"]):
            for party in sorted({str(r) for m in item["messages"] for r in m["recipients"]}):
                v = View(party)
                for k, m in enumerate(item["messages"], 1):
                    if party in {str(m["sender"])} | {str(r) for r in m["recipients"]}:
                        assert v.hear(TEXTS[(item["id"], k)]) == []
                assert v.held == []


# ---------------------------------------------------------------- independent confirmation

def test_only_independent_confirmation_raises_standing():
    """A confirmation from a fork of a counted confirmer, or one resting on the same
    source as the position, raises nothing; each that raises states its independent source
    (`inv.independent-confirmation`). The fork's lineage is what its first message states;
    a view that is not told of it counts the fork as its own lineage."""
    item = next(i for i in items() if i["id"] == "e2-confirmation")
    fork = next(m for m in item["messages"] if m["sender"] == 4)
    # the fork's message without its first move, the statement of its lineage
    unstated = message("(move " + fork["notation"].split(") (move ", 1)[1], sender=4,
                       recipients=(1, 2, 3), time=int(fork["time"]) - 1759622400)
    for party, stated in (("1", True), ("3", True), ("1", False)):
        view = View(party)
        for k, m in enumerate(item["messages"], 1):
            if party == str(m["sender"]) or party in {str(r) for r in m["recipients"]}:
                text = TEXTS[(item["id"], k)] if stated or m["sender"] != 4 else unstated
                assert view.hear(text) == []
        counted = D.corroboration(view, ("1", "1"))
        lineage = C.lineage(view)
        lineages = [lineage.get("1", "1")]
        for c in counted:
            assert c["sources"] and c["lineage"] not in lineages
            lineages.append(c["lineage"])
        expected = [("2", "1")] if stated else [("2", "1"), ("4", "1")]
        assert [c["entry"] for c in counted] == expected
        assert len(D.confirmations(view, ("1", "1"))) == 3


# ---------------------------------------------------------------- common ground

P = "(situation break (UNDERGOER (term network DEFINITE)))"


def test_neither_acknowledgement_nor_silence_grounds_without_a_convention():
    item = next(i for i in items() if i["id"] == "e2-common-ground")
    for party in ("1", "2"):
        view = View(party)
        for k in range(1, len(item["messages"]) + 1):
            view.hear(TEXTS[(item["id"], k)])
        grounded = {(c["entry"], c["part"]) for c in D.common_ground(view, now=1e12)}
        assert (("1", "2"), None) not in grounded       # acknowledged only
        assert (("1", "1"), None) in grounded           # agreed


def test_silence_grounds_only_under_a_declared_interval_and_without_objection():
    """Silence accepts only for a participant bound to the convention that its silence
    accepts, by its own commitment, and only over the convention's interval
    (`conventions.silence`)."""
    position = message("(move ASSERTED-POSITION (assertion OBSERVATION %s))" % P)
    convention = message("(move NORMATIVE-ENTRY COMMITMENT BOUND SPEAKERS-OWN (situation "
                         "assent (EVENT-TIME EXACTLY 60 SECOND) (ACTOR (term SELF))))",
                         sender=2, recipients=(1,), time=-100)
    t = 1759622400
    plain = View("1")
    plain.hear(position)
    assert D.common_ground(plain, now=t + 10 ** 6) == []
    declared = View("1")
    assert declared.hear(convention) == []
    assert C.silence(declared, "2") == 60.0 and C.silence(declared, "1") is None
    declared.hear(position)
    assert D.common_ground(declared, now=t + 59) == []
    assert [c["entry"] for c in D.common_ground(declared, now=t + 60)] == [("1", "1")]
    challenge = message("(move ISSUE CHALLENGE NONE (names 1 1 ASSERTED-POSITION %s) "
                        "(situation POLAR break (UNDERGOER (term network DEFINITE))))" % IS,
                        sender=2, recipients=(1,), time=30, identifier=2, first=2)
    assert declared.hear(challenge) == []
    assert D.common_ground(declared, now=t + 600) == []


def test_presupposed_content_needs_the_viewers_own_acceptance():
    """B's view holds A's presupposing position out of the common ground until B itself
    accepts it, never by accommodation; A's view needs B's acceptance alone."""
    item = next(i for i in items() if i["id"] == "e2-common-ground")
    views = {p: View(p) for p in ("1", "2")}
    for k in range(1, len(item["messages"]) + 1):
        for v in views.values():
            v.hear(TEXTS[(item["id"], k)])
    agree = message("(move ASSERTED-POSITION NONE (names 1 2 ASSERTED-POSITION %s) "
                    "(assertion REPORT CERTAIN (SOURCE (term (party 1))) (situation "
                    "CONJUNCTION (CONTENT (situation #1 run POLARITY.NEGATIVE (UNDERGOER "
                    "(term service DEFINITE)))) (CONTENT (situation cause (ACTOR (term "
                    "(names 1 1 ASSERTED-POSITION %s))) (CONTENT @1))))))" % (IS, IS),
                    sender=2, recipients=(1,), identifier=3, first=3, time=300)
    for v in views.values():
        assert v.hear(agree) == []
    for p, v in views.items():
        assert (("1", "2"), None) in {(c["entry"], c["part"]) for c in D.common_ground(v)}, p


# ---------------------------------------------------------------- inference kept apart

def _said(expected: dict, item_id: str, handle: tuple, recipients: dict) -> list:
    """What a move says: its normal form's content; for an acceptance that names the
    entry it accepts in place of restating it, the device of shared context, the content
    of that entry with deixis resolved under its author, which the speaker answers for as
    the convention's expansion and not as a hearer's inference."""
    n = expected[(item_id, handle)]
    if not shared_context(n):
        return n["constituents"]
    named = (str(n["named"]["author"]), str(n["named"]["number"]))
    return resolve_deixis(expected[(item_id, named)]["constituents"], named[0],
                          recipients[named])


def test_what_a_hearer_infers_is_never_recorded_as_said():
    """After every corpus exchange, and after its hearer resolves each set of readings
    and draws an inference from each entry, the record attributes to each speaker
    exactly the content of its move's normal form, or what its device of shared context
    stands for (`inv.inference-not-said`)."""
    expected = _expected()
    recipients = {(str(m["sender"]), str(m["first entry"] + i)): tuple(
        str(r) for r in m["recipients"]) for _, _, m, t in MESSAGES
        for i in range(len(api.parse(t).moves))}
    for item in items():
        for party in sorted({str(r) for m in item["messages"] for r in m["recipients"]}):
            view = View(party)
            for k, m in enumerate(item["messages"], 1):
                if party in {str(m["sender"])} | {str(r) for r in m["recipients"]}:
                    view.hear(TEXTS[(item["id"], k)])
            for h, e in list(view.entries.items()):
                for node in _readings(e.content):
                    view.resolve(h, node["readings"][0])
                view.infer([h], [_negated(e.content)], "implicature")
            for h in view.entries:
                assert view.said(h) == _said(expected, item["id"], h, recipients)
            assert all(i.holder == party for i in view.inferences)


def _readings(node):
    if isinstance(node, dict):
        if node.get("kind") == "readings":
            yield node
        for v in node.values():
            yield from _readings(v)
    elif isinstance(node, list):
        for x in node:
            yield from _readings(x)


def _negated(content):
    """A stand-in for a scalar implicature: the first situation, its polarity reversed."""
    content = copy.deepcopy(content)
    for node in _situations(content):
        for p in node["parts"]:
            if p.get("member") == "g.situations-and-contents.polarity.affirmative":
                p["member"] = "g.situations-and-contents.polarity.negative"
                return node
        return node
    return {"kind": "situation", "name": None, "parts": []}


def _situations(node):
    if isinstance(node, dict):
        if node.get("kind") == "situation":
            yield node
        for v in node.values():
            yield from _situations(v)
    elif isinstance(node, list):
        for x in node:
            yield from _situations(x)


# ---------------------------------------------------------------- seeded exchanges with faults

CONTENTS = ["(situation run POLARITY.NEGATIVE (UNDERGOER (term service DEFINITE)))",
            "(situation break (UNDERGOER (term network DEFINITE)))",
            "(situation corrupt (UNDERGOER (term record DEFINITE)))"]
GROUNDS = ["OBSERVATION CERTAIN", "REPORT PROBABLE", "INFERENCE HIGHLY-PROBABLE",
           "TRAINED-KNOWLEDGE UNCERTAIN"]


def _script(rng, steps=10, fork=False):
    """A random exchange among three participants, each message to the other two: new
    positions, agreements, confirmations and concessions restating an earlier position,
    acknowledgements, challenges and summaries stating the standing they keep. Where
    `fork` holds, participant 3 opens by stating that it shares 2's lineage."""
    counts = {"1": 0, "2": 0, "3": 0}
    idents = {"1": 0, "2": 0, "3": 0}
    positions = []          # (handle, content index, grounds)
    script = []
    if fork:
        counts["3"] = idents["3"] = 1
        script.append(message("(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN "
                              "(situation descend (UNDERGOER (term SELF)) (CONTENT (term "
                              "(party 2))))))", sender=3, recipients=(1, 2), time=-10))
    for step in range(steps):
        s = rng.choice("123")
        recipients = tuple(p for p in "123" if p != s)
        others = [p for p in positions if p[0][0] != s]
        roll = rng.random()
        if not others or roll < 0.3:
            c, g = rng.randrange(3), rng.choice(GROUNDS)
            notation = "(move ASSERTED-POSITION (assertion %s %s))" % (g, CONTENTS[c])
            new = (c, g)
        elif roll < 0.55:
            (a, n), c, g = rng.choice(others)
            head = "ASSERTED-POSITION" if rng.random() < 0.7 else "CONCEDED-POSITION"
            if head == "ASSERTED-POSITION" and rng.random() < 0.5:
                grounds = "OBSERVATION CERTAIN INDEPENDENT (SOURCE (term %s))" % rng.choice(
                    ["TOOL", "SYSTEM", "(party %s)" % a])
            else:
                grounds = "REPORT CERTAIN (SOURCE (term (party %s)))" % a
            notation = "(move %s NONE (names %s %s ASSERTED-POSITION %s) (assertion %s %s))" \
                % (head, a, n, IS, grounds, CONTENTS[c])
            new = (c, grounds) if head == "ASSERTED-POSITION" else None
        elif roll < 0.7:
            (a, n), c, g = rng.choice(others)
            notation = "(move NOTHING-BEYOND-ITS-OWN-RECORD ACKNOWLEDGEMENT WHOLE-ENTRY " \
                       "ON-THE-MOVE (names %s %s ASSERTED-POSITION %s))" % (a, n, IS)
            new = None
        elif roll < 0.8:
            (a, n), c, g = rng.choice(others)
            notation = "(move ISSUE CHALLENGE NONE (names %s %s ASSERTED-POSITION %s) " \
                       "(situation POLAR %s))" % (a, n, IS, CONTENTS[c][len("(situation "):-1])
            new = None
        else:
            chosen = rng.sample(positions, min(len(positions), rng.randint(1, 2)))
            kept = S.lowest([S.standing_of(READ.moves(
                "(move ASSERTED-POSITION (assertion %s %s))" % (g, CONTENTS[c]))[0]
                ["constituents"][0], LANG, h[0]) for h, c, g in chosen], LANG)
            grounds = " ".join(LANG.items[b].gloss for b in sorted(kept.bases)) + " " + \
                " ".join(LANG.items[x.level].gloss for x in kept.strengths)
            names = " ".join("(names %s %s ASSERTED-POSITION %s)" % (h[0], h[1], IS)
                             for h, _, _ in sorted(chosen))
            notation = "(move SUMMARY NONE %s (assertion %s %s))" % (
                names, grounds, CONTENTS[chosen[0][1]])
            new = None
        counts[s] += 1
        idents[s] += 1
        handle = (s, str(counts[s]))
        if new is not None:
            positions.append((handle, new[0], new[1]))
        script.append(message(notation, sender=int(s), recipients=tuple(map(int, recipients)),
                              identifier=idents[s], first=counts[s], time=step * 10))
    return script


def _deliver(rng, script, party):
    """What one participant receives: its own messages, and each other one lost, kept
    or repeated, in an order shuffled within a window."""
    out = []
    for text in script:
        a = api.parse(text)
        if a.message.envelope.sender.text == party:
            out.append(text)
            continue
        r = rng.random()
        if r < 0.15:
            continue
        out.append(text)
        if r > 0.9:
            out.append(text)
    for i in range(len(out) - 1):
        if rng.random() < 0.3:
            out[i], out[i + 1] = out[i + 1], out[i]
    return out


def test_seeded_exchanges_with_faults_keep_the_invariants():
    """Over seeded exchanges in which messages are lost, repeated and reordered, every
    view normalises as parsing alone does, attributes to each speaker exactly what it
    said, counts no confirmation of a shared lineage or source, and grounds nothing
    without every other participant's acceptance on record."""
    rng = random.Random(40)
    for run in range(60):
        script = _script(rng, fork=bool(run % 2))
        normal = {}
        for text in script:
            a = api.parse(text)
            env = a.message.envelope
            for i, n in enumerate(a.normal):
                normal[(env.sender.text, str(env.first_entry.integer() + i))] = \
                    strip_private(n)
        for party in "123":
            view = View(party)
            for text in _deliver(rng, script, party):
                view.hear(text)
            for h, e in view.entries.items():
                assert e.normal == normal[h]
                assert view.said(h) == normal[h]["constituents"]
            lineage = C.lineage(view)
            for e in view.entries.values():
                seen = {lineage.get(e.handle[0], e.handle[0])}
                for c in D.corroboration(view, e.handle):
                    assert c["lineage"] not in seen and c["sources"]
                    seen.add(c["lineage"])
            for c in D.common_ground(view):
                for p, ev in c["evidence"].items():
                    kind, h = ev
                    assert kind in ("author", "position")
                    if kind == "author":
                        assert p == c["entry"][0]
                    else:
                        assert h[0] == p and D.accepts(view, view.entries[h], c["entry"],
                                                       c["part"])


# ---------------------------------------------------------------- the expected kind

def test_an_expected_kind_is_the_entrys_kind_without_its_bindingness():
    """An entry's kind is what its move added, with the kind of issue, normative entry or
    setting; the bindingness its move stated is no part of it, so the productions state
    the expected kind of a reference as both readers read it, and a reference that writes
    a bindingness after the kind it expects is refused
    (specification/grammar.md#references-and-targets)."""
    rule = LANG.grammar["productions"].split("\nexpected-kind =", 1)[1].split("\nconstituent")[0]
    alternatives = " ".join(line.split("--")[0] for line in rule.splitlines())
    assert "bindingness" not in alternatives and "adds" not in alternatives.split()
    for kind in ("ISSUE kind-of-issue", "NORMATIVE-ENTRY kind-of-normative-entry",
                 "SETTING kind-of-setting", "NOTHING-BEYOND-ITS-OWN-RECORD"):
        assert kind in alternatives
    text = message("(move ACT-ACCEPTANCE SPEAKERS-OWN (names 1 1 NORMATIVE-ENTRY ASSIGNMENT "
                   "%s) (situation carry (ACTOR (term SELF)) (UNDERGOER (term battery "
                   "DEFINITE))))" % IS, sender=2, recipients=(1,))
    assert api.parse(text).diagnostics == []
    kind, status = (LANG.items[i].form for i in (
        "g.force.kind-of-normative-entry.assignment",
        "g.reference.expected-status-of-an-entry.in-force"))
    bound = LANG.items["g.force.bindingness.on-acceptance"].form
    assert text.count("%s %s" % (kind, status)) == 1
    edited = text.replace("%s %s" % (kind, status), "%s %s %s" % (kind, bound, status))
    assert "d.parser.unexpected-word" in [d.code for d in api.parse(edited).diagnostics]
