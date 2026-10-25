"""Protocol messages as a writer asks for them
(specification/protocol.md#protocol-messages): the parts of each statement from what the
writer gives, checked for being writable, and the message written with identifier and
first entry zero, one recipient and the integrity check value. `api.state` reads it
back."""
from __future__ import annotations

from . import data
from .negotiation import lacks_parts, understood_parts
from .writer import Envelope, StatementError, Writer

STATEMENTS = ("holds", "send-again", "not-held", "understands", "lacks")


def write_statement(kind: str, sender: int, recipient: int, time, channels=(), entries=(),
                    about: str | None = None, signer=None) -> str:
    """The protocol message `api.state` writes, before it is read back."""
    if kind not in STATEMENTS:
        raise StatementError("no statement %r: the statements are %s" % (
            kind, ", ".join(STATEMENTS)))
    envelope = Envelope(sender, (recipient,), time, identifier=0, first_entry=0)
    channels, entries = _channels(channels), _naturals(entries, "entries")
    if kind in ("understands", "lacks") and (channels or entries):
        raise StatementError("%s takes no channels or entries" % kind)
    if kind != "lacks" and about is not None:
        raise StatementError("only lacks names a received message")
    if kind == "holds" and (entries or not channels):
        raise StatementError("holds states the serials held of one or more channels")
    if kind in ("send-again", "not-held") and not (channels or entries):
        raise StatementError("%s names serials of a channel, entries, or both" % kind)
    if kind == "understands":
        parts = understood_parts()
    elif kind == "lacks":
        parts = _lacks(about, recipient)
    else:
        parts = [("channel", r, s) for r, s in channels]
        parts += [("entries", entries)] if entries else []
    w = Writer(data.load())
    words = w.envelope(sender=envelope.sender, recipients=envelope.recipients,
                       time=envelope.time, identifier=0, first_entry=0)
    return w.message(words, [w.statement(kind, parts)], integrity=True, signer=signer)


def _lacks(about, recipient: int) -> list:
    """The parts of `LACKS` for the received message `about`."""
    if not isinstance(about, str):
        raise StatementError("lacks names the received message it cannot read")
    from .api import parse
    a = parse(about)
    if a.message is None:
        raise StatementError("what lacks names is not a message: %s"
                             % "; ".join(d.as_text() for d in a.diagnostics[:3]))
    env = a.message.envelope
    if env.sender.text != str(recipient):
        raise StatementError("lacks goes to the sender of the message it names, "
                             "participant %s" % env.sender.text)
    if not a.lacking:
        raise StatementError("this reader lacks nothing the message names")
    return lacks_parts(tuple(int(r.text) for r in env.recipients),
                       env.identifier.integer(), a.lacking)


def _naturals(values, what: str) -> tuple:
    """`values`, the statement's `what`, as whole numbers of zero or more."""
    if not isinstance(values, (list, tuple)):
        raise StatementError("the %s are a list of whole numbers, not %r" % (what, values))
    out = []
    for v in values:
        if isinstance(v, bool) or not isinstance(v, int) or v < 0:
            raise StatementError("each of the %s is a whole number of zero or more, not %r"
                                 % (what, v))
        out.append(v)
    return tuple(out)


def _channels(channels) -> list:
    out = []
    for c in channels:
        try:
            recipients, serials = c
        except (TypeError, ValueError):
            raise StatementError("a channel is a pair of its recipients and its serials, "
                                 "not %r" % (c,)) from None
        recipients = _naturals(recipients, "recipients")
        serials = _naturals(serials, "serials")
        if not recipients or not serials:
            raise StatementError("a channel names one or more recipients and serials")
        out.append((recipients, serials))
    return out
