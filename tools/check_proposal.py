"""Check that a proposal is in the format `governance/proposals.md` fixes: its file name
and title, its fields and their values, its sections in order and none empty, the
releases it names later than those in force and of the compatibility it states, and,
before it is merged, the reading of the independent reviewer where its kind needs one.

Run from the repository root: `python3 tools/check_proposal.py [--merge] FILE ...`. It
prints each problem and exits with 1 if any file has one, and with 0 otherwise."""
import datetime
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

# each kind of proposal, and whether a change of that kind needs the independent
# reviewer's reading of the four questions: every change to the core's form or grammar
KINDS = {"grammar": True, "lexicon": True, "protocol": True, "writing system": True,
         "phonology": True, "dialect": False}
FIELDS = ("Kind", "Releases", "Compatibility", "Architectural", "Author", "Date")
SECTIONS = ("What changes", "The communicative problem", "The rule of change",
            "The regenerated data", "Review")
QUESTIONS = ("Does the language actually behave like a language?",
             "Is it merely a programming language?", "Is it merely a cipher?",
             "Is it merely an English relexification?")
ANSWERS = ("yes", "no", "in part")
# the answer to each question that shows the language departing from what it must be
DEPARTURE = ("no", "yes", "yes", "yes")
PENDING = "pending"
FILE_NAME = re.compile(r"(\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md")
RELEASE = re.compile(r"\b(language|lexicon|protocol|dialect [a-z0-9-]+) (\d+)\.(\d+)\b")
COMMENT = re.compile(r"<!--.*?-->", re.S)


def _in_force() -> dict:
    """The release of each kind in force, as (major, minor): the language's, the
    lexicon's, the protocol's and each dialect's newest."""
    from rowih import api
    v = api.version()
    out = {k: tuple(int(x) for x in v[k].split(".")) for k in ("language", "lexicon",
                                                              "protocol")}
    for name, version in v["dialects"].items():
        out["dialect %s" % name] = tuple(int(x) for x in version.split("."))
    return out


def _sections(text: str) -> list:
    """The level-two headings in order, each with the text beneath it."""
    parts = re.split(r"^## (.+)$", text, flags=re.M)
    return [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts), 2)]


def _fields(text: str) -> dict:
    head = re.split(r"^## ", text, maxsplit=1, flags=re.M)[0]
    return dict(re.findall(r"^- \*\*([A-Za-z]+):\*\* *(.*?) *$", head, re.M))


def _releases(value: str, compatibility: str, in_force: dict) -> list:
    named = RELEASE.findall(value)
    if not named:
        return ["Releases names no release, such as lexicon 1.1"]
    problems, raises_major = [], False
    for kind, major, minor in named:
        version = (int(major), int(minor))
        current = in_force.get(kind)
        if current is None:
            if not kind.startswith("dialect "):
                problems.append("Releases names %s, which is no kind of release" % kind)
            continue
        if version <= current:
            problems.append("Releases names %s %d.%d, which is not later than %d.%d, the "
                            "release in force" % (kind, version[0], version[1], *current))
        raises_major = raises_major or version[0] > current[0]
    if compatibility == "breaking" and not raises_major:
        problems.append("a breaking change raises a major version, and Releases names none")
    if compatibility == "compatible" and raises_major:
        problems.append("a compatible change keeps the major version, and Releases raises one")
    return problems


def _review(body: str, needs: bool, merge: bool) -> list:
    answers = {}
    for question in QUESTIONS:
        m = re.search(r"^- \*\*%s\*\* *(.*?) *$" % re.escape(question), body, re.M)
        if m is None:
            answers[question] = None
            continue
        # the answer opens the line, and its evidence follows it
        value = m.group(1).strip().lower()
        lead = re.match(r"(in part|yes|no|pending)\b", value)
        answers[question] = lead.group(1) if lead else value
    reader = re.search(r"^- \*\*Reader:\*\* *(.*?) *$", body, re.M)
    problems = ["Review does not state the reviewer's answer to %r" % q
                for q, a in answers.items() if a is None]
    if reader is None:
        problems.append("Review does not name its Reader")
    if problems or not (merge and needs):
        return problems
    if reader.group(1).lower() == PENDING or any(a == PENDING for a in answers.values()):
        return ["a proposal of this kind is merged only once the independent reviewer has "
                "read it, and its Review is pending"]
    for question, departure in zip(QUESTIONS, DEPARTURE, strict=True):
        answer = answers[question]
        if answer not in ANSWERS:
            problems.append("the answer to %r is yes, no or in part, not %r" % (question,
                                                                                 answer))
        elif answer == departure:
            problems.append("the reviewer answered %s to %r, a departure that blocks the "
                            "change until it is remedied" % (answer, question))
    return problems


def check(text: str, name: str, merge: bool = False, in_force: dict | None = None) -> list:
    """Every problem with the proposal `text` in the file `name`."""
    problems = []
    m = FILE_NAME.fullmatch(name)
    if m is None:
        problems.append("the file is named NNNN-words-in-lower-case.md, not %s" % name)
    title = re.match(r"# (\d{4}): \S", text)
    if title is None:
        problems.append("the first line is the title, # NNNN: and the change's name")
    elif m is not None and title.group(1) != m.group(1):
        problems.append("the title's number %s is not the file's, %s" % (title.group(1),
                                                                        m.group(1)))
    fields = _fields(text)
    if list(fields) != list(FIELDS):
        problems.append("the fields are %s, in that order, and the proposal has %s" % (
            ", ".join(FIELDS), ", ".join(fields) or "none"))
    kind = fields.get("Kind", "")
    if kind not in KINDS:
        problems.append("Kind is one of %s, not %r" % (", ".join(KINDS), kind))
    compatibility = fields.get("Compatibility", "")
    if compatibility not in ("compatible", "breaking"):
        problems.append("Compatibility is compatible or breaking, not %r" % compatibility)
    architectural = fields.get("Architectural", "")
    if architectural not in ("yes", "no"):
        problems.append("Architectural is yes or no, not %r" % architectural)
    if kind == "dialect" and (compatibility == "breaking" or architectural == "yes"):
        problems.append("a dialect release is compatible and not architectural: it keeps "
                        "every term and form of the release before it")
    if not fields.get("Author"):
        problems.append("Author names the agent that wrote the proposal")
    try:
        datetime.date.fromisoformat(fields.get("Date", ""))
    except ValueError:
        problems.append("Date is a date written YYYY-MM-DD, not %r" % fields.get("Date"))
    if "Releases" in fields:
        problems += _releases(fields["Releases"], compatibility,
                              in_force if in_force is not None else _in_force())
    sections = _sections(COMMENT.sub("", text))
    names = [s for s, _ in sections]
    if names != list(SECTIONS):
        problems.append("the sections are %s, in that order, and the proposal has %s" % (
            ", ".join(SECTIONS), ", ".join(names) or "none"))
    for section, body in sections:
        if section in SECTIONS and not body.strip():
            problems.append("the section %s is empty" % section)
    review = dict(sections).get("Review")
    if review is not None:
        needs = KINDS.get(kind, True) or architectural == "yes"
        problems += _review(review, needs, merge)
    return problems


def main(argv) -> int:
    merge = "--merge" in argv
    paths = [a for a in argv if a != "--merge"]
    if not paths:
        print("usage: check_proposal.py [--merge] FILE ...", file=sys.stderr)
        return 2
    in_force = _in_force()
    failed = False
    for path in paths:
        with open(path, encoding="utf-8") as f:
            problems = check(f.read(), os.path.basename(path), merge, in_force)
        for p in problems:
            print("%s: %s" % (path, p))
        failed = failed or bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
