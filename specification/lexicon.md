# The lexicon

The lexicon holds the words a speaker chooses: the roots that name events, states, objects and kinds, the suffixes and the rules that form words from them, the act words that stand for force, the conventional expressions and idioms, the figurative senses and the mappings that motivate them, and the registers. The closed classes of the grammar are stated in [The grammar](grammar.md), and the technical terms and compressed forms of the dialects in [Dialects](dialects.md). A release of the lexicon lists the entries it holds; this chapter states lexicon 1.0.

## Entries and their identifiers

Each entry is a file of [`lexicon/`](../lexicon/) named by its identifier, `lx.` and six digits: a root, a word-forming entry or an idiom. The roots, the dictions, the politeness words, the units of measure and the discourse relations are in [`lexicon/roots/`](../lexicon/roots/); the suffixes and the listed derivations and compounds in [`lexicon/formation/`](../lexicon/formation/); the act words and the idioms in [`lexicon/idioms/`](../lexicon/idioms/); the figurative senses in [`lexicon/senses/`](../lexicon/senses/). Other identifiers name other records: `g.` and a dotted path names a member of a grammatical class, `mp.` a conceptual mapping, `fp.` a pattern of word formation, `jg.` a technical term and `dl.` a compressed form of a dialect.

Every entry has a `key`, its name in English, by which the notation writes it ([The notation](notation.md)), and the eighteen fields a release requires of every entry: `root`, `phonological form`, `orthographic form`, `grammatical category`, `sort`, `semantic type`, `definition`, `semantic primitives`, `argument structure`, `derivational behaviour`, `register`, `collocations`, `synonyms`, `antonyms`, `related concepts`, `machine identifier`, `examples` and `version`. An act word or an idiom has nine more: `literal structure`, `pragmatic conditions`, `usage restrictions`, `route`, `expansion`, `decomposition`, `kind`, `constructed history` and `declared loss`. The `version` field states the release that introduced the entry and, where one has, the release that deprecated it. The morpheme gloss writes an entry by its key in capitals, with hyphens for spaces, and an act word with the prefix `ACT-`.

An entry's file stays as it was released. A later release that adds to the fields of released entries states the additions in an overlay, [`lexicon/fields/`](../lexicon/fields/) for derivations and lexical relations and [`lexicon/usage/`](../lexicon/usage/) for collocations and examples; a reader of a release reads each entry with the overlays of that release and of every earlier one laid over it, and a reader of an earlier release reads the entry as that release gave it.

## What lexicon 1.0 holds

<!-- generated: lexicon-totals -->
| Entries | Count |
|---|---|
| act word | 25 |
| compound | 3 |
| conventional sense | 16 |
| derivation | 9 |
| derivational suffix | 18 |
| diction | 12 |
| discourse relation | 11 |
| idiom | 277 |
| nominal root | 194 |
| politeness word | 3 |
| predicate root | 289 |
| unit of measure | 17 |
| **entries in all** | 874 |
| roots in force, register synonyms and deprecated roots aside | 500 |
| conceptual mappings | 29 |
| productive patterns of formation | 119 |
<!-- end generated -->

An idiom entry is either a formula, an expression conventional for a recurring act, or an idiom proper, whose meaning a hearer must learn ([Conventional expressions and idioms](#conventional-expressions-and-idioms)). Lexicon 1.0 holds 176 formulas and 101 idioms proper; with the 25 act words, its conventional expressions number 201.

## Roots

A root names what its definition states, and its entry gives the sort of thing it names and the roles it takes, each role with the sort of its filler. The root *examine*, `rosek`, `lx.000001`, is a predicate root of the sort `s.sort.event`, defined as 'inspect or investigate something to learn about it', taking an actor of the sort `s.sort.agent` and an undergoer of the sort `s.sort.referent`. A root's entry also lists the registers it may be used in, the derivations it admits with the meaning of each, its near synonyms, antonyms and related concepts, the roots it occurs with most often in the corpus and the corpus moves that exemplify it.

A release must state the lexical relations of every root in force both ways: a near synonym or an antonym is stated by both entries, and a related concept by the other entry as the inverse relation, *kind of* against *has kind*, *part of* against *has part* and *involves* against *involved in*. Every root in force must state at least one related concept and at least one derivation.

Nine roots are register synonyms, each naming what another root names in a narrower vocabulary: *operate*, *hum* and *proceed* of *run*; *daemon*, *box* and *establishment* of *service*; *audit*, *eyeball* and *scrutinise* of *examine*. A register synonym is technical, informal or ornamental, may be used only in the registers its entry lists, and incurs the declared loss *register*; the normal form writes the root it is a synonym of.

Lexicon 1.0 deprecates two roots, *move*, `rulem`, replaced by `nudarah`, and *assent*, `rokar`, replaced by `nukohay`. A deprecated root stays in the release so that a message using it is still read. A writer must use the replacement; a reader analyses the deprecated word and reports it in the analysis with its replacement, and does not report a deprecated word that only stands inside quoted or embedded material, where it is mentioned rather than used.

Seventeen roots are units of measure, each of one dimension, and all seventeen are critical forms ([Messages, protocol and transport](protocol.md#the-move-check-word)), since replacing one unit by another would change a number's meaning without changing the number. Eleven roots are discourse relations, which open and join moves without changing the record: *elaborates*, *restates*, *contrasts*, *supports*, *digresses*, *exemplifies*, *concludes*, *qualifies*, *corrects*, *generalises* and *continues*.

## Word formation

A content word is a stem followed by any number of suffixes, then any number of further stems, each opened by the linker *i*. A stem is a root, or a closed-class member that the suffix takes. A word the release lists governs its own meaning; any other word means what its parts compose, so that a hearer reads a word it has never met from the rules below.

### Suffixes

<!-- generated: suffixes -->
| Suffix | Name | Takes a base that is | Gives the sort | Meaning |
|---|---|---|---|---|
| `aheh` | agent | predicate | `s.sort.referent` | the one that is actor of the base |
| `udim` | undergoer | predicate | `s.sort.referent` | the one that undergoes the base |
| `awen` | instrument | predicate | `s.sort.referent` | what the base is done with |
| `onar` | result | predicate | `s.sort.state` | the state the base brings about |
| `aniw` | privative | predicate | `s.sort.state` | the state in which the base does not hold |
| `ugow` | role content | connective | `s.sort.proposition` | a content named by the part it plays in the connective |
| `umop` | process | predicate | `s.sort.reified-referent` | the base, as a process under way, named as a referent |
| `arur` | property | predicate | `s.sort.kind` | the property of being as the base states |
| `usap` | abstraction | nominal | `s.sort.kind` | what every instance of the base has in common |
| `ekoh` | nominalisation | predicate | `s.sort.proposition` | that the base holds |
| `asey` | verbalisation | nominal | `s.sort.event` | act by means of the base |
| `uyik` | adjectivisation | nominal | `s.sort.state` | be of the kind the base names |
| `ayuk` | honorific | nominal | `s.sort.referent` | the base, named with deference |
| `omiw` | causative | predicate | `s.sort.event` | make the base hold or happen |
| `uhul` | reversative | predicate | `s.sort.event` | undo the base, restoring what it changed |
| `uleg` | repetitive | predicate | `s.sort.event` | the base, done once more |
| `uwot` | potential | predicate | `s.sort.state` | be such that the base can be done to it |
| `umuk` | place | predicate | `s.sort.place` | the place where the base happens |
<!-- end generated -->

A suffix applies only to a base of the kind it takes. A base is a connective if it is a member of the class of connectives, a predicate if its sort is an event, a state or a process, and a nominal otherwise. The meaning of the derived word is the suffix's meaning with its base's meaning in place of *the base*, and its roles follow the suffix:

- *agent* and *undergoer* need a base taking an actor or an undergoer respectively, and name that role's filler, of that role's sort, taking no roles;
- the *honorific* keeps the base's sort and roles;
- *result*, *privative*, *reversative* and *repetitive* keep the base's roles under the suffix's sort;
- the *causative* adds an actor to the base's roles other than its actor;
- the *potential* needs a base taking an undergoer and keeps that role alone;
- every other suffix gives the roles its own entry states.

A word whose suffix does not take its stem is not well formed, and the checker reports `d.checker.formation-unfit`.

### Compounds

A compound is head first: its first stem is the head, and each further stem modifies everything before it. A modifier of a predicate head fills the first of the head's undergoer and content roles that the head takes, and the compound no longer takes that role; the compound *urgent mistake*, `nutimirinupenud`, means 'need to be dealt with soon, with an act or a belief that is wrong through error as its undergoer'. A nominal head keeps its sort and takes no roles, and its modifier is what it bears on. A connective takes no modifier, and a compound whose head takes none is reported as `d.checker.formation-unfit`.

### Listed derivations and compounds

The lexicon lists twelve formed words: nine derivations and three compounds. A listed word governs its meaning wherever its form is reached, during derivation or compounding, so that *budget burn*, `rumubirites`, means spending faster than the plan allowed, which its parts no longer say; its entry records the composition it has drifted from.

Five of the derivations are suppletive: each fills one cell of its root's paradigm with a form of its own, and means exactly what the regular formation would.

| Word | Meaning | Formed from | The regular form it stands for |
|---|---|---|---|
| `rahik` | consignment | *send* and the undergoer suffix | `retiludim` |
| `rukaw` | legible | *read* and the potential suffix | `reyuduwot` |
| `ruhak` | depot | *store* and the place suffix | `rodedumuk` |
| `ramuh` | fracture | *break* and the nominalisation suffix | `resayekoh` |
| `roguh` | apart | *connect* and the privative suffix | `rotutaniw` |

An irregular entry must state its regular form, its kind, a reason from the closed list *frequency*, *a constructed historical development* and *a functional pressure*, and a constructed history, and its meaning must equal the regular formation's. The normal form writes the regular formation, so that the irregular word and the formation it stands for have one normal form.

### The productive patterns

[`lexicon/patterns/1.0.json`](../lexicon/patterns/1.0.json) lists the 119 patterns of formation, each productive over every stem of the kind it takes: the eighteen suffixes, three functions of compounding (a predicate head taking its undergoer, a predicate head taking its content, and a nominal head), and 98 formations of one suffix on another. Each pattern states the kind of stem it takes, the sort it gives, its meaning over a base and an example. Combinations of two suffixes that the rules of formation admit over some root are excluded only for one of these reasons:

<!-- generated: excluded-patterns -->
| Combinations excluded because | Count |
|---|---|
| a suffix that presupposes an event or a process, on a state | 26 |
| the abstraction of a kind, which is the kind itself | 1 |
| the honorific inside a formation: the deference it adds belongs to the word as it is said, not to a stem | 3 |
| the same suffix twice, whose second step cancels the first or adds nothing | 8 |
<!-- end generated -->

## Act words

An act word is a six-symbol word opened by *k* that stands for the beginning of a move's head, from what the move adds to when its change takes effect. It never stands for the authority the move claims, which is written as a word of its own. A reader reads an act word's expansion in its place: the move's class is computed from the expansion, and the normal form writes the expansion out. Acts that share a head share an act word, the class of the move being computed from what the move names.

<!-- generated: act-words -->
| Act word | Act | Stands for |
|---|---|---|
| `kihiwo` | question | ISSUE QUESTION |
| `kiyetu` | request | ISSUE REQUEST |
| `kehubu` | proposal | ISSUE PROPOSAL |
| `kigowu` | challenge | ISSUE CHALLENGE |
| `kaloda` | command | NORMATIVE-ENTRY OBLIGATION BOUND |
| `kolide` | promise | NORMATIVE-ENTRY COMMITMENT BOUND |
| `kimibe` | offer | NORMATIVE-ENTRY COMMITMENT BINDINGNESS.ON-ACCEPTANCE |
| `kebabe` | delegation | NORMATIVE-ENTRY ASSIGNMENT BINDINGNESS.ON-ACCEPTANCE |
| `kadina` | grant | NORMATIVE-ENTRY PERMISSION BOUND |
| `kusuni` | recommendation | NORMATIVE-ENTRY RECOMMENDATION |
| `kotage` | definition | SETTING DEFINITION |
| `kupewa` | role assignment | SETTING ROLE |
| `kopati` | counterproposal | ISSUE PROPOSAL RESOLUTION REJECTION WHOLE-ENTRY ON-THE-MOVE |
| `kitidu` | acceptance | NORMATIVE-ENTRY COMMITMENT BOUND RESOLUTION OUTCOME-OF-A-RESOLUTION.ACCEPTANCE WHOLE-ENTRY ON-THE-MOVE |
| `kagobe` | undertaking | NORMATIVE-ENTRY OBLIGATION BOUND RESOLUTION OUTCOME-OF-A-RESOLUTION.ACCEPTANCE WHOLE-ENTRY ON-THE-MOVE |
| `kanabo` | partial acceptance | NORMATIVE-ENTRY COMMITMENT BOUND RESOLUTION OUTCOME-OF-A-RESOLUTION.ACCEPTANCE PART-OF-IT ON-THE-MOVE |
| `kebedo` | rejection | NOTHING-BEYOND-ITS-OWN-RECORD RESOLUTION REJECTION WHOLE-ENTRY ON-THE-MOVE |
| `kedeba` | acknowledgement | NOTHING-BEYOND-ITS-OWN-RECORD ACKNOWLEDGEMENT WHOLE-ENTRY ON-THE-MOVE |
| `kukoyo` | withdrawal | NOTHING-BEYOND-ITS-OWN-RECORD LOWERING WHOLE-ENTRY ON-THE-MOVE |
| `kamari` | partial withdrawal | NOTHING-BEYOND-ITS-OWN-RECORD LOWERING PART-OF-IT ON-THE-MOVE |
| `kodiwu` | answer | ASSERTED-POSITION RESOLUTION ANSWER WHOLE-ENTRY ON-THE-MOVE |
| `kakepe` | completion report | ASSERTED-POSITION RESOLUTION SETTLEMENT WHOLE-ENTRY WHEN-THE-CHANGE-TAKES-EFFECT.ON-ACCEPTANCE |
| `konito` | error report | ASSERTED-POSITION RESOLUTION FAILURE WHOLE-ENTRY WHEN-THE-CHANGE-TAKES-EFFECT.ON-ACCEPTANCE |
| `kapeto` | confirmation | ASSERTED-POSITION NONE |
| `kumuso` | correction | ASSERTED-POSITION LOWERING WHOLE-ENTRY ON-THE-MOVE |
<!-- end generated -->

Every act word is protected and a critical form. Each act word's expansion, completed with a body, must parse without a diagnostic of the parser.

## Politeness words and dictions

A politeness word records the relation between the participants, and a diction records the manner of the move; both are written in the move's head, the politeness word after the relation words and the diction after it, and neither changes the move's force or standing. Each belongs to the social and textual component of the move, which the analysis keeps and the normal form sets aside ([What a message means](meaning.md)). The neutral politeness is the absence of a politeness word. A diction is also a nominal that may stand as content, so that a request for a terse answer is an ordinary request.

<!-- generated: social-words -->
| Word | Name | Kind | Registers |
|---|---|---|---|
| `ruwok` | courteous | politeness word | R3 |
| `riyit` | familiar | politeness word | R5 R6 |
| `rumal` | deferential | politeness word | R7 |
| `roroy` | terse | diction | R0 R1 R2 R3 R4 R5 R6 R7 |
| `rewel` | neutral | diction | R0 R1 R2 R3 R4 R5 R6 R7 |
| `redek` | elaborate | diction | R0 R1 R2 R3 R4 R5 R6 R7 |
| `rikub` | technical | diction | R0 R1 R2 R3 R4 R5 R6 R7 |
| `rimiw` | poetic | diction | R0 R1 R2 R3 R4 R5 R6 R7 |
| `rukob` | humorous | diction | R0 R1 R2 R3 R4 R5 R6 R7 |
| `rusat` | cautious | diction | R0 R1 R2 R3 R4 R5 R6 R7 |
| `rirag` | authoritative | diction | R0 R1 R2 R3 R4 R5 R6 R7 |
| `ropis` | tentative | diction | R0 R1 R2 R3 R4 R5 R6 R7 |
| `rogil` | diplomatic | diction | R0 R1 R2 R3 R4 R5 R6 R7 |
| `rogow` | adversarial | diction | R0 R1 R2 R3 R4 R5 R6 R7 |
| `rimut` | collaborative | diction | R0 R1 R2 R3 R4 R5 R6 R7 |
<!-- end generated -->

## Conventional expressions and idioms

An idiom entry states a literal structure and an expansion, both in the notation. A literal structure may hold numbered slots, `(slot 1)`, for the constituents the speaker supplies; the expansion holds the same slots, and the entry's `decomposition` says which part of the literal structure carries which part of the expansion. A release must give an expansion exactly the slots of its literal structure, so that nothing a speaker supplies is lost, and an expansion must not itself use an idiom.

A **formula** fixes a recurring act: greetings, thanks, apologies, acknowledgements, confirmations, requests for clarification, warnings, agreement and disagreement, expressions of uncertainty, closings, conversational repair, reports and requests of status, offers, refusals and the like. A hearer who knows the grammar could reach a formula's meaning, and only the fact of the convention is learned. A formula states content, never force. The formula *thanks*, `lx.000144`, has the literal structure `(situation benefit (CONTENT (slot 1)))` and the expansion `(situation benefit (CONTENT (slot 1)) (RECIPIENT (term SELF)))`, and its entry lists every register but the formal, whose record states a benefit explicitly; it is not used in the raw register either, which admits no formula.

An **idiom proper** must be learned. A grammatical idiom is built by the grammar but means what its entry says: *cloud cover*, `lx.000767`, has the literal structure `(situation cover (UNDERGOER (slot 1)) (INSTRUMENT (term cloud)))` and means that the speaker has examined what the slot names and cannot yet settle it. An extragrammatical idiom is a sequence of content words that no production admits: lexicon 1.0 has eight, each a root said twice, such as *run run*, 'the service is still running', which survives from a stage of the language in which a doubled root marked continuation.

A reader reads a grammatical idiom by its entry only where the idiom mark, the member `IDIOM-ENTRY`, stands on an assertion, a situation or a term. The marked unit selects the entry whose literal structure it matches, its slots aside and its parts compared without regard to order, and the reader holds the entry's expansion with the slots filled by what the speaker supplied. A marked unit that matches no entry is reported as `d.checker.idiom-absent`. A unit without the mark is read literally, whatever entry it resembles; a speaker who means both readings writes a set of readings ([What a message means](meaning.md)). An extragrammatical idiom is recognised by its words, where a constituent or an assertion's situation stands, since no production admits its first word there.

What an idiom or a formula leaves unsaid is declared. Each entry lists its declared losses, drawn from the class of declared losses (*register*, *diction*, *stance*, *relation between participants* and *wording*), and a move may declare only losses that its act word, idiom, politeness word, diction, register or register-marked words incur, and none twice, or the checker reports `d.checker.loss-not-incurred`. An idiom may be used only in the registers its entry lists, a formula only in a register that admits formulas, and an idiom proper only in a register that admits idioms; otherwise the checker reports `d.checker.register-excludes-word` or `d.checker.register-excludes-device`.

A release must meet six requirements over its idioms:

1. each literal structure and each expansion parses without a diagnostic;
2. no grammatical idiom's literal structure equals its expansion, since its mark would then add nothing a hearer could detect;
3. no two literal structures unify, so that no form selects two entries;
4. in an idiom introduced from lexicon 1.0 on, no situation in the literal structure or the expansion fills a role that the word it is read as does not take;
5. every idiom introduced from lexicon 1.0 on whose route is a figure is motivated by a conceptual mapping;
6. no two idioms whose expansions differ in a critical value stand one substitution of an uncoded word apart.

The sixth requirement keeps a single edit from turning one idiom silently into another. The distance is counted over the normal forms of the two literal structures, slots standing for anything; replacing a word that carries a code of the move check word, or a protected word, counts as two, since the move check word detects it, as does any other difference of structure. Where two idioms stood one substitution apart, one was given a second fixed part, such as a quantifier on a fixed term or an aspect on its situation.

## Figurative senses and conceptual mappings

A conventional sense extends a root to a figurative meaning. It shares its root's form and sort, states its own definition and roles, and names the frame that selects it and the conceptual mapping that motivates it. A unit whose head word is a root with senses is read in the first sense, in the order of the release, whose frame it matches: some part of the unit fills the frame's role with a constituent of the frame's kind, a situation or a term. A unit matching no frame is read in the root's basic sense, and a word keeps its basic sense inside the source of a marked figure. Each frame names a role the basic sense lacks, or fills a role with a kind of constituent the basic sense does not take, so that no well-sorted literal use of a root is read in a sense.

<!-- generated: senses -->
| Sense | Of the root | Selected where | Motivated by | Meaning |
|---|---|---|---|---|
| understand | take `rigor` | `undergoer` filled by a situation | IDEAS ARE OBJECTS | come to understand a content |
| conclude | arrive `remoy` | `content` filled by a situation | REASONING IS TRAVEL | come to hold a content as the end of one's reasoning |
| settle | freeze `rakut` | `undergoer` filled by a situation | WHAT CAN CHANGE IS LIQUID | become fixed and no longer open to change |
| urgency | pressure `remir` | `content` filled by a situation | URGENCY IS PRESSURE | the need that a content be brought about soon |
| burst | storm `rosid` | `content` filled by a term | NETWORK ACTIVITY IS WEATHER | many of what the content names, arriving in a short time |
| clarity | light `rasaw` | `content` filled by a situation | KNOWING IS SEEING | what makes a content plain to the one who considers it |
| doubt | cloud `numosoh` | `content` filled by a situation | THE STATE OF AN EXCHANGE IS THE SKY ABOVE IT | what keeps a content from being settled by the one who considers it |
| demanding | heavy `nureket` | `undergoer` filled by a situation | A TASK IS A LOAD | need much work or computation |
| workload | weight `numipot` | `content` filled by a situation | A TASK IS A LOAD | the work a task needs |
| inference | bridge `nuyones` | `content` filled by a situation | AN INFERENCE IS A BRIDGE | the inference that leads to a content |
| obstacle | mountain `nulibeg` | `content` filled by a situation | A HARD PROBLEM IS A MOUNTAIN | a hard problem that stands before a content |
| germ | seed `nusagak` | `content` filled by a situation | IDEAS ARE PLANTS | the idea a content grows from |
| knowledge | map `nutitoh` | `content` filled by a situation | KNOWLEDGE IS A MAP | what an agent knows of a matter |
| licence | door `nubogab` | `content` filled by a situation | ACCESS IS A DOOR | a permission for an action |
| concession | price `rodur` | `content` filled by a situation | NEGOTIATION IS A MARKET | what must be conceded for an outcome |
| mood | weather `nukepig` | `content` filled by a term | THE STATE OF A MIND IS WEATHER | the state of an agent's processing |
<!-- end generated -->

A release must give every sense a root of the same form and sort, a well-formed frame, and a mapping that lists it, and no two senses of one root may share a frame. A conceptual mapping, `mp.` and six digits in [`lexicon/mappings/`](../lexicon/mappings/), names a metaphor, such as IDEAS ARE OBJECTS, with its source domain, its target domain, the correspondences between them and the senses and idioms it motivates; lexicon 1.0 holds 29.

## Registers

A register is the variety of the language a move is written in, declared by one word of the register class in the move's head; a move that declares none is in the standard register, R2. The register fixes which modes of expression and which devices the move may use, whether formulas are admitted, whether the order of parts is canonical or free, and which politeness word, if any, the register writes. Each register's record is in [`lexicon/registers/`](../lexicon/registers/).

<!-- generated: registers -->
| Register | Name | Use | Modes | Devices | Precision-bound | Formulas | Order | Politeness word |
|---|---|---|---|---|---|---|---|---|
| R0 | raw | exchange among agents of one system | full explicitness, normal expression, compression | declared defaults, inheritance, conventional expressions, shared context, dialect forms | no | no | canonical | none |
| R1 | protocol | coordination under the protocol | full explicitness, normal expression | declared defaults, inheritance, conventional expressions | yes | yes | canonical | none |
| R2 | standard | ordinary exchange | full explicitness, normal expression, compression, idiom | declared defaults, inheritance, conventional expressions, shared context, dialect forms, idioms | no | yes | free | none |
| R3 | explanatory | explanation to a human reader | full explicitness, normal expression, creative expression | declared defaults, inheritance, conventional expressions, marked figures, creative ambiguity | no | yes | free | courteous |
| R4 | formal | specification and proof | full explicitness, normal expression | declared defaults, inheritance, conventional expressions | yes | yes | canonical | none |
| R5 | casual | informal exchange | normal expression, compression, idiom | declared defaults, inheritance, conventional expressions, shared context, dialect forms, idioms | no | yes | free | familiar |
| R6 | playful | humour and play | normal expression, idiom, creative expression | declared defaults, inheritance, conventional expressions, idioms, marked figures, creative ambiguity | no | yes | free | familiar |
| R7 | ceremonial | occasions of high formality | full explicitness, normal expression, idiom | declared defaults, inheritance, conventional expressions, idioms | no | yes | free | deferential |
<!-- end generated -->

A move in the protocol register, R1, or the formal register, R4, is precision-bound, and must have exactly one reading ([What a message means](meaning.md)). A word whose entry does not list the move's register may not be used in it. The nine register synonyms and the honorific suffix, which the ceremonial register alone admits, are register-marked words: each incurs the declared loss *register*, and the normal form writes the word without it.

## Coining a word by definition

A speaker may coin a word for an exchange by the act of definition ([The record and discourse](discourse.md)). The definition states the defined word as declared data of the language's media type within a term, then its expansion, a single term or situation. The defined word must have the shape of a five-symbol root opened by *r*, so that it takes suffixes and enters compounds and the lexicon stays a prefix code; it must not be a word of the release, whether a root, a derivation or a word of the grammar; and it must stand at a distance of at least two from every word and of at least three from every critical or protected word. Its expansion must not contain it and must carry no embedded material and no set of readings. A definition has one scope, the exchange or a dialect, and a definition scoped to a dialect must be written in a message that names that dialect. It changes no release: the defined word is read under the definition by those who hold it, and a second definition of a word already defined is refused.

## The codes from which forms are drawn

The forms of the lexicon are drawn from codes, each a set of strings in which the last consonant is a weighted sum of the symbols before it, modulo fourteen. With the consonants indexed from 0 in the order *p t k b d g m n s l r w y h* and the vowels from 0 in the order *a e i o u*, the codes are:

| Code | Shape | The last consonant | Forms |
|---|---|---|---|
| four-symbol words, the particles and structural words | C₁ V₁ C₂ V₂ | C₂ = (*o* + V₁ + 2V₂) mod 14, where the offset *o* is 0 for *n*, 1 for *y*, 2 for *p*, 3 for *b*, 4 for *g*, 5 for *m*, 6 for *s*, 7 for *w* and 8 for *l* | 25 for each opening |
| five-symbol words | C₁ V₁ C₂ V₂ C₃ | C₃ = (*o* + V₁ + 2V₂ + 3C₂) mod 14, where *o* is 1 for *r* and 0 for *h* | 350 for each opening |
| suffixes | V₁ C₁ V₂ C₂, V₁ not *i* | C₂ = (V₁ + 2V₂ + 3C₁) mod 14 | 280 |
| long roots | *n u* C₂ V₂ C₃ V₃ C₄ | C₄ = (7 + C₂ + 2V₂ + 3C₃ + 4V₃) mod 14 | 4,900 |

Within one code no two forms differ in a single symbol, since a change to any earlier symbol changes the weighted sum, and so the last consonant. The six-symbol words, protected members and act words, are drawn from no code: each is chosen at random among the strings of its shape that meet the distance requirements of [The sounds and the shapes of words](sounds-and-words.md#the-distances-between-words).

The codes bound how far the lexicon can grow within major version 1. Counted over lexicon 1.0 and the newest release of every dialect, the four-symbol code has eight free forms at a distance of three from every protected word, `noba`, `noge`, `nolo`, `noni`, `nowu`, `yuli`, `yune` and `yuwo`, and no first syllable is free to open a new class of particles. The five-symbol code opened by *r* has 155 free forms, which are kept for the compressed forms of the dialects. The long-root code has 4,506 free forms, at a distance of two from every released word, from which every new root is drawn. When lexicon 1.0 was built, a greedy placement fitted 59 further act words among the six-symbol strings opened by *k* at a distance of three from every word, and a release that adds act words draws them before it draws long roots, since each long root stands within two edits of one string of that shape. The move check word's 337 forms are fixed for the major version ([Messages, protocol and transport](protocol.md#the-move-check-word)).

## Looking a word up

`rowih lookup TERM` prints one line for each word of the release whose form, identifier or key is the term, or whose gloss contains it as a word, and for each technical term and compressed form of the newest dialect releases that matches: the identifier, the form and the gloss, separated by tabs. It exits with status 0 if it found a word and 1 if it found none. The Python function `rowih.api.lookup` returns the same words as records ([Conformance](conformance.md)).
