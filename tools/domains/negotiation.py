"""Negotiation: prices proposed, countered and met, trades and loans, shares divided and
accepted in part, competition and peace, offers on conditions, disputes brought to a
judge, what each party owns, and what an outcome costs in concessions and permissions."""
from .compose import Exchange, names, party, term

NAME = "negotiation"
SLUG = "negotiation"
DIALECTS = ["negotiation"]

TOPIC = dict(
    tasks=[("sell", "map"), ("buy", "data"), ("trade", "resource"), ("pay", "money"),
           ("give", "gift"), ("allocate", "share"), ("lend", "battery"), ("own", "land")],
    contents=[
        ("(situation fair (UNDERGOER (term price DEFINITE)))", "the price is fair"),
        ("(situation expensive (UNDERGOER (term map DEFINITE)))", "the map is expensive"),
        ("(situation cheap (UNDERGOER (term data DEFINITE)))", "the data is cheap"),
        ("(situation enough (UNDERGOER (term money DEFINITE)) (CONTENT (situation buy "
         "(ACTOR (term SELF)) (UNDERGOER (term machine DEFINITE)))))", "the money is enough "
                                                                       "to buy the machine"),
        ("(situation important (UNDERGOER (term reward DEFINITE)))", "the reward is important"),
        ("(situation high (UNDERGOER (term risk DEFINITE)))", "the risk is high"),
    ],
    things=["map", "data", "battery", "gift", "land", "machine"])

GOODS = ["map", "data", "battery", "machine", "food", "medicine", "key", "image", "program",
         "vehicle", "land", "thing"]
OFFER = "(situation %s (ACTOR %s) (UNDERGOER %s) (RECIPIENT %s))"


def pricing(p, n):
    """A sale proposed at a price, countered, and accepted at the counter."""
    good = p(GOODS)
    asked, countered = 40 + 10 * (n % 6), 30 + 10 * (n % 6) - 5
    x = Exchange()
    first = x.send(1, [2], "(move ACT-PROPOSAL SPEAKERS-OWN (situation sell (ACTOR (term "
                           "SELF)) "
                   "(UNDERGOER %s) (RECIPIENT %s) (CONTENT (term price (q EXACTLY %d)))))" % (
                       term(good, "DEFINITE"), party(2), asked))
    second = x.send(2, [1], "(move ACT-COUNTERPROPOSAL SPEAKERS-OWN %s (situation buy (ACTOR "
                    "(term SELF)) (UNDERGOER %s) (CONTENT (term price (q EXACTLY %d)))))" % (
                        names(1, first, "proposal"), term(good, "DEFINITE"), countered))
    x.send(1, [2], "(move ACT-ACCEPTANCE SPEAKERS-OWN %s (situation buy (ACTOR %s) (UNDERGOER "
           "%s) (CONTENT (term price (q EXACTLY %d)))))" % (
               names(2, second, "proposal"), party(2), term(good, "DEFINITE"), countered))
    return "agent 1 proposes to sell agent 2 the %s for %d; agent 2 counters with %d, and " \
           "agent 1 accepts" % (good, asked, countered), x.messages


def trading(p, n):
    """One thing traded for another, or lent to be returned."""
    verb = p(["trade", "lend", "give"])
    good, other = p(GOODS), p(GOODS[::-1])
    x = Exchange()
    if verb == "trade":
        proposed = x.send(1, [2], "(move ACT-PROPOSAL SPEAKERS-OWN (situation trade (ACTOR "
                          "(term SELF)) (UNDERGOER %s) (RECIPIENT %s) (CONTENT %s)))" % (
                              term(good, "DEFINITE"), party(2), term(other, "DEFINITE")))
        x.send(2, [1], "(move ACT-ACCEPTANCE SPEAKERS-OWN %s (situation trade (ACTOR %s) "
               "(UNDERGOER %s) (RECIPIENT (term SELF)) (CONTENT %s)))" % (
                   names(1, proposed, "proposal"), party(1), term(good, "DEFINITE"),
                   term(other, "DEFINITE")))
        return "agent 1 proposes to trade agent 2 the %s for the %s, and agent 2 accepts" % (
            good, other), x.messages
    if verb == "lend":
        offered = x.send(1, [2], "(move ACT-OFFER SPEAKERS-OWN %s)" % (
            OFFER % ("lend", "(term SELF)", term(good, "DEFINITE"), party(2))))
        x.send(2, [1], "(move ACT-ACCEPTANCE SPEAKERS-OWN %s %s)" % (
            names(1, offered, "commitment"), OFFER % ("lend", party(1), term(good, "DEFINITE"),
                                                      "(term SELF)")),
               "(move ACT-PROMISE SPEAKERS-OWN (situation return (UNDERGOER %s) (CONTENT "
               "%s) (EVENT-TIME 2 DAY HENCE)))" % (term(good, "DEFINITE"), party(1)))
        return "agent 1 offers to lend agent 2 the %s; agent 2 accepts and promises to " \
               "return it in two days" % good, x.messages
    x.send(1, [2], "(move ACT-OFFER SPEAKERS-OWN %s (CONDITION (situation give (ACTOR %s) "
           "(UNDERGOER %s) (RECIPIENT (term SELF))))))" % (
               (OFFER % ("give", "(term SELF)", term(good, "DEFINITE"), party(2)))[:-1],
               party(2), term(other, "DEFINITE")))
    return "agent 1 offers to give agent 2 the %s if agent 2 gives it the %s" % (
        good, other), x.messages


def dividing(p, n):
    """A share of a resource proposed, and accepted in part."""
    whole = p(["budget", "resource", "land", "money", "energy"])
    mine = 50 + 5 * (n % 5)
    yours = 100 - mine
    x = Exchange()
    share = "(situation #%d allocate (ACTOR %%s) (UNDERGOER (term share (q EXACTLY %d " \
            "percent) (CONTENT (term %s DEFINITE)))) (RECIPIENT %%s))"
    split = "(situation CONJUNCTION (CONTENT %s) (CONTENT %s))" % (
        share % (1, mine, whole), share % (2, yours, whole))
    proposed = x.send(1, [2], "(move ACT-PROPOSAL SPEAKERS-OWN %s)" % (
        split % ("(term SELF)", party(2), "(term SELF)", "(term SELF)")))
    x.send(2, [1], "(move ACT-PARTIAL-ACCEPTANCE SPEAKERS-OWN %s (situation allocate (ACTOR "
           "%s) (UNDERGOER (term share (q EXACTLY %d percent) (CONTENT (term %s "
           "DEFINITE)))) (RECIPIENT (term SELF))))" % (
               names(1, proposed, "proposal")[:-1] + " part 1)", party(1), mine, whole))
    return "agent 1 proposes to give agent 2 %d percent of the %s and keep %d percent; " \
           "agent 2 accepts the first part" % (mine, whole, yours), x.messages


def competing(p, n):
    """Agents competing for one prize, fighting or making peace."""
    verb = p(["compete", "fight", "win", "peace"])
    prize = p(["resource", "market", "reward", "land", "money"])
    x = Exchange()
    if verb == "compete":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
               "compete PROGRESSIVE (ACTOR %s) (UNDERGOER %s) (CONTENT %s))))" % (
                   party(3), party(4), term(prize, "DEFINITE")))
        english = "agent 1 observes that agents 3 and 4 are competing for the %s" % prize
    elif verb == "fight":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion REPORT PROBABLE (situation fight "
               "PROGRESSIVE (ACTOR (term enemy DEFINITE)) (UNDERGOER (term friend "
               "DEFINITE)))))")
        english = "agent 1 reports that the enemy is fighting the friend"
    elif verb == "win":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation win "
               "PERFECTIVE (ACTOR %s) (CONTENT %s))))" % (party(3), term(prize, "DEFINITE")))
        english = "agent 1 observes that agent 3 has won the %s" % prize
    else:
        x.send(1, [2], "(move ACT-PROPOSAL SPEAKERS-OWN (situation CONJUNCTION (CONTENT "
               "(situation fight POLARITY.NEGATIVE (ACTOR (term INCLUSIVE-COLLECTIVE "
               "READING-OF-A-COLLECTIVE.JOINT)) (UNDERGOER %s))) (CONTENT (situation "
               "possess (HOLDER (term INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)) "
               "(UNDERGOER (term peace DEFINITE))))))" % party(3))
        english = "agent 1 proposes that they stop fighting agent 3 and keep the peace"
    return english, x.messages


def disputing(p, n):
    """A dispute over what was taken: blame, a judge, a punishment and forgiveness."""
    good = p(GOODS)
    kind = p(["blame", "judge", "punish", "forgive"])
    x = Exchange()
    took = "(situation steal PERFECTIVE (ACTOR %s) (UNDERGOER %s))" % (party(3), term(
        good, "DEFINITE"))
    seen = x.send(1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN %s))" % took)
    if kind == "blame":
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
               "blame (ACTOR (term SELF)) (UNDERGOER %s) (CONTENT %s))))" % (party(3), took))
        english = "and blames agent 3 for it"
    elif kind == "judge":
        judged = "(situation judge (ACTOR %%s) (UNDERGOER %s) (CONTENT (term law DEFINITE)))" \
            % party(3)
        asked = x.send(1, [2], "(move ACT-REQUEST SPEAKERS-OWN %s)" % (judged % party(2)))
        x.send(2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN %s %s)" % (
            names(1, asked, "request"), judged % "(term SELF)"))
        english = "and asks agent 2 to judge agent 3 by the law, which agent 2 undertakes"
    elif kind == "punish":
        x.send(2, [1], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE (situation "
               "punish (EVENT-TIME AFTER NOW) (ACTOR (term community DEFINITE)) (UNDERGOER "
               "%s) (CONTENT %s))))" % (party(3), took))
        english = "and agent 2 expects the community to punish agent 3 for it"
    else:
        x.send(1, [2], "(move ASSERTED-POSITION NONE %s qualifies (assertion INTROSPECTION "
               "CERTAIN (situation forgive (ACTOR (term SELF)) (UNDERGOER %s) (CONTENT %s))))"
               % (names(1, seen, "position"), party(3), took))
        english = "and, qualifying it, says that it forgives agent 3"
    return "agent 1 observes that agent 3 has taken the %s without right, %s" % (
        good, english), x.messages


def owning(p, n):
    """What a party owns or holds, and where its bounds lie."""
    good = p(["land", "house", "market", "river", "forest", "vehicle"])
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION (assertion RETRIEVAL CERTAIN (situation own "
           "(HOLDER %s) (UNDERGOER %s))))" % (party(3), term(good, "DEFINITE")),
           "(move ASSERTED-POSITION (assertion RETRIEVAL CERTAIN (situation inside "
           "(UNDERGOER %s) (CONTENT (term boundary DEFINITE (CONTENT (term country "
           "DEFINITE)))))))" % term(
               good, "DEFINITE"))
    return "agent 1 states from its records that agent 3 owns the %s, which lies within the " \
           "boundary of the country" % good, x.messages


def valuing(p, n):
    """What a thing is worth to the parties: its value, its cost and its risk."""
    good = p(GOODS)
    state = p(["expensive", "cheap"])
    worth = p(["value", "cost", "reward", "risk"])
    x = Exchange()
    first = x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE "
                           "(situation %s "
                   "(UNDERGOER %s))))" % (state, term(good, "DEFINITE")))
    x.send(2, [1], "(move ASSERTED-POSITION NONE %s contrasts (assertion INFERENCE PROBABLE "
           "(situation %s (UNDERGOER (term %s DEFINITE (CONTENT %s))))))" % (
               names(1, first, "position"), "high" if state == "cheap" else "low", worth,
               term(good, "DEFINITE")))
    return "agent 1 holds that the %s is %s; agent 2 answers, by contrast, that its %s is %s" \
        % (good, state, worth, "high" if state == "cheap" else "low"), x.messages


def conceding(good, licence):
    """The senses concession and licence: what an outcome costs and what it permits."""
    x = Exchange()
    if not licence:
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INFERENCE PROBABLE (situation high "
               "(UNDERGOER (term price DEFINITE (CONTENT (situation trade (ACTOR (term "
               "SELF)) (UNDERGOER %s) (RECIPIENT %s))))))))" % (term(good, "DEFINITE"),
                                                                 party(2)))
        english = "what it must concede to trade agent 2 the %s is high" % good
    else:
        x.send(1, [2], "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation "
               "possess (HOLDER (term SELF)) (UNDERGOER (term door DEFINITE (CONTENT "
               "(situation sell (ACTOR (term SELF)) (UNDERGOER %s))))))))" % term(good,
                                                                              "DEFINITE"))
        english = "it holds the licence to sell the %s" % good
    return "agent 1 states that %s" % english, x.messages


SCHEMAS = [pricing, trading, dividing, competing, disputing, owning, valuing]
# each sense of negotiation said once
FIXED = [conceding("map", False), conceding("land", True)]

# Exchanges written by hand for idiom range in negotiation.
AUTHORED = [
    ("a haggle over a map: agent 1 asks sixty, agent 2 counters with forty, agent 1 comes "
     "to fifty and says there is a door in its price, and agent 2 accepts as the prices meet",
     Exchange.scripted(
         (1, [2], "(move ACT-PROPOSAL SPEAKERS-OWN (situation sell (ACTOR (term SELF)) "
                  "(UNDERGOER (term map DEFINITE)) (RECIPIENT (term (party 2))) (CONTENT "
                  "(term price (q EXACTLY 60)))))"),
         (2, [1], "(move ACT-COUNTERPROPOSAL SPEAKERS-OWN (names 1 1 ISSUE PROPOSAL OPEN) "
                  "(situation buy (ACTOR (term SELF)) (UNDERGOER (term map DEFINITE)) "
                  "(CONTENT (term price (q EXACTLY 40)))))"),
         (1, [2], "(move ACT-COUNTERPROPOSAL SPEAKERS-OWN (names 2 1 ISSUE PROPOSAL OPEN) "
                  "(situation sell (ACTOR (term SELF)) (UNDERGOER (term map DEFINITE)) "
                  "(RECIPIENT (term (party 2))) (CONTENT (term price (q EXACTLY 50)))))",
          "(move ASSERTED-POSITION (assertion INTROSPECTION CERTAIN (situation IDIOM-ENTRY "
          "possess (HOLDER (term price DEFINITE)) (UNDERGOER (term door)))))"),
         (2, [1], "(move ACT-ACCEPTANCE SPEAKERS-OWN (names 1 2 ISSUE PROPOSAL OPEN) "
                  "(situation sell (ACTOR (term (party 1))) (UNDERGOER (term map "
                  "DEFINITE)) (RECIPIENT (term SELF)) (CONTENT (term price (q EXACTLY 50)))))",
          "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation IDIOM-ENTRY "
          "meet (ACTOR (term price)) (UNDERGOER (term price)))))"))),
    ("agent 2 offers a gift on condition of payment; agent 1 says the gift has a price and "
     "declines it",
     Exchange.scripted(
         (2, [1], "(move ACT-OFFER SPEAKERS-OWN (situation give (ACTOR (term SELF)) "
                  "(UNDERGOER (term gift DEFINITE)) (RECIPIENT (term (party 1))) "
                  "(CONDITION (situation pay (ACTOR (term (party 1))) (UNDERGOER (term "
                  "money INDEFINITE)) (RECIPIENT (term SELF))))))"),
         (1, [2], "(move ASSERTED-POSITION (assertion INFERENCE CERTAIN (situation "
                  "IDIOM-ENTRY contain (UNDERGOER (term gift)) (CONTENT (term price)))))",
          "(move ACT-REJECTION SPEAKERS-OWN (names 2 1 NORMATIVE-ENTRY COMMITMENT "
          "EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE) (situation give (ACTOR (term (party 2))) "
          "(UNDERGOER (term gift DEFINITE)) (RECIPIENT (term SELF)) (CONDITION (situation "
          "pay (ACTOR (term SELF)) (UNDERGOER (term money INDEFINITE)) (RECIPIENT (term "
          "(party 2)))))))"))),
    ("agent 1 observes that agent 3's price keeps walking and recommends that agent 2 wait "
     "before it buys",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION PROBABLE (situation "
                  "IDIOM-ENTRY walk (ACTOR (term price)))))",
          "(move ACT-RECOMMENDATION (situation wait (ACTOR (term (party 2))) (CONTENT "
          "(situation buy (ACTOR (term (party 2))) (UNDERGOER (term data DEFINITE))))))"))),
]
