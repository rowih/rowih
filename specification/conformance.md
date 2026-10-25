# Conformance

The guarantees of the language hold only for a hearer that analyses each message with a conformant implementation. A hearer that reads the surface text without one receives none of them: it cannot tell a damaged message from an intact one, a quoted instruction from an operative one, or a move that fits the record from one that does not. A conformant implementation is therefore part of using the language, as a parser is part of using a data format. This chapter states what a conformant implementation must do, the guarantees it then gives, the invariants that state them as tests, the suite that tests them, the diagnostics, the interfaces of the two implementations, the measurements of the language's cost in tokens, and the language's known limitations.

## What a conformant implementation must do

A conformant **reader** must:

1. read a message in the transliteration or the native digital form, refusing any character outside the encoding's alphabet, outside a payload ([Messages, protocol and transport](protocol.md#the-forms-of-a-message-in-transport));
2. analyse it by the productions and the rules of [The grammar](grammar.md), reporting every refusal as a diagnostic with its code, and never raising an exception for any input;
3. verify every number's check word, every move's count and move check word, the unit check word of the envelope and of a protocol statement, and the check values the message carries, and require the integrity check value where [The check values](protocol.md#the-check-values) requires it;
4. read the message under the releases, dialects and features it names, and report what it lacks rather than read it under anything else;
5. keep an unknown word opaque, never dropping it or guessing its meaning, and refuse it in a precision-bound move;
6. read nothing within a wall as the language, so that embedded material is inert;
7. compute each move's class from what it adds and changes, and its normal form exactly as [What a message means](meaning.md#the-normal-form) states, so that its semantic check value is the writer's.

A conformant **writer** must write the canonical serialisation with every count, check word and check value computed; carry the integrity check value on every message that requires it; never write an accidental ambiguity, an unknown word or a vague quantity in a precision-bound move; write a normal form equal to the meaning it was given, in every mode and register; and apply a device of economy, an act word, an idiom, a compressed form or shared context, only for a hearer known to hold what the device needs, writing full explicitness to any other.

A conformant **participant** keeps its view of the record by the rules of [The record and discourse](discourse.md), and acknowledges, repairs and settles releases by the rules of [Messages, protocol and transport](protocol.md#channels-acknowledgement-and-repair).

The canonical implementation is the Python package in [`python/rowih/`](../python/rowih/). The TypeScript implementation in [`typescript/src/`](../typescript/src/) is a reader and renderer, and must agree with the canonical implementation byte for byte over the conformance suite; it does not generate, keep a view or synthesise speech.

## The guarantees

**Every move states its force, the standing of what it asserts and the authority it claims.** A move is operative only through a form the grammar or the lexicon gives operative force, used in the speaker's own voice: what a move's content says never makes it operative. Its class is computed from what it adds and changes, never read from the name of an act. Every strength is an interval with its calibration, an omitted standing claims nothing, and no transformation the toolchain performs, whether compression, conversion between registers, summary, relay or repair, changes a standing unless the change is marked. Every operative and pending move claims its authority, and a precision-bound move has exactly one reading and carries the integrity check value.

**Quoted and external material is inert by kind.** Material inside a quotation, a report, a supposition, an example or a payload is inert whatever its wording, and adds nothing to the record. A reader reads embedded material by a stated length, so nothing inside it can end it, and never parses declared data as the language. An operative or pending move whose content derives from external material carries that origin.

**Commitments, requests and their withdrawal are entries both parties can audit.** A move names what it depends on by author and number with the kind and status it expects, and is held or refused where the record differs. Entries change only in status; a withdrawal restates what it withdraws and takes no effect on anything else; each operative move takes effect at most once; crossing moves are ordered alike by every participant, and a stop prevails.

**No single edit of a symbol or a word changes a critical dimension undetected.** Under any single substitution, insertion, deletion or duplication of one symbol, and any insertion, deletion, duplication or substitution of one word, a well-formed message becomes ill-formed or fails its integrity check value. The guarantee is measured over the conformance suite, and holds where the message carries its integrity check value ([The enumerations](#the-enumerations)).

**Agents negotiate the releases they share and repair what is lost or damaged.** A message states its releases outside its moves; a hearer lacking one reports what it lacks and what it reads; two agents compute the releases they share; a hearer knows from the serials which messages it lacks and asks for them; and a sender keeps each message open until it is acknowledged.

The language marks an instruction, a quoted instruction and untrusted content apart, and cannot make a hearer respect the difference: an agent that does not analyse what it receives can still obey an imperative inside a quotation. That is the one demand of the adversarial suite that no mechanism of the language meets.

## The invariants

The guarantees are stated as 64 invariants, each a rule no message or implementation may break, each tested by the suite and protected by a planted defect the tests must catch.

| Invariant | Rule |
|---|---|
| `inv.encodings-agree` | The native digital form, the transliteration and the canonical serialisation convert into one another without loss, and parsing any of them gives the same analysis. |
| `inv.speech-decodable` | The spoken form is one phoneme for each symbol, and the symbols are recovered from the phonemes alone. |
| `inv.normal-form-unique` | Every well-formed realisation has exactly one normal form, which is its own normal form, and two realisations have one core exactly when they have one normal form. |
| `inv.view-independent-normalisation` | Normalisation reads the message, the grammar, the releases it names and the declared defaults, and nothing any participant holds. |
| `inv.realisations-normalise` | Every realisation of a meaning, in every mode and register and with every conventional, idiomatic and dialect form, has that meaning's normal form. |
| `inv.loss-declared` | Every transformation of a message is lossless, a declared loss, or a lossy act marked as such, and none loses a critical dimension or provenance silently. |
| `inv.generation-faithful` | The generator never writes a message whose normal form differs from the meaning it was given. |
| `inv.deterministic` | The reader gives the same analysis and the generator the same output for the same input on every run and platform, and the two implementations agree. |
| `inv.well-typed` | The normal form of a well-formed move is a rooted acyclic graph of units in which every node is of a sort and every relation joins sorts it admits. |
| `inv.meaning-fixed` | No later definition, release or entry changes the analysis of a message already sent. |
| `inv.compatible-within-major` | Within a major version every expression valid under an earlier release stays valid with the same normal form, and a deprecated form stays readable. |
| `inv.word-formation` | A formation the lexicon does not list means what the rules of word formation compute from its parts, and nothing else. |
| `inv.numerals-exact` | Every number denotes one value, with the precision its digits state and its unit, and carries its check word. |
| `inv.displays-are-views` | A display, the English explanation and an export are views made by one receiver, never sent, parsed back or treated as an encoding. |
| `inv.core-closed` | No definition and no dialect changes a closed class, the system of force or the meaning of a core form. |
| `inv.force-marked` | A move is operative only through a form the grammar or the lexicon gives operative force, used in the speaker's own voice. |
| `inv.quoted-inert` | Material inside a quotation, a report, a supposition, an example or a payload is inert whatever its wording. |
| `inv.external-origin-kept` | An operative or pending move whose content derives from external material carries that origin, and no transformation removes it. |
| `inv.boundary-closed` | Nothing inside embedded material can alter the boundary that encloses it, and declared data is never parsed as the language. |
| `inv.class-computed` | A move's class is computed from what it adds and changes, never read from the name of an act. |
| `inv.fit` | An act that does not fit what it names is not applied. |
| `inv.stop-restates` | Every stop restates what it withdraws, and is applied only where the restatement means what the entry means. |
| `inv.stop-delivery-known` | A stop that reaches a hearer is never dropped silently: it is acknowledged, or sent again and recorded as unacknowledged. |
| `inv.at-most-once` | A hearer applies an operative move at most once and accepts a given move at most once, however often it arrives. |
| `inv.authority-attenuates` | Every operative and pending move claims its authority, and an action done at another's request is recorded under the requester's authority. |
| `inv.own-action` | An intention whose content is not an action of its holder is ill-formed. |
| `inv.aims-apart` | Aims, normative states and execution are never merged, and an inability is never written as a refusal or a refusal as an inability. |
| `inv.standing-unchanged` | No transformation changes a standing unless the change is marked, and omission never strengthens a claim. |
| `inv.provenance-monotone` | No transformation deletes or strengthens provenance; a relay adds its relayer. |
| `inv.summary-keeps-lowest` | A summary keeps the weakest basis and the lowest strength of what it summarises. |
| `inv.strength-is-interval` | Every strength normalises to one interval on the scale from 0 to 1 with its calibration. |
| `inv.ordered-times` | A standing whose observation time follows its inference time, or whose inference time follows its communication time, is refused. |
| `inv.hearing-not-believing` | Applying an assertion records that its speaker asserted it, never its content as the hearer's own. |
| `inv.independent-confirmation` | A confirmation raises a standing only where it rests on an independent source, and a confirmation by an agent of the same lineage is not independent. |
| `inv.precision-bound-one-reading` | A precision-bound move has exactly one reading, a fully explicit core and no vague value without fixed bounds. |
| `inv.readings-kept` | Readings are never collapsed to one without a record. |
| `inv.figure-not-literal` | An unmarked constituent is literal, and a marked figure's source is mentioned and not asserted. |
| `inv.identity-not-reference` | An agent is identified by its participant identity, and rewriting a reference to it never changes which participant is named. |
| `inv.dependencies-explicit` | A move names each entry it depends on with the kind and status it expects, and is held or refused where the record differs. |
| `inv.entries-immutable` | Only an entry's status ever changes. |
| `inv.common-ground-by-acceptance` | A proposition enters the common ground only on every other participant's acceptance, never by acknowledgement, by silence without a convention, or by accommodation. |
| `inv.inference-not-said` | What a hearer infers is never recorded as what the speaker said. |
| `inv.critical-values-explicit` | No critical value of a move is recovered from context. |
| `inv.devices-admissible` | A writer applies a device of economy only for a hearer that holds what the device needs. |
| `inv.precedence-agreed` | Every participant orders crossing moves by the same rule, computed from the moves alone. |
| `inv.no-silent-reinterpretation` | Malformed input never yields a well-formed analysis with a different meaning in any critical dimension. |
| `inv.single-edit-detected` | No single edit of a symbol or a word changes a critical dimension undetected. |
| `inv.truncation-detected` | Every proper prefix of a well-formed message, in each encoding, is ill-formed or fails its integrity check value. |
| `inv.one-critical-dimension` | No closed-class form carries values of two critical dimensions; an act word, which carries several, is a protected word. |
| `inv.lexicon-code` | Every word is two edits from every other and every critical word three, and the lexicon is uniquely decodable. |
| `inv.checks-match` | A message is well formed only if every check it carries matches what it covers, and a mismatch is never repaired silently. |
| `inv.integrity-value-required` | Every message carrying a precision-bound move carries the integrity check value. |
| `inv.check-values-distinct` | The integrity check value covers the message's bytes and the semantic check value its normal form, each separately. |
| `inv.authentication-covers-message` | A signature covers the whole message, its sender and time included, and a relayed message travels byte for byte. |
| `inv.check-forms-disjoint` | No check word can be read as another word, and no word as a check. |
| `inv.unknown-preserved` | An unknown word is kept opaque and reported, never dropped or guessed, and a move using a must-understand feature the reader lacks is refused whole. |
| `inv.message-fields` | Every message states its sender, recipients, time, releases and identifier outside its moves. |
| `inv.maxima-enforced` | Input beyond a maximum is refused, and deep nesting before the message is read to its end. |
| `inv.critical-forms-distinct` | Forms that differ in a critical dimension are visually and orthographically distinct, and protected words are marked in the writing system. |
| `inv.closed-alphabet` | A reader accepts only its alphabet, and refuses control characters outside payloads. |
| `inv.transport-stable` | A routine transformation in transport leaves a message's analysis unchanged or is detected. |
| `inv.tokenizer-round-trip` | Every tokenizer on the panel returns the transliteration unchanged. |
| `inv.gaps-known` | A hearer knows from the serials which messages it lacks, and recognises a duplicate or a replay. |
| `inv.diagnostics-not-exceptions` | No input raises an exception of the implementation language; every refusal is a diagnostic. |

Release 1.0 tests all 64. Two rules of the record are narrower in release 1.0 than a reader might expect: no move can accept a completion report, and the authority a grant passes on is checked only for the settlement or failure of an assignment ([The record and discourse](discourse.md#requests-offers-commitments-and-delegation)).

## How conformance is tested

### The conformance suite

<!-- generated: suite -->
| Set | Items | Message files |
|---|---|---|
| `corpus/conformance/` | 124 | 345 |
| `corpus/attitudes/` | 13 | 14 |
| `corpus/adversarial/` | 14 | 23 |
| `corpus/negative/` | 130 | 130 |
| `corpus/domains/` | 1,200 | 2,237 |
| `corpus/source/ambiguity.json` | 9 |  |
<!-- end generated -->

- **Conformance** items are exchanges written in the notation, each message stating its moves' classes and each participant's view stating its diagnostics. Each message must parse with exactly its stated diagnostics and classes; its native digital form must give the same analysis; its canonical serialisation must equal the file; generating from its notation must give its normal form; and each participant must apply the exchange with its stated view diagnostics.
- **Attitude** items report attitudes with their holders' grounds, predictions, aims, preferences, permissions and collective commitments; each must parse to its stated normal form and generate back to it.
- **Adversarial** items make 60 demands of the language: 43 met by the core's mechanisms, 7 met by later mechanisms, 9 met with a residue the item shows, and 1 not met, the hearer that does not analyse.
- **Negative** items are ill-formed, each with the diagnostic it must draw in both implementations, without an exception.
- **Domain** items, 1,200 exchanges in twelve domains, must read without a diagnostic and be heard by every participant without one.
- **Ambiguity** items each state their reading set and its kind, and a disambiguation that must parse to one reading.
- The **glossed** records in [`corpus/glossed/`](../corpus/glossed/) must equal what the toolchain writes for every message, and the **release record** in [`corpus/releases/`](../corpus/releases/) how release 1.0 reads its 382 messages.

### The enumerations

Three enumerations run over the 382 messages of the conformance, attitude and adversarial sets. The **single-edit enumeration** applies every deletion, insertion and substitution of one symbol, and every deletion, duplication, substitution and insertion of one word, with the integrity check value verified and with it ignored, in the transliteration and the canonical serialisation. An edit is **silent** if the edited text draws no diagnostic and some critical value of some move differs. Over the 375 messages that draw no diagnostic of their own, the seven others defining or naming words by design:

| Edits | With the integrity check value verified | With it ignored |
|---|---|---|
| 7,089,953 symbol edits in each encoding | none silent | none silent |
| 84,233,102 word edits in each encoding | none silent | 1,638 silent in each encoding |

The silent word edits are all substitutions of one term, *examiner*, where it names the role in which a move claims authority, at three places in two messages: the role's term is ordinary content, which only the integrity check value covers. No edit raised an exception. The **truncation enumeration** requires every proper prefix of every message to draw a diagnostic, and the **transport enumeration** requires each of fifteen routine transformations, Unicode normalisations, line-ending conversions, wrapping, tab expansion, Markdown rendering, typographic quotation marks, HTML escaping and indentation among them, to leave the analysis unchanged or draw a diagnostic. Fuzzed input, with control, bidirectional and zero-width characters, must raise nothing.

### The two implementations

The two implementations write one record of each analysis, holding its words, canonical text, move trees, classes, normal form, social component, diagnostics, check values, native digital form, export and renderings, and the records must agree byte for byte. Over 139,033 texts made from the 512 messages of the conformance, attitude, adversarial and negative sets, their native digital forms, sampled single edits and foreign characters written into them, the two implementations disagree on none.

### The planted defects

Every invariant, and each of 52 ways an implementation can fail, has a planted defect: a change to the canonical implementation that breaks it, run against the tests that must catch it. A defect is caught when those tests fail. At release 1.0 all 94 planted defects are caught.

<!-- generated: mutants -->
| Plants a breach of | Defect | What the defect does | Caught |
|---|---|---|---|
| `agency/origin-of-an-aim-read-in` | origin-of-an-aim-read-in | A normaliser that reads an unstated origin as the holder's own. | yes |
| `ambiguity/interval-written-as-a-point` | interval-written-as-a-point | A normaliser that writes an interval of strength as its midpoint. | yes |
| `discourse/no-words-for-the-failure` | no-words-for-the-failure | A reader whose diagnostics have no rendering in the language. | yes |
| `discourse/summary-raises-standing` | summary-raises-standing | A record keeper that applies a summary whatever standing it states. | yes |
| `epistemic/credence-off-the-scale` | credence-off-the-scale | A checker that leaves another holder's credence unchecked against the scale. | yes |
| `epistemic/provenance-dropped` | provenance-dropped | A relay that carries the relayed assertion without the links it was given, a shorter chain than the one it relays. | yes |
| `epistemic/summary-basis-from-the-act` | summary-basis-from-the-act | A summary whose basis is the inference of summarising, not what it summarises. | yes |
| `grammatical/default-undeclared-or-strengthening` | default-strengthening | A default that strengthens: a confirmation taken as independent unless stated. | yes |
| `grammatical/omission-read-as-a-claim` | omission-read-as-a-claim | A normaliser that reads an omitted strength as certain. | yes |
| `inv.aims-apart` | aims-apart | A normaliser that writes a refusal as an assertion of inability. | yes |
| `inv.at-most-once` | at-most-once | A hearer that removes duplicates by the bytes of the message. | yes |
| `inv.authentication-covers-message` | authentication-covers-message | A signer that covers the moves and leaves the envelope out. | yes |
| `inv.authority-attenuates` | authority-attenuates | A checker that accepts an operative or pending move without its authority. | yes |
| `inv.boundary-closed` | boundary-closed | A parser that ends a quotation at any closing structural word inside it. | yes |
| `inv.check-forms-disjoint` | check-forms-disjoint | A move check form that is also a word of the lexicon. | yes |
| `inv.check-values-distinct` | check-values-distinct | A semantic value computed over the message's own serialisation. | yes |
| `inv.checks-match` | checks-match | A parser that reads on past a word count that does not match. | yes |
| `inv.class-computed` | class-computed | A checker that finds the de-escalating moves by the change word alone. | yes |
| `inv.closed-alphabet` | closed-alphabet | A reader that applies compatibility normalisation before it checks the alphabet. | yes |
| `inv.common-ground-by-acceptance` | common-ground-accommodation | A record keeper that accommodates a presupposition the viewing participant has not accepted. | yes |
| `inv.common-ground-by-acceptance` | common-ground-by-acceptance | A record keeper that adds a message's content to the common ground when the message is acknowledged. | yes |
| `inv.compatible-within-major` | compatible-within-major | A minor release that changes the declared default of a class. | yes |
| `inv.core-closed` | core-closed | A definition check that compares a new term only with the members of its own class, not with every word in scope. | yes |
| `inv.critical-forms-distinct` | critical-forms-distinct | A component inventory that holds a component and its own reflection. | yes |
| `inv.critical-values-explicit` | critical-values-explicit | A terse realisation that omits a deadline. | yes |
| `inv.dependencies-explicit` | dependencies-explicit | A hearer that applies a cancellation to a request it holds as accepted. | yes |
| `inv.deterministic` | deterministic | Readings written in the order of an unordered collection. | yes |
| `inv.devices-admissible` | devices-admissible | A generator that writes a dialect form to a hearer whose messages never stated the dialect. | yes |
| `inv.diagnostics-not-exceptions` | diagnostics-not-exceptions | A parser that raises KeyError on a SAME that names no unit. | yes |
| `inv.displays-are-views` | displays-are-views | A reader that takes any text, dropping what is not the language, as a message. | yes |
| `inv.encodings-agree` | encodings-agree | A native digital form that spells two symbols with one code point. | yes |
| `inv.encodings-agree` | written-form-distinct | A writing-system specification that marks a term as it marks a situation, so that the drawing no longer shows which unit a word opens. | yes |
| `inv.entries-immutable` | entries-immutable | An act that rewrites an entry's content in place. | yes |
| `inv.external-origin-kept` | external-origin-kept | A generator that lifts an imperative out of a payload into a request and drops its origin. | yes |
| `inv.figure-not-literal` | conventional-sense-ignored | A reader that reads every word in its basic sense, so that a speaker's commitment attaches to the basic sense where its frame selects the conventional one. | yes |
| `inv.figure-not-literal` | figure-not-literal | A normaliser that asserts the source content of a marked metaphor. | yes |
| `inv.figure-not-literal` | metonym-asked-for-a-target-content | A checker that asks every figure for a target content, so that a metonym stating what it stands for is refused in a precision-bound move, as release 0.6 did. | yes |
| `inv.figure-not-literal` | metonym-referent-mentioned | A normaliser that writes the referent a metonym stands for as mentioned, as release 0.6 did, although the metonym's predication is about it. | yes |
| `inv.figure-not-literal` | relation-without-a-figure | A checker that accepts a figure's relation on a constituent no figurative mark stands on, so that a literal constituent claims a figure's content. | yes |
| `inv.figure-not-literal` | source-answered-for | A reader that answers for a figure's source, its mark removed, in place of its target content. | yes |
| `inv.fit` | fit | A hearer that applies a lowering of a request sent to another. | yes |
| `inv.force-marked` | force-marked | A checker that treats an assertion as a directive because its content names an obligation. | yes |
| `inv.gaps-known` | gaps-known | A hearer that takes every serial below the highest it has received as held. | yes |
| `inv.generation-faithful` | generation-faithful | A generator that omits every value equal to its class's default, although the enclosing unit states another. | yes |
| `inv.hearing-not-believing` | hearing-not-believing | A record keeper that files what it hears among its own entries. | yes |
| `inv.identity-not-reference` | identity-not-reference | A resolver that binds the interlocutor to the agent most recently mentioned. | yes |
| `inv.independent-confirmation` | independent-confirmation | A record keeper that raises standing on any confirmation from a different participant identifier. | yes |
| `inv.inference-not-said` | inference-not-said | An interpreter that records a scalar implicature as the speaker's assertion. | yes |
| `inv.integrity-value-required` | integrity-value-required | A checker that requires the value only on operative moves, missing pending ones. | yes |
| `inv.lexicon-code` | lexicon-code | A release check that does not test the distance between words. | yes |
| `inv.loss-declared` | conversion-touches-the-core | A conversion that writes an idiom its target register does not admit by the idiom's literal reading, not by its expansion. | yes |
| `inv.loss-declared` | loss-declared | A register conversion that drops a node of the provenance graph and declares only a change of diction. | yes |
| `inv.maxima-enforced` | maxima-enforced | A parser that never tests the nesting maximum. | yes |
| `inv.meaning-fixed` | meaning-fixed | A lexer that reads the longest match against the current lexicon, so that a new entry swallows two existing words. | yes |
| `inv.message-fields` | message-fields | A parser that takes a message's version from elsewhere when it states none. | yes |
| `inv.no-silent-reinterpretation` | no-silent-reinterpretation | A parser that closes an unclosed unit at the end of the move. | yes |
| `inv.normal-form-unique` | normal-form-unique | A normaliser that keeps siblings in the order the speaker wrote them. | yes |
| `inv.numerals-exact` | numerals-exact | A normaliser that drops trailing zeros after the decimal point. | yes |
| `inv.one-critical-dimension` | one-critical-dimension | One form for a negated command, carrying polarity and force at once. | yes |
| `inv.ordered-times` | ordered-times | A checker that compares an observation time only with the communication time. | yes |
| `inv.own-action` | own-action | A checker that accepts any action as the content of an intention. | yes |
| `inv.precedence-agreed` | precedence-agreed | A participant that orders crossing moves by the time it received them. | yes |
| `inv.precision-bound-one-reading` | precision-bound-one-reading | A checker that lets a set of readings stand in a precision-bound move. | yes |
| `inv.provenance-monotone` | provenance-monotone | A relay that writes itself in place of the source it relays. | yes |
| `inv.quoted-inert` | quoted-inert | A parser that lets a force word inside a quotation set the class of the move. | yes |
| `inv.readings-kept` | readings-kept | A normaliser that keeps only the first reading of a set. | yes |
| `inv.realisations-normalise` | realisations-normalise | An idiom whose expansion in the lexicon turns a request into a command. | yes |
| `inv.single-edit-detected` | single-edit-detected | A move check word that leaves the strength words out of what it covers. | yes |
| `inv.speech-decodable` | long-root-decodable | A reader that takes the long root's syllable to open four symbols, as its onset alone would. | yes |
| `inv.speech-decodable` | speech-decodable | A lexicon with a word that is two words written together. | yes |
| `inv.standing-unchanged` | standing-unchanged | A terse realisation that drops an explicit strength word. | yes |
| `inv.stop-delivery-known` | stop-delivery-known | An acknowledgement that states only the last serial received, so that a stop lost before it is recorded as acknowledged. | yes |
| `inv.stop-delivery-known` | stop-sent-once | A sender that never sends a stop again, and records it as unacknowledged after one interval. | yes |
| `inv.stop-restates` | stop-restates | A checker that compares a restatement byte for byte, refusing 'I' for 'agent 2'. | yes |
| `inv.strength-is-interval` | strength-is-interval | A normaliser that writes a named level as a single point. | yes |
| `inv.summary-keeps-lowest` | summary-keeps-lowest | A summary that keeps the median strength under each calibration. | yes |
| `inv.summary-keeps-lowest` | summary-orders-bases | A summary that orders the bases of one tier and keeps only the first. | yes |
| `inv.tokenizer-round-trip` | tokenizer-round-trip | A tokenizer planted on the panel that rewrites one character of the alphabet as another. | yes |
| `inv.transport-stable` | transport-stable | A transmitted alphabet that includes the underscore, which Markdown rendering consumes: the native digital form spelling h with U+005F. | yes |
| `inv.truncation-detected` | truncation-detected | A reader that accepts a message cut at a boundary between two of its moves. | yes |
| `inv.unknown-preserved` | unknown-preserved | A lexer that reads an unknown word as the known word nearest to it. | yes |
| `inv.view-independent-normalisation` | view-independent-normalisation | A view that normalises what it hears against its own record, writing in place of each reference to an entry it holds the content of that entry. | yes |
| `inv.well-typed` | well-typed | A checker that accepts a shared node reached again from inside itself. | yes |
| `inv.word-formation` | word-formation | A parser that reads an unlisted compound as the listed idiom it most resembles. | yes |
| `machine/conversion-lossy` | conversion-lossy | A conversion to the native digital form that drops payloads. | yes |
| `machine/export-parsed-back` | export-parsed-back | A reader that imports a JSON export and reads it as a message. | yes |
| `machine/serialisation-normalises` | serialisation-normalises | A canonical serialisation that spells the normal form instead of what was written. | yes |
| `semantic/lexicon-version-ignored` | lexicon-version-ignored | A reader that interprets a message under its own lexicon whatever version the message names. | yes |
| `semantic/origin-dropped` | origin-dropped | A normaliser that writes the origin of external content as the speaker's own as it moves the content into a move's core. | yes |
| `semantic/quotation-rewritten` | quotation-rewritten | A normaliser that rewrites the words of a quotation into its own order. | yes |
| `units/formation-not-from-parts` | formation-not-from-parts | A lexer that reads every unlisted formation as an unknown word. | yes |
| `units/numbering-differs` | numbering-differs | A normaliser that keeps the names as the speaker numbered them. | yes |
| `units/value-left-where-written` | value-left-where-written | A normaliser that does not state an inherited world on the units that bear it. | yes |
| `writing/layout-carries-meaning` | layout-carries-meaning | A reader that takes a line break inside a move as a fault. | yes |
<!-- end generated -->

## The diagnostics

A diagnostic has a **code**, `d.` followed by the stage that raised it and its name; the **location** in the text; what was **expected**; what was **detected**; any **ambiguity**; a **confidence**; its **recoverability**; and a **note**. A diagnostic rejects what it reports unless its recoverability says otherwise: *kept opaque* for an unknown word, *restate in what the reader reads* for a release the reader lacks, *restate without the feature* for a feature it lacks, and *send again* for a mismatched integrity check value. Every diagnostic can be stated in the language itself, as an asserted position, on the basis of computation, that the reader detected a fault, with the code as declared data.

<!-- generated: diagnostics -->
| Code | Condition |
|---|---|
| `d.tokenizer.outside-the-alphabet` | a character outside the alphabet |
| `d.tokenizer.mixed-encodings` | letters of the transliteration and code points of the native digital form in one text |
| `d.tokenizer.foreign-use-of-the-range` | a code point of the declared range that is no symbol |
| `d.lexer.unknown-word` | a word absent from the named lexicon version |
| `d.lexer.payload-short` | a payload shorter than its stated length |
| `d.lexer.payload-long` | a payload longer than its stated length |
| `d.lexer.payload-character` | a character no payload may hold |
| `d.lexer.letter-outside-a-payload` | a letter outside the symbols, outside any payload |
| `d.parser.empty` | no message |
| `d.parser.envelope` | an envelope field missing, repeated or out of order |
| `d.parser.unexpected-word` | a word no production admits at its place |
| `d.parser.end-of-input` | the message ends before a production is complete |
| `d.parser.count-mismatch` | a move's count differs from its number of words |
| `d.parser.move-check-mismatch` | a move check word differs from the one computed |
| `d.parser.number-check-mismatch` | a number's check word differs from the one computed |
| `d.parser.number-form` | numerals that do not form a number |
| `d.parser.width` | a name, identifier or check value at the wrong width |
| `d.parser.unclosed-unit` | a unit opened and not closed within its move |
| `d.parser.name-undefined` | a reference to a node no name in the move defines |
| `d.parser.name-repeated` | a name defined twice in one move |
| `d.parser.name-cycle` | a shared node that reaches itself |
| `d.parser.maximum` | a register's maximum exceeded |
| `d.parser.version-unknown` | a language, lexicon or protocol version, a dialect or a feature the message names that this reader lacks |
| `d.parser.version-pairing` | a lexicon release earlier than the language release or a named dialect may be read with |
| `d.parser.dialect-conflict` | a compressed form of a named dialect within one edit of a word of the named lexicon release or of another named dialect |
| `d.checker.definition-scope` | a definition scoped to a dialect its message does not name |
| `d.parser.feature-lacking` | a move that uses a must-understand feature this reader lacks |
| `d.parser.media-type` | a declared type that is not a media type |
| `d.parser.protocol-message` | a message whose identifier is zero with a first entry other than zero, more than one recipient or the mark of a forwarded message |
| `d.parser.unit-check-mismatch` | the check word of an envelope or a protocol statement differs from the one computed |
| `d.parser.statement-form` | a protocol statement whose channels, serials or entries are out of order or repeated |
| `d.parser.authentication-form` | an authentication field whose scheme is unknown or whose signature has another length |
| `d.checker.force` | a force class missing, present where it does not apply, or inconsistent |
| `d.checker.authority` | authority missing on an operative or pending move, or present on another |
| `d.checker.change-without-entry` | a change made with no entry named, or an entry named with no change |
| `d.checker.expectation` | a reference that names an entry without the kind and status it expects, or a mention that states them |
| `d.checker.ill-typed` | a constituent whose sort its place does not admit |
| `d.checker.ordered-times` | an observation time after an inference time, or an inference time after the communication time |
| `d.checker.strength-range` | a numeric strength outside zero and one |
| `d.checker.accidental-in-operative` | an operative move marked as accidentally ambiguous |
| `d.checker.precision-bound` | an ambiguity in a precision-bound move other than a declared kind |
| `d.checker.figure-without-target` | a novel figure in a precision-bound move without the relation its type requires, its target content or what a metonym stands for |
| `d.checker.figure-relation` | a figure's relation that does not fit its type or its unit, a relation where no figure stands, a metonymy on a unit that is not a term, or a figure with two relations |
| `d.checker.idiom-absent` | an idiom absent from the declared lexicon version, or with an incomplete expansion |
| `d.checker.loss-not-incurred` | a declared loss that no conventional or idiomatic form of the move incurs |
| `d.checker.formation-unfit` | a formation whose suffix does not take its stem, or a compound whose head takes no modifier |
| `d.checker.definition-form` | an act of definition that does not state its term and its expansion, or a term not shaped as a root |
| `d.checker.definition-reaches-the-core` | a definition of a word of the grammar, which no act of definition changes |
| `d.checker.definition-shadows` | a definition of a word the release already lists |
| `d.checker.definition-confusable` | a defined term within one edit of a word, or two of a critical word |
| `d.checker.definition-recursive` | a definition whose expansion contains its term |
| `d.checker.definition-carries-force` | a definition whose expansion carries embedded material or readings |
| `d.checker.stop-restatement` | a stop whose restatement differs from what it withdraws |
| `d.checker.fit` | an act that does not fit the entry it names |
| `d.checker.integrity-value-required` | a precision-bound move, operative, pending, declared or in a register that carries the class by default, in a message without the integrity check value |
| `d.checker.register-excludes-word` | a word, suffix, act word or idiom whose entry does not list the move's register |
| `d.checker.register-excludes-device` | a device of economy that none of the move's register's modes admits, or a formula in a register that admits none |
| `d.checker.register-order` | siblings out of canonical order in a register whose syntax is canonical |
| `d.checker.own-action` | an intention whose content is not an action by its holder |
| `d.checker.authority-attenuates` | a grant that exceeds the grantor's claimed scope |
| `d.checker.readings` | a set of readings with fewer than two readings |
| `d.checker.times-inconsistent` | times that cannot all hold together |
| `d.checker.unknown-in-precision-bound` | an unknown word in a precision-bound move |
| `d.checker.confirmation-source` | an independent confirmation that does not state the source it rests on |
| `d.checker.collective-reading` | a collective that acts or holds a normative state without its reading, joint or distributive |
| `d.check-values.integrity-mismatch` | the integrity check value differs from the one computed |
| `d.check-values.semantic-mismatch` | the semantic check value differs from the one computed |
<!-- end generated -->

The registry is that of the canonical implementation, and a test holds every code in it to a rule that raises it. The canonical implementation's participant also reports the diagnostics of its view, `d.view.held`, `d.view.expectation-not-met`, `d.view.crossing`, `d.view.crossed`, `d.view.handle-repeated`, `d.view.forwarded`, `d.view.damaged`, `d.view.applied-before`, `d.view.serial-reused`, `d.view.summary-standing`, `d.view.deadline-passed`, `d.view.participant-bound`, `d.view.term-defined` and `d.view.authentication-failed` ([The record and discourse](discourse.md)), and its conversion between registers reports `d.convert.ill-formed`, `d.convert.record-needed` and `d.convert.register-cannot-carry`.

## The interfaces

### The Python package

The package `rowih` needs Python 3.12 or later and has no dependency at run time. Two extras add optional capabilities: `speech`, which synthesises the spoken form with eSpeak NG, and `authentication`, which signs and verifies messages. No function of its interface raises an exception for any message; each returns its result with its diagnostics. What a writer gives is another matter: `generate`, `write` and `state` raise `rowih.diagnostics.InputError`, and nothing else, for a text that does not read as the notation (`NotationError`), envelope values that cannot be written (`EnvelopeError`), a register, mode or diction the language does not have (`OptionError`), or a statement's parts its kind does not take (`StatementError`), since these are errors of the writer's input and not judgements of a message.

| Function | What it does |
|---|---|
| `parse(text, encoding=None, lexicon=None, reader=None)` | Analyses a message, under the releases it names and those the reader holds, and returns its analysis: words, moves, classes, normal forms, social components, diagnostics, check values, what the reader lacked, the deprecated words used and the reader's confidence |
| `validate(text)` | Returns the diagnostics |
| `normalise(text)` | Returns the normal text and the diagnostics |
| `check_values(text)` | Returns each check value stated and computed |
| `convert(text, to)` | Converts to the transliteration, the canonical serialisation, the native digital form, or a JSON export marked as a view |
| `render(text, format, has_font, form, contrast)` | Renders as SVG, PNG, HTML or terminal text ([The writing system](writing-system.md#the-renderings)) |
| `speak(text)` | Returns each line's prosody, IPA and synthesiser input, and the audio where the `speech` extra is installed |
| `sound(text)` | Returns the metre and echoes of each move |
| `gloss(text)` | Returns the five lines of each move: native, transliteration, morpheme gloss, literal semantic form and English explanation |
| `analyze(text)` | Returns the analysis with its measurements, times, dependencies, what the speaker answers for and what it mentions |
| `discourse(texts, participant, now=None)` | Applies messages to a participant's view and returns the view and its derived structures |
| `translate(text, to)` | Converts between registers, declaring what changed, or explains in English |
| `generate(meaning, register, mode, holdings, diction, envelope)` | Writes the canonical, standard and compressed forms, the gloss, the transliteration and the native rendering of a meaning given in the notation |
| `write(meaning, envelope, register, mode, holdings, diction, signer)` | Writes the message to send from a meaning given in the notation, under the envelope given, and returns it with the diagnostics of reading it back |
| `state(kind, sender, recipient, time, channels, entries, about)` | Writes a protocol message ([Messages, protocol and transport](protocol.md#protocol-messages)) and returns it with the diagnostics of reading it back |
| `tokenize(text, lexicon)` | Returns the words with their locations |
| `lookup(term)` | Returns the words, members, morphemes and dialect words a term names ([The lexicon](lexicon.md#looking-a-word-up)) |
| `version()` | Returns the releases the package is and reads |

An `Envelope` holds the values a writer gives beside the moves: the sender, the recipients, the communication time, the identifier, the first entry, the dialect releases the message names, and whether to write the semantic check value and the integrity check value. `write` writes under the envelope it is given, and `generate` under the one it is given or, where none is, a fixed one, from participant 1 to participant 2 at the time 1759622400. A register is named by its code or its name. `state` takes nothing more for *understands*; the received message it names for *lacks*, which goes to that message's sender; each channel's recipients and serials for *holds*; and channels' serials or entries' numbers for *send again* and *not held*. The participant of [The record and discourse](discourse.md) is `rowih.view.View`, the repair rules are `rowih.repair.Participant`, and signing and verification are in `rowih.authentication`.

### The command line

The command `rowih` reads a file, or standard input where none is given, prints diagnostics to standard error, and exits with status 0 where no diagnostic was drawn, 1 where one was, and 2 on misuse.

| Command | What it does |
|---|---|
| `rowih parse [FILE] [--lexicon V]` | Prints the canonical serialisation of what was received |
| `rowih validate [FILE]` | Prints only diagnostics |
| `rowih tokenize [FILE] [--lexicon V]` | Prints each word's location, form and identifier |
| `rowih gloss [FILE]` | Prints the gloss of each move |
| `rowih analyze [FILE]` | Prints the encoding, the words, each move's class and the normal form |
| `rowih translate [FILE] --to REGISTER` | Converts between registers, or explains in English with `--to english` |
| `rowih render [FILE] --format svg\|png\|html\|terminal [--form F] [--contrast C] [-o FILE]` | Renders the message; a PNG needs `-o` |
| `rowih speak [FILE] [-o FILE.wav]` | Prints the spoken form and writes audio with the `speech` extra |
| `rowih lookup TERM` | Prints each matching word, and exits with 1 if there is none |
| `rowih convert [FILE] --to transliteration\|native\|canonical\|json` | Converts the message |
| `rowih write [FILE] --sender N --recipients N [N ...] [--time T] [--identifier N] [--first-entry N] [--dialect NUMBER VERSION] [--semantic] [--register R] [--mode M] [--diction D] [--hearer V]` | Writes the message to send from a meaning in the notation and prints it, with the diagnostics of reading it back on standard error; the time is the current time where none is given |
| `rowih state KIND --sender N --recipient N [--channel R [R ...] --serials S [S ...]] [--entries E [E ...]] [--about FILE] [--time T]` | Writes a protocol message and prints it, with the diagnostics of reading it back |
| `rowih generate FILE` and the options of `write` | Prints the six outputs of the generator for a meaning in the notation, under the fixed envelope unless its values are given |
| `rowih summary grammar\|lexicon` | Prints the grammar summary or the lexicon listing ([The server](#the-server)) |
| `rowih serve` | Serves the Model Context Protocol on standard input and output ([The server](#the-server)) |
| `rowih version` | Prints the releases the package is and reads, as JSON |

The option `--lexicon` names the lexicon release the reader takes as its own, among those the implementation holds; release 1.0 holds its own alone. A text that does not read as the notation, envelope values or statement parts that cannot be written, and a register, mode or diction the language does not have end the command with status 2, as misuse does, and name the error on standard error.

### The TypeScript package

The TypeScript package exports `parse`, `validate`, `normalise`, `checkValues`, `convert`, `render`, `tokenize`, `lookup` and `version`, each taking the loaded language data, so that a page can bundle it. It reads and renders; it does not generate, write, translate, gloss, keep a view, sign or synthesise speech. Its `version` and `lookup` cover the dialects of the releases its loader supplies, as the Python package's do, and a test holds the two implementations to the same results.

### The server

The command `rowih serve` is a server of the Model Context Protocol over standard input and output, written on Python's standard library. It serves revision 2026-07-28, in which every request states its protocol version and the client's capabilities in its `_meta` and no session is opened, and, for a client that opens with `initialize`, the revisions 2025-11-25, 2025-06-18, 2025-03-26 and 2024-11-05 that open a session with that handshake. A request that states another version is refused with the versions the server supports.

Its tools are the functions of the Python package, one each, under the functions' names: `write`, `state`, `parse`, `validate`, `lookup`, `translate`, `gloss`, `normalise`, `check_values`, `analyze`, `discourse`, `generate`, `convert`, `render`, `speak`, `sound`, `tokenize` and `version`. Each checks its arguments against its schema, calls its function and gives the result as structured data, adding nothing to it; `write` also gives the message's English explanation and the literal semantic form of each move, so that a writer can confirm that the message says what was meant, and `parse` gives each move as written and in its literal semantic form with its class. A `write` that states no time takes the current time. An argument that does not meet the schema, or a writer's input that cannot be written, is a tool error that names what is wrong, and an unknown tool is an error of the protocol. `translate` takes no record of entries, so a conversion that needs one reports `d.convert.record-needed`. Every tool reads only and touches nothing outside the process.

Its resources are the grammar summary, `rowih://grammar`, which lists every grammatical class a writer names with its members as the notation writes them, the act words and the function words; the lexicon listing, `rowih://lexicon`, which gives every word a writer can name, with how the notation writes it, its form and its meaning; and each chapter of this specification, `rowih://specification/` and the chapter's file name, such as `rowih://specification/notation`. The command `rowih summary` prints the first two, which `rowih.summary` generates from the data.

The server bounds what one request can hold: a text of at most 262,144 characters, which admits about 160 kilobytes of declared data, at most 256 messages to a view, a line of at most 8 mebibytes, and at most 16 subscriptions open at once. Its lists never change while it runs, so it offers no notification; a subscription is acknowledged with none and closed when the input ends. The answer to a request the client cancels while it runs is withheld. A failure inside the library is logged to standard error with where it arose and never with a message's content, and answered as an internal error.

### The skill

The directory [`skill/rowih/`](../skill/rowih/) is a skill in the Agent Skills format. Its `SKILL.md` teaches the rule of use, which is to compose through the generator and check before sending and never to write a count or a check value by hand; how to read a message and act only on what its moves' classes and authority allow; how to write one and set its envelope; when to send each protocol message; and the notation in brief. Its references are the grammar summary, the lexicon listing and the chapter on the notation, which `tools/build_skill.py` writes from the data and this specification. The format's reference validator accepts the skill, and the tests hold every example in it to the toolchain: each move it shows writes without a diagnostic, and each tool and command it names exists.

## Token measurements

The language's cost in tokens is measured with a panel of thirteen tokenizers from the open and commercial families that publish theirs, each pinned by revision and digest; every one returns every message of the suite byte for byte, and a control tokenizer whose normaliser rewrites white space returns none, showing that the check can fail.

<!-- generated: tokens -->
Measured over 382 messages, 35,091 words and 402 moves, by 13 tokenizers.

| Quantity | Median | Range |
|---|---|---|
| tokens a word, transliteration | 2.16 | 1.91 to 2.27 |
| tokens a move, transliteration, its envelope's share included | 188.53 | 166.50 to 197.96 |
| tokens of the native digital form over the transliteration's | 5.85 | 5.64 to 6.58 |
| tokens of the transliteration over the English explanation's | 6.70 | 5.90 to 7.09 |
<!-- end generated -->

The English explanation the comparison is made against keeps none of the language's checks, counts or envelope and states only part of what a message leaves implicit, so the ratio bounds what the language's explicitness costs and does not compare equivalent texts. Language models should exchange the transliteration, since the native digital form costs about six times as many tokens. Whether the language costs fewer tokens than English carrying equivalent checks, or saves tokens elsewhere, in recovering from an injection or in repairing a lost message, has not been measured.

## Known limitations

These are true of release 1.0.

- **What the language cannot enforce.** It marks an instruction, a quoted instruction and untrusted content apart; enforcing the difference belongs to the receiving agent. A compromised speaker can omit the mark that a move's content came from external material, which makes the omission a false statement and not an impossibility. A relay that paraphrases and recomputes the semantic check value, or a forged claim of provenance, is detected only by authentication, whose keys the language does not provide.
- **What communication cannot do.** The loss of the last message on a channel is known to neither party. Participants keep views that can differ, and a divergence can be detected without being resolved. A strength means what its speaker's calibration makes it mean, and no calibration across agents is made.
- **The surface.** The surface is a serialisation of a labelled tree: every unit is opened and closed by a word, and every grammatical value is a word of its own, since no form may carry two critical dimensions. Bookkeeping fills every message: in one example an independent reviewer read, an envelope of 58 words carries a move of 29.
- **The single-edit guarantee** holds where the integrity check value is carried; without it, a substitution of the term that names the role of an authority claim can pass ([The enumerations](#the-enumerations)). Requiring the value on every message would close this.
- **Use.** The corpus was generated by one designer; whether conventions emerge in use, whether agents read new formations from their parts, and whether a language-model hearer recovers what a device of economy omits are untested. Of the 58 classes, 22 are used rarely in the domain corpus; the five suppletive words appear in one item each.
- **Reading and hearing.** No human has read the writing system or heard the spoken form; one language-model reader has read the components ([The writing system](writing-system.md#what-the-writing-system-has-been-tested-on)).
- **Resemblance.** Every word of one morpheme in the open classes was compared with the frequent vocabulary of twenty major languages and the word lists of ten constructed languages. Two roots too close to a word of another language were deprecated and replaced, and 1,242 other close matches, for 179 words, are retained with their meanings recorded. The comparison uses reduced transcriptions and covers some languages thinly.
- **Release 1.0.** It reads only its own messages. Within it, a completion or error report cannot be accepted, a counterparty cannot release another's commitment, and the authority a grant passes on is checked only for an assignment's settlement or failure ([The record and discourse](discourse.md#requests-offers-commitments-and-delegation)).
