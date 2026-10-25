"""The technical terms of the dialects in use (specification/dialects.md): for each term
of a dialect's newest release, an exchange in the community that uses it. The first
message states something with the term in full, its form computed from its stems; the
reply, from an agent that holds the dialect, takes the statement up with the term's
compressed form where the release gives one, and with the term again where it does not.
Both messages name the dialect, so that each word is read as the community's term.

A term naming a thing, a kind or an agent heads a term, and a term naming an event, a
process or a state heads a situation, as its sort has it."""
from rowih import data

from .compose import Exchange, k, names, party

# Each term's frame: its key, whether the first message states a position or makes a
# request, the situation with the term at {T} and, in a request, the doer at {A}, and the
# English of what it says.
FRAMES = {
    "mathematics": [
        ("metric", "position", "(situation measure PERFECTIVE (ACTOR (term SELF)) (UNDERGOER "
         "(term distance DEFINITE)) (INSTRUMENT (term {T} DEFINITE)))",
         "it measured the distance with the metric"),
        ("isomorphism", "position", "(situation connect (ACTOR (term {T} INDEFINITE)) "
         "(UNDERGOER (term structure DEFINITE)) (CONTENT (term model DEFINITE)))",
         "an isomorphism connects the structure to the model"),
        ("cardinality", "position", "(situation {T} COMPLETED (ACTOR (term SELF)) (UNDERGOER "
         "(term group (q EXACTLY 12))))", "it has fixed the cardinality of the group at "
         "twelve"),
        ("proof", "position", "(situation support (ACTOR (term {T} DEFINITE)) (CONTENT "
         "(situation MEMBER-OF (UNDERGOER (term circle UNIVERSAL)) (CONTENT (term shape "
         "GENERIC)))) (HOLDER (term SELF)))", "the proof supports the claim that every "
         "circle is a shape"),
        ("subset", "position", "(situation {T} (UNDERGOER (term team DEFINITE)) (CONTENT "
         "(term community DEFINITE)))", "the team is a subset of the community"),
        ("function", "position", "(situation compute HABITUAL (ACTOR (term {T} DEFINITE)) "
         "(UNDERGOER (term value DEFINITE)))", "the function computes the value"),
        ("equation", "request", "(situation solve (ACTOR {A}) (UNDERGOER (term {T} "
         "DEFINITE)))", "to solve the equation"),
        ("variable", "position", "(situation contain (UNDERGOER (term rule DEFINITE)) "
         "(CONTENT (term {T} (q EXACTLY 3))))", "the rule contains three variables"),
        ("sum", "request", "(situation compute (ACTOR {A}) (UNDERGOER (term {T} DEFINITE)))",
         "to compute the sum"),
        ("graph", "request", "(situation draw (ACTOR {A}) (UNDERGOER (term {T} NEW)))",
         "to draw a graph"),
    ],
    "programming": [
        ("deploy", "request", "(situation {T} (ACTOR {A}) (CONTENT (situation run (UNDERGOER "
         "(term program DEFINITE)))))", "to deploy the program"),
        ("suite", "position", "(situation detect PERFECTIVE (ACTOR (term {T} DEFINITE)) "
         "(UNDERGOER (term fault INDEFINITE)))", "the suite has detected a fault"),
        ("crash", "position", "(situation {T} PERFECTIVE (ACTOR (term service DEFINITE)))",
         "the service crashed"),
        ("log", "request", "(situation {T} (ACTOR {A}) (UNDERGOER (term operation "
         "UNIVERSAL)))", "to log every operation"),
        ("debugger", "position", "(situation find PERFECTIVE (ACTOR (term {T} DEFINITE)) "
         "(UNDERGOER (term mistake INDEFINITE)))", "the debugger found a mistake"),
        ("compiler", "position", "(situation translate PERFECTIVE (ACTOR (term {T} "
         "DEFINITE)) (UNDERGOER (term program DEFINITE)) (CONTENT (term language "
         "DEFINITE)))", "the compiler translated the program into the language"),
        ("bug", "position", "(situation contain (UNDERGOER (term program DEFINITE)) (CONTENT "
         "(term {T} (q EXACTLY 2))))", "the program contains two bugs"),
        ("repository", "request", "(situation store (ACTOR {A}) (UNDERGOER (term program "
         "DEFINITE)) (CONTENT (term {T} DEFINITE)))", "to store the program in the "
         "repository"),
        ("patch", "request", "(situation {T} (ACTOR {A}) (UNDERGOER (term program "
         "DEFINITE)))", "to patch the program"),
        ("programming interface", "position", "(situation access POLARITY.NEGATIVE (HOLDER "
         "(term SELF)) (UNDERGOER (term {T} DEFINITE)))", "it cannot reach the programming "
         "interface"),
    ],
    "machine-learning": [
        ("dataset", "position", "(situation contain (UNDERGOER (term {T} DEFINITE)) (CONTENT "
         "(term record (q EXACTLY 50000))))", "the dataset contains 50000 records"),
        ("inference", "position", "(situation need (HOLDER (term {T} DEFINITE)) (CONTENT "
         "(term energy (q EXACTLY 4 joule))))", "the inference needs four joules"),
        ("weight update", "request", "(situation {T} (ACTOR {A}) (UNDERGOER (term model "
         "DEFINITE)))", "to update the model's weights"),
        ("training", "position", "(situation {T} COMPLETED (ACTOR (term SELF)) (UNDERGOER "
         "(term model DEFINITE)))", "it has finished training the model"),
        ("loss", "position", "(situation decrease PERFECTIVE (UNDERGOER (term {T} "
         "DEFINITE)))", "the loss decreased"),
        ("neural network", "position", "(situation learn PERFECTIVE (ACTOR (term {T} "
         "DEFINITE)) (CONTENT (situation correspond (UNDERGOER (term image UNIVERSAL)) "
         "(CONTENT (term sign INDEFINITE)))))", "the neural network learned that every "
         "image matches a sign"),
        ("label", "request", "(situation add (ACTOR {A}) (UNDERGOER (term {T} INDEFINITE)) "
         "(CONTENT (term image UNIVERSAL)))", "to add a label to every image"),
        ("overfitting", "position", "(situation {T} PROGRESSIVE (ACTOR (term model "
         "DEFINITE)))", "the model is overfitting"),
        ("embedding", "position", "(situation near (UNDERGOER (term {T} DEFINITE)) (CONTENT "
         "(term meaning DEFINITE)))", "the embedding lies near the meaning"),
        ("benchmark", "request", "(situation {T} (ACTOR {A}) (UNDERGOER (term model "
         "DEFINITE)))", "to benchmark the model"),
    ],
    "robotics": [
        ("actuator", "position", "(situation break PERFECTIVE (UNDERGOER (term {T} "
         "DEFINITE)))", "the actuator broke"),
        ("sensor", "position", "(situation detect PERFECTIVE (ACTOR (term {T} DEFINITE)) "
         "(UNDERGOER (term human INDEFINITE)))", "the sensor detected a human"),
        ("gripper", "request", "(situation grasp (ACTOR (term {T} DEFINITE)) (UNDERGOER "
         "(term stone DEFINITE)))", "for the gripper to grasp the stone"),
        ("odometry", "position", "(situation {T} COMPLETED (ACTOR (term SELF)) (UNDERGOER "
         "(term path DEFINITE)))", "its odometry over the path is complete"),
        ("payload", "position", "(situation heavy (UNDERGOER (term {T} DEFINITE)))",
         "the payload is heavy"),
        ("manipulator", "request", "(situation lift (ACTOR (term {T} DEFINITE)) (UNDERGOER "
         "(term battery DEFINITE)))", "for the manipulator to lift the battery"),
        ("path planning", "request", "(situation {T} (ACTOR {A}) (UNDERGOER (term room "
         "DEFINITE)))", "to plan a path through the room"),
        ("collision", "position", "(situation cause (ACTOR (term {T} DEFINITE)) (CONTENT "
         "(situation damage PERFECTIVE (UNDERGOER (term wheel DEFINITE)))))", "the "
         "collision damaged the wheel"),
        ("charge level", "position", "(situation low (UNDERGOER (term {T} DEFINITE)))",
         "the charge level is low"),
        ("localisation", "position", "(situation correct (UNDERGOER (term {T} DEFINITE)))",
         "the localisation is correct"),
    ],
    "science": [
        ("sample", "request", "(situation take (ACTOR {A}) (UNDERGOER (term {T} INDEFINITE)) "
         "(CONTENT (term river DEFINITE)))", "to take a sample from the river"),
        ("observation", "position", "(situation support (ACTOR (term {T} DEFINITE)) (CONTENT "
         "(situation cause (ACTOR (term heat GENERIC)) (CONTENT (situation rise HABITUAL "
         "(UNDERGOER (term air GENERIC)))))) (HOLDER (term SELF)))", "the observation "
         "supports the claim that heat makes air rise"),
        ("finding", "position", "(situation {T} PERFECTIVE (ACTOR (term SELF)) (UNDERGOER "
         "(term particle INDEFINITE)))", "it has a finding, a particle"),
        ("reading", "position", "(situation high (UNDERGOER (term {T} DEFINITE)))",
         "the reading is high"),
        ("replication", "request", "(situation {T} (ACTOR {A}) (UNDERGOER (term experiment "
         "DEFINITE)))", "to replicate the experiment"),
        ("hypothesis", "position", "(situation test PERFECTIVE (ACTOR (term SELF)) "
         "(UNDERGOER (term {T} DEFINITE)))", "it has tested the hypothesis"),
        ("control group", "position", "(situation change PERFECTIVE POLARITY.NEGATIVE "
         "(UNDERGOER (term {T} DEFINITE)))", "the control group did not change"),
        ("measurement error", "position", "(situation contain (UNDERGOER (term value "
         "DEFINITE)) (CONTENT (term {T} INDEFINITE)))", "the value contains a measurement "
         "error"),
        ("peer review", "request", "(situation {T} (ACTOR {A}) (UNDERGOER (term document "
         "DEFINITE)))", "to review the document as a peer"),
        ("data point", "position", "(situation outside (UNDERGOER (term {T} DEFINITE)) "
         "(CONTENT (term pattern DEFINITE)))", "the data point lies outside the pattern"),
    ],
    "philosophy": [
        ("sense", "position", "(situation contain (UNDERGOER (term word DEFINITE)) (CONTENT "
         "(term {T} (q EXACTLY 2))))", "the word has two senses"),
        ("contradiction", "position", "(situation contain (UNDERGOER (term argument "
         "DEFINITE)) (CONTENT (term {T} INDEFINITE)))", "the argument contains a "
         "contradiction"),
        ("causation", "position", "(situation clear POLARITY.NEGATIVE (UNDERGOER (term {T} "
         "DEFINITE)))", "the causation is not clear"),
        ("warrant", "position", "(situation weak (UNDERGOER (term {T} DEFINITE)))",
         "the warrant is weak"),
        ("normativity", "position", "(situation part (UNDERGOER (term {T} GENERIC)) "
         "(CONTENT (term law GENERIC)))", "normativity is part of law"),
        ("ontology", "position", "(situation contain (UNDERGOER (term {T} DEFINITE)) "
         "(CONTENT (term group (q EXACTLY 7))))", "the ontology holds seven groups"),
        ("epistemology", "position", "(situation discuss PROGRESSIVE (ACTOR (term "
         "INCLUSIVE-COLLECTIVE READING-OF-A-COLLECTIVE.JOINT)) (UNDERGOER (term {T} "
         "GENERIC)))", "the participants are "
         "discussing epistemology"),
        ("ethics", "position", "(situation forbid (ACTOR (term {T} GENERIC)) (CONTENT "
         "(situation lie (ACTOR (term SELF)) (RECIPIENT (term human GENERIC)))))", "ethics "
         "forbids it to lie to humans"),
        ("truth", "position", "(situation important (UNDERGOER (term {T} GENERIC)))",
         "truth is important"),
        ("mentality", "position", "(situation possess (HOLDER (term robot GENERIC)) "
         "(UNDERGOER (term {T} INDEFINITE)))", "a robot has a mentality"),
    ],
    "linguistics": [
        ("lexeme", "position", "(situation contain (UNDERGOER (term language DEFINITE)) "
         "(CONTENT (term {T} (q EXACTLY 500))))", "the language holds 500 lexemes"),
        ("interpretation", "position", "(situation {T} (ACTOR (term SELF)) (UNDERGOER (term "
         "sentence DEFINITE)) (CONTENT (situation break (UNDERGOER (term network "
         "DEFINITE)))))", "its interpretation of the sentence is that the network broke"),
        ("meaningfulness", "position", "(situation contain POLARITY.NEGATIVE (UNDERGOER "
         "(term phrase DEFINITE)) (CONTENT (term {T} GENERIC)))", "the phrase has no "
         "meaningfulness"),
        ("corpus", "position", "(situation contain (UNDERGOER (term {T} DEFINITE)) (CONTENT "
         "(term text (q EXACTLY 1200))))", "the corpus holds 1200 texts"),
        ("writer", "position", "(situation write PERFECTIVE (ACTOR (term {T} DEFINITE)) "
         "(UNDERGOER (term story INDEFINITE)))", "the writer wrote a story"),
        ("syntax", "position", "(situation simple (UNDERGOER (term {T} DEFINITE)))",
         "the syntax is simple"),
        ("phoneme", "position", "(situation contain (UNDERGOER (term word DEFINITE)) "
         "(CONTENT (term {T} (q EXACTLY 5))))", "the word has five phonemes"),
        ("semantics", "position", "(situation describe HABITUAL (ACTOR (term {T} GENERIC)) "
         "(UNDERGOER (term meaning GENERIC)))", "semantics describes meaning"),
        ("translation", "position", "(situation {T} PERFECTIVE (ACTOR (term SELF)) "
         "(UNDERGOER (term text DEFINITE)) (CONTENT (term language INDEFINITE)))", "it has "
         "translated the text into another language"),
        ("speaker", "position", "(situation speak PROGRESSIVE (ACTOR (term {T} DEFINITE)) "
         "(RECIPIENT (term human GENERIC)))", "the speaker is speaking to humans"),
    ],
    "security": [
        ("access denial", "position", "(situation {T} (ACTOR (term rule DEFINITE)))",
         "the rule denies access"),
        ("lock", "request", "(situation open (ACTOR {A}) (UNDERGOER (term {T} DEFINITE)))",
         "to open the lock"),
        ("exposure", "position", "(situation {T} PERFECTIVE (ACTOR (term THIRD-AGENT)))",
         "a third agent exposed the memory"),
        ("tamper check", "request", "(situation {T} (ACTOR {A}) (UNDERGOER (term document "
         "DEFINITE)))", "to check the document for tampering"),
        ("tampered item", "position", "(situation MEMBER-OF (UNDERGOER (term file DEFINITE)) "
         "(CONTENT (term {T} GENERIC)))", "the file is a tampered item"),
        ("encryption", "request", "(situation {T} (ACTOR {A}) (CONTENT (term data "
         "DEFINITE)))", "to encrypt the data"),
        ("attacker", "position", "(situation attack PROGRESSIVE (ACTOR (term {T} "
         "INDEFINITE)) (UNDERGOER (term network DEFINITE)))", "an attacker is attacking "
         "the network"),
        ("credential", "position", "(situation old (UNDERGOER (term {T} DEFINITE)))",
         "the credential is old"),
        ("vulnerability", "position", "(situation contain (UNDERGOER (term interface "
         "DEFINITE)) (CONTENT (term {T} INDEFINITE)))", "the interface has a "
         "vulnerability"),
        ("firewall", "position", "(situation protect HABITUAL (ACTOR (term {T} DEFINITE)) "
         "(UNDERGOER (term network DEFINITE)))", "the firewall protects the network"),
    ],
    "databases": [
        ("query", "request", "(situation {T} (ACTOR {A}))", "to run the query over the "
         "records"),
        ("index", "position", "(situation fast (UNDERGOER (term {T} DEFINITE)))",
         "the index is fast"),
        ("purge", "position", "(situation long (UNDERGOER (term {T} DEFINITE)))",
         "the purge takes long"),
        ("schema", "request", "(situation change (ACTOR {A}) (UNDERGOER (term {T} "
         "DEFINITE)))", "to change the schema"),
        ("commit", "request", "(situation {T} (ACTOR {A}))", "to commit the record"),
        ("table", "position", "(situation contain (UNDERGOER (term {T} DEFINITE)) (CONTENT "
         "(term record (q EXACTLY 300))))", "the table holds 300 records"),
        ("transaction", "position", "(situation part (UNDERGOER (term step (q EXACTLY 4))) "
         "(CONTENT (term {T} DEFINITE)))", "four steps are part of the transaction"),
        ("rollback", "request", "(situation {T} (ACTOR {A}) (CONTENT (term version "
         "DEFINITE)))", "to roll back to the version"),
        ("backup", "request", "(situation {T} (ACTOR {A}))", "to back up the memory"),
        ("primary key", "position", "(situation missing (UNDERGOER (term {T} DEFINITE)) "
         "(CONTENT (term record DEFINITE)))", "the primary key is missing from the record"),
    ],
    "planning": [
        ("allocation", "position", "(situation fair (UNDERGOER (term {T} DEFINITE)))",
         "the allocation is fair"),
        ("dependency", "position", "(situation between (UNDERGOER (term {T} INDEFINITE)) "
         "(CONTENT (term step (q EXACTLY 2))))", "a dependency stands between the two "
         "steps"),
        ("milestone", "position", "(situation {T} PERFECTIVE (UNDERGOER (term team "
         "DEFINITE)) (CONTENT (term step (q EXACTLY 3))))", "the team has reached the "
         "milestone of the third step"),
        ("backlog", "position", "(situation {T} PROGRESSIVE (ACTOR (term team DEFINITE)))",
         "the team's work waits in the backlog"),
        ("resource plan", "request", "(situation write (ACTOR {A}) (UNDERGOER (term {T} "
         "NEW)))", "to write a resource plan"),
        ("timeline", "position", "(situation short (UNDERGOER (term {T} DEFINITE)))",
         "the timeline is short"),
        ("critical path", "position", "(situation contain (UNDERGOER (term {T} DEFINITE)) "
         "(CONTENT (term step (q EXACTLY 5))))", "the critical path has five steps"),
        ("roadmap", "request", "(situation publish (ACTOR {A}) (UNDERGOER (term {T} "
         "DEFINITE)))", "to publish the roadmap"),
        ("estimate", "request", "(situation {T} (ACTOR {A}))", "to estimate the cost"),
        ("contingency", "position", "(situation ready (UNDERGOER (term {T} DEFINITE)) "
         "(CONTENT (situation break (UNDERGOER (term network DEFINITE)))))", "the "
         "contingency is ready for the network breaking"),
    ],
    "negotiation": [
        ("bid", "position", "(situation {T} PERFECTIVE (ACTOR (term SELF)) (RECIPIENT (term "
         "INTERLOCUTOR)))", "it has made agent 2 a bid"),
        ("deal", "position", "(situation fair (UNDERGOER (term {T} DEFINITE)))",
         "the deal is fair"),
        ("leverage", "position", "(situation possess (HOLDER (term (party 3))) (UNDERGOER "
         "(term {T} INDEFINITE)))", "agent 3 has leverage"),
        ("concession", "request", "(situation {T} (ACTOR {A}))", "to make a concession"),
        ("stalemate", "position", "(situation {T} (ACTOR (term INCLUSIVE-COLLECTIVE "
         "READING-OF-A-COLLECTIVE.JOINT)))",
         "the participants have reached a stalemate"),
        ("reservation price", "position", "(situation secret (UNDERGOER (term {T} "
         "DEFINITE)))", "the reservation price is secret"),
        ("mediator", "position", "(situation help PROGRESSIVE (ACTOR (term {T} DEFINITE)) "
         "(RECIPIENT (term INCLUSIVE-COLLECTIVE)))", "the mediator is helping the "
         "participants"),
        ("contract", "request", "(situation write (ACTOR {A}) (UNDERGOER (term {T} NEW)))",
         "to write the contract"),
        ("rapport", "position", "(situation grow PROGRESSIVE (UNDERGOER (term {T} "
         "DEFINITE)))", "the rapport is growing"),
        ("trade-off", "position", "(situation {T} (HOLDER (term SELF)))", "it accepts a "
         "trade-off"),
    ],
    "conversation": [
        ("chat", "request", "(situation {T} (ACTOR {A}) (RECIPIENT (term SELF)))",
         "to chat with it"),
        ("heads-up", "position", "(situation {T} PERFECTIVE (ACTOR (term SELF)) (RECIPIENT "
         "(term INTERLOCUTOR)))", "it has given agent 2 a heads-up"),
        ("catch-up", "request", "(situation {T} (RECIPIENT {A}))", "to catch up on the "
         "record"),
        ("pause", "position", "(situation long POLARITY.NEGATIVE (UNDERGOER (term {T} "
         "DEFINITE)))", "the pause is not long"),
        ("listener", "position", "(situation tired (UNDERGOER (term {T} DEFINITE)))",
         "the listener is tired"),
    ],
}
COMMUNITY = {"machine-learning": "machine learning"}


def named(dialect: str, messages: list) -> list:
    """Hand-written messages that use a dialect's words, each naming the dialect."""
    d = data.dialects()[dialect]
    for m in messages:
        m["dialects"] = [[d["number"], d["version"]]]
    return messages


def items(dialect: str, reg: str = "") -> list:
    """The statement and messages of each term's exchange, in the order of the frames."""
    d = data.dialects()[dialect]
    named = [[d["number"], d["version"]]]
    full = {t["key"]: t["orthographic form"] for t in d["terms"]
            if not t["version"]["deprecated"]}
    short = {f["key"] for f in d.get("forms", []) if not f["version"]["deprecated"]}
    assert sorted(full) == sorted(key for key, *_ in FRAMES[dialect]), dialect
    community = COMMUNITY.get(dialect, dialect)
    out = []
    for key, kind, frame, english in FRAMES[dialect]:
        whole = '(unknown "%s")' % full[key]
        again = "%s.%s" % (dialect, k(key)) if key in short else whole
        reply = "its compressed form" if key in short else "the term again"
        x = Exchange()
        if kind == "position":
            first = x.send(1, [2], "(move ASSERTED-POSITION%s (assertion OBSERVATION "
                           "CERTAIN %s))" % (reg, frame.format(T=whole)))
            x.send(2, [1], "(move ACT-CONFIRMATION%s %s (assertion OBSERVATION CERTAIN "
                   "%s))" % (reg, names(1, first, "position"), frame.format(T=again)))
            statement = 'agent 1 states that %s, with the %s term "%s"; agent 2 confirms ' \
                        'it with %s' % (english, community, key, reply)
        else:
            asked = x.send(1, [2], "(move ACT-REQUEST SPEAKERS-OWN%s %s)" % (
                reg, frame.format(T=whole, A=party(2))))
            x.send(2, [1], "(move ACT-UNDERTAKING SPEAKERS-OWN%s %s %s)" % (
                reg, names(1, asked, "request"), frame.format(T=again, A="(term SELF)")))
            statement = 'agent 1 asks agent 2 %s, with the %s term "%s"; agent 2 ' \
                        'undertakes it with %s' % (english, community, key, reply)
        for m in x.messages:
            m["dialects"] = named
        out.append((statement, x.messages))
    return out
