"""What every domain's schemas compose items with: the picker that spreads the vocabulary
over the lexicon, and the notation of terms, assertions, moves and messages."""
import collections

START = 1760000000      # the first message's communication time
STEP = 60               # seconds between messages of an item


class Picker:
    """The least-used of the candidates offered, the earlier one where two are as used,
    with every word drawn counted."""

    def __init__(self):
        self.used = collections.Counter()

    def __call__(self, candidates):
        best = min(range(len(candidates)), key=lambda i: (self.used[candidates[i]], i))
        self.used[candidates[best]] += 1
        return candidates[best]

    def note(self, *keys):
        for key in keys:
            self.used[key] += 1


def plural(n: int, word: str) -> str:
    """A count of a unit in English."""
    return "%d %s%s" % (n, word, "" if n == 1 else "s")


def k(key: str) -> str:
    """A word as the notation writes it."""
    return key.replace(" ", "-")


def term(key: str, *values: str) -> str:
    return "(term %s)" % " ".join([k(key)] + list(values))


def assertion(basis: str, strength: str, situation: str) -> str:
    return "(assertion %s %s %s)" % (basis, strength, situation)


def asserted(basis: str, strength: str, situation: str, head: str = "") -> str:
    head = (" " + head) if head else ""
    return "(move ASSERTED-POSITION%s %s)" % (head, assertion(basis, strength, situation))


def message(sender: int, recipients, k_index: int, identifier: int, *moves: str) -> dict:
    return {"sender": sender, "recipients": list(recipients),
            "time": str(START + STEP * k_index), "identifier": identifier,
            "notation": " ".join(moves)}


# What a reference expects of the entry it names, by the kind of move that added it.
EXPECTED = {
    "position": "ASSERTED-POSITION EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE",
    "supposition": "SUPPOSITION EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE",
    "question": "ISSUE QUESTION OPEN",
    "request": "ISSUE REQUEST OPEN",
    "proposal": "ISSUE PROPOSAL OPEN",
    "challenge": "ISSUE CHALLENGE OPEN",
    "obligation": "NORMATIVE-ENTRY OBLIGATION EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE",
    "commitment": "NORMATIVE-ENTRY COMMITMENT EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE",
    "assignment": "NORMATIVE-ENTRY ASSIGNMENT EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE",
    "permission": "NORMATIVE-ENTRY PERMISSION EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE",
    "recommendation": "NORMATIVE-ENTRY RECOMMENDATION EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE",
    "definition": "SETTING DEFINITION EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE",
    "role": "SETTING ROLE EXPECTED-STATUS-OF-AN-ENTRY.IN-FORCE",
}


def names(author: int, number: int, kind: str) -> str:
    """A reference to the entry `number` of agent `author`, added by a move of `kind`."""
    return "(names %d %d %s)" % (author, number, EXPECTED[kind])


def party(n: int) -> str:
    return "(term (party %d))" % n


class Exchange:
    """The messages of one item, each sender's entries counted as protocol 0.2 counts
    them, one for each move, so that a reference names the entry it means."""

    def __init__(self):
        self.messages = []
        self.entries = collections.Counter()
        self.written = collections.Counter()
        self.sent = collections.Counter()

    def send(self, sender: int, recipients, *moves: str) -> int:
        """Add a message and return the number of the entry its first move adds."""
        first = self.entries[sender] + 1
        m = message(sender, recipients, len(self.messages), self.sent[sender] + 1, *moves)
        if first != self.written[sender] + 1:
            # after a message lost in transit, which the item does not hold
            m["first entry"] = first
        self.entries[sender] += len(moves)
        self.written[sender] += len(moves)
        self.sent[sender] += 1
        self.messages.append(m)
        return first

    @classmethod
    def scripted(cls, *messages) -> list:
        """The messages of a hand-written item, each (sender, recipients, moves...)."""
        x = cls()
        for sender, recipients, *moves in messages:
            x.send(sender, recipients, *moves)
        return x.messages

    def lose(self, sender: int, moves: int = 1) -> int:
        """A message the sender sent that never arrived: its serial and entries are
        spent, and the item holds no record of it. Returns its serial."""
        self.sent[sender] += 1
        self.entries[sender] += moves
        return self.sent[sender]
