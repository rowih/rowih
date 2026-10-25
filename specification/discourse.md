# The record and discourse

Every move adds an entry to a record, and may change the status of entries it names. The entries record what each participant has asserted, asked, proposed, promised, granted, delegated, defined and withdrawn, so that each participant can audit what was committed, by whom, on what authority and with what result. There is no shared record held anywhere: each participant keeps its own view of the record from the messages it has received, and the rules of this chapter make every view built from the same messages hold the same entries, whatever order the messages arrived in. This chapter states the entries, how a move names and changes them, the derived structures of an exchange, and what the record guarantees.

The record is kept by a participant's view, which the canonical Python implementation provides in [`python/rowih/view.py`](../python/rowih/view.py); a view is not part of the analysis of a single message, and the diagnostics a view reports begin `d.view.`.

## Entries and their handles

An entry is identified by its **handle**: its author's participant number and its number in the author's count of its own entries, which starts at 1 and runs across all the author's channels. The envelope of every message states the number of the entry its first move adds, and the *k*-th move of the message adds entry *first entry* + *k* − 1, so every hearer gives every entry the handle its author gave it, whatever messages it has missed. A protocol message adds no entry.

An entry holds its kind, its content (the normal form of its move's constituents), its author, its time, the entries it depends on and its **status**. Nothing but its status ever changes: a correction is a new entry, not an edit. An issue begins *open*; every other entry begins *in force*. The statuses are *open*, *in force*, *resolved*, *lowered* and *withdrawn*. An entry's **kind** is what its move added, with the sub-kind of an issue, a normative entry or a setting, and without the bindingness.

| A move that adds | Adds an entry, which begins | And its author answers for |
|---|---|---|
| an asserted position | in force | the content, at the standing stated |
| a conceded position | in force | only that the position is on its record |
| a supposition | in force | nothing about truth |
| a summary | in force | fidelity to the entries it names |
| an issue | open | the authority it claims, for a request or a proposal |
| a normative entry | in force | the performance, to its counterparty |
| a setting | in force | the authority under which it is declared |
| nothing beyond its own record | in force | the scope of what it changes |

## How a participant receives a message

A participant applies the moves of a message it receives in order, each under the handle its envelope gives. It applies nothing from a message that did not parse, that carries a diagnostic other than an unknown word kept opaque, or that is a protocol message. It records the releases and dialects the message states. A message from an agent whose key the participant holds must verify by its signature, `d.view.authentication-failed` ([Messages, protocol and transport](protocol.md#authentication)). A message that arrives damaged is asked for again, `d.view.damaged`; a message applied before is not applied again, `d.view.applied-before`, nor is a message that reuses a serial, `d.view.serial-reused`, so that each operative move takes effect at most once. A message marked *forwarded* is not its sender's and is not applied, `d.view.forwarded`, unless it carries another message whole as declared data that verifies by its own sender's key, which is then received as that sender's.

A participant applies a move in these steps, the first failure ending the attempt:

1. **Hold.** A move that names an entry the participant does not hold, or holds only reduced, or a message it does not hold, is held until what it names arrives, `d.view.held`. Every entry or message a move names, in its head, its content or its authority, is a dependency; a mention is not.
2. **Expectation.** Every entry a move names must have the kind and the status the reference expects, and the part it names must exist, `d.view.expectation-not-met`, unless the failure is a crossing ([Crossing moves](#crossing-moves)).
3. **Fit and restatement**, for a move that names an entry in its head ([What a change may name](#what-a-change-may-name), [Stops](#stops)).
4. **Standing**, for a summary: its assertions state the lowest standing of what it summarises ([What a message means](meaning.md#standing-and-provenance)), `d.view.summary-standing`.
5. **Deadline**, for an acceptance ([Deadlines](#deadlines)).
6. **Handle, binding and definition**: a handle already held is refused, `d.view.handle-repeated`; a role setting binds a participant ([Roles](#roles)); a definition must not redefine a term in force ([Definitions](#definitions)).
7. **Effect.** The change takes effect on the entry named, and the new entry is stored.

A held move is applied when what it depends on arrives. What a hearer records is what the speaker said, with the status of its content; what the hearer infers from it is recorded apart, as the hearer's own inference, and never as said. Hearing is not believing: an assertion is recorded as the speaker's, at the speaker's standing.

A participant may **forget** the content of an entry, keeping its handle, kind and status, and hold it reduced; it restores the content from the message that added it, sent again byte for byte. A move that names a reduced entry is held until the content returns.

## Naming entries and messages

A move acts on what it **names**: an entry, by its author, its number, and the kind and status the speaker expects it to have; or a message, by its sender and the first entry its envelope states, or by its sender, its serial and the recipients of its channel ([The grammar](grammar.md#references-and-targets)). A **mention** cites an entry without depending on it, and a move must not act on what it only mentions, `d.checker.expectation`. A move may name an entry only once the entry has been sent to the hearer; nothing names "the latest entry". A reference may narrow to a part of an entry, the unit with the name stated, as the entry's own content numbered it.

## Changes and their effects

A move that names an entry in its head changes it, the change *none* included, and a move that changes an entry must name it ([The grammar](grammar.md#the-rules-beyond-the-productions)).

| Change | Effect on the entry named, when it takes effect |
|---|---|
| none | no change of status |
| acknowledgement | no change of status; it records receipt and accepts nothing |
| resolution | *resolved*, except that the acceptance of a commitment or an assignment leaves it *in force*, binding from then on |
| lowering of the whole entry | *withdrawn* |
| lowering of part of it | *lowered* |

A change takes effect **on the move**, when the move is applied, or **on acceptance**, when the move's own entry is accepted. A counterproposal to an entry in force, which rejects it on acceptance, therefore declines that entry only when the counterproposal is accepted. Every change is recorded on the entry with the status it had before, so that the history of the entry can be audited.

A change to part of an entry states the extent *part of it* and names the part with *part*; release 1.0 does not check that the two go together.

## What a change may name

A resolution must fit the entry it names, `d.checker.fit`:

| Outcome | May name |
|---|---|
| answer | a question; a challenge |
| acceptance | a request; a proposal; a commitment; an assignment |
| rejection | a request; a proposal; a commitment; an assignment |
| settlement | an obligation; an assignment |
| failure | an obligation; an assignment; a request |

These rules also apply, each reported as `d.checker.fit`:

- an issue is resolved by the participant it is addressed to, so a participant does not answer, accept or reject its own entry;
- a participant lowers only its own asserted position, conceded position, supposition, summary, proposal, commitment, assignment or permission; a request may be lowered by its author, as a cancellation, or by a recipient, as a refusal, and by no one else;
- an acknowledgement and a challenge name another participant's move;
- a proposal that names an entry is a counterproposal, and rejects what it answers;
- the settlement or failure of another participant's assignment is made on behalf of the assignment's author, `d.checker.authority-attenuates`.

## Stops

A **stop** is a de-escalating move ([The grammar](grammar.md#the-class-of-a-move)): one that lowers an entry of a binding kind, or rejects or settles it, with effect on the move, adding nothing that binds. A stop, and every withdrawal of an entry, must restate what it withdraws: its content must be the content of the entry named, or of the part named, once the deixis of each is resolved under its own speaker and recipients and the references within each are compared by handle. A stop with no content, or whose restatement differs from what it names, is refused, `d.checker.stop-restatement`, so that a stop that reached the wrong entry takes no effect. A correction, an asserted position that lowers the speaker's own position, adds a new position in place of the old and need not restate it.

A stop must also be delivered: its sender keeps it open until each addressee acknowledges it, and sends it again until the protocol's limit ([Messages, protocol and transport](protocol.md#channels-acknowledgement-and-repair)).

## Crossing moves

Two moves **cross** when each was made against an entry as it stood before the other changed it, so that the one that arrives second fails its expectation. A participant recognises a crossing when the failing move expected the entry's kind and the status the entry had before another move changed it. One of the two prevails, ranked by these criteria in order:

1. a stop prevails over a move that is not one;
2. the move of the entry's author prevails over another's;
3. the move with the earlier communication time prevails;
4. the move of the participant with the lower number prevails;
5. the move with the lower entry number prevails.

The rank is computed from the two moves alone, so every participant that holds both ranks them alike. If the arriving move loses, it is refused, `d.view.crossed`, and the participant records which move prevailed. If it prevails, `d.view.crossing`, the participant orders the losing move after it and applies every move again from an empty record, so that the record depends on the moves and not on the order they arrived in. A move that depended on the losing move's entry stays held in every view alike. A stop that crossed an acceptance still stops.

## Requests, offers, commitments and delegation

A **request** is pending and claims authority. Its addressee accepts it by adding an obligation, bound, that resolves the request with an acceptance on the move, or rejects it; the request is then resolved. An **offer** is a commitment binding on acceptance, and a **delegation** an assignment binding on acceptance; both are operative and in force, and their acceptance leaves them in force, binding from then on. A **command** is an obligation, a **promise** a commitment and a **grant** a permission, each bound on the move.

A commitment ends in one of three ways: it is discharged when its holder performs and reports the performance; it is released by its counterparty; or it is retracted by its holder, a stop that leaves the commitment on record as withdrawn. A report of completion or of failure is an asserted position that settles or fails the duty it names on acceptance, and is pending. An action performed at another's request is recorded under the requester's authority: a report that settles another participant's assignment claims authority on behalf of the assignment's author. A refusal lowers or rejects a request and is a move; an inability is a capability denied, asserted as content, and the two are kept apart by force.

Release 1.0 states three limits of these rules. A completion or error report stays pending: acceptance may name a request, a proposal, a commitment or an assignment, and not the asserted position a report adds, so the record has no move that accepts a report and settles the duty. A counterparty cannot release a commitment, an assignment or a permission of another's, since only an entry's author lowers it, so the release of these kinds is not written as a change to them. And the authority a move claims is checked against what it acts on only for the settlement or failure of an assignment; a delegation granting more than its grantor holds is not refused.

## Negotiation

A negotiation is derived from the record, not written: it is the sequence of proposals, counterproposals, acceptances and rejections on one issue. It opens at a request, a proposal, an offer or a delegation, and each later round is the counterproposal that rejected the round before. It ends where the last round's last change leaves it:

- **agreed**, when a round is accepted, wholly or in part, and conditionally where the accepted content states a condition;
- **rejected**, when a round is rejected;
- **abandoned**, when the round's author withdraws it, and **refused**, when another lowers it;
- **lapsed**, when it has a deadline that has passed with no change;
- **open** otherwise.

Every other figure of negotiation is composed from these moves: a conditional acceptance accepts content holding a condition; a partial acceptance accepts part of what it names; a compromise is a counterproposal between the last two offers; a reservation is a position that names the acceptance and bears the relation *contrasts*; a priority is a preference over an order; an allocation is the content of a proposal.

## Challenges and disagreement

A challenge is an issue that names another participant's position. Its author's answer is grounds, an asserted position that resolves the challenge with an answer, or the position's retraction. A challenge ends **retracted** when the position is withdrawn or lowered, stays **open** while the position's author has not answered it, and, once answered, ends **agreed** where the challenger holds a position in force accepting the challenged one, and as a **disagreement recorded** otherwise, which both participants' views hold alike.

## Summaries and confirmations

A summary names every entry it summarises, each with its expectation and the change *none*, and is the only move that names more than one entry ([The grammar](grammar.md#the-rules-beyond-the-productions)); it replaces nothing and keeps the lowest standing of what it summarises ([What a message means](meaning.md#standing-and-provenance)). A confirmation names a position with the change *none* and restates it. A confirmation raises the standing of the position it names only if it names the whole position, restates it, rests on an independent source other than its own author, and neither its lineage nor its source was counted before. A participant's lineage is stated by an asserted position that it descends from another participant; agents of one lineage, such as forks or instances of one model, raise nothing by confirming each other.

## Common ground

A proposition enters a participant's common ground when every other participant has given evidence of accepting it: by being its author; by holding a position in force that names it and restates it; or by silence, where the participant has committed to accept by silence the positions it receives within an interval, the interval has passed, and it has made no move that objects to the entry. An acknowledgement accepts nothing and objects to nothing; a move bearing the relation *elaborates* or *supports* with the change *none* does not object, and any other move naming the entry does. Without such a commitment, silence is not acceptance. A presupposed content enters only when the viewing participant has accepted it too; nothing is accommodated.

## Roles

A role setting binds a participant number to an agent: its one constituent is a term holding the participant and the agent's identifier as declared data. A participant number already bound to another agent, or an agent already bound to another number, is refused, `d.view.participant-bound`. The corpus's handshake opens with `(move SETTING ROLE SPEAKERS-OWN (term (party 1) (data "text/plain" "urn:agent:alpha")))`.

## Definitions

A definition ([The lexicon](lexicon.md#coining-a-word-by-definition)) is a setting, in force from its communication time until it is lowered, and gives the defined word its meaning in every later message of the exchange; a definition scoped to a dialect gives it only in messages that name the dialect. It never reaches a message earlier than itself. A definition of a word that a definition in force already defines is refused, `d.view.term-defined`. Once a definition is withdrawn, the word is unknown again. A defined word is unknown to the release, so a precision-bound move writes its expansion where it would use the word.

## Deadlines

A deadline is the latest acceptable time for the response or the action a move asks for. It is computed from the time of the entry that states it: *now* is the entry's time, a time on the clock is itself, and an offset is counted from the entry's time. An acceptance whose communication time is later than the deadline of the entry it accepts is refused, `d.view.deadline-passed`; a rejection, a lowering or any other move is not checked against the deadline. Both participants compute a lapse from values they share.

## Threads and other derived structures

A move that names an entry replies to it and joins its thread, and a summary joins the thread of each entry it names. From the record a participant may also derive the open issues, the action items (each normative entry in force with its responsible party and deadline), the positions and conclusions, the summaries, the topics of each thread, and the terms defined. These are views of the record; they add nothing to it.

## What the record guarantees

The rules above give a participant these guarantees, each tested in [Conformance](conformance.md):

- an entry is immutable but for its status, and a handle names the same content in every view;
- a move that depends on an entry or a message is held until it arrives, and refused if what arrives is not what it expected;
- every commitment, request and withdrawal stands in the record with its author, its authority, its deadline and its status, and every participant that holds the same messages derives the same negotiations, conflicts and action items;
- a withdrawal restates what it withdraws, and does not take effect on anything else;
- crossing moves are ordered alike by every participant, and a stop prevails;
- each operative move takes effect at most once;
- nothing enters the common ground without acceptance, and nothing a hearer infers is recorded as said.
