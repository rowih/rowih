# What a message means

A move has two parts to its meaning. Its **core** is what it does and says: its force, its content, the standing and provenance of what it asserts, its times and the entries it names. Its **social and textual component** is how it is said: its register, its diction, the stance and the relation between the participants it conveys, and its wording. The core is what a hearer acts on and what the language's guarantees protect; the social and textual component is kept by the analysis and set aside by the normal form, and a move that leaves any of it unstated in its core declares the loss ([The lexicon](lexicon.md#conventional-expressions-and-idioms)). This chapter states what each class of the grammar contributes to the core, how the normal form states the core in full, and what the English explanation of a move is.

Truth is never marked. Nothing a speaker says places a proposition in the world except as the speaker's claim, and a hearer that receives an assertion records that the speaker asserted it, not that it holds. What a hearer decides to do with a move is never part of the move's meaning.

## Force

The force of a move is what it does to the record its participants share ([The record and discourse](discourse.md)). Four dimensions generate every act: the kind of entry the move adds, the kind of entry it names, whose that entry is, and what the move does to it. Whose the entry is follows from the reference, which states the entry's author, so it needs no class.

What a move adds is one of eight kinds:

- an **asserted position**, a proposition the speaker puts on record with its standing and answers for;
- a **conceded position**, a proposition the speaker grants without asserting it;
- a **supposition**, a proposition entertained without standing, whose content is evaluated within the supposition;
- a **summary** of entries it names ([Standing and provenance](#standing-and-provenance));
- an **issue**: a question, a request, a proposal or a challenge;
- a **normative entry**: a commitment, public and answerable to a counterparty; an obligation, a requirement imposed by an authority or a norm, which holds whether or not it is accepted; a permission, an authorisation to act; an assignment, a task delegated; or a recommendation, a suggestion that binds no one;
- a **setting**: a definition, a version, a role, a calibration, which declares how a participant's numbers are to be read, or a relation between the participants, such as thanks or an apology;
- **nothing beyond its own record**, for a move that only changes the entries it names, such as a rejection, an acknowledgement or a withdrawal.

A normative entry other than a recommendation states its **bindingness**: *on acceptance*, binding when the hearer accepts it, as an offer or a delegation; *bound*, binding on the move, as a promise, a command or a grant; or *bound within a protocol*, a commitment whose conditions of release the protocol in force fixes.

A move that names an entry states its **change**: *none*, for a move that names an entry and changes nothing, such as an agreement, a confirmation, a challenge or a summary; a **resolution**, which closes an issue or discharges an entry with its outcome, an *answer*, an *acceptance*, a *rejection*, a *settlement* or a *failure*; a **lowering**, which reduces or removes what the entry claims, as a retraction, a cancellation, a refusal, a release or the correction of one's own position does; or an **acknowledgement**, which records the receipt of the move it names and changes no status. A change other than none states its **extent**, the whole entry or a part of it, and **when it takes effect**, on the move or on acceptance; a change that takes effect on acceptance waits for the hearer to accept it.

The **authority** a move claims is the speaker's own, that of a named principal on whose behalf it acts, or that of a named role. Authority is always a claim: the language states it and lets a hearer check that it was stated, and whether the speaker holds it is decided outside the language. An action done at another's request is recorded under the requester's authority.

## Standing and provenance

The **standing** of an assertion is the speaker's grounds for it, made public: its basis and its strength. Only the speaker's own grounds are standing; the grounds of a reported attitude are part of the content reported. Every assertion has a standing, stated or by default, and the default claims nothing: a basis left unstated is the unstated basis, and a strength left unstated is the unstated strength, which is the whole of the interval from 0 to 1. Omitting a standing never strengthens a claim.

A **basis** says where the speaker's grounds come from. *Observation* is the speaker's own perception, or the output of a tool it invoked; *introspection* is its access to its own states; *retrieval* is a stored record with its own time and source; *trained knowledge* comes from the speaker's parameters, with no record and no source to cite, and must never be presented as retrieval; *computation* is a deterministic procedure; *inference* is reasoning from records available as premises; *simulation* is the outcome of a modelled course of events; *report* is another agent's communication, whose provenance names the agent; *source lost* is held with the record of its origin lost. The bases fall into three tiers by what a hearer can check, not by how reliable they are: the first has a citable origin, the second has nothing to cite, and the third claims none. Bases within a tier are not ranked against each other.

<!-- generated: basis-tiers -->
| Tier | Basis |
|---|---|
| 1 | `teyuhu` OBSERVATION |
| 1 | `tadowe` INTROSPECTION |
| 1 | `turimi` RETRIEVAL |
| 1 | `tinopo` COMPUTATION |
| 1 | `tilase` INFERENCE |
| 1 | `tuwohu` SIMULATION |
| 1 | `tukika` REPORT |
| 2 | `tiruni` TRAINED-KNOWLEDGE |
| 2 | `tukemu` SOURCE-LOST |
| 3 | `tineti` BASIS.UNSTATED |
<!-- end generated -->

A **strength** is an interval of probability. The named strengths are these intervals; a numeric strength, written as a number in the assertion, is a point, or an interval written with `~`, or the interval from a number to 1 after *at least* and from 0 to a number after *at most*. A numeric strength must lie within 0 and 1. Strengths are compared by the lower end of their intervals, a closed end claiming less than an open one at the same value.

<!-- generated: strength-intervals -->
| Strength | Interval of probability |
|---|---|
| `tebilo` CERTAIN | [0.99, 1] |
| `tamepi` HIGHLY-PROBABLE | [0.9, 1] |
| `tomupu` PROBABLE | [0.66, 1] |
| `tusido` UNCERTAIN | [0.33, 0.66] |
| `topeka` SPECULATIVE | (0, 1] |
| `topuge` STRENGTH.UNSTATED | [0, 1] |
<!-- end generated -->

A number means what its **calibration** makes it mean. The named strengths are under the calibration of the lexicon; a participant may declare its own calibration by a setting, and two numeric strengths are the same only under the same calibration. The language does not calibrate one agent's numbers against another's.

**Provenance** is the history of what is asserted. An assertion may state at most two provenance links: a *source*, who or what supplied the content; a *relayer*, the participant that passed it on; and a *premise*, a record an inference was drawn from. A term may state its source, and only a source. The links of a conversation form a directed graph without cycles, which a transformation may summarise and must never delete or strengthen. A relay is the relayer's own assertion, on the basis of report, naming the participant heard as its source and the relayer as its relayer, with no strength of its own; a relayer that vouches for what it relays does so in a further assertion.

A **confirmation** is an asserted position that names an asserted or a conceded position with the change *none*. A confirmation alone states its **independence**: *same source*, the default and the weaker, or *independent*, which must name the independent source as a provenance link. A confirmation by another instance of the same model is not independent.

A **summary** names every entry it summarises, and its assertion states the standing those entries support together: the bases of the lowest tier present among them, every such basis where there are several, and for each calibration the strength with the least lower end, or the smallest interval containing those that tie. A summary that summarises an unstated strength states the unstated strength alone. The assertion of a summary names the calibrating participant of each numeric strength it states.

The times of a standing are ordered: what was observed was observed no later than it was inferred from, and inferred no later than it was said. An assertion whose observation time follows its inference time, or whose inference time follows its communication time, is refused. An assertion based on observation of a situation in the actual world places the situation's start no later than the end of the observation.

## Attitudes and aims

An attitude is content: *A believes P* is a situation, whose holder is A and whose content is P, and which a speaker asserts with its own standing. A reported attitude may carry the holder's grounds, its own basis and strength, which are part of what is reported. Attitudes nest within the limit on nesting.

The kinds of attitude are *belief*, treating a proposition as true; *credence*, a degree on the scale of probability; *acceptance*, treating a proposition as true for a purpose, as an assumption is; *entertaining*, holding a hypothesis neither believed nor disbelieved; *desire*, a state of affairs held preferable and not adopted; *goal*, a state of affairs adopted as something to bring about; *intention*, a goal to which the holder's own future action is committed, whose content must be an action of the holder's or a plan of such actions; *preference*, an ordering of alternatives; and four stances toward a question: *unexamined*, *settled*, *unresolved* and *unresolvable*.

The **origin of an aim** says whose will stands behind an aim or a normative state: the holder's own, its principal's, an instruction received, or a norm, without saying whether that will has power over the hearer. The **status of a normative state** reports where a commitment or obligation stands: *in force*, *discharged*, *released*, *withdrawn* or *retracted by its holder*. The **counterparty** is the one a normative state is owed to. The **execution phase** says where an action stands: *not yet begun*, *attempted*, *completed*, *failed* or *abandoned*; it differs from aspect, which is how the speaker presents any situation.

## Situations and contents

A situation is headed by its predicate, a content word, and states its participants by role. The **participations** are the *actor*, whose doing the situation is; the *undergoer*, whom it changes or affects; the *recipient*, to whom something passes; the *instrument*, with which an actor acts; the *holder*, whose state or attitude it is; and the *content*, what an attitude, an act or an aim takes. A root's entry states the roles it takes and the sort of each role's filler.

- **Aspect** is how the situation is presented: *stative*, *perfective*, *progressive*, *inceptive*, *completive*, *interrupted*, *continuative*, *iterative* or *habitual*.
- **Polarity** is *affirmative* or *negative*, its scope the unit it is written in.
- The **world of evaluation** is where the content is evaluated: the *actual* world, *within a supposition*, *within a fiction* or *counterfactual*; a world written on a situation holds for everything within it.
- The **status of content** says whether the content is *at issue*, *presupposed*, *conventionally implied*, or *resting on an unstated assumption*, the mark of an assumption whose content is not given.
- **Information structure** marks a *topic*, a *focus* or a *contrastive focus*.
- A **question** is *polar* (whether P), *constituent* (who or what) or *alternative* (P or Q).
- The **connectives** join contents, each a content filler: *conjunction*, *inclusive disjunction*, *exclusive disjunction* and *equivalence*; the *condition* is a role whose filler is the condition.
- The **structural relations** *identity* and *member of* stand as predicates.

## Reference

A term refers. A participant is named by its number, with *party*, and the number is the participant's identity in the exchange; an agent is identified by that identity, not by its model, its principal or its role, and an expression that refers to an agent is not the agent. The **person** classes a referent as the speaker (*self*), the hearer (*interlocutor*), a *third agent*, an *inclusive collective* of speaker and hearer, an *exclusive collective* of the speaker and others, a *system*, a *tool*, the *environment* or an *external source*. A collective that acts, or that holds a normative state, must state its **reading**: *joint*, under one shared obligation, or *distributive*, each member for itself.

- The **existence commitment** says what the speaker claims of the referent's existence: *asserted to exist*, *mentioned without existence asserted*, *within a supposition*, *within a declared fiction*, *predicted to exist* or *asserted not to exist*. Uncertainty about existence is not a value of this class; it is the standing of a claim that the referent exists.
- **Access** says whether the referent is *present* to the speaker's observation, *absent*, *internal* to an agent, as a plan or a memory is, or *external*, identified by an identifier whose verification is stated.
- **Verification** of an external referent is *unverified*, the default, *verified by the speaker*, or *verified by a named third party*, which must name its source. Verification and a source stand only on an external referent.
- The **discourse status** is *new*, *given*, *inferable* from something introduced, or *in the speaker's view of the common ground*. A referent reached through a reference was introduced where it was first written and is never new.
- **Specificity** distinguishes a *specific* referent from a *non-specific* one, as a particular verifier differs from whichever verifier is found.
- The **quantifiers** are *universal*, *existential*, *definite*, *indefinite*, *generic*, *distributive* and *collective*.

## Time

A time is written on the unit it describes, with its index ([The grammar](grammar.md#units)): the **event time**, when the situation holds; the **reference time**, the time the content is about; the **execution time** of an action; the **observation time**, when the evidence for an assertion was acquired; the **inference time**, when a derived record was derived; the **validity interval**, during which the speaker vouches for what it asserts; the **communication time**, the envelope's time; and the move's **deadline**, the latest acceptable time.

A time on the clock is a number of seconds since 1970-01-01T00:00:00Z on the UTC time scale, every day counted as 86,400 seconds. An offset is counted from the communication time in units of fixed length: a second, a minute of 60 seconds, an hour of 3,600, a day of 86,400, a week of 604,800, a month of 2,629,746 and a year of 31,556,952. The thirteen relations are those of Allen's interval algebra: *before*, *after*, *meets*, *met by*, *overlaps*, *overlapped by*, *starts*, *started by*, *during*, *contains*, *finishes*, *finished by* and *equals*; a relation is always one of them, never a disjunction. A bare index as the target of a relation names that index of the nearest unit that bears it.

The times of a move form a network of constraints on the start and end of each time, which must be consistent; a move whose times cannot all hold is refused, `d.checker.times-inconsistent`. A duration fixes the length of an interval, exactly, from below after *at least* or from above after *at most*. Where a situation states both an event time and a reference time, its aspect relates them: a stative, progressive or continuative situation holds throughout the reference time, a perfective one lies within it, a completive or interrupted one ends within it, and an inceptive one begins within it. Tense is not marked; a reader may derive it from the network, as past, present, future or undetermined, and such a derivation adds nothing to the move's meaning.

## Numbers and quantities

A number may be a decimal, negative, a ratio, a power of ten written with the exponent, or an interval between two numbers. A **comparator** says how the number bounds the quantity: *exactly*, *at least*, *at most*, *approximately*, *as a representative quantity*, or unstated. A quantity of a referent is written in its term with its unit, a unit of measure or a time unit, and *per* a time unit makes it a rate. The comparator, the numerals and the unit each carry a critical dimension, since changing any of them changes what the number claims.

## Ambiguity

A set of readings states that a constituent has more than one reading, and of what kind its ambiguity is: *accidental*, a failure of encoding, which the generator never produces; *productive*, left for a context in the speaker's view of the common ground to resolve, the hearer's resolution being an inference; *strategic*, used to avoid a commitment, which is permitted and attributable; *creative*, serving humour, metaphor or poetry; or *epistemic*, the speaker's inability to decide between the readings. A set holds at most two readings, and each is normalised in the same world. A precision-bound move holds no set of readings ([The grammar](grammar.md#precision-bound-moves)).

## Figures

A figure is marked on the constituent it applies to: *metaphor*, *metonymy*, *irony* or *hyperbole*; a constituent without a mark is literal. A metaphor, an irony or a hyperbole may state its **target content**, what it means, as a situation or a constituent of the figure's own kind; a metonymy may state what it **stands for**, as a term, and stands only on a term. A figure states one relation, and in a precision-bound move it must state the one its type requires. The **source** of a figure, the constituent as written, is mentioned and not asserted, which is why a metaphor is not a false literal statement; its target content is asserted under the assertion's standing. A figure that states no target content leaves one that the speaker meant and did not state, which a hearer may infer and must record as an inference.

What a speaker answers for, in a move with figures, is the move with each marked figure replaced by its target content or the referent it stands for, and with each word read in its conventional sense where its frame selects one ([The lexicon](lexicon.md#figurative-senses-and-conceptual-mappings)). A figure meant both ways is a set of readings of the creative kind, and the speaker answers for both.

## The normal form

The normal form states the core of a move in full. A reader computes it from the move as written, the grammar, the lexicon release the message names and the declared defaults, and from nothing any participant holds. Two moves with one normal form mean the same thing, and a move written with an act word, an idiom, a register synonym, an irregular word or a compressed dialect form has the normal form of the same move written out.

To compute the normal form, a reader:

1. reads each act word as its expansion, each marked idiom as its entry's expansion with its slots filled, each extragrammatical idiom as its expansion, each register synonym as the root it stands for, each irregular word as its regular formation, and each compressed form of a named dialect as the term it compresses;
2. sets aside the act word, the declared losses, the politeness word, the diction and the register, keeping the authority, the deadline, the references, the discourse relations and the declaration *precision-bound*;
3. states every default, as the table below gives;
4. orders the parts of every unit canonically, and numbers the units reached twice in the order the normal form reaches them.

A word read in a conventional sense is written as the root it shares its form with; the frame that selects the sense is in the normal form, so the sense is too.

| Where | The default stated | When |
|---|---|---|
| assertion | the unstated basis | no basis is written |
| assertion | the unstated strength | no strength and no numeric strength is written |
| assertion | *same source* | the move is a confirmation |
| situation | the world of the enclosing content | no world is written; a move's content begins in the actual world, or within the supposition where the move adds one |
| situation | *affirmative* | no polarity is written |
| situation | *at issue* | no status of content is written |
| situation | the aspect of its predicate's sort | no aspect is written, no connective joins it and it states no condition: *perfective* for an event, *stative* for a state, *progressive* for a process, and *stative* for an attitude or a report of a normative state whose predicate gives none |
| attitude | the unstated basis and strength | the holder's grounds are not written |
| aim, or report of a normative state | the unstated origin | no origin is written |
| action | the unstated execution phase | the situation is an action the move asks for or binds, and not an attitude or a report; each content a connective joins in such an action takes it too |
| term that refers | the existence commitment of its world | none is written: *asserted to exist* in the actual world, *within a supposition*, *within a declared fiction*, or *mentioned without existence asserted* in a counterfactual or within the source of a figure |
| term that refers | the discourse status | none is written: *given* if the term names a participant, a dialect or the speaker, the hearer or both, or holds a reference, and *new* otherwise |
| external referent | *unverified* | no verification is written |
| quantity | the unstated comparator | no comparator is written |

The parts of a unit stand in this order: content words; then values, in the order of the classes in [`language/grammar.json`](../language/grammar.json) and of the members within each class; times, in the order of the indices; quantities; a participant, then a dialect; references; role fillers, in the order of the role classes and of the roles within each; and nested constituents, assertions before situations, terms, sets of readings, walls and units used again. Parts of one rank are ordered by their words, a unit used again standing for the SHA-256 digest of its own words, so that the order never depends on how the writer numbered its names. A move's references are ordered by their targets. The normal form's units are then numbered in the order its traversal reaches them.

The **normal text** of a message writes the normal form of each move as words, with its count and its move check word recomputed, one move to a line and each line ended by a line feed, with no envelope. The semantic check value is computed over it ([Messages, protocol and transport](protocol.md#the-check-values)): two messages with one semantic check value have, but for a collision of probability 10⁻⁹, one normal form for each move, whatever their registers, dictions, act words, idioms and orders of writing.

## The English explanation

A reader may explain a move in English, generated from its normal form: the sender and a verb for its force, the entries it names, its content as each unit's predicate and participants, its values, its standing and its times, and its class in brackets where it is operative, pending or de-escalating. The explanation says every value the normal form holds except a default the reader would supply where the value stands, so that nothing a speaker or an entry's expansion states is dropped. The conformance corpus gives, for `e4-act-words.1`, *Agent 1 requests that agent 2 examine the fault (authority: speaker's own) [pending].*

The explanation is a literal rendering in English word order, without inflection, made by the receiver that generates it and marked as such. It is a view, not the language: it is not a translation, it cannot be parsed back, it carries none of the message's checks, and the social and textual component, set aside by the normal form, is absent from it. A move in the raw register written with an act word and the same move in the standard register written out have the same explanation.

## The semantic ontology

The meanings the language can express are organised in [`language/semantics.json`](../language/semantics.json) as 101 elements in seven families: the sorts of thing a node can be, the relations between nodes, the operators, the kinds of value, the paradigms, the components, and the kinds derived from the rest. Each element is placed in the grammar, in the lexicon, or among the derived kinds, which are composed from other elements and need no form of their own. Every grammatical class serves one element, and every lexicon entry states the sort of what it names.

<!-- generated: ontology -->
| Family | Placed in | Elements | Names |
|---|---|---|---|
| sort | grammatical | 27 | referent, agent, collective, tool, environment, external source, kind, reified referent, situation, state, event, process, attitude, normative state, proposition, question, action for an agent, state of affairs, grounds, move, record entry, message, expression, declared data, lexicon entry, set of readings, figure |
| sort | lexical | 4 | object, place, capability, private record state |
| component | grammatical | 1 | social and textual component |
| component | lexical | 1 | humour and aesthetic effect |
| value | grammatical | 5 | number, time, scale, identifier, version |
| paradigm | grammatical | 5 | referent status, aspect, execution phase, information structure, content status |
| relation | grammatical | 21 | actor, undergoer, recipient, instrument, holder, content of, on behalf of, in role, under authority of, origin of aim, counterparty, condition, time relation, member of, identity, premise of, source of, names, mentions, maps to, stands for |
| relation | lexical | 8 | place of, beneficiary, cause, part of, supports, undermines, bears on, correspondence |
| operator | grammatical | 5 | polarity, world of evaluation, quantifier, conjunction and disjunction, irony |
| derived | derived | 24 | tense, frequency, prediction, plan, uncertainty, inability, conflict, disagreement, change of attitude, result, counterfactual relation, causal uncertainty, joint action, distributive action, tool-mediated action, automated action, unintended effect, quality, having evidence, generalisation, analogy, narrative, negotiation, synchronisation |
<!-- end generated -->

A derived kind is expressed by composing the elements it is made of: tense is the relation of an event time to the communication time, a prediction a proposition whose event time follows its assertion, a plan an intention whose content is a structure of actions ordered by time and condition, and an inability a capability denied with its cause, which a refusal, a move that lowers a request, is not.
