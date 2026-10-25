"""Authentication of a message (specification/protocol.md#authentication). The language
references authentication and does not provide it: it fixes what a signature covers, the
canonical serialisation of the whole message, its claims of sender and time included,
without the authentication field and the integrity check value's; it carries the signature
in a field of the envelope by a scheme the field names; and a quoted message is carried
byte for byte, so that its signature stays checkable. Keys come from the configuration of
the agent that holds them, never from a message.

Scheme 1 is Ed25519 (RFC 8032 § 5.1), through the `cryptography` package, which the
`authentication` extra installs; a call that needs it without it fails at once."""
from __future__ import annotations

from .diagnostics import Diagnostic
from . import serialise

ED25519 = 1


def _ed25519():
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
    except ImportError as e:  # the optional extra is not installed
        raise RuntimeError("authentication needs the `authentication` extra "
                           "(cryptography)") from e
    return ed25519


def covered(analysis) -> bytes:
    """The bytes an authentication covers: the canonical serialisation of the message
    without its authentication and integrity check value fields."""
    env = analysis.message.envelope
    drop = {id(w) for w in env.integrity_words}
    if env.authentication is not None:
        drop |= {id(w) for w in env.authentication.words}
    envelope = " ".join(w.form for w in env.words if id(w) not in drop)
    body = "".join(" ".join(w.form for w in line) + "\n" for line in analysis.message.lines)
    return serialise.covered(envelope, body)


def keypair(seed: bytes) -> tuple:
    """The private and public key of the 32-byte seed, as raw bytes."""
    ed25519 = _ed25519()
    from cryptography.hazmat.primitives import serialization
    private = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    public = private.public_key().public_bytes(serialization.Encoding.Raw,
                                               serialization.PublicFormat.Raw)
    return seed, public


def signer(private: bytes) -> tuple:
    """The (scheme, sign) pair `Writer.message` takes, for a raw Ed25519 private key."""
    key = _ed25519().Ed25519PrivateKey.from_private_bytes(private)
    return ED25519, key.sign


def verify(analysis, public: bytes) -> bool:
    """Whether a parsed message carries an authentication by `public` that covers it."""
    env = analysis.message.envelope
    auth = env.authentication
    if auth is None or auth.scheme.integer() != ED25519:
        return False
    from cryptography.exceptions import InvalidSignature
    key = _ed25519().Ed25519PublicKey.from_public_bytes(public)
    try:
        key.verify(auth.signature, covered(analysis))
    except InvalidSignature:
        return False
    return True


def sign(text: str, private: bytes) -> str:
    """The message `text` signed by `private`: its envelope and moves as written, the
    authentication field written after the envelope's count, and the integrity check
    value computed again over the result, since it covers the signature."""
    from .api import parse
    from .writer import Writer
    a = parse(text)
    if a.message is None:
        raise ValueError("a message that does not parse is not signed")
    env = a.message.envelope
    drop = {id(w) for w in env.integrity_words}
    if env.authentication is not None:
        drop |= {id(w) for w in env.authentication.words}
    envelope = [w.form for w in env.words if id(w) not in drop]
    moves = [[w.form for w in line] for line in a.message.lines]
    return Writer().message(envelope, moves, integrity=env.integrity is not None,
                            signer=signer(private))


def agent_of(view, analysis) -> str | None:
    """The agent a message's sender is: the binding of its participant number the view
    holds, or, for the message that makes it, the binding the message itself states."""
    from .moves import participant_binding
    sender = analysis.message.envelope.sender.text
    if sender in view.roster:
        return view.roster[sender]
    for t in analysis.moves:
        bound = participant_binding(t)
        if bound is not None and bound[0] == sender:
            return bound[1]
    return None


def key_for(view, analysis) -> bytes | None:
    """The key the view's configuration holds for a message's sender, or None."""
    agent = agent_of(view, analysis)
    return view.keys.get(agent) if agent is not None else None


def refusal(view, analysis):
    """The diagnostic of a message the view must refuse for its authentication: its
    configuration holds a key for the sender and the message does not verify by it. A
    message from an agent the view holds no key for is not checked, since a claim of
    role or principal carries no weight beyond what a hearer can verify."""
    if not view.keys:
        return None
    key = key_for(view, analysis)
    if key is None or verify(analysis, key):
        return None
    env = analysis.message.envelope
    return Diagnostic("d.view.authentication-failed", env.words[0].span,
                      expected=["an authentication by agent %s's key"
                                % agent_of(view, analysis)],
                      note="the message is refused, and its serial is not taken as held")
