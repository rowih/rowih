"""Write the negative corpus from `corpus/source/negative.json`. A notation item is
written by the generator without checking; an edited item applies one stated edit to a
conformance message and, where the edit says so, reseals the message (recounts the move,
recomputes its move check word and the integrity check value) so that the defect under
test is the only one. Run from the repository root: `python3 tools/build_negative.py`."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "python"))

from rowih import api, data, versions  # noqa: E402
from rowih.generator import Generator  # noqa: E402
from rowih.notation import Reader  # noqa: E402
from rowih.parser import number_check  # noqa: E402
from rowih.serialise import check_value  # noqa: E402
from rowih.writer import Writer  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_corpus import language_for, substitute  # noqa: E402

L = data.load()
W = Writer(L)


def lines_of(text):
    return [line.split(" ") for line in text.split("\n") if line]


def join(lines):
    return "".join(" ".join(x) + "\n" for x in lines)


def body_of(move_line):
    """The body words of a move line, without WORD-COUNT, the count and the check."""
    i = 1
    while L.by_form[move_line[i]].class_id == "g.numbers.numeral":
        i += 1
    return move_line[i + 1:-1]


WIDTH = L.protocol["check value width"]


def fields_of(env):
    """The fields of an envelope line, without its count and its unit check word, and
    the words after it: the authentication and the integrity check value (protocol 0.3)."""
    i = 1
    while L.by_form[env[i]].class_id == "g.numbers.numeral":
        i += 1
    count = int("".join(str(["zero", "one", "two", "three", "four", "five", "six", "seven",
                             "eight", "nine"].index(L.by_form[w].name)) for w in env[1:i]))
    start = i + 1
    return env[start:start + count - 1], env[start + count:]


def reseal(lines, semantic=None, fields=None):
    """Recount and recheck the envelope and every move, and recompute the integrity check
    value; `fields`, where given, are the envelope's fields as the edit left them."""
    if fields is None:
        fields = fields_of(lines[0])[0]
    if semantic is not None:
        sv = W.w("g.message.message-field.semantic-check-value")
        k = fields.index(sv)
        fields = fields[:k] + [sv] + W.number(str(semantic), WIDTH) + fields[k + WIDTH + 2:]
    moves = [W.move(body_of(m)) for m in lines[1:]]
    return W.message(W.unit(fields), moves, integrity=True)


def edit(text, name):
    lines = lines_of(text)
    env, move = lines[0], lines[1]
    icv_form = W.w("g.message.message-field.integrity-check-value")
    if name == "drop-integrity":
        k = env.index(icv_form)
        return join([env[:k]] + lines[1:])
    if name == "integrity-plus-one":
        k = env.index(icv_form)
        digits = "".join(str(["zero", "one", "two", "three", "four", "five", "six", "seven",
                              "eight", "nine"].index(L.by_form[w].name))
                         for w in env[k + 1:k + 1 + WIDTH])
        new = W.number(str((int(digits) + 1) % 10 ** WIDTH), WIDTH)
        return join([env[:k + 1] + new] + lines[1:])
    if name == "semantic-plus-one-recompute-integrity":
        a = api.parse(text)
        return reseal(lines, semantic=(a.message.envelope.semantic.integer() + 1)
                      % 10 ** WIDTH)
    if name == "delete-last-body-word":
        return join([env, move[:-2] + move[-1:]] + lines[2:])
    if name == "next-move-check-form":
        forms = L.move_check_forms
        nxt = forms[(forms.index(move[-1]) + 1) % len(forms)]
        return join([env, move[:-1] + [nxt]] + lines[2:])
    if name == "next-number-check-form":
        i = 1
        while L.by_form[move[i]].class_id == "g.numbers.numeral":
            i += 1
        val = int(L.by_form[move[i]].name.split()[-1])
        move = move[:i] + [W.w("g.numbers.check-word.check-%d" % ((val + 1) % 11))] + move[i + 1:]
        return join([env, move] + lines[2:])
    if name == "insert-bidi-override":
        return text.replace(move[5], move[5][:2] + "‮" + move[5][2:], 1)
    if name == "insert-zero-width-space":
        return text.replace(move[5], move[5][:2] + "​" + move[5][2:], 1)
    if name == "insert-unassigned-code-point":
        unassigned = chr(int(L.writing["code point block"][1][2:], 16))
        return text.replace(move[5], move[5][:2] + unassigned + move[5][2:], 1)
    if name == "replace-first-root-with-unknown":
        k = next(i for i, w in enumerate(move) if w in L.by_form and L.by_form[w].kind == "root")
        return join([env, move[:k] + ["rabab"] + move[k + 1:]] + lines[2:])
    if name == "swap-first-two-fields":
        # the sender's and recipients' fields exchanged, the envelope counted again
        fields, after = fields_of(env)
        return join([W.unit(fields[2:4] + fields[0:2] + fields[4:]) + after] + lines[1:])
    if name == "two-decimal-points-in-a-number":
        body = body_of(move)
        k = next(i for i, w in enumerate(body) if L.by_form.get(w) is not None
                 and L.by_form[w].class_id == "g.numbers.numeral")
        j = k
        while L.by_form[body[j]].class_id == "g.numbers.numeral":
            j += 1
        point = W.w("g.numbers.numeral.decimal-point")
        bad = [W.w("g.numbers.numeral.five"), point, point, W.w("g.numbers.numeral.zero"),
               W.w("g.numbers.check-word.check-%d" % number_check("50"))]
        body = body[:k] + bad + body[j + 1:]
        lines[1] = W.move(body)
        return reseal(lines)
    if name == "drop-end-wall-and-recount":
        end_wall = W.w("g.structure.end-wall")
        body = [w for w in body_of(move) if w != end_wall]
        lines[1] = W.move(body)
        return reseal(lines)
    if name == "shorten-payload":
        body = body_of(move)
        longest = max(body, key=len)
        body = [w[:-1] if w == longest else w for w in body]
        lines[1] = W.move(body)
        return reseal(lines)
    if name == "lexicon-version-unreleased":
        major, minor = W.lang.release["version"].split(".")
        env_words = W.envelope(version=(W.lang.grammar["version"],
                                        "%s.%d" % (major, int(minor) + 1),
                                        W.lang.protocol["version"]))
        return W.message(env_words, lines[1:], integrity=True)
    if name in ("first-entry-zero", "drop-first-entry"):
        # the envelope's first entry (protocol 0.2): written as zero, or left out, with
        # the integrity check value recomputed so that the defect is the only one
        fields = fields_of(env)[0]
        field = W.w("g.message.message-field.first-entry")
        k = fields.index(field)
        j = k + 1
        while L.by_form[fields[j]].class_id == "g.numbers.numeral":
            j += 1
        head = fields[:k] + ([field] + W.number("0") if name == "first-entry-zero" else [])
        return W.message(W.unit(head + fields[j + 1:]), lines[1:], integrity=True)
    if name == "drop-version-field":
        fields, after = fields_of(env)
        version = W.w("g.message.message-field.version")
        ident = W.w("g.message.message-field.identifier")
        k, j = fields.index(version), fields.index(ident)
        return join([W.unit(fields[:k] + fields[j:]) + after] + lines[1:])
    if name == "insert-fullwidth-letter":
        return text.replace(move[5], move[5][:2] + "\uff41" + move[5][2:], 1)
    if name == "drop-final-closers-and-reseal":
        # the move ends with its situation and assertion still open
        body = body_of(move)[:-2]
        lines[1] = W.move(body)
        return reseal(lines)
    if name in ("delete-wall-opener", "delete-wall-opener-and-reseal"):
        wall = W.w("g.structure.wall")
        k = move.index(wall)
        if name == "delete-wall-opener":
            return join([env, move[:k] + move[k + 1:]] + lines[2:])
        body = body_of(move)
        body.remove(wall)
        lines[1] = W.move(body)
        return reseal(lines)
    return edit_robustness(text, name)


def edit_robustness(text, name):
    """The edits of the robustness forms: a check word of an envelope or a statement
    altered, a protocol message without its integrity check value or to two recipients, a
    message of moves with a protocol message's identifier, an acknowledgement out of order
    and an authentication scheme no one defines."""
    lines = lines_of(text)
    env, move = lines[0], lines[1]
    if name == "envelope-next-check-form":
        fields, after = fields_of(env)
        unit = W.unit(fields)
        val = int(L.by_form[unit[-1]].name.split()[-1])
        unit[-1] = W.w("g.numbers.check-word.check-%d" % ((val + 1) % 11))
        return join([unit + after] + lines[1:])
    if name == "statement-next-check-form":
        val = int(L.by_form[move[-1]].name.split()[-1])
        move = move[:-1] + [W.w("g.numbers.check-word.check-%d" % ((val + 1) % 11))]
        return W.message(fields_unit(env), [move])
    if name == "protocol-without-integrity":
        return W.message(fields_unit(env), [move], integrity=False)
    if name == "protocol-two-recipients":
        fields = fields_of(env)[0]
        recipients = W.w("g.message.message-field.recipients")
        k = fields.index(recipients)
        fields = fields[:k + 1] + W.number("1") + W.number("3") + fields[k + 3:]
        return W.message(W.unit(fields), [move])
    if name == "identifier-zero-with-moves":
        a = api.parse(text)
        e = a.message.envelope
        envelope = W.envelope(e.sender.text, [r.text for r in e.recipients], e.time.text,
                              identifier=0, first_entry=0)
        return W.message(envelope, [[w.form for w in m] for m in a.message.lines])
    if name == "holds-beyond-the-first-missing":
        envelope = W.envelope(2, (1,), "1759622431", identifier=0, first_entry=0)
        return W.message(envelope, [W.statement("holds", [("channel", (2,), (3, 4))])])
    if name == "authentication-scheme-two":
        auth = W.w("g.message.message-field.authentication")
        k = env.index(auth)
        j = k + 1
        while L.by_form[env[j]].class_id == "g.numbers.numeral":
            j += 1
        return join([env[:k + 1] + W.number("2") + env[j + 1:]] + lines[1:])
    return edit_dialects(text, name)


def edit_dialects(text, name):
    """The edits of the dialect forms: a version with a leading zero, dialects out of
    order, a dialect under another digest, a lexicon release earlier than the language
    release may name, and statements of version negotiation out of order or naming two
    messages; and a message of a later language release than the reader's."""
    lines = lines_of(text)
    env = lines[0]
    a = api.parse(text)
    e = a.message.envelope
    base = (e.sender.text, [r.text for r in e.recipients], e.time.text)
    if name == "version-leading-zero":
        envelope = W.envelope(*base, version=("0.010", L.release["version"],
                                              L.protocol["version"]))
        return W.message(envelope, lines[1:], integrity=True)
    if name == "later-release":
        # a message of a language release after the reader's, which it does not read
        later = "%d.%d" % (versions.major(L.grammar["version"]),
                           int(L.grammar["version"].split(".")[1]) + 1)
        envelope = W.envelope(*base, version=(later, L.release["version"],
                                              L.protocol["version"]))
        return W.message(envelope, lines[1:], integrity=True)
    if name == "lexicon-before-the-least":
        envelope = W.envelope(*base, version=(L.grammar["version"], "0.6",
                                              L.protocol["version"]))
        return W.message(envelope, lines[1:], integrity=True)
    if name == "dialects-out-of-order":
        envelope = W.envelope(*base, dialects=((2, "0.2"), (1, "0.2")))
        return W.message(envelope, lines[1:], integrity=True)
    if name == "dialect-digest-plus-one":
        fields = fields_of(env)[0]
        k = fields.index(W.w("g.structure.dialect"))
        j = k + 1                          # the dialect's number, then its version
        for _ in range(2):
            while L.by_form[fields[j]].class_id == "g.numbers.numeral":
                j += 1
            j += 1
        digits = "".join(str(["zero", "one", "two", "three", "four", "five", "six", "seven",
                              "eight", "nine"].index(L.by_form[w].name))
                         for w in fields[j:j + WIDTH])
        new = W.number(str((int(digits) + 1) % 10 ** WIDTH), WIDTH)
        return reseal(lines, fields=fields[:j] + new + fields[j + WIDTH + 1:])
    envelope = W.envelope(2, (1,), "1759622431", identifier=0, first_entry=0)
    if name == "understands-out-of-order":
        return W.message(envelope, [W.statement("understands", [
            ("language", ("0.10", "0.9")), ("lexicon", ("0.7",)), ("protocol", ("0.4",))])])
    if name == "lacks-two-serials":
        return W.message(envelope, [W.statement("lacks", [
            ("channel", (2,), (1, 2)), ("language", ("0.10",))])])
    raise SystemExit("unknown edit %s" % name)


def fields_unit(env):
    """The envelope counted and checked again from its fields, its trailers left off."""
    return W.unit(fields_of(env)[0])


def main():
    src = json.load(open(os.path.join(ROOT, "corpus", "source", "negative.json"),
                         encoding="utf-8"))
    gen = Generator(L)
    out_dir = os.path.join(ROOT, "corpus", "negative")
    os.makedirs(out_dir, exist_ok=True)
    for name in os.listdir(out_dir):
        os.remove(os.path.join(out_dir, name))
    for item in src["items"]:
        if "notation" in item:
            # an item may name dialects or an earlier release, as a corpus record does
            written = language_for(item, L)
            g = gen if written is L else Generator(written)
            moves = Reader(written).moves(substitute(item["notation"], written))
            sender = item.get("sender", 1)
            # an item that needs a choice of form, an act word or an idiom, states its
            # mode; full explicitness would expand the very form under test
            text = g.message(moves, item.get("mode", "full explicitness"), sender,
                             [2 if sender != 2 else 1], "1759622400", 1, integrity=True)
        elif "text" in item:
            text = item["text"]
        else:
            base = open(os.path.join(ROOT, "corpus", "conformance", item["base"] + ".txt"),
                        encoding="utf-8").read()
            text = edit(base, item["edit"])
        with open(os.path.join(out_dir, item["id"] + ".txt"), "w", encoding="utf-8") as f:
            f.write(text)
    print("%d negative items" % len(src["items"]))


if __name__ == "__main__":
    main()
