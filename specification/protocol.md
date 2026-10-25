# Messages, protocol and transport

A message carries its own checks. Every number ends in a check word, every move states how many words it holds and ends in a check word computed over its critical words, the envelope does the same over its fields, and a message may carry a check value over its whole text and another over its meaning. A hearer that verifies these detects damage instead of absorbing it, and asks for what it lacks. This chapter states the envelope, the counts, the check words and the check values with their algorithms, the protocol messages by which participants acknowledge, repair and settle the releases they share, authentication, relaying, the media type and the binding to agent transports.

## The envelope

The envelope is the first line of a message. It is a counted unit: the word *word count* and a count, then the fields, then the unit check word; the authentication and the integrity check value follow outside the count.

| Field | Form | What follows it | Required |
|---|---|---|---|
| word count | `wila` | the number of words from the sender to the unit check word, that word included | always |
| sender | `waho` | the sender's participant number | always |
| recipients | `watu` | one or more participant numbers | always |
| communication time | `wesa` | the time the message was sent ([Communication time](#communication-time)) | always |
| version | `were` | three versions: the language's, the lexicon's and the protocol's | always |
| dialect | `yuga` | a dialect's number, version and digest, once for each dialect the message uses, in ascending order of number, none twice | where the message uses a dialect |
| identifier | `weyi` | the message's serial on its channel, at six digits; zero for a protocol message | always |
| first entry | `lewe` | the number of the entry the first move adds; zero for a protocol message | always |
| forwarded | `wiwe` | nothing | optional |
| semantic check value | `weku` | the semantic check value, at nine digits | optional |
| | | the unit check word | always |
| authentication | `luya` | the scheme, the signature's length in bytes and the signature as a payload | optional |
| integrity check value | `wepo` | the integrity check value, at nine digits | where [The check values](#the-check-values) requires it |

The fields stand in this order, each once. A field missing, repeated or out of order is `d.parser.envelope`, and so are dialects out of order. Language 1.0 messages state the versions `1.0 1.0 0.5`.

The envelope of the conformance item `e8-acknowledgement.1` reads:

```
wila nasu namo yiba waho nake yabe watu nadi yagi wesa nake negi neta nelu nebe nadi nadi nasu napa napa yata
were nake nika napa yabe nake nika napa yabe napa nika neta yiba weyi napa napa napa napa napa nake yede
lewe nake yabe yabe wepo nake napa nebe nelu napa nelu negi neno nake yata
```

(broken here into three lines for reading; it is one line): a count of 43, sender 1, recipient 2, communication time 1759622400, versions 1.0, 1.0 and 0.5, identifier 000001, first entry 1, the unit check word `yabe`, and the integrity check value 106909781.

### Participants and channels

A participant is a number, bound to an agent's own identifier by the role setting that opens the exchange ([The record and discourse](discourse.md#roles)). A **channel** is a sender and a set of recipients; the order in which the recipients are written does not matter. The identifier of a message is its **serial** on its channel, from one, so that a gap in the serials shows a hearer what it has not received.

### Communication time

The communication time is a number of seconds since 1970-01-01T00:00:00Z on the UTC time scale, every day counted as 86,400 seconds, with a decimal fraction where the sender states one. Offsets and relations in the content of a move are counted from it ([What a message means](meaning.md#time)).

## Numbers and their check words

A number is its numerals followed by its check word ([The grammar](grammar.md#numbers-and-names)). The check word's value is computed over the digits alone, the signs neither weighed nor counted:

> check = (Σ *dᵢ* × ((*i* mod 10) + 1)) mod 11, where *dᵢ* is the *i*-th digit counted from 0 at the left.

The eleven check words `yata`, `yabe`, `yagi`, `yano`, `yalu`, `yeka`, `yede`, `yemi`, `yeso`, `yeru` and `yiba` stand for the values 0 to 10. The time 1759622400 has the weighted sum 1·1 + 7·2 + 5·3 + 9·4 + 6·5 + 2·6 + 2·7 + 4·8 + 0·9 + 0·10 = 154, which is 0 modulo 11, so its check word is `yata`.

## The count and the move check word

Every move begins with *word count* and a count of the words of its body, its move check word included, a payload counting as one word. The move check word ends the body, and its value is computed over the body's other words:

> value = (Σ *cⱼ* × ((*j* mod (*p* − 1)) + 1)) mod *p*, where *j* counts the words from 1, *cⱼ* is the code of the *j*-th word, and *p* is the modulus.

A word's **code** is its position, counting from 1, in the release's list of critical forms ([`language/grammar.json`](../language/grammar.json), `critical forms`), and 0 for every other word, a payload or an unknown word among them. The critical forms are the words whose substitution would change a critical dimension silently: the members of the force and standing classes, the polarity, the comparators, the persons and readings of a collective, the times, the numerals and check words, the figurative types and embedded material, the roles, the kinds of reference and expected statuses, the structural words that point at participants, names, parts, messages and dialects, the units of measure, the connectives, the relations of a figure, the declaration *precision-bound*, the idiom mark, the act words and the registers. Lexicon 1.0 uses the first 235. Within a major version the list only grows, each new form appended at its end, so that no released word's code changes.

### The move check word

The move check word is the word whose value is the result. Its forms are five-symbol words opened by *h*, listed in [`language/grammar.json`](../language/grammar.json) in the order of their values, and the modulus is the number of forms. From major version 1 the modulus is the largest prime not above the number of admissible forms, the five-symbol words opened by *h* at a distance of three from every protected word, fixed with the first release of the major version: 346 forms are admissible, and the modulus is 337. A release of major version 1 may add critical forms while their number stays below the modulus less one.

<!-- generated: move-check-forms -->
```
  0  habal habew habot habub hadep hadum hagat hagon hahaw haheh
 10  hakam hakes hakup halet halog hamad hamem hamor hanan hanoh
 20  hanut hapek hapom hared haros harur hasar hasey hasip hasok
 30  hasud hatab hateg hatin hatuw hawen hawil hawow hawuh hayer
 40  hayop hebar hebey hebud hedah hedib hedog hedun hegak hegim
 50  hegos hehay hehik hehod hehum hekan hekiw hekoh hekut helap
 60  helus hemag hemen hemil hemuh henas hener henuk hepat hepeb
 70  hepon hepul hereg herin heruw hesaw hesug hetem hetis hetor
 80  hetuy hewam hewes hewir hewoy hewup heyot heyub hibaw hibeh
 90  hibit hibob hibug hidek hidid hidom higab higeg higol hihah
100  hihet hihib hihog hihun hiker hikuk hileb hilon hilul himes
110  himir himoy himup hinal hinew hinih hipak hiped hirad hirem
120  hiris hiruy hisay hisep hisod hisum hitag hitow hituh hiwel
130  hiwut hiyey hiyud hobep hobik hobod hobum hodat hodig hodon
140  hodul hogem hogis hogor hoguy hohap hohek hohom hohus hokih
150  hokot holak holim holos holur homan homiw homut honip honok
160  honud hopab hopin horen horow hoset hosib hosog hosun hotam
170  hotoy hotup hower howiy howuk hoyaw hoyit hoyug hubet hubog
180  hubun hudak huded hudim hudur hugag hugen hugil hugow huguh
190  huhat huhig huhon huhul hukok hukud huleg hulin hulol huluw
200  humas humer humop humuk hunaw hunob hunug hupis hures hurir
210  huroy hurup husap husek husom husus hutan hutel hutiw huwal
220  huwew huwot huwub huyay huyik huyod huyum hodeb helom hadik
230  hukey hetad halib hekel howop harim himam hahob hudos hopeg
240  hupem hipim hokub helid hunit hagig homoh hagul hupad higin
250  hageb hoyob hakir hupor hamis henop haday howas hiten hilat
260  hebip huwih hepig humiy holed heseh hipos horag higuw hosah
270  hukip hahit herol helek horuh hemow hobay hohid hayas hesob
280  hupuy hayuk hiror huyep hopuw hatol habih hopol halah hulab
290  homel hiyok harak herab hitil hikiy hebok hanel hokew hoyeh
300  hahug honar hinub hiwoh hipur hidap hiwan honey heged hadod
310  hapap hutut hidus hubah heyew hokal hogad hamuy hehep hikop
320  hubib horil hiyar halun hotes hinot hotir hawag hapus hilig
330  haniw hikas huheb hedet hisik heyal huram
```
<!-- end generated -->

Because the modulus is prime, the codes are distinct and below it, and every weight lies between 1 and *p* − 1, replacing a critical word by any other word, or any word by a critical one, changes the value. The move check word does not weigh content roots, which have the code 0; the integrity and semantic check values cover them.

In the conformance item `e8-acknowledgement.2`, the move `wila nake neno yede kanume kayoti kosiki wopi rosek biwo wodu laku nadi yagi wuwa bihu wodu raniy gona wuwa woko hawen` has the count 18 and seventeen words before its check word. The coded words are *issue* (code 5, weight 2), *request* (10, 3), *speaker's own* (39, 4), *actor* (152, 7), *party* (166, 9), the numeral two (121, 10), its check word (136, 11) and *undergoer* (153, 13); the weighted sum is 7,449, which is 35 modulo 337, and the move check word is the form of value 35, `hawen`.

A count that cannot be met is `d.parser.count-mismatch`, a last word that is not a move check word is the same, and a move check word of the wrong value is `d.parser.move-check-mismatch`.

### The unit check word

The envelope and the statement of a protocol message end in a **unit check word**, a number check word computed over the words between the unit's count and itself:

> value = (Σ *kᵢ* × ((*i* mod 10) + 1)) mod 11, where *i* counts the words from 0 and *kᵢ* is the word's code below.

A word takes its own code where it has one and its class's otherwise; a word with neither, such as a digit or a payload, adds 0 but still occupies its position.

<!-- generated: unit-check-codes -->
| Word or class | Code |
|---|---|
| `g.numbers.check-word` | 7 |
| `g.protocol.protocol-statement.holds` | 1 |
| `g.protocol.protocol-statement.send-again` | 2 |
| `g.protocol.protocol-statement.not-held` | 3 |
| `g.protocol.statement-part.channel` | 4 |
| `g.protocol.statement-part.serials` | 5 |
| `g.protocol.statement-part.entries` | 6 |
| `g.message.message-field` | 8 |
| `g.message.forwarded` | 8 |
| `g.numbers.numeral.decimal-point` | 9 |
| `g.numbers.numeral.negative` | 10 |
| `g.numbers.numeral.ratio` | 10 |
| `g.numbers.numeral.exponent` | 10 |
| `g.numbers.numeral.interval` | 10 |
| `g.protocol.protocol-statement.understands` | 1 |
| `g.protocol.protocol-statement.lacks` | 2 |
| `g.protocol.statement-part.language-version` | 4 |
| `g.protocol.statement-part.lexicon-version` | 5 |
| `g.protocol.statement-part.protocol-version` | 6 |
| `g.protocol.statement-part.lacking-features` | 3 |
| `g.structure.dialect` | 8 |
<!-- end generated -->

The statement words added in protocol 0.4 take the codes of words that cannot stand where they do, since all eleven residues are in use. In the envelope of `e8-acknowledgement.1`, the coded words weigh to 672, which is 1 modulo 11, so the unit check word is `yabe`. A mismatch is `d.parser.unit-check-mismatch`.

## The check values

A check value is a SHA-256 digest (FIPS 180-4) of a text, read as a big-endian integer, reduced modulo 10⁹ and written as a number of nine digits with zeros on the left:

> value = int(SHA-256(UTF-8(text))) mod 10⁹

The **integrity check value** is computed over the canonical serialisation of the message without the integrity check value's own field: the envelope's words, the authentication field included, as the first line, each move or the statement as a line of its own, words separated by one space and every line ended by a line feed. It detects any change in transit to any word the message carries. The **semantic check value** is computed over the message's normal text ([What a message means](meaning.md#the-normal-form)), and detects a change of meaning: two realisations of one meaning give one value. A reader compares the semantic check value only where the integrity check value matched or is absent.

A message must carry the integrity check value if it is a protocol message or if any of its moves is precision-bound, whether by its class, by declaration or by its register ([The grammar](grammar.md#precision-bound-moves)); its absence there is `d.checker.integrity-value-required`. A message of inert moves alone may omit it, and a writer should not: a message without it cannot show that it was cut between two of its moves, nor tell an unknown word from a damaged one. A mismatch is `d.check-values.integrity-mismatch`, after which the hearer asks for the message again, or `d.check-values.semantic-mismatch`. The analysis reports its confidence in the message as *verified* where the integrity check value matched, *lowered* where it did not, and *unchecked* where the message carried none.

The message `e8-acknowledgement.1`, its integrity field removed, has the SHA-256 digest `f973ed52…7a0a55`, whose value modulo 10⁹ is 106909781, the value its envelope states.

## Protocol messages

A protocol message is an envelope whose identifier and first entry are zero, followed by one **statement** in place of moves. It has one recipient, is not forwarded, carries the integrity check value, takes no serial on its channel and adds no entry; a protocol message that breaks one of these is `d.parser.protocol-message`. Every word of a statement is a fixed form, which every release reads alike, so a hearer reads a protocol message whatever release its envelope names.

| Statement | Form | What it says |
|---|---|---|
| holds | `lupe` | an acknowledgement: for each of the addressee's channels the sender is on, the last serial it holds with none missing before it, then each serial it holds beyond that |
| send again | `luki` | a request for messages by their channel and serials, or for entries of the addressee's by their numbers, whose content alone is asked for |
| not held | `ludo` | that what was asked for is no longer held |
| understands | `yiwu` | the language, lexicon and protocol releases the sender reads, the dialects it offers and the features it lacks ([Versions and features](#versions-and-features)) |
| lacks | `yoda` | one message of the addressee's, by its channel and serial, and what of its releases, dialects and features the sender lacks |

The statement is counted and checked as the envelope is. Its channels are named once each, by their recipients in ascending order; the serials a *holds* states beyond the first are ascending and beyond the first gap; the serials and entries of a *send again* or *not held* are ascending from one; and the versions and features of an *understands* are ascending. A statement out of order is `d.parser.statement-form`. The acknowledgement of `e8-acknowledgement.4`, `wila neno yeso lupe lumu nadi yagi yige namo yano yabe`, says that its sender holds the addressee's channel to participant 2 up to serial 3, with none missing.

## Channels, acknowledgement and repair

Four rules keep the participants of an exchange in step:

1. **A sender keeps each message open until each addressee acknowledges it.** It sends the message again, byte for byte, each time the interval before sending again passes without an acknowledgement, up to the times stated, and then records the addressee as not having acknowledged it. An acknowledgement that states the message held closes it.
2. **Every addressee acknowledges a sender** once its quiet interval has passed since the first message it received from that sender after its last acknowledgement, stating what it holds of each of the sender's channels it is on. A participant may declare its own quiet interval toward another by committing to acknowledge within a duration; a participant cannot bind another to one.
3. **A hearer asks for what it knows it lacks**: each serial missing or damaged on a channel it is on, and each entry it holds reduced. It asks at once, again after each interval before sending again, up to the times stated, and then records the loss. A sender asked for what it holds sends it again byte for byte; asked for what it no longer holds, it answers *not held*, and both record the loss.
4. **A participant that forgot holds what it lost reduced**: the handle, kind and status of each entry, without its content, so that "I no longer hold your entry" and "I never received your message" are different reports with different remedies.

<!-- generated: repair-defaults -->
| Default | Value |
|---|---|
| the quiet interval, after which an addressee acknowledges | 30 seconds |
| the interval before a message or a request is sent again | 120 seconds |
| the times a message or a request is sent again | 4 |
<!-- end generated -->

A message that arrives damaged is not applied, and is asked for again like a gap. A message applied before is not applied again, so each operative move takes effect at most once, and a different message under a serial already held is refused ([The record and discourse](discourse.md#how-a-participant-receives-a-message)). A protocol message is not acknowledged, since it takes no serial. A fork, a new participant made from another, has its own identity, states its lineage in its first message and acknowledges each channel of its origin's that it inherits. A report in the language of a message never received names the message by its serial ([The grammar](grammar.md#references-and-targets)).

The canonical Python implementation provides these rules as a participant in [`python/rowih/repair.py`](../python/rowih/repair.py).

## Authentication

A message may be signed. The authentication field states a scheme, the signature's length in bytes and the signature as a payload.

<!-- generated: authentication-schemes -->
| Scheme | Name | Specification | Signature bytes | Public key bytes |
|---|---|---|---|---|
| 1 | Ed25519 | RFC 8032 § 5.1, pure Ed25519 | 64 | 32 |
<!-- end generated -->

The signature covers the canonical serialisation of the message without its authentication and integrity check value fields, so it covers the sender, the time and the semantic check value. The integrity check value is computed after the signature and covers it, so a signature damaged in transit fails the integrity check, while a forgery passes it and fails verification. A field whose scheme is unknown or whose signature has another length is `d.parser.authentication-form`.

The language references authentication and does not provide keys: a participant holds the public keys of the agents it knows from its own configuration, never from a message. A participant that holds a key for a message's sender refuses the message unless it verifies, `d.view.authentication-failed`, and does not take its serial as held, so a forgery cannot displace the genuine message. A participant without a key for the sender verifies nothing, and a claim of provenance then carries no weight beyond what it can check. Authentication is a may-ignore feature: a reader without it passes over the field and still tells damage by the integrity check value. Verification needs the `authentication` extra of the Python package.

## Relaying

A participant relays a message by asserting, on the basis of report, that its sender sent it, with the sender as source and itself as relayer, and carrying the message byte for byte, final line feed included, as declared data of the language's own media type. The relay is the relayer's own report and is inert however imperative what it carries; a hearer that holds the original sender's key, and finds that the carried message verifies by it, also receives the carried message as that sender's, at most once. A participant may relay a position instead, reporting that its author holds it, with the author's assertion carried whole and its deixis and times made absolute. A relay of a relay nests nothing.

A message marked *forwarded* is not applied, `d.view.forwarded`: its envelope names no speaker but its sender, so forwarding is done by relaying.

## Versions and features

The envelope names the releases a message is written in, and a reader reads a message only under releases it holds.

<!-- generated: reads -->
| Release | Reads the messages of | Least lexicon |
|---|---|---|
| language 1.0 | 1.0 | 1.0 |
| protocol 0.5 | 0.5 |  |
<!-- end generated -->

From major version 1, a language release reads every earlier release of its major version, with the meaning each gave its messages, and a message of a language release names a lexicon release no earlier than the release's least lexicon. A reader that lacks a release, a dialect or a feature a message names reports `d.parser.version-unknown` and interprets none of the message; a message whose lexicon is earlier than its language admits, or than a dialect it names was formed from, is `d.parser.version-pairing`.

A **feature** is a mechanism added after the first release, which a reader may lack. A word belongs to a feature by its class, its own identifier or the grammatical category of its lexicon entry, and a conventional sense where a frame selects it. A reader lacking a **may-ignore** feature passes over its words in a move's head and keeps a word of it standing as content opaque; a reader lacking a **must-understand** feature rejects every move that uses it, `d.parser.feature-lacking`.

<!-- generated: features -->
| Number | Feature | Flag | Since protocol | Why |
|---|---|---|---|---|
| 1 | time spans | must-understand | 0.2 | an interval's end, a time |
| 2 | act words | must-understand | 0.5 | a word that stands for force values |
| 3 | idioms | must-understand | 0.5 | an expression whose meaning is its entry's expansion |
| 4 | declared losses | may-ignore | 0.5 | a record of the social and textual component, which the normal form sets aside |
| 5 | registers | must-understand | 0.6 | two registers make a move precision-bound |
| 6 | politeness words | may-ignore | 0.6 | a record of the social and textual component, in a move's head |
| 7 | dictions | may-ignore | 0.6 | a record of the social and textual component, in a move's head; a diction written as a term's content word is content, which a reader lacking it keeps opaque |
| 8 | conventional senses | must-understand | 0.7 | a sense shares its root's form, so a reader lacking it would read the root literally |
| 9 | mention by serial | must-understand | 0.9 | what a reference names |
| 10 | authentication | may-ignore | 0.9 | the integrity check value covers the signature, so a reader that passes over it still tells damage; it verifies nothing, as a reader without the sender's key |
| 11 | dialects | must-understand | 0.10 | a dialect form means its expansion only to a reader holding its dialect |
<!-- end generated -->

Two agents settle the releases they share with *understands* and *lacks*. Each states, in *understands*, the releases it reads, the dialects it offers and the features it lacks; their common subset is the latest language, protocol and lexicon releases both read, the lexicon no earlier than that language's least lexicon, every dialect both offer under one digest and formed from no later lexicon, and every feature either lacks. Each writes to the other within the common subset. A hearer that cannot interpret a message states, in *lacks*, which message and what it lacks of it, and the speaker restates its moves within the common subset, or both record the loss. A message in a release the hearer lacks is still acknowledged.

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

Every register of protocol 0.5 declares these values ([The grammar](grammar.md#the-maxima)). A new protocol release computes them again; a release that keeps its protocol keeps them.

## The forms of a message in transport

A message in the transliteration uses the nineteen letters of the phonology outside payloads, the lowercase letters and the digits 2 to 7 inside payloads, and the separators space, tab, line feed and carriage return, in UTF-8. A writer writes the canonical serialisation; a reader accepts any run of separators between words, recomputes the canonical serialisation from what it parsed, and so is unaffected by a transport that changes line endings, expands tabs or collapses spaces. A transport that breaks a word, by wrapping it or escaping it, changes a count and is detected. The native digital form writes each symbol as its code point in the Private Use Area, U+F3A0 to U+F3B2, three bytes in UTF-8, with payloads, separators and lines as in the transliteration; a text using that range is read as the language only if it parses, and any other use of the range is reported as foreign use ([The writing system](writing-system.md)).

A **payload** is the base-32 encoding of RFC 4648 § 6 in lower case without padding, of (8 × *bytes* + 4) div 5 characters, preceded by its length in bytes as a number; a reader ignores separators within it and decodes exactly the stated length. A payload that is short, long or not canonical is `d.lexer.payload-short`, `d.lexer.payload-long` or `d.lexer.payload-character`. **Declared data** within a wall is its media type, as a payload of the form RFC 6838 § 4.2 gives (`d.parser.media-type` otherwise), then its data as a payload; a reader never parses declared data as the language, so it is inert by kind. A quoted or relayed message travels as declared data of the language's media type.

## The media type and the binding to agent transports

The media type of a Rowih message is `text/prs.rowih`, in the personal tree of RFC 6838 § 3.3. Its charset is always UTF-8, and it has one parameter, `encoding`, with the values `transliteration`, the default and the form of the canonical serialisation, and `native`. A message states its own version, so the type has no version parameter. An agent declares that it accepts or produces Rowih by listing the media type where its transport lists media types.

When a message travels within another protocol, the message's own fields govern: a field of the transport is checked against them and never read in their place.

- **Agent2Agent.** The message is the text of a part, `Part.text`, whose `Part.mediaType` is the media type with its `encoding` parameter; `Message.messageId` is a string the sender makes that carries the message's channel and identifier; `Message.role` follows the direction of the call and is never read as the sender; and an agent card lists the media type in its default input and output modes. A task's state follows the entries in the record that correspond to it, and three distinctions the record keeps have no state of their own in Agent2Agent: a proposed and an assigned task, an accepted task and one in progress, and an abandoned task and a refused one. The party responsible, the authority claimed and each party's acceptance travel only in the language.
- **The Model Context Protocol.** The message is an embedded resource whose `text` is the message, whose `mimeType` is the media type with its `encoding` parameter, and whose `uri` is a URI the sending agent controls that names the message. That protocol has no state of a task, so the record travels only in the language.

The field names are those of the Agent2Agent specification as published on 2026-10-03 and of the Model Context Protocol's schema of revision 2025-06-18, against which the binding was written; a later revision of either may rename them.

An export of a message to another format is a view, marked with the encoding it was made from; no reader parses an export as the language.
