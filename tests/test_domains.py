"""The domain corpus of version 1.0 (specification/conformance.md#the-conformance-suite):
its source is what `tools/build_domains.py` generates, each of the twelve domains holds
100 items, every message reads with no diagnostic within the protocol's maxima, every
participant hears the items it takes part in with no diagnostic in its view of the
exchange, the two implementations write the same record of every message, and the items
marked as written by hand are the domains' hand-written ones."""
import collections
import copy
import json
import os
import sys

from rowih import api, parity

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import build_corpus  # noqa: E402
import build_domains  # noqa: E402
from rowih.generator import Generator  # noqa: E402
from rowih.notation import Reader  # noqa: E402

with open(os.path.join(ROOT, "corpus", "source", "domains.json"), encoding="utf-8") as f:
    SOURCE = json.load(f)["items"]


def texts(item) -> list:
    """The built text of each message of a corpus item."""
    out = []
    for k in range(1, len(item["messages"]) + 1):
        path = os.path.join(ROOT, "corpus", "domains", "%s.%d.txt" % (item["id"], k))
        with open(path, encoding="utf-8") as f:
            out.append(f.read())
    return out


def views(item, built: list) -> dict:
    """Each participant's diagnostics, having heard every message it sent or received."""
    parties = {m["sender"] for m in item["messages"]} | {
        r for m in item["messages"] for r in m["recipients"]}
    return {p: [d.code for d in api.discourse(
        [t for t, m in zip(built, item["messages"])
         if m["sender"] == p or p in m["recipients"]], str(p), now=1760100000)["diagnostics"]]
        for p in sorted(parties)}


def test_the_source_is_what_the_generator_writes():
    items, _ = build_domains.build()
    assert json.loads(json.dumps(items)) == SOURCE


def test_each_of_the_twelve_domains_holds_100_items():
    counts = collections.Counter(item["domain"] for item in SOURCE)
    # the domains, as the corpus names them
    assert counts == {name: 100 for name in [
        "basic communication", "agent coordination", "task delegation", "negotiation",
        "error correction", "scientific communication", "programming and tool use",
        "uncertainty and evidence", "casual discourse", "humour and creativity",
        "formal reasoning", "metalinguistic communication"]}


def test_every_message_reads_with_no_diagnostic_within_the_maxima():
    with open(os.path.join(ROOT, "language", "protocol.json"), encoding="utf-8") as f:
        maxima = json.load(f)["maxima"]
    for item in SOURCE:
        for k, text in enumerate(texts(item), 1):
            a = api.parse(text)
            assert a.diagnostics == [], (item["id"], k, [d.code for d in a.diagnostics])
            assert len(a.words) <= maxima["message words"], (item["id"], k)


def test_every_participant_hears_its_items_with_no_diagnostic():
    for item in SOURCE:
        heard = views(item, texts(item))
        assert heard == {p: [] for p in heard}, item["id"]


def test_the_views_find_a_reference_to_an_entry_never_made():
    item = next(i for i in SOURCE if len(i["messages"]) == 2
                and "(names 1 1 ISSUE REQUEST OPEN)" in i["messages"][1]["notation"])
    planted = copy.deepcopy(item)
    planted["messages"][1]["notation"] = planted["messages"][1]["notation"].replace(
        "(names 1 1 ISSUE REQUEST OPEN)", "(names 1 9 ISSUE REQUEST OPEN)")
    gen = Generator()
    firsts = build_corpus.first_entries(planted, gen.lang)
    built = [gen.message(Reader(gen.lang).moves(build_corpus.substitute(m["notation"],
                                                                        gen.lang)),
                         "normal expression", m["sender"], m["recipients"], m["time"],
                         m["identifier"], first_entry=firsts[k])
             for k, m in enumerate(planted["messages"])]
    assert all("d.view.held" in codes for codes in views(planted, built).values())
    assert all(codes == [] for codes in views(item, texts(item)).values())


def test_a_partial_withdrawal_restates_its_part_without_writing_the_default_phase():
    """Each conjunct of a commitment's content takes the execution phase the content takes
    by default, so a part restated alone, as a partial withdrawal restates it, has the
    normal form it has within the conjunction."""
    item = next(i for i in SOURCE if "ACT-PARTIAL-WITHDRAWAL" in i["messages"][-1]["notation"])
    bare = copy.deepcopy(item)
    for m in bare["messages"]:
        m["notation"] = m["notation"].replace(" EXECUTION-PHASE.UNSTATED", "")
    gen = Generator()
    firsts = build_corpus.first_entries(bare, gen.lang)
    built = [gen.message(Reader(gen.lang).moves(build_corpus.substitute(m["notation"],
                                                                        gen.lang)),
                         "normal expression", m["sender"], m["recipients"], m["time"],
                         m["identifier"], first_entry=firsts[k])
             for k, m in enumerate(bare["messages"])]
    assert "EXECUTION-PHASE" not in "".join(m["notation"] for m in bare["messages"])
    assert all(codes == [] for codes in views(bare, built).values()), views(bare, built)


def test_both_implementations_write_the_same_record_of_every_message():
    built = [t for item in SOURCE for t in texts(item)]
    python = [parity.record_line(t, False) for t in built]
    assert parity.typescript_records(built) == python


def test_the_items_marked_as_written_by_hand_are_the_hand_written_ones():
    written = {s for d in build_domains.DOMAINS for s, _ in getattr(d, "AUTHORED", ())}
    marked = {item["statement"] for item in SOURCE if item.get("authored")}
    assert marked == written and len(marked) == sum(
        len(getattr(d, "AUTHORED", ())) for d in build_domains.DOMAINS)


# ---------------------------------------------------------------- the occasions of the idioms

# What the scene of each entry shows before the entry is said, the occasion its pragmatic
# conditions name.
OCCASION = {
    "smooth path": "(situation leave INCEPTIVE (UNDERGOER (term SELF))",
    "leaf dry": "(situation lose PERFECTIVE (HOLDER (term SELF))",
    "copied out": "(situation receive ITERATIVE (RECIPIENT (term SELF))",
    "not made clear": "(move ACT-QUESTION (situation IDIOM-ENTRY mean",
    "undertaking broken": "(move ACT-ERROR-REPORT",
    "budget taken": "(situation consume PERFECTIVE",
    "mistake sent": "(CONTENT (term mistake INDEFINITE))",
    "gift lost": "(situation give (ACTOR (term SELF)) (UNDERGOER (term record",
    "late arrival": "(situation late (UNDERGOER",
    "top near": " COMPLETIVE (ACTOR (term SELF))",
    "meaning asked": "(readings STRATEGIC",
    "sentences long": "(situation CONJUNCTION",
    "night returning": "(situation receive POLARITY.NEGATIVE PERFECTIVE",
    "lost from the map": "(move ACT-REQUEST",
}


# The question each idiom said in answer answers, as its pragmatic conditions name it.
QUESTION = {
    "quiet network": "(situation POLAR change PERFECTIVE (UNDERGOER (term thing EXISTENTIAL)))",
    "running": "(situation POLAR run (UNDERGOER (term service DEFINITE)))",
    "run run": "(situation POLAR run (UNDERGOER (term service DEFINITE)))",
    "not running": "(situation POLAR run (UNDERGOER (term service DEFINITE)))",
    "rain falling": "(situation POLAR receive (RECIPIENT (term INTERLOCUTOR))",
    "wait wait": "(situation POLAR receive PERFECTIVE (RECIPIENT (term INTERLOCUTOR))",
    "work work": "(situation POLAR progress (UNDERGOER (situation work (ACTOR (term "
                 "INTERLOCUTOR)))))",
    "working": "(situation POLAR progress (UNDERGOER (situation work (ACTOR (term "
               "INTERLOCUTOR)))))",
    "done": "(situation POLAR progress (UNDERGOER (situation work (ACTOR (term "
            "INTERLOCUTOR)))))",
    "read read": "(situation POLAR read PERFECTIVE (ACTOR (term INTERLOCUTOR))",
    "send send": "(situation POLAR send PERFECTIVE (ACTOR (term INTERLOCUTOR))",
    "find find": "(situation POLAR find PERFECTIVE (ACTOR (term INTERLOCUTOR))",
}


def scene(key: str) -> list:
    """The messages of the item that says the entry `key`, over a fresh picker."""
    import domains
    from domains import conventional
    from domains.compose import Picker
    from domains.phrasing import BY_KEY
    ident = BY_KEY[key]
    domain = next(d for d in domains.DOMAINS if d.SLUG == conventional.domain_of(ident))
    return conventional.item(ident, conventional.Topic(Picker(), **domain.TOPIC), 0)[1]


def test_an_idiom_said_in_answer_answers_the_question_its_conditions_name():
    for key, asked in QUESTION.items():
        question, answer = (m["notation"] for m in scene(key)[-2:])
        assert question.startswith("(move ACT-QUESTION") and asked in question, key
        assert answer.startswith("(move ACT-ANSWER (names 1 1 ISSUE QUESTION OPEN)"), key


def test_an_idiom_follows_the_occasion_its_conditions_name():
    for key, shown in OCCASION.items():
        messages = scene(key)
        assert any(shown in m["notation"] for m in messages[:-1]), key
        assert shown not in messages[-1]["notation"], key


def test_the_thanks_for_waiting_is_the_deliverers_and_a_repetition_follows_the_speaker():
    messages = scene("waited for")
    report = next(m for m in messages if "ACT-COMPLETION-REPORT" in m["notation"])
    assert messages[-1]["sender"] == report["sender"] == 2
    first, repeated, remark = scene("sound returning")
    assert (first["sender"], repeated["sender"], remark["sender"]) == (1, 2, 1)
    assert first["notation"] == repeated["notation"]
