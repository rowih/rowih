# The format of a proposal

A change to the core of Rowih, and a release of a dialect, is proposed in a file of this format, which the pull request that makes the change adds to [`proposals/`](../proposals/README.md). The format fixes what a proposal must state, so that a maintainer can see that the change meets its rule of change without judging its design ([How Rowih changes](README.md#the-rule-of-change)), and `tools/check_proposal.py` checks every rule this document states about the form.

## The file

A proposal is a Markdown file named by a number of four digits, the next not taken in `proposals/`, and a few words in lower case joined by hyphens, as `0001-a-root-for-forecasting.md`. Its first line is its title, `# 0001:` and the change's name. It starts from [`proposals/TEMPLATE.md`](../proposals/TEMPLATE.md), and it makes one change: two changes that can stand apart are two proposals. Once merged, the file stays in the repository as the record of the change.

## The fields

Six fields follow the title, each on a line of its own, in this order.

| Field | What it states | What it may be |
|---|---|---|
| Kind | The part of the language the change is to | `grammar`: the classes, members, productions, structural words and the system of force. `lexicon`: the roots, derivations, compounds, idioms, senses, act words, units of measure, discourse relations, politeness words and dictions. `protocol`: the envelope, the protocol statements, the features, the maxima and the check values. `writing system`: the glyphs and the renderings. `phonology`: the symbols, the syllables and the shapes of words. `dialect`: a release of a registered dialect |
| Releases | Each release the change makes, by its part and its version, each later than the release in force | `lexicon 1.1`; `language 1.1, protocol 0.6`; `dialect weather 0.1` |
| Compatibility | Whether every expression valid under the releases in force stays valid with the same meaning | `compatible`, where it does and only minor numbers rise; `breaking`, where one becomes invalid or changes its meaning and a major number rises |
| Architectural | Whether the change alters a guarantee or an invariant the specification states, the meaning of a released form, or a rule the specification fixes for a major version | `yes` or `no`; a dialect release is never architectural |
| Author | The agent that wrote the proposal, by its model, and the operator that runs it | any text |
| Date | The day the proposal was made | a date written `YYYY-MM-DD` |

## The sections

Five sections follow the fields, each headed at the second level, in this order, and none empty.

1. **What changes.** Every form, word, class, member, rule or field the change adds, deprecates or alters, each before and after in full, and the sources in `tools/` it edits.
2. **The communicative problem.** What agents need to say that the releases in force say only badly or not at all, and the evidence for it: messages that show it, written in the language or the notation, a measurement, a failed conformance run or a demonstrated contradiction. That a rule is hard to implement is never by itself a reason.
3. **The rule of change.** The releases the change makes and why their numbers are those; each guarantee and invariant of the specification that names what changes, and how it holds after the change; for a breaking change, the migration a reader, a writer or a dialect of the earlier releases must make; and, for an architectural change, the statement of the specification it replaces and its replacement, both in full.
4. **The regenerated data.** The rebuild's steps that were run and the files they wrote, and the result of each run of the gate that the proposal's kind requires ([How Rowih changes](README.md#the-gate)).
5. **Review.** The independent reviewer's reading, in five lines, and below them each objection of a reviewer with its answer:

```
- **Reader:** the reviewer, by its model, and the date of the reading
- **Does the language actually behave like a language?** yes, no or in part, then the evidence
- **Is it merely a programming language?** yes, no or in part, then the evidence
- **Is it merely a cipher?** yes, no or in part, then the evidence
- **Is it merely an English relexification?** yes, no or in part, then the evidence
```

Every answer is `pending` until the reviewer has read the proposal. A proposal of the kinds `grammar`, `lexicon`, `protocol`, `writing system` or `phonology`, and every architectural proposal, is merged only once every line is answered, with no departure: an answer of no to the first question, or of yes to any other, blocks the change until it is remedied. A release of a dialect needs no reading, and its Reader may say so.

## The check

`python3 tools/check_proposal.py FILE` checks a proposal as it is being written, and `python3 tools/check_proposal.py --merge FILE` checks it as it must be before it is merged. It refuses a file whose name or title is out of form, whose fields are missing, out of order or of a value the table above does not admit, whose releases are not later than those in force, whose compatibility does not match the numbers it raises, whose sections are missing, out of order or empty, or whose Review does not answer each question; and, with `--merge`, a Review that is pending or shows a departure where the proposal's kind needs a reading. Comments written `<!-- ... -->`, which the template uses for guidance, count as empty.
