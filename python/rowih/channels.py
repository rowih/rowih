"""Channels and their serials
(specification/protocol.md#channels-acknowledgement-and-repair). A message's identifier is
its serial on its channel, the channel being its sender and the set of its recipients, so
that a hearer knows from the serials which of a sender's messages it lacks up to the
latest it has received, and recognises a duplicate or a replay as such (`inv.gaps-known`).

A serial counts as received when its message arrived intact, whatever the view then
did with it: a message its checker refused was still held. It counts as damaged when
the counted, checked envelope arrived and the rest did not, intact: the message failed
its integrity check value, or carried none and had a word or a move rejected. A hearer
asks again for what is damaged as for what is missing."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

# The diagnostics that show a message arrived damaged rather than written ill-formed.
DAMAGE = ("d.check-values.integrity-mismatch",)


@dataclass
class Channel:
    sender: str
    recipients: tuple              # participant numbers as text, ascending
    # each serial received intact, with the digest of the canonical serialisation that
    # arrived under it, so that another message under a serial already held is told
    # from a duplicate
    received: dict = field(default_factory=dict)
    damaged: set = field(default_factory=set)
    # serials both parties record as lost: asked for, and stated not held by the sender
    lost: set = field(default_factory=set)

    @property
    def highest(self) -> int:
        return max(list(self.received) + list(self.damaged) + list(self.lost), default=0)

    def lacking(self) -> list:
        """Each serial up to the highest known that is not held intact and not recorded
        as lost, the damaged among them."""
        return [s for s in range(1, self.highest + 1)
                if s not in self.received and s not in self.lost]

    def holding(self) -> tuple:
        """What an acknowledgement states of the channel: the last serial held with none
        missing before it, then each serial held beyond that one."""
        through = 0
        while through + 1 in self.received:
            through += 1
        return (through,) + tuple(sorted(s for s in self.received if s > through + 1))


def key_of(envelope) -> tuple:
    """The channel a message travels on: its sender and the set of its recipients."""
    return (envelope.sender.text,
            tuple(str(r) for r in sorted({r.integer() for r in envelope.recipients})))


def digest(canonical: str) -> str:
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def damaged(analysis) -> bool:
    """Whether a message whose envelope parsed arrived damaged: it failed its integrity
    check value, or it carries none and a word or a move of it was rejected, which
    without the value cannot be told from damage."""
    codes = {d.code for d in analysis.diagnostics}
    if codes & set(DAMAGE):
        return True
    env = analysis.message.envelope
    return env.integrity is None and any(
        d.code.startswith(("d.parser.", "d.lexer.", "d.tokenizer."))
        and d.recoverability != "kept opaque" for d in analysis.diagnostics)


def note(channels: dict, analysis) -> str:
    """Record a message whose envelope parsed on its channel. Returns what it was: new,
    a duplicate of one held, another message under a serial already held, damaged, or a
    protocol message, which takes no serial."""
    env = analysis.message.envelope
    if env.is_protocol:
        return "protocol"
    k = key_of(env)
    channel = channels.setdefault(k, Channel(*k))
    serial = env.identifier.integer()
    if damaged(analysis):
        if serial not in channel.received:
            channel.damaged.add(serial)
        return "damaged"
    d = digest(analysis.canonical)
    if serial in channel.received:
        return "duplicate" if channel.received[serial] == d else "serial-reused"
    channel.received[serial] = d
    channel.damaged.discard(serial)
    channel.lost.discard(serial)
    return "new"


def lacks(channels: dict, participant: str) -> dict:
    """What a participant lacks on each channel it is a recipient of, as {channel:
    serials}; channels it lacks nothing on are left out."""
    out = {}
    for k, channel in channels.items():
        if participant in channel.recipients and channel.sender != participant:
            missing = channel.lacking()
            if missing:
                out[k] = missing
    return out
