# The grammar

A message is a sequence of words, and the grammar states which sequences are messages. Its productions fix the order of the envelope, the moves and their heads, and bracket every unit of content between an opening and a closing word, so that each string of words has one structure. The checker then applies the rules that the productions do not state: which values may stand in which unit, which parts must occur together, and what a move's force requires. This chapter states the productions, the structural words, the grammatical classes, the class computed for each move, and the rules a well-formed move obeys. The check words and check values are stated in [Messages, protocol and transport](protocol.md), and what each class and member means in [What a message means](meaning.md).

## The productions

In the productions, a word in capitals is a structural word or a member of a class, named by the last part of its identifier, and a name in lower case is a production or a class. Braces enclose what may occur any number of times, including none, brackets what may occur once or not at all, and a vertical bar separates alternatives. A comment, after `--`, states a condition the production does not express.

<!-- generated: productions -->
```
message       = envelope move { move }
              | envelope statement
                -- a protocol message: its identifier and first entry are zero, so that
                -- it takes no serial on its channel and adds no entry; it has one
                -- recipient and carries the integrity check value
envelope      = WORD-COUNT number
                SENDER participant RECIPIENTS participant { participant }
                COMMUNICATION-TIME number VERSION version version version
                { DIALECT number version digest }
                IDENTIFIER identifier FIRST-ENTRY number [ FORWARDED ]
                [ SEMANTIC-CHECK-VALUE check-value ] unit-check
                [ AUTHENTICATION number number payload ]
                [ INTEGRITY-CHECK-VALUE check-value ]
                -- the count states the words from SENDER to the unit check word, which
                -- it includes (protocol 0.3)
                -- the k-th move adds the entry numbered first entry + k - 1 in the
                -- sender's count of its own entries
                -- AUTHENTICATION states its scheme, the length of its signature in
                -- bytes and the signature, which covers the canonical serialisation
                -- without this field and the integrity check value's
                -- the three versions are the language's, the lexicon's and the
                -- protocol's; each dialect the message uses is named by its number, its
                -- version and its digest, in ascending order of number (language 0.10)
participant   = number
version       = number of two integers, major and minor, with the decimal point between
                them and neither with a leading zero
digest        = number written at the check value width
identifier    = number written at the identifier width
check-value   = number written at the check value width
statement     = WORD-COUNT number ( HOLDS holding { holding }
                                  | ( SEND-AGAIN | NOT-HELD ) asked { asked }
                                  | UNDERSTANDS understood
                                  | LACKS CHANNEL participant { participant }
                                    SERIALS number lacked { lacked } )
                statement-check
                -- every word of a statement is a fixed form, which every version reads
                -- alike; the count states the words after it, the check word included
holding       = CHANNEL participant { participant } SERIALS number { number }
                -- the recipients of one of the addressee's channels; the last of its
                -- serials the sender holds with none missing before it, then each serial
                -- it holds beyond that one
asked         = CHANNEL participant { participant } SERIALS number { number }
              | ENTRIES number { number }
                -- messages by their channel and serials, or entries of the addressee's
                -- by their numbers, whose content alone is asked for
understood    = LANGUAGE-VERSION version { version } LEXICON-VERSION version { version }
                PROTOCOL-VERSION version { version } { DIALECT number version digest }
                [ LACKING-FEATURES number { number } ]
                -- the versions its sender reads, each list ascending, the dialects it
                -- holds and the features it lacks (protocol 0.4)
lacked        = LANGUAGE-VERSION version | LEXICON-VERSION version
              | PROTOCOL-VERSION version | DIALECT number version digest
              | LACKING-FEATURES number { number }
                -- a message of the addressee's, by its channel and serial, and what of
                -- the versions, dialects and features it uses its sender lacks, in the
                -- order the alternatives are written here
statement-check = unit-check
unit-check    = a number check word, computed by the rule of the unit check word over the
                words between the unit's count and itself
move          = WORD-COUNT number body
body          = head { constituent } move-check
                -- the count states the words of the body, the move check word included,
                -- a payload counting as one word
head          = ( adds [ change ] | act-word [ rest-of-force ] ) [ authority ]
                [ DEADLINE time-spec ] [ named ] { relation-word } [ politeness-word ]
                [ diction ] { declared-loss } [ register ] [ PRECISION-BOUND ]
                -- an act word stands for the force values its entry expands to, a
                -- beginning of adds and change; rest-of-force is what the expansion
                -- leaves of them, read as written
                -- the declared losses are distinct members, each a loss some form of
                -- the move incurs: an act word or idiom, the politeness word, the
                -- diction, the register or a register-marked word
                -- the register holds over the move's whole surface, the standard
                -- register where none is written; the protocol and formal registers
                -- make the move precision-bound
                -- the politeness word and the diction are words of the lexicon; a
                -- diction may also stand as a term's content word
adds          = ISSUE kind-of-issue
              | NORMATIVE-ENTRY kind-of-normative-entry [ bindingness ]
                -- bindingness is required unless the kind is RECOMMENDATION
              | SETTING kind-of-setting
              | ASSERTED-POSITION | CONCEDED-POSITION | SUPPOSITION | SUMMARY
              | NOTHING-BEYOND-ITS-OWN-RECORD
change        = NONE | ( RESOLUTION outcome-of-a-resolution | LOWERING | ACKNOWLEDGEMENT )
                extent when-the-change-takes-effect
                -- change is present exactly when the move names an entry
authority     = SPEAKERS-OWN | ON-BEHALF-OF-A-NAMED-PRINCIPAL term | IN-A-NAMED-ROLE term
                -- present exactly when the move is operative or pending
named         = reference { reference }
                -- more than one reference only after SUMMARY, which names the entries
                -- it summarises with the change NONE
reference     = NAMES target [ PART name ] | MENTIONS target [ PART name ]
target        = participant number expected-kind expected-status
                -- an entry, by its author and its number; the expectation is required
                -- after NAMES and absent after MENTIONS
              | MESSAGE-TARGET participant number
              | MESSAGE-SERIAL participant number participant { participant }
                -- a message, by its sender, its serial and the recipients of its
                -- channel, which names a message its speaker does not hold
                -- a message, by its sender and the first entry its envelope states,
                -- which no other message of that sender states, on any channel
expected-kind = ISSUE kind-of-issue | NORMATIVE-ENTRY kind-of-normative-entry
              | SETTING kind-of-setting
              | ASSERTED-POSITION | CONCEDED-POSITION | SUPPOSITION | SUMMARY
              | NOTHING-BEYOND-ITS-OWN-RECORD
                -- the kind of the entry named, which is what its move added
                -- without the bindingness, no part of an entry's kind
constituent   = assertion | situation | term | wall | reading-set | SAME name
              | extragrammatical-idiom
extragrammatical-idiom = content-word content-word { content-word }
                -- the words of an extragrammatical idiom the release lists, recognised
                -- where a constituent or an assertion's situation stands, which no other
                -- production admits; the core holds its expansion
assertion     = ASSERTION [ NAME name ] { assertion-part } situation { situation | assertion-part }
                END-ASSERTION
assertion-part = basis | strength | numeric-strength | independence-of-a-confirmation
              | provenance | time-value | figurative-part | information-structure
              | status-of-content | IDIOM-ENTRY | extragrammatical-idiom
                -- in an assertion of a summary, several bases of one tier and several
                -- strengths, one for each calibration
numeric-strength = [ comparator ] number [ PARTY participant ]
                -- a point or an interval within 0 and 1; PARTY, the participant whose
                -- calibration the number is under, is written in an assertion of a
                -- summary, where it is required, and nowhere else
provenance    = provenance-link ( term | situation | assertion | reference | SAME name )
situation     = SITUATION [ NAME name ] { situation-part } END-SITUATION
situation-part = content-word | polarity | aspect | world-of-evaluation | status-of-content
              | information-structure | kind-of-question | kind-of-attitude | origin-of-an-aim
              | kind-of-normative-entry | bindingness | status-of-a-normative-state
              | execution-phase | structural-relation | basis | strength | numeric-strength
              | time-value | figurative-part | role-filler | connective-part
              | IDIOM-ENTRY
                -- the idiom mark: the unit is read by the entry whose literal structure
                -- it matches, slots aside, and the core holds that entry's expansion
role-filler   = ( participation | COUNTERPARTY ) filler
filler        = term | situation | assertion | wall | reading-set | SAME name
connective-part = CONDITION filler | CONJUNCTION | INCLUSIVE-DISJUNCTION
              | EXCLUSIVE-DISJUNCTION | EQUIVALENCE
term          = TERM [ NAME name ] { term-part } END-TERM
term-part     = content-word | quantity | PARTY participant | DIALECT number | reference
              | person
              | quantifier | existence-commitment | access | verification | discourse-status
              | specificity | reading-of-a-collective | information-structure
              | figurative-part | role-filler | wall | SOURCE ( term | reference | SAME name )
              | IDIOM-ENTRY
                -- SOURCE, on an external referent, names who identified or verified it,
                -- and is required with VERIFIED-BY-A-NAMED-THIRD-PARTY
                -- DIALECT makes a term the dialect whose number follows (language 0.10)
quantity      = [ comparator ] number [ unit-word ] [ PER time-unit ]
unit-word     = time-unit | a unit root
figurative-part = figurative-type | ( TARGET-CONTENT | STANDS-FOR ) filler
                -- one relation to a figure, fitted to its type (language 0.7): a target
                -- content on a metaphor, an irony or a hyperbole, a situation or a unit of
                -- the figure's own kind; what a term stands for on a metonym, a term; and a
                -- metonymy only on a term
time-value    = time-index time-spec
time-spec     = point [ UNTIL point ]           -- an interval; after an observation, event,
                                                -- reference or execution time
              | point point                     -- after VALIDITY-INTERVAL: from, until
              | [ comparator ] number time-unit -- a duration; after an event, reference or
                                                -- execution time
              | [ comparator ] number PER time-unit
                                                -- a rate; after an event time, on a
                                                -- situation iterative or habitual
point         = NOW | number [ time-unit ( AGO | HENCE ) ] | time-relation time-reference
time-reference = time-index | SAME name time-index | NOW | number [ time-unit ( AGO | HENCE ) ]
wall          = WALL DECLARED-DATA number payload number payload END-WALL
              | WALL ( QUOTATION | EXAMPLE ) { word } END-WALL
reading-set   = READINGS kind-of-ambiguity filler filler { filler } END-READINGS
name          = number written at the name width
number        = numeral { numeral } check-word
content-word  = root { suffix } { LINKER root { suffix } } | a closed-class member { suffix }
              | dialect-form
                -- a compressed form of a dialect the message names, a word of the root's
                -- shape standing alone, whose meaning is the term it compresses
                -- (language 0.10)
move-check    = one of the forms of the move check word
```
<!-- end generated -->

## The message and its lines

A message is an envelope followed by one or more moves, or by one protocol statement; a message of the second kind is a protocol message ([Messages, protocol and transport](protocol.md#protocol-messages)). The transliteration writes the envelope on the first line and each move on a line of its own, words separated by one space and every line ended by a line feed; a reader must accept any run of spaces, tabs, line feeds and carriage returns between words. A message must hold at most 155 words, a payload counting as one, and a reader refuses a longer message before reading it, with the diagnostic `d.parser.maximum`.

## The move

A move is its count, its body and its move check word. The count is a number stating how many words the body holds, the move check word included, a payload counting as one word. A reader reads the count, takes that many words, requires the last to be a move check word, and compares it with the move check word computed over the words before it; a mismatch is `d.parser.move-check-mismatch`, and a count that cannot be met is `d.parser.count-mismatch`. Only then does it read the head and the constituents. Because the check precedes the grammar, a damaged word anywhere in a move shows first as a mismatch of the count or the move check word, unless the damage falls on a word the move check word does not weigh. A move that is refused is reported, and reading resumes after its counted body.

## The head

The head states the move's force, and its parts stand in this order:

1. **What the move adds**: an issue with its kind, a normative entry with its kind and, unless the kind is a recommendation, its bindingness, a setting with its kind, or one of *asserted position*, *conceded position*, *supposition*, *summary* and *nothing beyond its own record*. An act word may stand in place of the beginning of the head, and the rest of the force follows it as written ([The lexicon](lexicon.md#act-words)); a member the act word already stands for must not be written again.
2. **The change**, present exactly when the move names an entry: *none*, or a resolution with its outcome (*answer*, *acceptance*, *rejection*, *settlement* or *failure*), a lowering or an acknowledgement, each followed by its extent (*whole entry* or *part of it*) and when it takes effect (*on the move* or *on acceptance*).
3. **The authority claimed**, present exactly when the move is operative or pending: *speaker's own*, or *on behalf of a named principal* or *in a named role*, each followed by the term that names the principal or the role.
4. **The deadline**: the member *deadline* and a time.
5. **The references**: what the move acts on, and, after a summary alone, further entries it summarises.
6. **Discourse relations**, any number.
7. **A politeness word.**
8. **A diction.**
9. **Declared losses**, any number, each distinct.
10. **The register**, the standard register where none is written.
11. **The declaration** *precision-bound*.

A part written out of this order is not consumed where it stands, and the reader reports it as `d.parser.unexpected-word` where it next expects a constituent.

## References and targets

A reference begins *names* or *mentions*. *Names* is a dependency: the move acts on what it names, and the reader resolves it against the record. *Mentions* is not resolved, and states no expectation. A reference's target is one of three:

- an entry, by its author's participant number and its number in the author's count of entries, followed, after *names*, by the kind of entry expected and the status expected (*open*, *in force*, *resolved*, *lowered* or *withdrawn*); the expected kind is what the entry's move added, without its bindingness;
- a message, after *message target*, by its sender and the first entry its envelope states, which no other message of that sender states;
- a message, after *message serial*, by its sender, its serial and the recipients of its channel, which names a message the speaker does not hold.

A reference may narrow to a part of an entry with *part* and a name, the number of the part in the traversal of the entry's normal form. A reference may stand in the head, as a part of a term or as a role's filler. What a move may do to what it names is stated in [The record and discourse](discourse.md).

## Units

The content of a move is made of three units. An **assertion** asserts a situation, with the standing of the assertion and its provenance. A **situation** is an event, a state, an attitude, an aim or a connective joining contents. A **term** is a referent: a thing, a participant, a quantity or a dialect. Each unit opens with its structural word, may be named, holds its parts in any order, and closes with its closing word. A unit holds content words, values of the classes it admits, times, quantities, references, role fillers and nested constituents.

| Unit | Values of these classes | Times | Roles it takes |
|---|---|---|---|
| assertion | basis, strength, independence of a confirmation, information structure, status of content, figurative type, the idiom mark | observation time, inference time, validity interval | provenance links; the relations of a figure |
| situation | aspect, polarity, world of evaluation, status of content, information structure, kind of question, kind of attitude, origin of an aim, kind of normative entry, bindingness, status of a normative state, execution phase, structural relation, connective, figurative type, the idiom mark; basis and strength only in an attitude | event time, reference time, execution time | participation, counterparty, the condition; the relations of a figure |
| term | person, quantifier, existence commitment, access, verification, discourse status, specificity, reading of a collective, information structure, figurative type, the idiom mark | none | participation; the source alone of the provenance links; the relations of a figure |

An assertion must hold a situation, or a named unit, a set of readings or an extragrammatical idiom in its place. A situation stands as a constituent of the move, in an assertion, or after a role; an assertion or a term stands as a constituent of the move or after a role, and never as a bare part of another unit. A unit must not hold two values of one class, except that a situation may hold several connectives and the assertion of a summary several bases and strengths. A quantity stands in a term, in an assertion as its numeric strength, or in an attitude; *party* and *dialect* stand only in a term. A rate stands only on a situation whose aspect is iterative or habitual. Each of these is reported as `d.checker.ill-typed`.

A **wall** encloses embedded material: declared data, given as its media type and its bytes as two payloads, or a quotation or an example, given as words. Material within a wall is inert by kind: no word in it acts as a word of the move, and an instruction it holds cannot become operative. A **set of readings** holds two readings of one kind of ambiguity ([What a message means](meaning.md#ambiguity)); fewer than two is `d.checker.readings`, and more than two `d.parser.maximum`.

A **name** gives a unit a number, at the name width of two digits, so that *same* and the name can stand for the unit elsewhere in the move; names are scoped to one move. A name used before it is defined is `d.parser.name-undefined`, a name defined twice `d.parser.name-repeated`, and names that reach themselves `d.parser.name-cycle`. Units nest at most five deep, and a deeper unit is refused where the depth is reached, with `d.parser.maximum`.

## Content words

A content word is a root with its suffixes and any further roots each opened by the linker, a closed-class member with its suffixes, or a compressed form of a dialect the message names ([The sounds and the shapes of words](sounds-and-words.md#how-a-words-opening-fixes-its-length)). A word the lexicon lists is read by its entry; a word that divides into the parts of a formation is read by composition ([The lexicon](lexicon.md#word-formation)); any other word is unknown. An unknown word is reported as `d.lexer.unknown-word` and kept opaque: the move is still read, and the word stands as content no hearer can interpret. A precision-bound move must not hold an unknown word, `d.checker.unknown-in-precision-bound`. An extragrammatical idiom is recognised by its words wherever a constituent or an assertion's situation stands, the longest the release lists being taken.

## Numbers and names

A number is its numerals, most significant first, followed by its check word. The numerals are the ten digits and five signs: the decimal point, the negative sign, the ratio, the exponent and the interval. A number has the form of an optional sign, digits, an optional fraction and an optional exponent, or two such pieces joined by a ratio or an interval; its whole part has no leading zero unless it is zero. The number check word covers its digits: each digit is multiplied by its weight, (*i* mod 10) + 1, where *i* counts the digits from 0 at the left, and the sum modulo 11 is the check word's value. The number 43 has the check word of 4 × 1 + 3 × 2 = 10, `yiba`, and is written `nasu namo yiba`. A mismatch is `d.parser.number-check-mismatch`, and a number of the wrong form `d.parser.number-form`. The signs are not weighed by the number's check word; the move check word or the unit check word covers them.

A participant, a count, an entry number, a name and a serial are whole numbers. A name is written at a width of two digits, an identifier at six and a check value or a digest at nine, with zeros on the left; a number at a fixed width must have exactly that many digits, `d.parser.width`. A version is two whole numbers, the major and the minor, joined by the decimal point, neither with a leading zero.

<!-- generated: fixed-forms -->
| Form | Identifier |
|---|---|
| `napa` | `g.numbers.numeral.zero` |
| `nake` | `g.numbers.numeral.one` |
| `nadi` | `g.numbers.numeral.two` |
| `namo` | `g.numbers.numeral.three` |
| `nasu` | `g.numbers.numeral.four` |
| `neta` | `g.numbers.numeral.five` |
| `nebe` | `g.numbers.numeral.six` |
| `negi` | `g.numbers.numeral.seven` |
| `neno` | `g.numbers.numeral.eight` |
| `nelu` | `g.numbers.numeral.nine` |
| `nika` | `g.numbers.numeral.decimal-point` |
| `nide` | `g.numbers.numeral.negative` |
| `nimi` | `g.numbers.numeral.ratio` |
| `niso` | `g.numbers.numeral.exponent` |
| `niru` | `g.numbers.numeral.interval` |
| `yata` | `g.numbers.check-word.check-0` |
| `yabe` | `g.numbers.check-word.check-1` |
| `yagi` | `g.numbers.check-word.check-2` |
| `yano` | `g.numbers.check-word.check-3` |
| `yalu` | `g.numbers.check-word.check-4` |
| `yeka` | `g.numbers.check-word.check-5` |
| `yede` | `g.numbers.check-word.check-6` |
| `yemi` | `g.numbers.check-word.check-7` |
| `yeso` | `g.numbers.check-word.check-8` |
| `yeru` | `g.numbers.check-word.check-9` |
| `yiba` | `g.numbers.check-word.check-10` |
| `waho` | `g.message.message-field.sender` |
| `watu` | `g.message.message-field.recipients` |
| `wesa` | `g.message.message-field.communication-time` |
| `were` | `g.message.message-field.version` |
| `weyi` | `g.message.message-field.identifier` |
| `wepo` | `g.message.message-field.integrity-check-value` |
| `weku` | `g.message.message-field.semantic-check-value` |
| `lewe` | `g.message.message-field.first-entry` |
| `luya` | `g.message.message-field.authentication` |
| `wila` | `g.message.word-count.word-count` |
| `wiwe` | `g.message.forwarded.forwarded` |
| `lupe` | `g.protocol.protocol-statement.holds` |
| `luki` | `g.protocol.protocol-statement.send-again` |
| `ludo` | `g.protocol.protocol-statement.not-held` |
| `yiwu` | `g.protocol.protocol-statement.understands` |
| `yoda` | `g.protocol.protocol-statement.lacks` |
| `lumu` | `g.protocol.statement-part.channel` |
| `yige` | `g.protocol.statement-part.serials` |
| `yini` | `g.protocol.statement-part.entries` |
| `yome` | `g.protocol.statement-part.language-version` |
| `yosi` | `g.protocol.statement-part.lexicon-version` |
| `yoro` | `g.protocol.statement-part.protocol-version` |
| `yoyu` | `g.protocol.statement-part.lacking-features` |
| `yuga` | `g.structure.dialect` |
<!-- end generated -->

These fixed forms are the words of numbers, of the envelope and of protocol statements. They have not changed since protocol 0.3, and the build of a release stops if any would change, so that every reader reads the envelope and the protocol alike.

## The structural words

A structural word brackets or connects units; it belongs to no class and carries no value of its own.

<!-- generated: structural-words -->
| Form | Gloss | What it does | Since |
|---|---|---|---|
| `wora` | ASSERTION | opens an assertion | 0.1 |
| `woye` | END-ASSERTION | closes an assertion | 0.1 |
| `wopi` | SITUATION | opens a situation | 0.1 |
| `woko` | END-SITUATION | closes a situation | 0.1 |
| `wodu` | TERM | opens a term | 0.1 |
| `wuwa` | END-TERM | closes a term | 0.1 |
| `wuhe` | READINGS | opens a set of readings | 0.1 |
| `wuti` | END-READINGS | closes a set of readings | 0.1 |
| `wubo` | WALL | opens embedded material | 0.1 |
| `wugu` | END-WALL | closes embedded material | 0.1 |
| `lasa` | NAME | names the unit it opens, by the checked number that follows | 0.1 |
| `lare` | SAME | stands for the named unit, by the checked number that follows | 0.1 |
| `layi` | MESSAGE-TARGET | makes the target of a reference a message, by its sender and identifier | 0.1 |
| `lapo` | PART | narrows a reference to the node of the entry whose number follows | 0.1 |
| `laku` | PARTY | makes a term the participant whose number follows | 0.1 |
| `lela` | UNTIL | ends an interval at the time that follows | 0.2 |
| `yilo` | MESSAGE-SERIAL | makes the target of a reference a message, by its sender, its serial and the recipients of its channel | 0.9 |
| `yuga` | DIALECT | names a dialect by the number that follows, and in the version field and a protocol statement its version and digest as well | 0.10 |
<!-- end generated -->

## The grammatical classes

A class is a closed set of members, each a value of one dimension of a move. Each class states what it applies to and its status there. An **obligatory** class must be given a value wherever it applies; a class with a **default** has a value where none is written, which the normal form states, and the default either claims nothing (as an unstated basis claims no basis) or is the weakest member. A class with a **critical dimension** carries one of the dimensions whose silent change would alter what a move does or claims; each such dimension is protected by the move check word, and the members of the classes marked *protected* are protected words, kept three edits from every other word ([The sounds and the shapes of words](sounds-and-words.md#the-distances-between-words)). A class added after the first release belongs to a feature, which a reader lacking it handles as its flag states ([Messages, protocol and transport](protocol.md#versions-and-features)). The grammar has 58 classes with 289 members in ten groups.

### Force

<!-- generated: classes:force -->
| Class | Applies to | Status | Critical dimension | Members |
|---|---|---|---|---|
| what the move adds<br>`g.force.what-the-move-adds` | every move | obligatory | operative force; protected | `kotepu` ASSERTED-POSITION · `ketako` CONCEDED-POSITION · `keguge` SUPPOSITION · `kimewi` SUMMARY · `kanume` ISSUE · `kukare` NORMATIVE-ENTRY · `kuwipe` SETTING · `kaniku` NOTHING-BEYOND-ITS-OWN-RECORD |
| kind of issue<br>`g.force.kind-of-issue` | an issue | obligatory | operative force; protected | `kuwona` QUESTION · `kayoti` REQUEST · `kiwuli` PROPOSAL · `kuruta` CHALLENGE |
| kind of normative entry<br>`g.force.kind-of-normative-entry` | a normative entry, or a report of one | obligatory | commitment status; protected | `kerihi` COMMITMENT · `kepehe` OBLIGATION · `kunehu` PERMISSION · `kegipa` ASSIGNMENT · `kemogo` RECOMMENDATION |
| bindingness<br>`g.force.bindingness` | a normative entry other than a recommendation | obligatory | commitment status; protected | `kidayo` BINDINGNESS.ON-ACCEPTANCE · `kesoha` BOUND · `kuhapu` BOUND-WITHIN-A-PROTOCOL |
| kind of setting<br>`g.force.kind-of-setting` | a setting | obligatory | operative force; protected | `konebi` DEFINITION · `kabusu` KIND-OF-SETTING.VERSION · `kayiyo` ROLE · `kibuda` CALIBRATION · `kigimi` RELATION |
| change made<br>`g.force.change-made` | a move that names an entry | obligatory | the scope of any retraction, revocation or cancellation; protected | `kitapi` NONE · `kodoyi` RESOLUTION · `kisahu` LOWERING · `kiyala` ACKNOWLEDGEMENT |
| outcome of a resolution<br>`g.force.outcome-of-a-resolution` | a resolution | obligatory | operative force; protected | `korolu` ANSWER · `komaka` OUTCOME-OF-A-RESOLUTION.ACCEPTANCE · `kawadu` REJECTION · `kobaso` SETTLEMENT · `kutomi` FAILURE |
| extent<br>`g.force.extent` | a change other than none | obligatory | the scope of any retraction, revocation or cancellation; protected | `kusodu` WHOLE-ENTRY · `kiduku` PART-OF-IT |
| when the change takes effect<br>`g.force.when-the-change-takes-effect` | a change other than none | obligatory | operative force; protected | `kuniya` ON-THE-MOVE · `kaweki` WHEN-THE-CHANGE-TAKES-EFFECT.ON-ACCEPTANCE |
| authority claimed<br>`g.force.authority-claimed` | every operative or pending move | obligatory | the identity of any agent who is obligated, authorised or held responsible, and the authority claimed; protected | `kosiki` SPEAKERS-OWN · `kesigu` ON-BEHALF-OF-A-NAMED-PRINCIPAL · `kekegi` IN-A-NAMED-ROLE |
<!-- end generated -->

### Standing

<!-- generated: classes:standing -->
| Class | Applies to | Status | Critical dimension | Members |
|---|---|---|---|---|
| basis<br>`g.standing.basis` | an asserted position, and any reported attitude | default: unstated (claims nothing) | epistemic standing; protected | `teyuhu` OBSERVATION · `tadowe` INTROSPECTION · `turimi` RETRIEVAL · `tiruni` TRAINED-KNOWLEDGE · `tinopo` COMPUTATION · `tilase` INFERENCE · `tuwohu` SIMULATION · `tukika` REPORT · `tukemu` SOURCE-LOST · `tineti` BASIS.UNSTATED |
| strength<br>`g.standing.strength` | an asserted position, and any reported attitude | default: unstated (claims nothing) | epistemic standing; protected | `tebilo` CERTAIN · `tamepi` HIGHLY-PROBABLE · `tomupu` PROBABLE · `tusido` UNCERTAIN · `topeka` SPECULATIVE · `topuge` STRENGTH.UNSTATED |
| provenance link<br>`g.standing.provenance-link` | grounds | default: no claim (claims nothing) | epistemic standing; protected | `tihidi` SOURCE · `tanudo` RELAYER · `tiwayu` PREMISE |
| independence of a confirmation<br>`g.standing.independence-of-a-confirmation` | a confirmation | default: same source (the weakest member) | epistemic standing; protected | `tegeyu` INDEPENDENT · `tawebe` SAME-SOURCE |
<!-- end generated -->

### Attitudes and aims

<!-- generated: classes:attitudes-and-aims -->
| Class | Applies to | Status | Critical dimension | Members |
|---|---|---|---|---|
| kind of attitude<br>`g.attitudes-and-aims.kind-of-attitude` | an attitude | obligatory |  | `paka` BELIEF · `pade` CREDENCE · `pami` KIND-OF-ATTITUDE.ACCEPTANCE · `paso` ENTERTAINING · `paru` DESIRE · `peba` GOAL · `pege` INTENTION · `peni` PREFERENCE · `pelo` UNEXAMINED · `pewu` SETTLED · `pida` UNRESOLVED · `pime` UNRESOLVABLE |
| origin of an aim<br>`g.attitudes-and-aims.origin-of-an-aim` | an aim or a normative state | default: unstated (claims nothing) |  | `pisi` HOLDERS-OWN · `piro` PRINCIPALS · `piyu` INSTRUCTION-RECEIVED · `poga` NORM · `pone` ORIGIN-OF-AN-AIM.UNSTATED |
| status of a normative state<br>`g.attitudes-and-aims.status-of-a-normative-state` | a report of a normative state | obligatory | commitment status | `poli` STATUS-OF-A-NORMATIVE-STATE.IN-FORCE · `powo` DISCHARGED · `pohu` RELEASED · `puma` STATUS-OF-A-NORMATIVE-STATE.WITHDRAWN · `puse` RETRACTED-BY-ITS-HOLDER |
| counterparty<br>`g.attitudes-and-aims.counterparty` | a normative state | default: no claim (claims nothing) |  | `puri` COUNTERPARTY |
| execution phase<br>`g.attitudes-and-aims.execution-phase` | an action or a task | default: unstated (claims nothing) |  | `puyo` NOT-YET-BEGUN · `pupu` ATTEMPTED · `baba` COMPLETED · `bage` FAILED · `bani` ABANDONED · `balo` EXECUTION-PHASE.UNSTATED |
<!-- end generated -->

### Situations and contents

<!-- generated: classes:situations-and-contents -->
| Class | Applies to | Status | Critical dimension | Members |
|---|---|---|---|---|
| aspect<br>`g.situations-and-contents.aspect` | a situation | default: the root's lexical aspect (declared by the lexicon) |  | `bawu` STATIVE · `beda` PERFECTIVE · `beme` PROGRESSIVE · `besi` INCEPTIVE · `bero` COMPLETIVE · `beyu` INTERRUPTED · `biga` CONTINUATIVE · `bine` ITERATIVE · `bili` HABITUAL |
| participation<br>`g.situations-and-contents.participation` | a situation | default: no claim (claims nothing) |  | `biwo` ACTOR · `bihu` UNDERGOER · `boma` RECIPIENT · `bose` INSTRUMENT · `bori` HOLDER · `boyo` CONTENT |
| kind of question<br>`g.situations-and-contents.kind-of-question` | a question | obligatory |  | `bopu` POLAR · `buna` CONSTITUENT · `bule` ALTERNATIVE |
| status of content<br>`g.situations-and-contents.status-of-content` | a content | default: at issue (the plain reading) |  | `buwi` AT-ISSUE · `buho` PRESUPPOSED · `butu` CONVENTIONALLY-IMPLIED · `gada` RESTING-ON-AN-UNSTATED-ASSUMPTION |
| information structure<br>`g.situations-and-contents.information-structure` | a constituent | default: no claim (claims nothing) |  | `game` TOPIC · `gasi` FOCUS · `garo` CONTRASTIVE-FOCUS |
| polarity<br>`g.situations-and-contents.polarity` | a situation | default: affirmative (the plain reading) | polarity and the scope of negation; protected | `tiyami` AFFIRMATIVE · `tiyuke` POLARITY.NEGATIVE |
| world of evaluation<br>`g.situations-and-contents.world-of-evaluation` | a content | default: the world of the enclosing content (fixed by the message) |  | `gayu` ACTUAL · `gega` WORLD-OF-EVALUATION.WITHIN-A-SUPPOSITION · `gene` WITHIN-A-FICTION · `geli` COUNTERFACTUAL |
| connective<br>`g.situations-and-contents.connective` | two contents | default: no claim (claims nothing) |  | `gewo` CONJUNCTION · `gehu` INCLUSIVE-DISJUNCTION · `gima` EXCLUSIVE-DISJUNCTION · `gise` CONDITION · `giri` EQUIVALENCE |
| quantifier<br>`g.situations-and-contents.quantifier` | a referent | default: no claim (claims nothing) |  | `giyo` UNIVERSAL · `gipu` EXISTENTIAL · `gona` DEFINITE · `gole` INDEFINITE · `gowi` GENERIC · `goho` QUANTIFIER.DISTRIBUTIVE · `gotu` COLLECTIVE |
| comparator<br>`g.situations-and-contents.comparator` | a number | default: unstated (claims nothing) | numerical values and their units | `gusa` EXACTLY · `gure` AT-LEAST · `guyi` AT-MOST · `gupo` APPROXIMATELY · `guku` AS-A-REPRESENTATIVE-QUANTITY · `maga` COMPARATOR.UNSTATED |
| structural relation<br>`g.situations-and-contents.structural-relation` | two referents | default: no claim (claims nothing) |  | `mane` IDENTITY · `mali` MEMBER-OF |
<!-- end generated -->

### Reference

<!-- generated: classes:reference -->
| Class | Applies to | Status | Critical dimension | Members |
|---|---|---|---|---|
| existence commitment<br>`g.reference.existence-commitment` | a referent | default: the world of the enclosing content (fixed by the message) |  | `mawo` ASSERTED-TO-EXIST · `mahu` MENTIONED-WITHOUT-EXISTENCE-ASSERTED · `mema` EXISTENCE-COMMITMENT.WITHIN-A-SUPPOSITION · `mese` WITHIN-A-DECLARED-FICTION · `meri` PREDICTED-TO-EXIST · `meyo` ASSERTED-NOT-TO-EXIST |
| access<br>`g.reference.access` | a referent | default: no claim (claims nothing) |  | `mepu` PRESENT · `mina` ABSENT · `mile` INTERNAL · `miwi` EXTERNAL |
| verification<br>`g.reference.verification` | an external referent | default: unverified (the weakest member) |  | `miho` UNVERIFIED · `mitu` VERIFIED-BY-THE-SPEAKER · `mosa` VERIFIED-BY-A-NAMED-THIRD-PARTY |
| discourse status<br>`g.reference.discourse-status` | a referent | default: new where first written and given after (fixed by the message) |  | `more` NEW · `moyi` GIVEN · `mopo` INFERABLE · `moku` IN-THE-SPEAKERS-VIEW-OF-THE-COMMON-GROUND |
| specificity<br>`g.reference.specificity` | a referent | default: no claim (claims nothing) |  | `mula` SPECIFIC · `muwe` NON-SPECIFIC |
| person<br>`g.reference.person` | a referent | default: no claim (claims nothing) | the identity of any agent who is obligated, authorised or held responsible, and the authority claimed | `muhi` SELF · `muto` INTERLOCUTOR · `mubu` THIRD-AGENT · `sama` INCLUSIVE-COLLECTIVE · `sase` EXCLUSIVE-COLLECTIVE · `sari` SYSTEM · `sayo` TOOL · `sapu` ENVIRONMENT · `sena` EXTERNAL-SOURCE |
| reading of a collective<br>`g.reference.reading-of-a-collective` | a collective that acts or holds a normative state | obligatory | the identity of any agent who is obligated, authorised or held responsible, and the authority claimed | `sele` JOINT · `sewi` READING-OF-A-COLLECTIVE.DISTRIBUTIVE |
| kind of reference<br>`g.reference.kind-of-reference` | a reference to an entry or a message | obligatory |  | `seho` NAMES · `setu` MENTIONS |
| expected status of an entry<br>`g.reference.expected-status-of-an-entry` | a reference that names an entry | obligatory |  | `sisa` OPEN · `sire` EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE · `siyi` RESOLVED · `sipo` LOWERED · `siku` EXPECTED-STATUS-OF-AN-ENTRY.WITHDRAWN |
<!-- end generated -->

### Time

<!-- generated: classes:time -->
| Class | Applies to | Status | Critical dimension | Members |
|---|---|---|---|---|
| time index<br>`g.time.time-index` | the unit each describes | default: no claim (claims nothing) | times and deadlines; protected | `dugewi` EVENT-TIME · `dunedo` REFERENCE-TIME · `didigi` OBSERVATION-TIME · `dotura` INFERENCE-TIME · `dekile` TIME-INDEX.COMMUNICATION-TIME · `detuse` EXECUTION-TIME · `diyiho` DEADLINE · `dorude` VALIDITY-INTERVAL |
| time relation<br>`g.time.time-relation` | two times | default: no claim (claims nothing) | times and deadlines; protected | `dinago` BEFORE · `dilode` AFTER · `dimuki` MEETS · `dokeha` MET-BY · `depiri` OVERLAPS · `dubime` OVERLAPPED-BY · `duwelu` STARTS · `dasili` STARTED-BY · `dolopi` DURING · `duduto` CONTAINS · `dihepe` FINISHES · `darole` FINISHED-BY · `duyade` EQUALS |
| time unit<br>`g.time.time-unit` | a stated duration or offset | obligatory | times and deadlines; protected | `diroya` SECOND · `deguna` MINUTE · `dewahi` HOUR · `domoto` DAY · `desesu` WEEK · `dubotu` MONTH · `dayabi` YEAR |
| time anchor<br>`g.time.time-anchor` | a time | default: no claim (claims nothing) | times and deadlines; protected | `dadoka` AGO · `dikara` HENCE · `dayira` NOW · `danawe` PER |
<!-- end generated -->

### Numbers

<!-- generated: classes:numbers -->
| Class | Applies to | Status | Critical dimension | Members |
|---|---|---|---|---|
| numeral<br>`g.numbers.numeral` | a number | obligatory | numerical values and their units | `napa` ZERO · `nake` ONE · `nadi` TWO · `namo` THREE · `nasu` FOUR · `neta` FIVE · `nebe` SIX · `negi` SEVEN · `neno` EIGHT · `nelu` NINE · `nika` DECIMAL-POINT · `nide` NUMERAL.NEGATIVE · `nimi` RATIO · `niso` EXPONENT · `niru` INTERVAL |
| check word<br>`g.numbers.check-word` | a number, an identifier and a count | obligatory | numerical values and their units | `yata` CHECK-0 · `yabe` CHECK-1 · `yagi` CHECK-2 · `yano` CHECK-3 · `yalu` CHECK-4 · `yeka` CHECK-5 · `yede` CHECK-6 · `yemi` CHECK-7 · `yeso` CHECK-8 · `yeru` CHECK-9 · `yiba` CHECK-10 |
<!-- end generated -->

### Ambiguity and figures

<!-- generated: classes:ambiguity-and-figures -->
| Class | Applies to | Status | Critical dimension | Members |
|---|---|---|---|---|
| kind of ambiguity<br>`g.ambiguity-and-figures.kind-of-ambiguity` | a set of readings | obligatory |  | `sola` ACCIDENTAL · `sowe` PRODUCTIVE · `sohi` STRATEGIC · `soto` CREATIVE · `sobu` EPISTEMIC |
| precision-bound declaration<br>`g.ambiguity-and-figures.precision-bound-declaration` | a move or an exchange | default: no claim (claims nothing) |  | `sura` PRECISION-BOUND |
| figurative type<br>`g.ambiguity-and-figures.figurative-type` | a constituent | default: literal (the plain reading) | the figurative type of a constituent as its mark states it | `suye` METAPHOR · `supi` METONYMY · `suko` IRONY · `sudu` HYPERBOLE |
| figure's relation<br>`g.ambiguity-and-figures.figures-relation` | a figure | default: no claim (claims nothing) |  | `wana` TARGET-CONTENT · `wale` STANDS-FOR |
| idiom selection<br>`g.ambiguity-and-figures.idiom-selection` | an expression larger than a word | default: no claim (claims nothing) |  | `wawi` IDIOM-ENTRY |
| declared loss<br>`g.ambiguity-and-figures.declared-loss` | a move | default: no claim (claims nothing) |  | `lehi` REGISTER · `leto` DICTION · `lebu` STANCE · `lira` RELATION-BETWEEN-PARTICIPANTS · `liye` WORDING |
| register<br>`g.ambiguity-and-figures.register` | a move | default: standard (the standard register, ordinary exchange) |  | `lipi` RAW · `liko` PROTOCOL · `lidu` STANDARD · `lowa` EXPLANATORY · `lohe` FORMAL · `loti` CASUAL · `lobo` PLAYFUL · `logu` CEREMONIAL |
<!-- end generated -->

### The message

<!-- generated: classes:message -->
| Class | Applies to | Status | Critical dimension | Members |
|---|---|---|---|---|
| message field<br>`g.message.message-field` | every message | obligatory |  | `waho` SENDER · `watu` RECIPIENTS · `wesa` MESSAGE-FIELD.COMMUNICATION-TIME · `were` MESSAGE-FIELD.VERSION · `weyi` IDENTIFIER · `wepo` INTEGRITY-CHECK-VALUE · `weku` SEMANTIC-CHECK-VALUE · `lewe` FIRST-ENTRY · `luya` AUTHENTICATION |
| word count<br>`g.message.word-count` | every move | obligatory |  | `wila` WORD-COUNT |
| forwarded<br>`g.message.forwarded` | a message | default: the sender is the speaker (fixed by the message) |  | `wiwe` FORWARDED |
| embedded material<br>`g.message.embedded-material` | a constituent | default: no claim (claims nothing) | operative force | `wihi` QUOTATION · `wito` DECLARED-DATA · `wibu` EXAMPLE |
<!-- end generated -->

### The protocol

<!-- generated: classes:protocol -->
| Class | Applies to | Status | Critical dimension | Members |
|---|---|---|---|---|
| protocol statement<br>`g.protocol.protocol-statement` | a protocol message | obligatory |  | `lupe` HOLDS · `luki` SEND-AGAIN · `ludo` NOT-HELD · `yiwu` UNDERSTANDS · `yoda` LACKS |
| statement part<br>`g.protocol.statement-part` | a protocol statement | obligatory |  | `lumu` CHANNEL · `yige` SERIALS · `yini` ENTRIES · `yome` LANGUAGE-VERSION · `yosi` LEXICON-VERSION · `yoro` PROTOCOL-VERSION · `yoyu` LACKING-FEATURES |
<!-- end generated -->

## The class of a move

Every move has a class, computed from what it adds and what it changes and never read from a word. The **binding kinds** of entry are the request, the commitment, the obligation, the permission, the assignment, the definition, the version and the role.

- A move is **operative** if it adds an entry of a binding kind other than a request, or if it names an entry of a binding kind whose expected status is open or in force and resolves or lowers it with effect on the move.
- A move is **pending** if it is not operative and it adds a request or a proposal, or it names such an entry and resolves or lowers it with effect on acceptance.
- An operative move is also **de-escalating** if it names such an entry, takes effect on the move, adds nothing that binds, and lowers it or resolves it by a rejection or a settlement.
- Every other move is **inert**.

A request is therefore pending, and its acceptance operative; an assertion is inert; a report of completion that takes effect when it is accepted is pending; and the withdrawal of an open request is operative and de-escalating. A move must claim authority exactly when it is operative or pending, `d.checker.authority`.

## Precision-bound moves

A move is precision-bound if it is operative or pending, if it declares itself precision-bound, or if its register is the protocol register, R1, or the formal register, R4. A precision-bound move has exactly one reading. It must hold no set of readings, `d.checker.precision-bound`, or `d.checker.accidental-in-operative` where the ambiguity is accidental and the move operative or pending; no quantity without fixed bounds, that is one with no interval and no comparator of *exactly*, *at least* or *at most*, `d.checker.precision-bound`; no unknown word, `d.checker.unknown-in-precision-bound`; and no novel figure without the relation that states its target, `d.checker.figure-without-target`. A message carrying a precision-bound move must carry its integrity check value ([Messages, protocol and transport](protocol.md#the-check-values)).

## The rules beyond the productions

A move that the productions admit must also obey these rules, each reported with the diagnostic given.

| Rule | Diagnostic |
|---|---|
| A change is present exactly when the move names an entry | `d.checker.change-without-entry` |
| What a move acts on is named, not mentioned | `d.checker.expectation` |
| A summary names at least one entry, with the change *none*; only a summary names more than one entry, and each further reference of a summary names an entry | `d.checker.force`, `d.checker.expectation` |
| Authority is claimed exactly when the move is operative or pending | `d.checker.authority` |
| A resolution, lowering or acknowledgement fits the entry it names ([The record and discourse](discourse.md)) | `d.checker.fit` |
| The settlement or failure of another's assignment is made on behalf of the assignment's author | `d.checker.authority-attenuates` |
| A de-escalating move restates what it withdraws, rejects or settles | `d.checker.stop-restatement` |
| Values stand in the units that admit them, once each, and roles, times and quantities where they belong | `d.checker.ill-typed` |
| A numeric strength lies within 0 and 1; the assertion of a summary states each numeric strength's calibrating participant, and no other assertion does | `d.checker.strength-range`, `d.checker.ill-typed` |
| An assertion holds at most two provenance links | `d.parser.maximum` |
| The bases of a summary's assertion are of one tier, none repeated, with one strength for each calibration | `d.checker.ill-typed` |
| Verification and a source stand only on an external referent, and verification by a named third party has a source | `d.checker.ill-typed` |
| A collective as an actor, or as the holder of a normative entry, states whether it acts jointly or each member alone | `d.checker.collective-reading` |
| An intention has a holder and a content that is an action of the holder's | `d.checker.own-action` |
| A confirmation's independence is stated only on a confirmation, and an independent confirmation names its source | `d.checker.ill-typed`, `d.checker.confirmation-source` |
| The observation time precedes the inference time, which precedes the communication time | `d.checker.ordered-times` |
| The times of a move are consistent | `d.checker.times-inconsistent` |
| A figure's relation fits its type, and a metonymy stands only on a term | `d.checker.figure-relation` |
| A word, a device and the order of parts are admitted by the move's register | `d.checker.register-excludes-word`, `d.checker.register-excludes-device`, `d.checker.register-order` |
| A marked idiom selects an entry, a formation's suffix takes its stem, and each declared loss is incurred, once | `d.checker.idiom-absent`, `d.checker.formation-unfit`, `d.checker.loss-not-incurred` |
| A definition is well formed ([The lexicon](lexicon.md#coining-a-word-by-definition)) | `d.checker.definition-form` and its kin |

## The maxima

<!-- generated: maxima -->
| Limit | Maximum |
|---|---|
| nesting | 5 |
| message words | 155 |
| readings | 2 |
| provenance links | 2 |
| definition expansion | 1 |
<!-- end generated -->

These are the least values that admit every item of the conformance suite, in normal expression and in full explicitness, and every register declares them in protocol 0.5. The depth of expansion is one: an idiom's expansion must not use an idiom, and a definition's expansion must not contain the word it defines.

## How a hearer reads a message

A conformant reader analyses a message in this order, and reports diagnostics in the same order:

1. **Tokenizing.** The text is the native digital form if any of its characters is one of the nineteen code points of the language, and the transliteration otherwise. Any character that is neither a symbol of the encoding, a separator nor a character of a payload is reported as `d.tokenizer.outside-the-alphabet`, and a code point of the language's block that is not a symbol as `d.tokenizer.foreign-use-of-the-range`; a word mixing the two encodings is `d.tokenizer.mixed-encodings`.
2. **Lexing.** Each word is looked up, divided into the parts of a formation, or reported as unknown; a letter outside the nineteen, outside a payload, is `d.lexer.letter-outside-a-payload`. Payloads are read after the words that announce them.
3. **Parsing**, by the productions, move by move, each refused move reported and reading resumed after it.
4. **Resolving the releases** the envelope names. A reader that lacks one reports `d.parser.version-unknown`, with what it reads, and interprets no move.
5. **Interpreting** each move: reading its act word and idioms by their entries, dropping a move that uses a must-understand feature the reader lacks, `d.parser.feature-lacking`, checking it by the rules above, computing its class and its normal form.
6. **Checking the values**: the integrity check value, then the semantic check value ([Messages, protocol and transport](protocol.md#the-check-values)).

No input raises an exception: every refusal is a diagnostic ([Conformance](conformance.md)).
