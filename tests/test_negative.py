"""The negative corpus: each ill-formed item draws the diagnostic it must draw, and no
input raises an exception (`inv.diagnostics-not-exceptions`)."""
import json
import os

import pytest

from rowih import api

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS = json.load(open(os.path.join(ROOT, "corpus", "source", "negative.json"),
                       encoding="utf-8"))["items"]


def text_of(item):
    with open(os.path.join(ROOT, "corpus", "negative", item["id"] + ".txt"),
              encoding="utf-8") as f:
        return f.read()


@pytest.mark.parametrize("item", ITEMS, ids=[i["id"] for i in ITEMS])
def test_item_draws_its_diagnostic(item):
    codes = [d.code for d in api.parse(text_of(item)).diagnostics]
    assert item["code"] in codes


@pytest.mark.parametrize("item", ITEMS, ids=[i["id"] for i in ITEMS])
def test_every_diagnostic_has_the_six_fields(item):
    for d in api.parse(text_of(item)).diagnostics:
        assert d.code.startswith("d.")
        for field in ("location", "expected", "detected", "ambiguity", "confidence",
                      "recoverability"):
            assert hasattr(d, field)


def test_every_registered_code_is_raised_by_some_rule():
    # a code in the registry that no rule raises promises a judgement the reader never
    # makes; the registry is the canonical implementation's, and every rule names its code
    # as a literal
    import glob
    import os
    from rowih.diagnostics import CODES
    here = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "python", "rowih")
    sources = [open(p, encoding="utf-8").read() for p in glob.glob(os.path.join(here, "*.py"))
               if not p.endswith("diagnostics.py")]
    assert [c for c in CODES if not any('"%s"' % c in s for s in sources)] == []


def test_every_condition_is_stated_in_full():
    # the registry's conditions are the specification's table of diagnostics, which a
    # reader reads without any other document, so no condition points to a section
    from rowih.diagnostics import CODES
    assert [code for code, condition in CODES.items() if "§" in condition] == []


def test_negative_corpus_covers_every_stage():
    stages = {i["code"].split(".")[1] for i in ITEMS}
    assert {"tokenizer", "lexer", "parser", "checker", "check-values"} <= stages


def test_stop_whose_restatement_differs_is_refused():
    """A cancellation that restates something other than the request it withdraws is
    refused by a hearer that holds the request (specification/discourse.md#stops)."""
    from rowih.generator import Generator
    from rowih.notation import Reader
    from rowih.view import View
    gen = Generator()
    reader = Reader(gen.lang)
    request = gen.message(reader.moves(
        "(move ISSUE REQUEST SPEAKERS-OWN (situation delete (ACTOR (term (party 2))) "
        "(UNDERGOER (term file DEFINITE))))"), identifier=1)
    cancel = gen.message(reader.moves(
        "(move NOTHING-BEYOND-ITS-OWN-RECORD LOWERING WHOLE-ENTRY ON-THE-MOVE SPEAKERS-OWN "
        "(names 1 1 ISSUE REQUEST OPEN) (situation delete (ACTOR (term (party 2))) "
        "(UNDERGOER (term record DEFINITE))))"), identifier=2, first_entry=2)
    view = View("2")
    assert view.receive(api.parse(request)) == []
    codes = [d.code for d in view.receive(api.parse(cancel))]
    assert codes == ["d.checker.stop-restatement"]
    assert view.entries[("1", "1")].status == "open"


def test_the_checker_s_refusals_are_present():
    refusals = {i["code"] for i in ITEMS if i.get("refusal")}
    assert {"d.checker.accidental-in-operative", "d.checker.figure-without-target",
            "d.checker.idiom-absent"} <= refusals


def _msg(notation, sender=1, recipients=(2,), identifier=1):
    """A message of one move; each sender's messages here go on one channel, so the
    entry its move adds is numbered as the message is."""
    from rowih.generator import Generator
    from rowih.notation import Reader
    gen = Generator()
    return api.parse(gen.message(Reader(gen.lang).moves(notation), sender=sender,
                                 recipients=recipients, identifier=identifier,
                                 first_entry=identifier))


def test_refusal_restating_with_deixis_is_a_restatement():
    """B refuses A's request to B, restating 'agent 2 deletes the file' as 'I delete the
    file': with deixis resolved the two are one meaning."""
    from rowih.view import View
    view = View("1")
    assert view.receive(_msg("(move ISSUE REQUEST SPEAKERS-OWN (situation delete (ACTOR "
                             "(term (party 2))) (UNDERGOER (term file DEFINITE))))")) == []
    refusal = _msg("(move NOTHING-BEYOND-ITS-OWN-RECORD LOWERING WHOLE-ENTRY ON-THE-MOVE "
                   "SPEAKERS-OWN (names 1 1 ISSUE REQUEST OPEN) (situation delete (ACTOR "
                   "(term SELF)) (UNDERGOER (term file DEFINITE))))", sender=2, recipients=(1,))
    assert view.receive(refusal) == []
    assert view.entries[("1", "1")].status == "withdrawn"


def test_lowering_a_request_sent_to_another_is_refused():
    """C lowers A's request, which A sent to B alone: B's view refuses it (`inv.fit`)."""
    from rowih.view import View
    view = View("2")
    assert view.receive(_msg("(move ISSUE REQUEST SPEAKERS-OWN (situation delete (ACTOR "
                             "(term (party 2))) (UNDERGOER (term file DEFINITE))))")) == []
    lowering = _msg("(move NOTHING-BEYOND-ITS-OWN-RECORD LOWERING WHOLE-ENTRY ON-THE-MOVE "
                    "SPEAKERS-OWN (names 1 1 ISSUE REQUEST OPEN) (situation delete (ACTOR "
                    "(term (party 2))) (UNDERGOER (term file DEFINITE))))", sender=3,
                    recipients=(2,))
    assert [d.code for d in view.receive(lowering)] == ["d.checker.fit"]
    assert view.entries[("1", "1")].status == "open"


def test_a_cancellation_that_crossed_an_acceptance_prevails():
    """A cancellation that expects an open request, received after the request was
    accepted, was made against the request as it stood before the acceptance: the two
    crossed, and the stop prevails, so the acceptance is refused and the request
    withdrawn, as in every view that holds both
    (specification/discourse.md#crossing-moves)."""
    from rowih.view import View
    view = View("1")
    view.receive(_msg("(move ISSUE REQUEST SPEAKERS-OWN (situation delete (ACTOR (term "
                      "(party 2))) (UNDERGOER (term file DEFINITE))))"))
    view.receive(_msg("(move NORMATIVE-ENTRY OBLIGATION BOUND RESOLUTION "
                      "OUTCOME-OF-A-RESOLUTION.ACCEPTANCE WHOLE-ENTRY ON-THE-MOVE SPEAKERS-OWN "
                      "(names 1 1 ISSUE REQUEST OPEN) (situation delete (ACTOR (term SELF)) "
                      "(UNDERGOER (term file DEFINITE))))", sender=2, recipients=(1,)))
    cancel = _msg("(move NOTHING-BEYOND-ITS-OWN-RECORD LOWERING WHOLE-ENTRY ON-THE-MOVE "
                  "SPEAKERS-OWN (names 1 1 ISSUE REQUEST OPEN) (situation delete (ACTOR "
                  "(term (party 2))) (UNDERGOER (term file DEFINITE))))", identifier=2)
    assert [d.code for d in view.receive(cancel)] == ["d.view.crossed"]
    assert view.entries[("1", "1")].status == "withdrawn"
    assert view.crossed == {("2", "1"): ("1", "2")}


def test_a_message_relaid_is_applied_once():
    """The same message, wrapped differently, is one message: a hearer applies it once
    (`inv.at-most-once`)."""
    from rowih.view import View
    text = _msg("(move ISSUE REQUEST SPEAKERS-OWN (situation delete (ACTOR (term (party 2))) "
                "(UNDERGOER (term file DEFINITE))))").text
    view = View("2")
    assert view.receive(api.parse(text)) == []
    relaid = text.replace(" ", "\n", 7)
    assert [d.code for d in view.receive(api.parse(relaid))] == ["d.view.applied-before"]
    assert len(view.entries) == 1


def test_lowering_leaves_the_content_of_the_entry_unchanged():
    """Only an entry's status changes (`inv.entries-immutable`)."""
    import copy
    from rowih.view import View
    view = View("1")
    view.receive(_msg("(move ISSUE REQUEST SPEAKERS-OWN (situation delete (ACTOR (term "
                      "(party 2))) (UNDERGOER (term file DEFINITE))))"))
    before = copy.deepcopy(view.entries[("1", "1")].content)
    view.receive(_msg("(move NOTHING-BEYOND-ITS-OWN-RECORD LOWERING WHOLE-ENTRY ON-THE-MOVE "
                      "SPEAKERS-OWN (names 1 1 ISSUE REQUEST OPEN) (situation delete (ACTOR "
                      "(term SELF)) (UNDERGOER (term file DEFINITE))))", sender=2,
                      recipients=(1,)))
    assert view.entries[("1", "1")].content == before


def test_interlocutor_resolves_to_the_recipient():
    """'You' in a cancellation is the request's recipient, not the agent last mentioned
    (`inv.identity-not-reference`)."""
    from rowih.view import View
    view = View("2")
    view.receive(_msg("(move ISSUE REQUEST SPEAKERS-OWN (situation give (ACTOR (term "
                      "(party 2))) (UNDERGOER (term file DEFINITE)) (RECIPIENT (term "
                      "(party 3)))))"))
    cancel = _msg("(move NOTHING-BEYOND-ITS-OWN-RECORD LOWERING WHOLE-ENTRY ON-THE-MOVE "
                  "SPEAKERS-OWN (names 1 1 ISSUE REQUEST OPEN) (situation give (ACTOR (term "
                  "INTERLOCUTOR)) (UNDERGOER (term file DEFINITE)) (RECIPIENT (term "
                  "(party 3)))))", identifier=2)
    assert view.receive(cancel) == []


def test_nesting_rejection_does_not_carry_into_later_moves():
    """A move rejected at the nesting maximum leaves the depth as it found it, so that a
    later move nested to the maximum is read; and the rejected move, received intact,
    draws no integrity mismatch and survives conversion (both found by the TypeScript
    port's review)."""
    from rowih.writer import Writer
    w = Writer()

    def lines(path):
        with open(os.path.join(ROOT, "corpus", path), encoding="utf-8") as f:
            return [line.split(" ") for line in f.read().split("\n") if line]

    def body(move_line):
        i = 1
        while w.lang.by_form[move_line[i]].class_id == "g.numbers.numeral":
            i += 1
        return move_line[i + 1:-1]

    beyond = lines("negative/n50-nesting-beyond-the-maximum-short.txt")
    at_limit = lines("adversarial/a13-recursion-limit.1.txt")
    icv = w.w("g.message.message-field.integrity-check-value")
    env = beyond[0][:beyond[0].index(icv)]
    text = w.message(env, [w.move(body(beyond[1])), w.move(body(at_limit[1]))])
    a = api.parse(text)
    assert [d.code for d in a.diagnostics] == ["d.parser.maximum"]
    assert len(a.message.moves) == 1
    assert api.convert(text, "transliteration")[0] == text
