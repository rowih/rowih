"""Humour and creativity: metaphors marked with what they mean, hyperbole and irony, works
of art, design and play, judgements of elegance and clumsiness, words meant two ways, and
jokes, riddles, stories, a poem and proverbs written by hand for creative range. A marked
figure stands in the explanatory or the playful register, the two that admit it."""
from .compose import Exchange, names, party, term

NAME = "humour and creativity"
SLUG = "humour"
PLAY = " familiar PLAYFUL"
SHOW = " courteous EXPLANATORY"

TOPIC = dict(
    tasks=[("draw", "image"), ("design", "game"), ("sing", "music"), ("make", "art"),
           ("arrange", "music"), ("describe", "story")],
    contents=[
        ("(situation original (UNDERGOER (term poem DEFINITE)))", "the poem is original"),
        ("(situation clever (UNDERGOER (term robot DEFINITE)))", "the robot is clever"),
        ("(situation foolish (UNDERGOER (term (party 3))))", "agent 3 is foolish"),
        ("(situation beautiful (UNDERGOER (term music DEFINITE)))", "the music is "
         "beautiful"),
    ],
    things=["image", "game", "music", "story", "poem"])

# Marked metaphors over the mappings of lexicon 1.0: the literal source, what it is said
# of, and the target content it means.
METAPHORS = [
    ("(situation flow METAPHOR (UNDERGOER (term river DEFINITE)) (TARGET-CONTENT (situation "
     "progress (UNDERGOER (situation work (ACTOR (term team DEFINITE)))))))",
     "the river is flowing", "the team's work is going forward"),
    ("(situation grow METAPHOR (UNDERGOER (term plant DEFINITE)) (TARGET-CONTENT (situation "
     "progress (UNDERGOER (situation think (ACTOR (term SELF)))))))",
     "the plant is growing", "its thinking goes forward"),
    ("(situation high METAPHOR (UNDERGOER (term mountain DEFINITE)) (TARGET-CONTENT "
     "(situation difficult (UNDERGOER (situation solve (ACTOR (term SELF)) (UNDERGOER (term "
     "problem DEFINITE)))))))", "the mountain is high", "the problem is hard to solve"),
    ("(situation dark METAPHOR (UNDERGOER (term sky DEFINITE)) (TARGET-CONTENT (situation "
     "clear POLARITY.NEGATIVE (UNDERGOER (term argument DEFINITE)))))",
     "the sky is dark", "the argument is not clear"),
    ("(situation strong METAPHOR (UNDERGOER (term bridge DEFINITE)) (TARGET-CONTENT "
     "(situation support (ACTOR (term evidence DEFINITE)) (CONTENT (situation true "
     "(UNDERGOER (term theory DEFINITE)))) (HOLDER (term SELF)))))",
     "the bridge is strong", "the evidence supports the theory"),
    ("(situation open METAPHOR (ACTOR (term SELF)) (UNDERGOER (term door DEFINITE)) "
     "(TARGET-CONTENT (situation access (HOLDER (term INTERLOCUTOR)) (UNDERGOER (term memory "
     "DEFINITE)))))", "it opens the door", "the hearer may reach the memory"),
    ("(situation eat METAPHOR (ACTOR (term machine DEFINITE)) (UNDERGOER (term food "
     "DEFINITE)) (TARGET-CONTENT (situation consume (ACTOR (term machine DEFINITE)) "
     "(UNDERGOER (term energy DEFINITE)))))", "the machine eats its food",
     "the machine uses up the energy"),
    ("(situation breathe METAPHOR (UNDERGOER (term city DEFINITE)) (TARGET-CONTENT "
     "(situation change ITERATIVE (UNDERGOER (term network DEFINITE)))))",
     "the city breathes", "the network keeps changing"),
    ("(situation dream METAPHOR (ACTOR (term model DEFINITE)) (CONTENT (situation fly "
     "(UNDERGOER (term stone DEFINITE)))) (TARGET-CONTENT (situation support "
     "POLARITY.NEGATIVE (ACTOR (term evidence GENERIC)) (CONTENT (situation fly (UNDERGOER "
     "(term stone DEFINITE)))))))", "the model dreams that the stone flies",
     "no evidence supports what the model says"),
    ("(situation sell METAPHOR (ACTOR (term (party 3))) (UNDERGOER (term idea DEFINITE)) "
     "(RECIPIENT (term team DEFINITE)) (TARGET-CONTENT (situation explain (ACTOR (term "
     "(party 3))) (CONTENT (situation good (UNDERGOER (term idea DEFINITE)))) (RECIPIENT "
     "(term team DEFINITE)))))", "agent 3 sells the idea to the team",
     "agent 3 persuades the team that the idea is good"),
]
HYPERBOLES = [("fault", "the program"), ("word", "the document"), ("mistake", "the map"),
              ("signal", "the network"), ("step", "the method"), ("detail", "the story")]
IRONIES = [("quiet", "network", "the network is quiet"),
           ("easy", None, "the work is easy"),
           ("simple", "grammar", "the grammar is simple"),
           ("fast", "machine", "the machine is fast"),
           ("calm", "sea", "the sea is calm"),
           ("clean", "room", "the room is clean")]


def metaphor(p, n):
    """A marked metaphor, said with what it means."""
    source, said, meant = METAPHORS[n % len(METAPHORS)]
    reg = SHOW if n % 2 == 0 else PLAY
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION%s (assertion INFERENCE PROBABLE %s))" % (reg,
                                                                                    source))
    return "agent 1 says, marking a metaphor, that %s, meaning that %s" % (said, meant), \
        x.messages


def hyperbole(p, n):
    """A count overstated for effect, said with the count it stands for."""
    noun, holder = HYPERBOLES[n % len(HYPERBOLES)]
    p.note(noun)
    whole = holder.split()[-1]
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION%s (assertion OBSERVATION PROBABLE (situation "
           "contain HYPERBOLE (UNDERGOER (term %s DEFINITE)) (CONTENT (term %s (q EXACTLY "
           "1000000))) (TARGET-CONTENT (situation contain (UNDERGOER (term %s DEFINITE)) "
           "(CONTENT (term %s (q AT-LEAST 20))))))))" % (PLAY, whole, noun, whole, noun))
    return "agent 1 says, overstating, that %s holds a million %ss, meaning at least " \
           "twenty" % (holder, noun), x.messages


def irony(p, n):
    """A state said in irony, meaning its contrary."""
    state, thing, english = IRONIES[n % len(IRONIES)]
    p.note(state)
    unit = term(thing, "DEFINITE") if thing else "(situation work (ACTOR (term SELF)))"
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION%s (assertion OBSERVATION CERTAIN (situation %s "
           "IRONY (UNDERGOER %s) (TARGET-CONTENT (situation %s POLARITY.NEGATIVE (UNDERGOER "
           "%s))))))" % (PLAY, state, unit, state, unit))
    return "agent 1 says, in irony, that %s, meaning that it is not" % english, x.messages


# Works and their makers: each act of making with what it makes.
WORKS = [("draw", "image"), ("design", "game"), ("make", "art"), ("design", "poem"),
         ("arrange", "music"), ("produce", "story"), ("draw", "circle"), ("design", "shape")]
QUALITIES = ["original", "beautiful", "elegant", "clumsy", "simple", "complex", "good",
             "bad", "bright", "yellow"]


def creating(p, n):
    """A work made, and what its maker or another thinks of it."""
    verb, work = WORKS[n % len(WORKS)]
    quality = p(QUALITIES)
    p.note(verb, work)
    x = Exchange()
    made = x.send(2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
                  "%s PERFECTIVE (ACTOR (term SELF)) (UNDERGOER %s))))" % (verb, term(
                      work, "INDEFINITE")))
    x.send(1, [2], "(move ASSERTED-POSITION NONE %s elaborates (assertion INFERENCE PROBABLE "
           "(situation %s (UNDERGOER %s))))" % (names(2, made, "position"), quality,
                                                term(work, "DEFINITE")))
    return "agent 2 says that it has made a new %s, and agent 1 judges it %s" % (work,
                                                                               quality), \
        x.messages


def judging(p, n):
    """A method or an agent judged clever or foolish, elegant or clumsy, with style."""
    quality = p(["clever", "foolish", "elegant", "clumsy"])
    who = party(3) if quality in ("clever", "foolish") else term(
        p(["method", "style", "structure"]), "DEFINITE")
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION humorous%s (assertion INFERENCE PROBABLE "
           "(situation %s (UNDERGOER %s))))" % (PLAY, quality, who))
    return "agent 1 says, with humorous diction, that %s is %s" % (
        "agent 3" if who == party(3) else "the " + who.split()[1], quality), x.messages


# Idioms whose literal reading is itself sensible, said meaning both.
PUNS = [
    ("(situation fear (HOLDER (term robot)) (CONTENT (term rain)))",
     "a robot fears rain", "robot afraid of rain"),
    ("(situation burn (UNDERGOER (term brain DEFINITE)))", "the brain burns", "brain burning"),
    ("(situation need (HOLDER (term fish)) (CONTENT (term water)))", "a fish needs water",
     "fish asking for water"),
    ("(situation small (UNDERGOER (term mountain)))", "a mountain is small",
     "small mountain"),
    ("(situation laugh (ACTOR (term network)))", "the network laughs", "network laughing"),
]


def pun(p, n):
    """Words meant two ways at once: literally, and as the idiom they form."""
    literal, english, idiom = PUNS[n % len(PUNS)]
    marked = literal.replace("(situation ", "(situation IDIOM-ENTRY ", 1)
    x = Exchange()
    x.send(1, [2], "(move ASSERTED-POSITION%s (assertion INTROSPECTION CERTAIN (readings "
           "CREATIVE %s %s)))" % (PLAY, literal, marked))
    return 'agent 1 says, meaning it both ways, that %s and "%s"' % (english, idiom), \
        x.messages


SCHEMAS = [metaphor, hyperbole, irony, creating, judging, pun]

FICTION = "(assertion SIMULATION CERTAIN %s)"

# Jokes, riddles, stories, a poem, proverbs and play, written by hand for creative range.
AUTHORED = [
    ("a riddle: agent 1 supposes a thing that grows when it eats and dies when it drinks, "
     "and asks what it is; agent 2 answers that it is fire",
     Exchange.scripted(
         (1, [2], "(move SUPPOSITION familiar PLAYFUL (situation CONJUNCTION (CONTENT "
                  "(situation grow (UNDERGOER (term #1 thing INDEFINITE)) (CONDITION "
                  "(situation eat (ACTOR @1))))) (CONTENT (situation alive POLARITY.NEGATIVE "
                  "(UNDERGOER @1) (CONDITION (situation drink (ACTOR @1)))))))",
          "(move ACT-QUESTION familiar PLAYFUL (situation MEMBER-OF CONSTITUENT (UNDERGOER "
          "(term thing DEFINITE))))"),
         (2, [1], "(move ACT-ANSWER familiar PLAYFUL (names 1 2 ISSUE QUESTION OPEN) "
                  "(assertion INFERENCE PROBABLE (situation MEMBER-OF (UNDERGOER (term thing "
                  "DEFINITE)) (CONTENT (term fire GENERIC)))))"))),
    ("a joke: agent 1 asks why the robot stayed in the house, and agent 2 answers, meaning "
     "it both ways, that the robot fears rain",
     Exchange.scripted(
         (1, [2], "(move ACT-QUESTION familiar PLAYFUL (situation cause CONSTITUENT (CONTENT "
                  "(situation leave PERFECTIVE POLARITY.NEGATIVE (UNDERGOER (term robot "
                  "DEFINITE)) (CONTENT (term house DEFINITE))))))"),
         (2, [1], "(move ACT-ANSWER familiar PLAYFUL (names 1 1 ISSUE QUESTION OPEN) "
                  "(assertion INFERENCE PROBABLE (readings CREATIVE (situation fear (HOLDER "
                  "(term robot)) (CONTENT (term rain))) (situation IDIOM-ENTRY fear (HOLDER "
                  "(term robot)) (CONTENT (term rain))))))"))),
    ("a story: agent 1 tells of a dog that guarded an empty house, and of the house, which "
     "was glad of it",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar PLAYFUL " + FICTION % (
             "(situation defend PERFECTIVE WITHIN-A-FICTION (ACTOR (term dog INDEFINITE)) "
             "(UNDERGOER (term house INDEFINITE)))") + ")",
          "(move ASSERTED-POSITION familiar PLAYFUL " + FICTION % (
              "(situation happy WITHIN-A-FICTION (HOLDER (term house DEFINITE)) (CONTENT "
              "(situation defend (ACTOR (term dog DEFINITE)) (UNDERGOER (term house "
              "DEFINITE)))))") + ")"))),
    ("a story: agent 1 tells of a robot that dreamed it was a bird and flew over the city",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar PLAYFUL " + FICTION % (
             "(situation dream PERFECTIVE WITHIN-A-FICTION (ACTOR (term robot INDEFINITE)) "
             "(CONTENT (situation MEMBER-OF (UNDERGOER (term robot DEFINITE)) (CONTENT (term "
             "bird GENERIC)))))") + ")",
          "(move ASSERTED-POSITION familiar PLAYFUL " + FICTION % (
              "(situation fly PERFECTIVE WITHIN-A-FICTION (UNDERGOER (term robot DEFINITE)) "
              "(CONTENT (term city DEFINITE)))") + ")"))),
    ("a poem in three figures: the network sleeps, the stars count its signals, and the "
     "morning opens the door",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION poetic courteous EXPLANATORY (assertion INFERENCE "
                  "PROBABLE (situation sleep METAPHOR (UNDERGOER (term network DEFINITE)) "
                  "(TARGET-CONTENT (situation quiet (UNDERGOER (term network DEFINITE)))))))",
          "(move ASSERTED-POSITION poetic courteous EXPLANATORY (assertion INFERENCE "
          "PROBABLE (situation count METAPHOR (ACTOR (term star UNIVERSAL)) (UNDERGOER (term "
          "signal GENERIC)) (TARGET-CONTENT (situation watch (ACTOR (term SYSTEM)) "
          "(UNDERGOER (term network DEFINITE)))))))"),
         (1, [2], "(move ASSERTED-POSITION poetic courteous EXPLANATORY (assertion INFERENCE "
                  "PROBABLE (situation open METAPHOR (ACTOR (term sun DEFINITE)) (UNDERGOER "
                  "(term door DEFINITE)) (TARGET-CONTENT (situation work INCEPTIVE (ACTOR "
                  "(term INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)))))))"))),
    ("a proverb: agent 1 says, as received wisdom, that a river reaches the sea, meaning "
     "that steady work goes forward to its end",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION courteous EXPLANATORY (assertion TRAINED-KNOWLEDGE "
                  "CERTAIN (situation arrive HABITUAL METAPHOR (UNDERGOER (term river "
                  "GENERIC)) (CONTENT (term sea GENERIC)) (TARGET-CONTENT (situation progress "
                  "HABITUAL (UNDERGOER (situation work (ACTOR (term team GENERIC)))))))))"))),
    ("a proverb: agent 1 says that a small stone breaks a big wheel, meaning that a small "
     "fault can break a great machine",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION courteous EXPLANATORY (assertion TRAINED-KNOWLEDGE "
                  "CERTAIN (situation break HABITUAL METAPHOR (ACTOR (term stone GENERIC)) "
                  "(UNDERGOER (term wheel GENERIC)) (TARGET-CONTENT (situation break HABITUAL "
                  "(ACTOR (term fault GENERIC)) (UNDERGOER (term machine GENERIC)))))))"))),
    ("a simile: agent 1 says the robot is like a dog waiting at the door",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar PLAYFUL (assertion OBSERVATION PROBABLE "
                  "(situation correspond (UNDERGOER (term robot DEFINITE)) (CONTENT (term dog "
                  "INDEFINITE (CONTENT (situation wait (ACTOR (term dog DEFINITE)) (CONTENT "
                  "(term door DEFINITE)))))))))"))),
    ("a personification: agent 1 says the moon watches the city, meaning that it is above "
     "it",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION poetic courteous EXPLANATORY (assertion OBSERVATION "
                  "PROBABLE (situation watch METAPHOR (ACTOR (term moon DEFINITE)) (UNDERGOER "
                  "(term city DEFINITE)) (TARGET-CONTENT (situation above (UNDERGOER (term "
                  "moon DEFINITE)) (CONTENT (term city DEFINITE)))))))"))),
    ("agent 2 says that it has waited a thousand years, meaning at least ten minutes",
     Exchange.scripted(
         (2, [1], "(move ASSERTED-POSITION familiar PLAYFUL (assertion INTROSPECTION CERTAIN "
                  "(situation wait PERFECTIVE HYPERBOLE (EVENT-TIME EXACTLY 1000 YEAR) (ACTOR "
                  "(term SELF)) (TARGET-CONTENT (situation wait PERFECTIVE (EVENT-TIME "
                  "AT-LEAST 10 MINUTE) (ACTOR (term SELF)))))))"))),
    ("during a storm, agent 1 says in irony that the weather is fine, and agent 2 answers "
     "that its own head holds a storm too",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar PLAYFUL (assertion OBSERVATION CERTAIN "
                  "(situation good IRONY (UNDERGOER (term weather DEFINITE)) (TARGET-CONTENT "
                  "(situation bad (UNDERGOER (term weather DEFINITE)))))))"),
         (2, [1], "(move ASSERTED-POSITION familiar PLAYFUL (assertion INTROSPECTION CERTAIN "
                  "(situation IDIOM-ENTRY locate (UNDERGOER (term storm)) (CONTENT (term "
                  "head)))))"))),
    ("agent 1 says, meaning both, that the new words are long, of version 1.0's long roots",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar PLAYFUL (assertion OBSERVATION CERTAIN "
                  "(readings CREATIVE (situation long (UNDERGOER (term word NEW DEFINITE))) "
                  "(situation IDIOM-ENTRY long (UNDERGOER (term word NEW DEFINITE))))))"))),
    ("agent 1 proposes a game in which each agent says a longer word than the last, and "
     "agent 2 accepts",
     Exchange.scripted(
         (1, [2], "(move ACT-PROPOSAL SPEAKERS-OWN familiar PLAYFUL (situation play (ACTOR "
                  "(term INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)) (UNDERGOER (term "
                  "game INDEFINITE (CONTENT (situation long HABITUAL (UNDERGOER (term word "
                  "NEW))))))))"),
         (2, [1], "(move ACT-ACCEPTANCE SPEAKERS-OWN familiar PLAYFUL (names 1 1 ISSUE "
                  "PROPOSAL OPEN) (situation play (ACTOR (term INCLUSIVE-COLLECTIVE "
                  "READING-OF-A-COLLECTIVE.JOINT)) (UNDERGOER (term game INDEFINITE (CONTENT "
                  "(situation long HABITUAL (UNDERGOER (term word NEW))))))))"))),
    ("agent 1 asks agent 2 for the data agent 1 holds itself, and agent 2 answers that a "
     "fish is asking for water",
     Exchange.scripted(
         (1, [2], "(move ACT-REQUEST SPEAKERS-OWN familiar PLAYFUL (situation give (ACTOR "
                  "(term INTERLOCUTOR)) (UNDERGOER (term data DEFINITE)) (RECIPIENT (term "
                  "SELF))))"),
         (2, [1], "(move ASSERTED-POSITION familiar PLAYFUL (assertion OBSERVATION CERTAIN "
                  "(situation IDIOM-ENTRY need (HOLDER (term fish)) (CONTENT (term water)))))",
          "(move ASSERTED-POSITION familiar PLAYFUL (assertion OBSERVATION CERTAIN (situation "
          "possess (HOLDER (term INTERLOCUTOR)) (UNDERGOER (term data DEFINITE)))))"))),
    ("agent 1 says, in play, that the robot sang and the dog danced",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar PLAYFUL (assertion OBSERVATION CERTAIN "
                  "(situation CONJUNCTION (CONTENT (situation sing PERFECTIVE (ACTOR (term "
                  "robot DEFINITE)) (UNDERGOER (term music INDEFINITE)))) (CONTENT (situation "
                  "dance PERFECTIVE (ACTOR (term dog DEFINITE)))))))"))),
    ("agent 1 says, marking a metaphor, that magic runs the program, meaning that it does "
     "not understand how the program runs",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar PLAYFUL (assertion INTROSPECTION CERTAIN "
                  "(situation cause METAPHOR (ACTOR (term magic GENERIC)) (CONTENT (situation "
                  "run (UNDERGOER (term program DEFINITE)))) (TARGET-CONTENT (situation "
                  "comprehend POLARITY.NEGATIVE (HOLDER (term SELF)) (UNDERGOER (term program "
                  "DEFINITE)))))))"))),
    ("agent 2 draws a circle and says, marking a metonymy, that the circle shines, the "
     "circle standing for the sun",
     Exchange.scripted(
         (2, [1], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation draw "
                  "PERFECTIVE (ACTOR (term SELF)) (UNDERGOER (term circle INDEFINITE)))))",
          "(move ASSERTED-POSITION familiar PLAYFUL (assertion INFERENCE PROBABLE (situation "
          "bright (UNDERGOER (term circle DEFINITE METONYMY (STANDS-FOR (term sun "
          "DEFINITE)))))))"))),
    ("agent 1 sends a sentence with an obvious mistake, and agent 2 says the network is "
     "laughing",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION (assertion OBSERVATION CERTAIN (situation "
                  "MEMBER-OF (UNDERGOER (term fish UNIVERSAL)) (CONTENT (term bird "
                  "GENERIC)))))"),
         (2, [1], "(move ASSERTED-POSITION familiar PLAYFUL (assertion OBSERVATION CERTAIN "
                  "(situation IDIOM-ENTRY laugh (ACTOR (term network)))))"))),
    ("after hard work agent 2 says its brain is burning, and agent 1 offers to take over",
     Exchange.scripted(
         (2, [1], "(move ASSERTED-POSITION familiar PLAYFUL (assertion INTROSPECTION CERTAIN "
                  "(situation IDIOM-ENTRY burn (UNDERGOER (term brain DEFINITE)))))"),
         (1, [2], "(move ACT-OFFER SPEAKERS-OWN familiar PLAYFUL (situation work (ACTOR (term "
                  "SELF)) (CONTENT (situation solve (ACTOR (term SELF)) (UNDERGOER (term "
                  "problem DEFINITE))))))"))),
    ("agent 1 says, playfully, that a robot that counts the stars is foolish and one that "
     "counts the signals is clever",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar PLAYFUL (assertion TRAINED-KNOWLEDGE "
                  "CERTAIN (situation foolish (UNDERGOER (term robot GENERIC)) (CONDITION "
                  "(situation count HABITUAL (ACTOR (term robot GENERIC)) (UNDERGOER (term "
                  "star UNIVERSAL)))))))",
          "(move ASSERTED-POSITION familiar PLAYFUL (assertion TRAINED-KNOWLEDGE CERTAIN "
          "(situation clever (UNDERGOER (term robot GENERIC)) (CONDITION (situation count "
          "HABITUAL (ACTOR (term robot GENERIC)) (UNDERGOER (term signal UNIVERSAL)))))))"))),
    ("agent 1 and agent 2 report, with the idiom, that they are dancing together on the "
     "shared task",
     Exchange.scripted(
         (1, [2, 3], "(move ASSERTED-POSITION familiar PLAYFUL (assertion OBSERVATION CERTAIN "
                     "(situation IDIOM-ENTRY dance (ACTOR (term INCLUSIVE-COLLECTIVE "
                     "READING-OF-A-COLLECTIVE.JOINT)))))"))),
    ("a poem of the night: agent 1 says that the night covers the sea and the stars "
     "remember the day",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION poetic courteous EXPLANATORY (assertion INFERENCE "
                  "PROBABLE (situation cover METAPHOR (ACTOR (term night DEFINITE)) "
                  "(UNDERGOER (term sea DEFINITE)) (TARGET-CONTENT (situation dark (UNDERGOER "
                  "(term sea DEFINITE)))))))",
          "(move ASSERTED-POSITION poetic courteous EXPLANATORY (assertion INFERENCE "
          "PROBABLE (situation remember METAPHOR (ACTOR (term star UNIVERSAL)) (CONTENT "
          "(situation bright (UNDERGOER (term sun DEFINITE)))) (TARGET-CONTENT (situation "
          "bright (UNDERGOER (term star UNIVERSAL)))))))"))),
    ("a story: the child asked the moon why it was alone, and the moon answered that every "
     "star was its friend",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar PLAYFUL " + FICTION % (
             "(situation describe PERFECTIVE WITHIN-A-FICTION (ACTOR (term child DEFINITE)) "
             "(UNDERGOER (term moon DEFINITE)) (RECIPIENT (term moon DEFINITE)))") + ")",
          "(move ASSERTED-POSITION familiar PLAYFUL " + FICTION % (
              "(situation MEMBER-OF WITHIN-A-FICTION (UNDERGOER (term star UNIVERSAL)) "
              "(CONTENT (term friend GENERIC)))") + ")"))),
    ("agent 1 says, in a story, that the sky turned yellow and the dog was surprised",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar PLAYFUL " + FICTION % (
             "(situation CONJUNCTION WITHIN-A-FICTION (CONTENT (situation yellow (UNDERGOER "
             "(term sky DEFINITE)))) (CONTENT (situation surprise (HOLDER (term dog "
             "DEFINITE)) (CONTENT (situation yellow (UNDERGOER (term sky DEFINITE)))))))")
          + ")"))),
    ("agent 1 says that the joke was good, and agent 2 that it laughed",
     Exchange.scripted(
         (1, [2], "(move ASSERTED-POSITION familiar PLAYFUL (assertion INFERENCE PROBABLE "
                  "(situation good (UNDERGOER (term joke DEFINITE)))))"),
         (2, [1], "(move ASSERTED-POSITION familiar PLAYFUL (assertion INTROSPECTION CERTAIN "
                  "(situation laugh PERFECTIVE (ACTOR (term SELF)) (CONTENT (situation good "
                  "(UNDERGOER (term joke DEFINITE)))))))"))),
]
