"""The conventional expressions and idioms of lexicon 1.0 in use
(specification/lexicon.md#conventional-expressions-and-idioms): each entry said in an
exchange that meets its pragmatic conditions, written with the idiom mark over the literal
structure the lexicon states for it, its slots filled with what the exchange supplies, in
a register the entry admits.

An entry's scene is the exchange its conditions call for: an opening before any other
move, thanks after the hearer's work, an acknowledgement naming the move it acknowledges,
an answer to the question it answers. A formula states content and never force, so the act
stays in the move's head beside it. The scene's other moves are about the domain's own
matter, a `Topic` of tasks, contents and things, so that each item says something the
domain's agents would say."""
from .compose import Exchange
from .courtesy import apologising, closing, opening, permission, thanking, wishing
from .grounding import acknowledging, clarifying, confirming, repairing
from .occasions import conversational, remark
from .phrasing import LANG, Topic
from .stance import answering_position, doubting, warning
from .work import (after_work, asking_status, compressed, offering, reminding, status,
                   turn)

__all__ = ["Topic", "LANG", "PLACEMENT", "domain_of", "entries_for", "item"]

SCENES = {
    "greeting": opening, "closure": closing, "thanks": thanking, "apologies": apologising,
    "acknowledgements": acknowledging, "confirmations": confirming,
    "requests for clarification": clarifying, "conversational repair": repairing,
    "warnings": warning, "agreement": answering_position,
    "disagreement": answering_position, "refusals": answering_position,
    "uncertainty": doubting, "status reports": status, "requests for status": asking_status,
    "offers": offering, "praise": after_work, "encouragement": after_work,
    "congratulations": after_work, "reminders": reminding, "turn-taking": turn,
    "well-wishing": wishing, "sympathy": wishing, "invitations": wishing,
    "requests for permission": permission,
    "conversational idioms": conversational, "compressed expressions": compressed,
    "agentic idioms": remark, "computational idioms": remark, "epistemic idioms": remark,
    "negotiation idioms": remark, "metaphorical expressions": remark,
    "humorous expressions": remark,
}



# The domain each class of the conventional language is said in, and the entries said in a
# domain other than their class's.
PLACEMENT = {
    "basic": ["greeting", "closure", "thanks"],
    "coordination": ["acknowledgements", "turn-taking", "agentic idioms", "well-wishing",
                     "invitations"],
    "delegation": ["status reports", "requests for status", "compressed expressions",
                   "offers", "refusals", "reminders", "requests for permission"],
    "negotiation": ["agreement", "disagreement", "negotiation idioms"],
    "correction": ["apologies", "conversational repair", "warnings"],
    "programming": ["computational idioms"],
    "evidence": ["uncertainty", "epistemic idioms", "confirmations"],
    "casual": ["praise", "encouragement", "congratulations", "sympathy",
               "conversational idioms"],
    "humour": ["humorous expressions", "metaphorical expressions"],
    "metalinguistic": ["requests for clarification"],
}
MOVED = {
    "market opened": "negotiation", "market closed": "negotiation",
    "counted in": "casual", "resting": "casual",
    "dirty data": "programming", "enemy approaching": "programming",
    "wheel turning": "programming", "signals piling": "programming",
    "watched by a third": "programming", "dark address": "programming",
    "old version": "programming", "memory letting go": "programming",
    "encode, said short": "programming", "open, said short": "programming",
    "authenticate, said short": "programming", "test, said short": "programming",
    "publish, said short": "programming", "repair, said short": "programming",
    "search, said short": "programming", "copy, said short": "programming",
    "write, said short": "programming", "delete, said short": "programming",
    "shut, said short": "programming", "read, said short": "programming",
    "compute, said short": "programming",
}


def domain_of(ident: str) -> str:
    e = LANG.entries[ident]
    return MOVED.get(e["key"]) or next(d for d, classes in PLACEMENT.items()
                                        if e["class"] in classes)


def entries_for(slug: str) -> list:
    """The entries said in the domain `slug`, in the order of the release."""
    return [i for i in LANG.idioms if domain_of(i) == slug]


def item(ident, t, n):
    """The statement and messages of the item that says the entry."""
    x = Exchange()
    statement = SCENES[LANG.entries[ident]["class"]](x, ident, t, n)
    return statement, x.messages
