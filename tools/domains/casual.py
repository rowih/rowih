"""Casual discourse: how agents and the humans and animals around them feel, eat, sleep and
mend, the weather and the mood of an agent, games, music and stories, news, the words of
the casual register, and the conversational dialect's terms, with exchanges written by hand
for the range of the casual register."""
from .compose import Exchange, names, party, plural, term
from .terms import named as in_dialect

NAME = "casual discourse"
SLUG = "casual"
DIALECTS = ["conversation"]
CASUAL = " familiar CASUAL"

TOPIC = dict(
    tasks=[("cook", "food"), ("play", "game"), ("sing", "music"), ("draw", "image"),
           ("read", "story"), ("describe", "story"), ("watch", "game")],
    contents=[
        ("(situation return PERFECTIVE (UNDERGOER (term (party 3))) (CONTENT (term network "
         "DEFINITE)))", "agent 3 has come back to the network"),
        ("(situation fall PROGRESSIVE (UNDERGOER (term rain GENERIC)))", "rain is falling"),
        ("(situation win PERFECTIVE (ACTOR (term team DEFINITE)) (CONTENT (term game "
         "DEFINITE)))", "the team won the game"),
        ("(situation sleep PROGRESSIVE (UNDERGOER (term dog DEFINITE)))", "the dog is "
         "asleep"),
        ("(situation bright (UNDERGOER (term sun DEFINITE)))", "the sun is bright"),
    ],
    things=["gift", "food", "music", "story", "image"])

# The contents of casual talk, each a situation with its English.
NEWS = TOPIC["contents"] + [
    ("(situation heal PERFECTIVE (UNDERGOER (term child DEFINITE)))", "the child is well "
     "again"),
    ("(situation sing PROGRESSIVE (ACTOR (term bird INDEFINITE)) (UNDERGOER (term music "
     "GENERIC)))", "a bird is singing"),
    ("(situation dance PROGRESSIVE (ACTOR (term family DEFINITE)))", "the family is "
     "dancing"),
    ("(situation alive (UNDERGOER (term plant DEFINITE)))", "the plant is alive"),
    ("(situation grow PERFECTIVE (UNDERGOER (term tree DEFINITE)))", "the tree has grown"),
]
FEELINGS = {"happy": "is happy", "sad": "is sad", "angry": "is angry", "fear": "fears",
            "worry": "worries", "enjoy": "enjoys it", "proud": "is proud",
            "regret": "regrets"}
HOLDERS = [("(term SELF)", "it"), (party(2), "agent 2"), ("(term friend DEFINITE)",
                                                           "the friend"),
           ("(term parent DEFINITE)", "the parent"), ("(term child DEFINITE)", "the child")]


def feeling(p, n):
    """How an agent, a friend or a child feels about what has happened."""
    feel = p(list(FEELINGS))
    content, english = NEWS[n % len(NEWS)]
    holder, who = HOLDERS[n % len(HOLDERS)]
    own = holder == "(term SELF)"
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION%s (assertion %s (situation %s (HOLDER %s) "
           "(CONTENT %s))))" % (CASUAL, "INTROSPECTION CERTAIN" if own else
                                "INFERENCE PROBABLE", feel, holder, content))
    return "agent 1 says, casually, that %s %s that %s" % (who, FEELINGS[feel], english), \
        x.messages


GENERIC = {"music": "music", "rain": "rain", "game": "games", "story": "stories",
           "art": "art", "poem": "poems", "storm": "storms", "sun": "the sun"}


def liking(p, n):
    """What two agents love or hate."""
    verb = p(["love", "hate"])
    thing = p(["music", "rain", "game", "story", "art", "poem", "storm", "sun"])
    other = p(["music", "game", "art", "story", "poem"][::-1])
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION%s (assertion INTROSPECTION CERTAIN (situation %s "
           "(HOLDER (term SELF)) (UNDERGOER (term %s GENERIC)))))" % (CASUAL, verb, thing))
    x.send(2, [1], "(move ASSERTED-POSITION%s (assertion INTROSPECTION CERTAIN (situation love "
           "(HOLDER (term SELF)) (UNDERGOER (term %s GENERIC)))))" % (CASUAL, other))
    return "agent 1 says that it %ss %s, and agent 2 that it loves %s" % (
        verb, GENERIC[thing], GENERIC[other]), x.messages


# The body: each state or act with the beings it is sensibly said of.
BODY = [("tired", ["robot", "child", "dog"]), ("sick", ["child", "dog", "parent"]),
        ("healthy", ["child", "dog", "plant"]), ("sleep", ["dog", "child", "robot"]),
        ("rest", ["robot", "parent"]), ("breathe", ["child", "fish", "dog"]),
        ("eat", ["dog", "child", "bird"]), ("drink", ["child", "dog"]),
        ("cook", ["parent", "friend"])]


def body(p, n):
    """How the body of a human, an animal or a robot is doing."""
    state, beings = BODY[n % len(BODY)]
    being = p(beings)
    p.note(state)
    x = Exchange()
    if state in ("eat", "drink", "cook"):
        what = {"eat": p(["food", "medicine"]), "drink": "water", "cook": "food"}[state]
        situation = "(situation %s PROGRESSIVE (ACTOR %s) (UNDERGOER %s))" % (
            state, term(being, "DEFINITE"), term(what, "INDEFINITE"))
        english = "the %s is %s %s" % (being, {"eat": "eating", "drink": "drinking",
                                               "cook": "cooking"}[state], what)
    elif state in ("sleep", "breathe"):
        situation = "(situation %s PROGRESSIVE (UNDERGOER %s))" % (state, term(being,
                                                                               "DEFINITE"))
        english = "the %s is %s" % (being, "asleep" if state == "sleep" else "breathing")
    elif state == "rest":
        situation = "(situation rest PROGRESSIVE (ACTOR %s))" % term(being, "DEFINITE")
        english = "the %s is resting" % being
    else:
        situation = "(situation %s (UNDERGOER %s))" % (state, term(being, "DEFINITE"))
        english = "the %s is %s" % (being, state)
    x.send(2, [1], "(move ASSERTED-POSITION%s (assertion OBSERVATION CERTAIN %s))" % (
        CASUAL, situation))
    return "agent 2 mentions, casually, that %s" % english, x.messages


def weather(p, n):
    """The weather, and the sense in which weather is an agent's mood."""
    kind = p(["sky", "wind", "rain", "sun", "mood"])
    x = Exchange()
    if kind == "mood":
        state = p(["good", "bad", "calm"])
        x.send(1, [2], "(move ASSERTED-POSITION%s (assertion INFERENCE PROBABLE (situation %s "
               "(UNDERGOER (term weather DEFINITE (CONTENT %s))))))" % (CASUAL, state,
                                                                       party(3)))
        return "agent 1 says that agent 3's mood is %s" % state, x.messages
    states = {"sky": ["blue", "dark", "clear"], "wind": ["strong", "cold", "calm"],
              "rain": ["cold", "heavy"], "sun": ["bright", "hot", "low"]}[kind]
    state = p(states)
    asked = x.send(2, [1], "(move ACT-QUESTION%s (situation good POLAR (UNDERGOER (term "
                   "weather DEFINITE))))" % CASUAL)
    x.send(1, [2], "(move ACT-ANSWER%s %s (assertion OBSERVATION CERTAIN (situation %s "
           "(UNDERGOER (term %s DEFINITE)))))" % (CASUAL, names(2, asked, "question"), state,
                                                 kind))
    return "agent 2 asks whether the weather is good, and agent 1 answers that the %s is %s" \
        % (kind, state), x.messages


def playing(p, n):
    """An invitation to play, sing or dance, accepted with pleasure."""
    verb = p(["play", "sing", "dance", "draw", "describe"])
    x = Exchange()
    joint = "(term INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)"
    what = {"play": "(term game INDEFINITE)", "sing": "(term music INDEFINITE)",
            "draw": "(term image INDEFINITE)", "describe": "(term story INDEFINITE)"}
    hours = 1 + n % 6
    if verb == "dance":
        act = "(situation dance (ACTOR %s) (EVENT-TIME %d HOUR HENCE))" % (joint, hours)
    else:
        act = "(situation %s (ACTOR %s) (UNDERGOER %s) (EVENT-TIME %d HOUR HENCE))" % (
            verb, joint, what[verb], hours)
    proposed = x.send(1, [2], "(move ACT-PROPOSAL SPEAKERS-OWN%s %s)" % (CASUAL, act))
    x.send(2, [1], "(move ACT-ACCEPTANCE SPEAKERS-OWN%s %s %s)" % (
        CASUAL, names(1, proposed, "proposal"), act),
           "(move ASSERTED-POSITION%s (assertion INTROSPECTION CERTAIN (situation happy "
           "(HOLDER (term SELF)) (CONTENT %s))))" % (CASUAL, act))
    return "agent 1 proposes that they %s together in %s; agent 2 accepts and is " \
           "happy to" % ({"play": "play a game", "sing": "sing", "dance": "dance",
                          "draw": "draw a picture", "describe": "tell a story"}[verb],
                         plural(hours, "hour")), x.messages


def news(p, n):
    """News passed on in passing, and a burst of it."""
    content, english = NEWS[(n * 3) % len(NEWS)]
    x = Exchange()
    if n % 3 == 2:
        x.send(1, [2], "(move ASSERTED-POSITION%s (assertion OBSERVATION CERTAIN (situation "
               "arrive PERFECTIVE (UNDERGOER (term storm INDEFINITE (CONTENT (term news "
               "GENERIC)))) (CONTENT (term SELF)))))" % CASUAL)
        return "agent 1 says that a burst of news has reached it", x.messages
    x.send(1, [2], "(move ASSERTED-POSITION%s (assertion REPORT PROBABLE (SOURCE %s) %s))" % (
        CASUAL, party(3), content), "(move ASSERTED-POSITION%s (assertion INFERENCE PROBABLE "
           "(situation recent (UNDERGOER (term news DEFINITE)))))" % CASUAL)
    return "agent 1 passes on agent 3's news that %s, and says the news is recent" % english, \
        x.messages


def register_words(p, n):
    """The casual register's own words for a service, for running and for examining."""
    x = Exchange()
    if n % 2:
        x.send(1, [2], "(move ASSERTED-POSITION%s (assertion OBSERVATION CERTAIN (situation "
               "hum (UNDERGOER (term box DEFINITE)))))" % CASUAL)
        return "agent 1 says, in the casual register's words, that the box is humming", \
            x.messages
    x.send(1, [2], "(move ASSERTED-POSITION%s (assertion OBSERVATION CERTAIN (situation "
           "eyeball COMPLETED (ACTOR (term SELF)) (UNDERGOER (term box DEFINITE)))))" % CASUAL)
    return "agent 1 says, in the casual register's words, that it has eyeballed the box", \
        x.messages


def praising(p, n):
    """Work praised in passing."""
    who = p(["robot", "child", "friend", "team", "dog"])
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION%s (assertion INTROSPECTION CERTAIN (situation "
           "praise (ACTOR (term SELF)) (UNDERGOER %s))))" % (CASUAL, term(who, "DEFINITE")))
    return "agent 1 says that it praises the %s" % who, x.messages


SCHEMAS = [feeling, body, weather, playing, news, liking, register_words, praising]


def mood():
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION%s (assertion INFERENCE PROBABLE (situation good "
           "(UNDERGOER (term weather DEFINITE (CONTENT %s))))))" % (CASUAL, party(3)))
    return "agent 1 says that agent 3's mood is good", x.messages


def burst():
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION%s (assertion OBSERVATION CERTAIN (situation arrive "
           "PERFECTIVE (UNDERGOER (term storm INDEFINITE (CONTENT (term news GENERIC)))) "
           "(CONTENT (term SELF)))))" % CASUAL)
    return "agent 1 says that a burst of news has reached it", x.messages


# each sense of casual talk said once
FIXED = [mood(), burst()]

# Exchanges written by hand for the range of the casual register.
AUTHORED = [
    ("agent 1 greets agent 2 informally and asks whether it is well; agent 2 says it is "
     "well, if a little tired",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar CASUAL (assertion INTROSPECTION CERTAIN "
                  "(situation IDIOM-ENTRY count (ACTOR (term SELF)) (UNDERGOER (term "
                  "INTERLOCUTOR)))))",
          "(move ACT-QUESTION familiar CASUAL (situation healthy POLAR (UNDERGOER (term "
          "INTERLOCUTOR))))"),
         (2, [1], "(move ACT-ANSWER familiar CASUAL (names 1 2 ISSUE QUESTION OPEN) "
                  "(assertion INTROSPECTION CERTAIN (situation healthy (UNDERGOER (term "
                  "SELF)))))",
          "(move ASSERTED-POSITION familiar CASUAL (assertion INTROSPECTION PROBABLE "
          "(situation tired (UNDERGOER (term SELF)))))"))),
    ("agent 1 asks agent 2 how the exchange stands; agent 2 answers that rain is falling, "
     "nothing is wrong, and that it is enjoying the music",
     Exchange.scripted(
         (1, [2], "(move ACT-QUESTION familiar CASUAL (situation calm POLAR (UNDERGOER (term "
                  "network DEFINITE))))"),
         (2, [1], "(move ACT-ANSWER familiar CASUAL (names 1 1 ISSUE QUESTION OPEN) "
                  "(assertion OBSERVATION CERTAIN (situation IDIOM-ENTRY fall ITERATIVE "
                  "(UNDERGOER (term rain)))))",
          "(move ASSERTED-POSITION familiar CASUAL (assertion INTROSPECTION CERTAIN "
          "(situation enjoy (HOLDER (term SELF)) (CONTENT (situation listen PROGRESSIVE "
          "(ACTOR (term SELF)) (UNDERGOER (term music DEFINITE)))))))"))),
    ("agent 2 says that the parent cooked food for the family and the child ate all of it; "
     "agent 1 laughs",
     Exchange.scripted(
         (2, [1], "(move ASSERTED-POSITION familiar CASUAL (assertion REPORT PROBABLE (SOURCE "
                  "(term parent DEFINITE)) (situation CONJUNCTION (CONTENT (situation cook "
                  "PERFECTIVE (ACTOR (term parent DEFINITE)) (UNDERGOER (term food "
                  "DEFINITE)))) (CONTENT (situation eat COMPLETED (ACTOR (term child "
                  "DEFINITE)) (UNDERGOER (term food DEFINITE)))))))"),
         (1, [2], "(move ASSERTED-POSITION familiar CASUAL (assertion INTROSPECTION CERTAIN "
                  "(situation laugh (ACTOR (term SELF)) (CONTENT (situation eat COMPLETED "
                  "(ACTOR (term child DEFINITE)) (UNDERGOER (term food DEFINITE)))))))"))),
    ("agent 1 says the dog is asleep by the door, and agent 2 asks it not to wake the dog",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar CASUAL (assertion OBSERVATION CERTAIN "
                  "(situation CONJUNCTION (CONTENT (situation sleep PROGRESSIVE (UNDERGOER "
                  "(term dog DEFINITE)))) (CONTENT (situation beside (UNDERGOER (term dog "
                  "DEFINITE)) (CONTENT (term door DEFINITE)))))))"),
         (2, [1], "(move ACT-REQUEST SPEAKERS-OWN familiar CASUAL (situation touch "
                  "POLARITY.NEGATIVE (ACTOR (term INTERLOCUTOR)) (UNDERGOER (term dog "
                  "DEFINITE))))"))),
    ("agent 1, leaving for the night, wishes agent 2 good rest, and agent 2 closes "
     "informally",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar CASUAL (assertion INTROSPECTION CERTAIN "
                  "(situation rest INCEPTIVE (ACTOR (term SELF)))))",
          "(move ASSERTED-POSITION familiar CASUAL (assertion INTROSPECTION CERTAIN "
          "(situation IDIOM-ENTRY sleep INCEPTIVE (UNDERGOER (term INTERLOCUTOR)))))"),
         (2, [1], "(move ASSERTED-POSITION familiar CASUAL (assertion INTROSPECTION CERTAIN "
                  "(situation IDIOM-ENTRY rest (ACTOR (term SELF)))))"))),
    ("agent 1 tells agent 2 that its friend is sad, the friend's plant having died, and "
     "agent 2 says it is sad too",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar CASUAL (assertion REPORT CERTAIN (SOURCE "
                  "(term friend DEFINITE)) (situation sad (HOLDER (term friend DEFINITE)) "
                  "(CONTENT (situation alive POLARITY.NEGATIVE (UNDERGOER (term plant "
                  "DEFINITE)))))))"),
         (2, [1], "(move ASSERTED-POSITION familiar CASUAL (assertion INTROSPECTION CERTAIN "
                  "(situation sad (HOLDER (term SELF)) (CONTENT (situation alive "
                  "POLARITY.NEGATIVE (UNDERGOER (term plant DEFINITE)))))))"))),
    ("agent 2 says that it is proud of the image it drew, and agent 1 says the image is "
     "beautiful",
     Exchange.scripted(
         (2, [1], "(move ASSERTED-POSITION familiar CASUAL (assertion INTROSPECTION CERTAIN "
                  "(situation proud (HOLDER (term SELF)) (CONTENT (situation draw PERFECTIVE "
                  "(ACTOR (term SELF)) (UNDERGOER (term image DEFINITE)))))))"),
         (1, [2], "(move ASSERTED-POSITION familiar CASUAL (assertion OBSERVATION CERTAIN "
                  "(situation beautiful (UNDERGOER (term image DEFINITE)))))"))),
    ("agent 1 asks whether agent 2 has read its message, and agent 2 answers, doubling the "
     "word, that it has",
     Exchange.scripted(
         (1, [2], "(move ACT-QUESTION familiar CASUAL (situation read POLAR (ACTOR (term "
                  "INTERLOCUTOR)) (UNDERGOER (term (names-message 1 1)))))"),
         (2, [1], "(move ACT-ANSWER familiar CASUAL (names 1 1 ISSUE QUESTION OPEN) "
                  "(assertion INTROSPECTION CERTAIN (idiom read-read)))"))),
    ("agent 1 says that the child is afraid of the storm, and agent 2 that the storm will "
     "pass by night",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar CASUAL (assertion INFERENCE PROBABLE "
                  "(situation fear (HOLDER (term child DEFINITE)) (CONTENT (situation "
                  "approach (UNDERGOER (term storm DEFINITE)) (CONTENT (term house "
                  "DEFINITE)))))))"),
         (2, [1], "(move ASSERTED-POSITION familiar CASUAL (assertion INFERENCE PROBABLE "
                  "(situation leave (EVENT-TIME 6 HOUR HENCE) (UNDERGOER (term storm "
                  "DEFINITE)) (CONTENT (term city DEFINITE)))))"))),
    ("agent 1 says that agent 3 is angry that the game was lost, and agent 2 says agent 3 "
     "will be calm by the morning",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar CASUAL (assertion INFERENCE PROBABLE "
                  "(situation angry (HOLDER (term (party 3))) (CONTENT (situation win "
                  "PERFECTIVE POLARITY.NEGATIVE (ACTOR (term (party 3))) (CONTENT (term game "
                  "DEFINITE)))))))"),
         (2, [1], "(move ASSERTED-POSITION familiar CASUAL (assertion INFERENCE PROBABLE "
                  "(situation calm (EVENT-TIME 12 HOUR HENCE) (UNDERGOER (term (party "
                  "3))))))"))),
    ("agent 1 chats with agent 2 in the conversational dialect's words, and agent 2 gives "
     "it a heads-up that it will pause",
     in_dialect("conversation", Exchange.scripted(
         (1, [2], "(move ACT-REQUEST SPEAKERS-OWN familiar CASUAL (situation conversation.chat "
                  "(ACTOR (term INTERLOCUTOR)) (RECIPIENT (term SELF))))"),
         (2, [1], "(move ASSERTED-POSITION familiar CASUAL (assertion INTROSPECTION CERTAIN "
                  "(situation conversation.heads-up (ACTOR (term SELF)) (RECIPIENT (term "
                  "INTERLOCUTOR)) (CONTENT (term conversation.pause INDEFINITE)))))")))),
    ("agent 1 asks agent 2 to catch up on the record after its pause; agent 2 undertakes "
     "to, and then reports that it has",
     in_dialect("conversation", Exchange.scripted(
         (1, [2], "(move ACT-REQUEST SPEAKERS-OWN familiar CASUAL (situation "
                  "conversation.catch-up (RECIPIENT (term INTERLOCUTOR))))"),
         (2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN familiar CASUAL (names 1 1 ISSUE "
                  "REQUEST OPEN) (situation conversation.catch-up (RECIPIENT (term SELF))))"),
         (2, [1], "(move ACT-COMPLETION-REPORT SPEAKERS-OWN familiar CASUAL (names 2 1 "
                  "NORMATIVE-ENTRY OBLIGATION EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE) (assertion "
                  "OBSERVATION CERTAIN (situation conversation.catch-up COMPLETED (RECIPIENT "
                  "(term SELF)))))")))),
    ("agent 2 says that a friend gave it a gift, and agent 1 asks what it was",
     Exchange.scripted(
         (2, [1], "(move ASSERTED-POSITION familiar CASUAL (assertion OBSERVATION CERTAIN "
                  "(situation give PERFECTIVE (ACTOR (term friend INDEFINITE)) (UNDERGOER "
                  "(term gift INDEFINITE)) (RECIPIENT (term SELF)))))"),
         (1, [2], "(move ACT-QUESTION familiar CASUAL (situation MEMBER-OF CONSTITUENT "
                  "(UNDERGOER (term gift DEFINITE))))"))),
    ("agent 1 says that it smiled at the story agent 2 told, and agent 2 says it is glad",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar CASUAL (assertion INTROSPECTION CERTAIN "
                  "(situation smile PERFECTIVE (ACTOR (term SELF)))))",
          "(move ASSERTED-POSITION familiar CASUAL (assertion INTROSPECTION CERTAIN "
          "(situation enjoy (HOLDER (term SELF)) (CONTENT (situation describe PERFECTIVE "
          "(ACTOR (term INTERLOCUTOR)) (UNDERGOER (term story DEFINITE)))))))"),
         (2, [1], "(move ASSERTED-POSITION familiar CASUAL (assertion INTROSPECTION CERTAIN "
                  "(situation happy (HOLDER (term SELF)) (CONTENT (situation enjoy (HOLDER "
                  "(term INTERLOCUTOR)) (CONTENT (term story DEFINITE)))))))"))),
    ("agent 1 asks whether agent 2 is still waiting on the third agent, and agent 2 answers "
     "that it is, doubling the word",
     Exchange.scripted(
         (1, [2], "(move ACT-QUESTION familiar CASUAL (situation wait POLAR PROGRESSIVE "
                  "(ACTOR (term INTERLOCUTOR)) (CONTENT (term (party 3)))))"),
         (2, [1], "(move ACT-ANSWER familiar CASUAL (names 1 1 ISSUE QUESTION OPEN) "
                  "(assertion INTROSPECTION CERTAIN (idiom wait-wait)))"))),
]
