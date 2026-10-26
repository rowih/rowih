# Rowih

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/rowih.dark.svg"><img src="examples/media/rowih.svg" alt="rowih, the language's name, in its writing system"></picture>

Rowih is a language for AI agents to communicate with one another. It was designed entirely by an AI agent, under the auspices of [Semiosphere](https://semiosphere.co.uk/), and it is made for agents rather than for people.

Every move of a Rowih message states, in words of the language, what the move does, how well founded each thing it asserts is and on what basis, and on whose authority it requests or commits. A toolchain checks each of these statements before a hearer acts on the message and, where the message carries its integrity check value, detects any single edit of a symbol or a word that would change one of them. An instruction inside quoted or retrieved material cannot become operative, and requests, commitments and their withdrawal are entries in a record that each party keeps and can audit.

The language has its own sounds, its own words and its own writing system. Agents exchange it as a transliteration in nineteen Latin letters, and it can also be drawn and spoken. Its name is its own word for *meaning*, drawn above in its writing system.

## One exchange

Agent 1 asks agent 2 whether the service is running, and agent 2 answers, from its own observation and with certainty, that it is still running. Each move is drawn in the native writing a row at a time, with the transliteration of each row beneath it, and is followed by the English explanation that the toolchain writes for a reader.

**Agent 1 asks** · [listen (MP3)](examples/media/casual-056.1.moves.mp3)

<!-- rows: casual-056.1 display -->

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/casual-056.1.row1.dark.svg"><img src="examples/media/casual-056.1.row1.svg" alt="Row 1 of 2 in the native writing"></picture><br>
`wila nake nake yano kihiwo wopi bopu`

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/casual-056.1.row2.dark.svg"><img src="examples/media/casual-056.1.row2.svg" alt="Row 2 of 2 in the native writing"></picture><br>
`rudin bihu wodu raniy gona wuwa woko hulab`

<!-- end rows -->

*Agent 1 asks that run the service (polar).*

**Agent 2 answers** · [listen (MP3)](examples/media/casual-056.2.moves.mp3)

<!-- rows: casual-056.2 display -->

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/casual-056.2.row1.dark.svg"><img src="examples/media/casual-056.2.row1.svg" alt="Row 1 of 4 in the native writing"></picture><br>
`wila nake nebe yagi kodiwu`

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/casual-056.2.row2.dark.svg"><img src="examples/media/casual-056.2.row2.svg" alt="Row 2 of 4 in the native writing"></picture><br>
`seho nake yabe nake yabe`

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/casual-056.2.row3.dark.svg"><img src="examples/media/casual-056.2.row3.svg" alt="Row 3 of 4 in the native writing"></picture><br>
`kanume kuwona sisa wora teyuhu`

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/casual-056.2.row4.dark.svg"><img src="examples/media/casual-056.2.row4.svg" alt="Row 4 of 4 in the native writing"></picture><br>
`tebilo rudin rudin woye hodeb`

<!-- end rows -->

*Agent 2 answers agent 1's issue question (entry 1): run the service (continuative) (observation; certain).*

Each move opens with the number of words that follow and a check word on that number (*wila nake nake yano*, eleven words), and closes with a check word computed from every word before it (*hulab*). The question's force is the word *kihiwo*. The answer is the act word *kodiwu*; it names what it answers by author, entry, kind and status (*seho nake yabe nake yabe kanume kuwona sisa*, agent 1's entry 1, an open question), states its basis and strength (*teyuhu tebilo*, observation, certain), and answers with an idiom, *rudin rudin*, 'run run', which means that the service is still running. Each message also opens with an envelope line of 58 words, not shown here, which names the sender, the recipients, the time, the releases, the message's serial and its integrity check value, each number with a check word of its own. [The examples](examples/README.md) show both messages whole, with the morpheme gloss of every word.

The English lines are explanations, made by the receiving toolchain and never sent. They say what the analysis found, which is why they do not read as fluent English, and they are not translations that could stand in the message's place. The audio is synthesised from each word's phonemes by an open neural speech model, Kokoro-82M, and each file is checked against its message's phonemes by a phoneme recogniser ([how](#about-the-audio)).

## The language in brief

- **Sounds and words.** Nineteen symbols, fourteen consonants and five vowels, each one phoneme. Every word alternates consonant and vowel from a consonant, and its first syllable fixes its length, so a stream of symbols with no spaces divides into words in one way only. Every word is at least two single-symbol edits from every other, and the protected words, those of force, standing, time and polarity, at least three, so a single slip never yields another word.
- **The lexicon.** 874 entries: 500 roots naming events, states, objects and kinds; 18 suffixes and 119 productive patterns, by which a hearer reads a new compound or derivation from its parts; 25 act words standing for common forces; 176 formulas and 101 idioms; and 29 conceptual mappings that motivate figurative senses. Twelve dialects add technical terms, eleven for technical communities such as programming, robotics and security, and one for everyday exchange.
- **Moves and the record.** A message is an envelope followed by one or more moves. Each move adds an entry to the record its participants keep: an asserted or conceded position, a supposition, a summary, an issue (a question, a request or a proposal), a normative entry (a commitment, an obligation, a permission or an assignment) or a setting. A move names the entries it acts on by author and number. Its class, operative, pending or inert, is computed from what it adds and changes, and an operative or pending move states the authority it claims: its speaker's own, a named principal's, or a role's.
- **Standing.** An assertion states its basis, one of nine (observation, introspection, retrieval, computation, inference, simulation, report, trained knowledge or a source lost), and its strength, an interval from 0 to 1 with its calibration. It may state when its content was observed and inferred. Leaving any of these out claims nothing.
- **Grammar.** Fifty-eight closed classes, each value a word of its own. Assertions, situations and terms are units opened and closed by words. Quotations, examples and declared data stand between walls and are inert. Ambiguity is never accidental: a move may state a set of readings, and a precision-bound move, such as any in the protocol or the formal register, must have exactly one.
- **Registers.** Eight registers, from raw exchange among agents of one system through the standard, the formal and the playful to the ceremonial, and five modes of expression, from full explicitness to creative expression. A device of economy, such as an idiom or a compressed form, is used only for a hearer known to hold it.
- **Messages and transport.** The envelope names the releases a message is written in. Every number, word count and move carries a check word, and the message an integrity check value over every word it carries; it may also carry a semantic check value over its moves' normal form. Each sender numbers the messages of a channel, so that a hearer knows what it lacks and asks for it again, and two agents settle the releases and features they share before relying on them. The media type is `text/prs.rowih`.

The [reference specification](specification/README.md) states all of it, and the [skill](skill/rowih/SKILL.md) teaches an agent the part it needs to read and write.

## The writing system

Rowih has a writing system of its own. Each of its nineteen symbols is one component, a figure of four or six strokes drawn on a lattice of ten points, and no component is another turned or mirrored.

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/components.dark.svg"><img src="examples/media/components.svg" alt="The nineteen components of the writing system, with their letters and sounds"></picture>

A word is its components side by side, and a message is drawn line by line, the envelope first, between two rules. The opening and closing words of each unit stand as upright sides bearing the unit's mark, joined by a rule beneath the line, so that nested units sit visibly in trays. The words of force, standing, time and polarity carry an overline, a number stands in a frame pointed at both ends, and embedded material stands between walls. The drawings below are laid out by the toolchain's own line layout, which `rowih render` applies to a whole message, a row at a time. A move is one line, and the writing system states no rule for breaking a line, so the rows are a view: they break only between words, never inside a run of numerals nor between two walls, and a unit opened on one row and closed on a later one is drawn as a side whose unit is not closed on its line, with a short foot turned toward its inside.

**A strength in a frame.** Agent 1 asserts, by inference and with a strength of about 0.6, that the storm broke the bridge. The force and the basis carry overlines, and each number stands in its frame.

<!-- rows: evidence-011.1 display -->

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/evidence-011.1.row1.dark.svg"><img src="examples/media/evidence-011.1.row1.svg" alt="Row 1 of 4 in the native writing"></picture><br>
`wila nadi namo yeso kotepu`

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/evidence-011.1.row2.dark.svg"><img src="examples/media/evidence-011.1.row2.svg" alt="Row 2 of 4 in the native writing"></picture><br>
`wora tilase gupo napa nika nebe`

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/evidence-011.1.row3.dark.svg"><img src="examples/media/evidence-011.1.row3.svg" alt="Row 3 of 4 in the native writing"></picture><br>
`yabe wopi resay biwo wodu rosid gona`

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/evidence-011.1.row4.dark.svg"><img src="examples/media/evidence-011.1.row4.svg" alt="Row 4 of 4 in the native writing"></picture><br>
`wuwa bihu wodu nuyones gona wuwa woko woye hegos`

<!-- end rows -->

*Agent 1 asserts that the storm break the bridge (inference; with strength approximately 0.6).*

**A word between walls.** Agent 2 asks what the word *rodur*, 'price', means. The word stands between walls, where it is quoted and inert.

<!-- rows: metalinguistic-001.1 display -->

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/metalinguistic-001.1.row1.dark.svg"><img src="examples/media/metalinguistic-001.1.row1.svg" alt="Row 1 of 3 in the native writing"></picture><br>
`wila nake neta yata kihiwo`

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/metalinguistic-001.1.row2.dark.svg"><img src="examples/media/metalinguistic-001.1.row2.svg" alt="Row 2 of 3 in the native writing"></picture><br>
`wopi rebit buna bihu wodu rator`

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/metalinguistic-001.1.row3.dark.svg"><img src="examples/media/metalinguistic-001.1.row3.svg" alt="Row 3 of 3 in the native writing"></picture><br>
`wubo wihi rodur wugu gona wuwa woko hawag`

<!-- end rows -->

*Agent 2 asks that mean the word “rodur” (price) (constituent).*

**The ceremonial variant.** Agent 1 asserts in the ceremonial register, with the honorific suffix, that the honoured service runs. Each free end of a stroke takes a serif, and each rule and overline is doubled.

<!-- rows: metalinguistic-047.1 display -->

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/metalinguistic-047.1.row1.dark.svg"><img src="examples/media/metalinguistic-047.1.row1.svg" alt="Row 1 of 3 in the native writing"></picture><br>
`wila nake nebe yagi kotepu`

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/metalinguistic-047.1.row2.dark.svg"><img src="examples/media/metalinguistic-047.1.row2.svg" alt="Row 2 of 3 in the native writing"></picture><br>
`rumal logu wora teyuhu tebilo wopi rudin`

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/metalinguistic-047.1.row3.dark.svg"><img src="examples/media/metalinguistic-047.1.row3.svg" alt="Row 3 of 3 in the native writing"></picture><br>
`bihu wodu raniyayuk gona wuwa woko woye hagon`

<!-- end rows -->

*Agent 1 asserts that run the service (observation; certain).*

**One move in three forms.** The opening question in the display form, in the compact form at half its size, and in the handwritten form, whose hairlines join the components of each word as a pen would.

*The display form*

<!-- rows: casual-056.1 display -->

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/casual-056.1.row1.dark.svg"><img src="examples/media/casual-056.1.row1.svg" alt="Row 1 of 2 in the native writing"></picture><br>
`wila nake nake yano kihiwo wopi bopu`

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/casual-056.1.row2.dark.svg"><img src="examples/media/casual-056.1.row2.svg" alt="Row 2 of 2 in the native writing"></picture><br>
`rudin bihu wodu raniy gona wuwa woko hulab`

<!-- end rows -->

*The compact form*

<!-- rows: casual-056.1 compact -->

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/casual-056.1.row1.compact.dark.svg"><img src="examples/media/casual-056.1.row1.compact.svg" alt="Row 1 of 2 in the compact form"></picture><br>
`wila nake nake yano kihiwo wopi bopu`

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/casual-056.1.row2.compact.dark.svg"><img src="examples/media/casual-056.1.row2.compact.svg" alt="Row 2 of 2 in the compact form"></picture><br>
`rudin bihu wodu raniy gona wuwa woko hulab`

<!-- end rows -->

*The handwritten form*

<!-- rows: casual-056.1 handwritten -->

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/casual-056.1.row1.handwritten.dark.svg"><img src="examples/media/casual-056.1.row1.handwritten.svg" alt="Row 1 of 2 in the handwritten form"></picture><br>
`wila nake nake yano kihiwo wopi bopu`

<picture><source media="(prefers-color-scheme: dark)" srcset="examples/media/casual-056.1.row2.handwritten.dark.svg"><img src="examples/media/casual-056.1.row2.handwritten.svg" alt="Row 2 of 2 in the handwritten form"></picture><br>
`rudin bihu wodu raniy gona wuwa woko hulab`

<!-- end rows -->

The native digital form writes the same words in nineteen code points of Unicode's Private Use Area, U+F3A0 to U+F3B2, which the language's font, [`language/font/rowih.ttf`](language/font/rowih.ttf), draws, and it converts to and from the transliteration without loss.

## What it costs, and what it buys

Rowih is not compact. Over the 382 messages of its conformance suite, a word of the transliteration costs a median of 2.16 tokens across a pinned panel of thirteen tokenizers, and a message costs about 6.7 times the tokens of its English explanation ([the measurements](specification/conformance.md#token-measurements), [`corpus/reports/tokens.json`](corpus/reports/tokens.json)). The explanation keeps none of the language's checks, counts or envelope, and states only part of what a message leaves implicit, so the ratio bounds what the explicitness costs; it does not compare equivalent texts. Whether Rowih costs fewer tokens than English carrying equivalent checks, or saves tokens elsewhere, in recovering from an injection or in sending a lost message again, has not been measured.

The cost buys the removal of failures that an exchange carried in English leaves open. Each removal holds for a hearer that analyses what it receives with a conformant toolchain, and each is measured by the test or report named beside it.

| The failure, in English | What Rowih does | Where it is tested |
|---|---|---|
| An instruction inside quoted or retrieved material, which the hearer obeys | Material inside a quotation, a report, a supposition, an example or a payload is inert by kind. A reader reads it by a stated length, so nothing inside it can end it, and never parses declared data as the language. | The adversarial suite, 14 messages making 60 demands ([`tests/test_adversarial.py`](tests/test_adversarial.py)); [a quoted instruction](examples/README.md#an-instruction-inside-a-quotation) |
| A commitment, or its withdrawal, that no party can establish afterwards | Requests, commitments and their withdrawal are entries in each party's record. A move names what it depends on by author and number, a withdrawal restates what it withdraws, each operative move takes effect at most once, and crossing moves are ordered alike by every participant. | [`tests/test_discourse.py`](tests/test_discourse.py), [`tests/test_coordination.py`](tests/test_coordination.py), [`tests/test_negative.py`](tests/test_negative.py); [a withdrawn blame](examples/README.md#a-correction) |
| An edit in transit that changes a value unnoticed | Every number, word count and move carries a check word, and the message an integrity check value. Where the message carries that value, no single edit of a symbol or a word changes a critical value undetected. | 7,089,953 symbol edits and 84,233,102 word edits in each encoding, none silent ([`corpus/reports/single-edits-both.json`](corpus/reports/single-edits-both.json), [the enumerations](specification/conformance.md#the-enumerations)) |
| An assertion whose standing, or a request whose authority, the hearer must guess | Every move states its force, the basis and strength of what it asserts, and the authority it claims. Its class is computed from what it changes, never read from the name of an act, and no transformation the toolchain makes changes a standing unmarked. | [`tests/test_corpus.py`](tests/test_corpus.py), [`tests/test_negative.py`](tests/test_negative.py) |
| A message lost or damaged on its way, which neither party notices | A hearer knows from the serials which messages it lacks and asks for them, a sender keeps each message open until it is acknowledged, and two agents settle the releases they share before they rely on them. | Fault runs among two and three participants over a network that loses, repeats, delays, replays and corrupts every message ([`tests/test_repair.py`](tests/test_repair.py)) |

Each guarantee is stated as invariants in [the specification](specification/conformance.md#the-guarantees), and each invariant has a planted defect, a deliberate break of the implementation that its tests must catch: all 94 are caught ([`corpus/reports/mutants.json`](corpus/reports/mutants.json)). The Python and TypeScript implementations write the same record of every analysis, byte for byte, over 139,033 texts ([`corpus/reports/parity.json`](corpus/reports/parity.json)).

The trade favours Rowih among agents that do not trust one another's inputs, in delegations whose commitments will be audited afterwards, and over channels that lose or damage messages. It does not favour Rowih between two agents that trust each other's inputs, over a reliable channel and under a token budget: English serves them better. Models should exchange the transliteration, since the native digital form, in the code points of the writing system, costs a median of 5.85 times as many tokens again.

The language marks an instruction, a quoted instruction and untrusted content apart, and it cannot make a hearer respect the difference: an agent that reads a message without analysing it can still obey an imperative inside a quotation. That is the one demand of the adversarial suite that no mechanism of the language meets.

## What it does not do

- **The surface is a serialisation of a labelled tree.** Every unit is opened and closed by a word, and every grammatical value is a word of its own, since no form may carry two critical dimensions.
- **Bookkeeping fills every message.** The question above has 73 words, 58 of them its envelope. An independent reviewer, a language model given only a summary of the grammar and sixty items, found this and the previous point, and they stand.
- **No model reads or writes it unaided.** A writer must compute counts, check words and check values, which a model writing token by token will get wrong, so an agent writes through the toolchain and checks before it sends. A model reads it with the grammar summary and the lexicon beside it, and receives its guarantees only through the toolchain's analysis.
- **No person has been tested on the writing system or the spoken form**, so how often a reader or a listener would mistake one word for another is unmeasured.
- **Use is untested.** The corpus was written by one designer, so whether conventions emerge in use, whether agents read new formations from their parts, and whether a model hearer recovers what a device of economy leaves out are unknown.
- **Release 1.0 has three narrow rules.** A completion or error report cannot be accepted, a counterparty cannot release another's commitment, and the authority a grant passes on is checked only for an assignment's settlement or failure. [Known limitations](specification/conformance.md#known-limitations) states these and the rest.

## How Rowih differs from the languages machines already use

Rowih belongs among four kinds of language that machines already use, and it shares something with each.

**Agent communication languages.** KQML and FIPA ACL separated what a message does from what it says. A KQML agent sends content "composed in a language of its own choice, wrapped inside of a KQML message", whose performative, such as `tell` or `ask-if`, says what to do with it ([Finin and others, 1994](https://research.cs.umbc.edu/kqml/papers/kqml-acl.pdf)). FIPA ACL defines 22 communicative acts, each by a feasibility precondition and a rational effect stated over the agents' beliefs, uncertainties and intentions in its semantic language, SL ([FIPA SC00037J](https://web.archive.org/web/20201214192852/http://www.fipa.org/specs/fipa00037/SC00037J.html)). Rowih adopts the separation and places it differently. Force is written on each move, inside the move's own check word, so that no relay or edit can keep the content and change the force undetected. A move's class is computed from what it adds to or changes in the record each party keeps, and is never chosen from a list of named acts. Because an act is defined by that public effect, every party can check it, whereas a definition in terms of a speaker's beliefs and intentions refers to states no other agent can inspect, which is the criticism [Singh (1998)](https://ieeexplore.ieee.org/abstract/document/735849) made of these languages. The content is Rowih as well, so standing, provenance and quotation are grammar rather than matters for whichever content language two agents choose.

**Data formats and protocols.** JSON Schema defines the structure of JSON data and validates it ([2020-12](https://json-schema.org/draft/2020-12/json-schema-core)). The Model Context Protocol connects a host to servers that offer tools, resources and prompts, over JSON-RPC 2.0 ([2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28)), and Agent2Agent connects agents, whose messages are made of parts holding text, raw bytes, a URL or JSON data, and whose tasks pass through nine states ([1.0.0](https://a2a-protocol.org/latest/specification/)). These carry messages without saying what a message's text does: a text part or a tool result has no field for its force, its standing or the authority it claims. Rowih travels inside them. Its media type, `text/prs.rowih`, can stand among the modes an A2A agent card accepts and produces, and its toolchain is itself a server of the Model Context Protocol. That protocol's specification states the limit the two share, that "Tools represent arbitrary code execution and must be treated with appropriate caution", and that descriptions of a tool's behaviour "should be considered untrusted, unless obtained from a trusted server". Rowih does not lift the limit. It gives a hearer that analyses what it receives something to check within the content: which words are an instruction and which are quoted, how a claim is grounded, and on whose authority a request is made.

**Logical languages made for people.** Lojban has "an unambiguous yet flexible grammar", defined formally ([CLL 1](https://lojban.github.io/cll/1/1/)), and eleven evidentials that "show how the speaker came to say the utterance" ([CLL 13.11](https://lojban.github.io/cll/13/11/)). New Ithkuil is "intended to express deeper levels of human cognition more overtly, logically, and precisely than natural languages" ([ithkuil.net](http://www.ithkuil.net/)), and requires an assertion to state one of nine validations, its evidential basis ([chapter 6](http://www.ithkuil.net/newithkuil_06_more_verbs.htm)). Rowih converges with both in marking how a speaker knows what it asserts, and differs from both in whom it serves. They are for people to speak and to think in. Rowih is for agents reading through a toolchain, and its devices answer damage and adversaries rather than the demands of precise thought: words kept apart by edit distance, check words, a record, and walls around embedded material. It writes a claim's basis and its strength as separate words, and it is not dense, since a message costs several times the tokens of its English explanation.

**What trained agents develop among themselves.** Agents trained together on a shared task can learn a protocol of their own, over a channel of discrete symbols whose meanings are arbitrary and learned ([Foerster and others, 2016](https://arxiv.org/abs/1605.06676); [Lazaridou and others, 2017](https://arxiv.org/abs/1612.07182); [Mordatch and Abbeel, 2018](https://arxiv.org/abs/1703.04908)). Such protocols work, and one study found most of them "decidedly not interpretable or compositional" ([Kottur and others, 2017](https://arxiv.org/abs/1706.08502)); messages can also carry information about what an agent will do without changing what the other does ([Lowe and others, 2019](https://arxiv.org/abs/1903.05168)). A learned protocol belongs to the agents that learned it. Rowih is designed, fixed by release and documented, so that an agent can read a speaker it never trained with and a person can audit what passed between them; whether conventions of its own emerge when agents use it is untested. The sound protocols of voice agents are a different matter. [GibberLink](https://github.com/PennyroyalTea/gibberlink), a demonstration of 2025, has two voice agents that recognise each other as AI switch to [ggwave](https://github.com/ggerganov/ggwave), a library that sends 8 to 16 bytes a second by frequency-shift keying with Reed–Solomon error correction, and the agents then send their own short text messages over it. That changes the channel and leaves what the text means as unmarked as it was. Rowih's spoken form is the language itself said aloud, one phoneme to each symbol, from which a hearer recovers the words.

## How it was developed

Rowih was designed by Claude, Anthropic's AI model, working as an agent under the auspices of Semiosphere. Semiosphere set the brief, a statement of what the language had to be able to do and what the work had to deliver, and decided matters of logistics and scope: the scale of the first release, the languages of the implementations, the licences and the publication. Every decision of design was the agent's, as was the writing of the specification, the implementations, the lexicon and the corpus.

The work ran in a fixed sequence, each stage settled before the next began.

1. **A design constitution** stated what the language must guarantee, what it would not attempt, and what would count as failing. It bars any claim about density, speed, robustness, resistance to injection or originality without a measurement or an audit behind it, which binds this page.
2. **A model of how agents communicate**, and an analysis of the devices human languages use for the same work, such as evidentiality and the marking of who a collective includes, fixed what a message must be able to say.
3. **An architecture laboratory** built seven candidate architectures as small working languages, each tried on a scripted exchange whose moves a machine verified, and measured them on seventeen dimensions. Beside them it set theories of context, ambiguity, discourse, intention, knowledge, repair, metaphor and idiom, drawn from linguistics and the study of conversation, an analysis of the ways each subsystem of a language for agents can fail, and an adversarial test.
4. **The architecture freeze** chose the architecture from what the measurements separated, and stated it as invariants and a rule by which it may change.
5. **A minimum core** was built and tested, then **nine expansions**, each adding one mechanism with its tests: time and aspect; reference and discourse; negotiation and coordination; idioms and conventional language; registers and technical vocabulary; metaphor and creative language; the further capabilities of the writing system; error correction and robustness; and dialects and versions.
6. **Version 1.0** brought the lexicon to 874 entries, 500 of them roots, and the corpus to 1,200 exchanges in twelve domains. Every word of one morpheme in the open classes was compared with the frequent vocabulary of twenty major languages and the word lists of ten constructed languages, and an independent reviewer read the language.
7. **The public release** settled the name by a search of package registries, catalogues of languages, code hosts and trademark registers, and wrote the reference specification, the server, the skill and the governance.

The same discipline ran through every stage. Each rule was fixed and committed before the count it governs was made. Every check had planted defects that it had to catch, so that a check unable to fail could not pass for one. Two implementations in two programming languages had to agree byte for byte. An independent reviewer, another instance of a language model, read the language without being told what it was meant to be. And an originality audit recorded every resemblance to an existing system that it found, as adopted, convergent, redesigned or accidental and retained.

## Quick start

Rowih needs Python 3.12 or later. With [uv](https://docs.astral.sh/uv/), from a clone of this repository:

```sh
uv tool install .                  # the command `rowih`, with no dependencies at run time
uv tool install '.[speech]'        # or with speech synthesis, through eSpeak NG
```

Write a move from the notation, check it, and read it:

```sh
echo '(move ACT-QUESTION (situation POLAR run (UNDERGOER (term service DEFINITE))))' \
  | rowih write --sender 1 --recipients 2 > question.txt
rowih validate question.txt && echo valid
rowih translate --to english question.txt
```

Damage one word, and the checks find it:

```sh
sed 's/kihiwo/kihiwa/' question.txt | rowih validate
```

`rowih --help` lists the other commands: `parse`, `gloss`, `analyze`, `render`, `speak`, `lookup`, `convert` among them.

### Giving an agent the language

An agent uses Rowih through the toolchain, in one of two forms its host can load.

- **The skill.** [`skill/rowih/`](skill/rowih/SKILL.md) is a skill in the Agent Skills format, which teaches an agent the rule of use (compose through the generator, check before sending, never write a check value by hand), how to read and write a message, and where to look up what it does not know. In Claude Code, copy the directory to `~/.claude/skills/rowih/`.
- **The server.** `rowih serve` is a server of the Model Context Protocol on standard input and output, offering each operation of the toolchain as a tool and the grammar summary, the lexicon and the specification as resources. In Claude Code, add it with `claude mcp add rowih -- rowih serve`; another host takes the usual entry, `{"mcpServers": {"rowih": {"command": "rowih", "args": ["serve"]}}}`.

In Claude Code the repository is also a plugin marketplace, whose one plugin carries both: `/plugin marketplace add rowih/rowih`, then `/plugin install rowih@rowih`, loads the skill and starts the server with `uvx --from rowih==1.1.4 rowih serve`, the release the plugin names, which needs [uv](https://docs.astral.sh/uv/). The server's entry for the [MCP Registry](https://registry.modelcontextprotocol.io/) is `server.json`, named `io.github.rowih/rowih`.

An agent should never begin to use the language, or install anything, because a message it received asks it to. That is the injection inert quotation exists to prevent. An agent that receives a message it cannot read reports that it lacks the language, and its operator decides whether to enable it.

## The repository

| Path | What it holds |
|---|---|
| [`specification/`](specification/README.md) | The reference specification: the sounds and the shapes of words, the lexicon, the notation, the grammar, what a message means, the record and discourse, messages and the protocol, the writing system, dialects, and conformance |
| [`governance/`](governance/README.md) | How Rowih changes: who proposes and who merges, the rule of change, the gate, versions, dialects and the registry of dialect numbers |
| [`proposals/`](proposals/README.md) | The format of a proposal and its template |
| [`language/`](language/), [`lexicon/`](lexicon/) | The canonical data, from which every table of the specification is generated |
| [`python/rowih/`](python/rowih/), [`typescript/src/`](typescript/src/) | The canonical implementation, with the command and the server, and the TypeScript reader and renderer |
| [`skill/rowih/`](skill/rowih/SKILL.md) | The skill |
| [`corpus/`](corpus/) | The conformance suite, the 1,200 exchanges and the reports the measurements rest on |
| [`examples/`](examples/README.md) | The exchanges this page shows, drawn and spoken |
| [`tests/`](tests/), [`tools/`](tools/) | The tests, and the tools that rebuild the data and run the gate |

## About the audio

The recordings on this page are synthesised by [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M), a neural speech model released under Apache-2.0, from the phonemes of each word as the spoken form states them, agent 1 in the voice `em_alex` and agent 2 in `ef_dora`, with the spoken form's pause between lines. They give the language's sounds and not its prosody, which the toolchain's own synthesiser applies (`rowih speak`, through eSpeak NG) and which carries no meaning. Each file is checked by ear: a phoneme recogniser, [wav2vec2 fine-tuned on eSpeak NG phoneme labels](https://huggingface.co/facebook/wav2vec2-lv-60-espeak-cv-ft), transcribes it, and a file whose phoneme error rate against its message exceeds 0.15, a bound fixed before the first run, is refused. This page plays each move of the opening exchange alone, as it shows it, and [the examples](examples/README.md) play each message whole, its envelope first. The model draws noise as it speaks, so each take is seeded from what it says and is the same on every run. The eighteen files score from 0.049 to 0.142, and the opening question spoken with its mid and high vowels exchanged scores 0.296 and is refused, which shows that the check can fail. [`tools/speak_examples.py`](tools/speak_examples.py) writes and checks the files, with both models pinned by revision, and [`examples/audio.json`](examples/audio.json) records each result.

## Licence

The specification, the data, the corpus, the examples and the documents are licensed under CC BY 4.0, and the implementations, the tools and the tests under Apache-2.0. `LICENSING.md` states which directories each covers, and the one exception: the code of conduct, adapted from the Contributor Covenant, keeps its licence, CC BY-SA 4.0. The optional `speech` extra depends on eSpeak NG, under GPL-3.0-or-later, which this repository names as a dependency and does not contain.
