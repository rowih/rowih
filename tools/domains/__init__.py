"""The domains of the corpus of version 1.0, in the order their items are built. Each
module states the domain's `NAME`, the `SLUG` its item identifiers open with, and the
`SCHEMAS` its generated items come from, each a function of the shared picker and the
schema's own count of items. A domain may also state the `TOPIC` its share of the
conventional language is said about, the `DIALECTS` whose technical terms it uses,
`FIXED`, items made once each from a table, and `AUTHORED`, the items written by hand for
idiom and creative range.

A domain's items are its fixed items, the conventional language `conventional.PLACEMENT`
gives it, its dialects' terms, its tabled and its authored items, and as many generated
items as bring it to 100."""
from . import (basic, casual, coordination, correction, delegation, evidence, formal,
               humour, metalinguistic, negotiation, programming, science)
from . import conventional, terms

DOMAINS = [basic, science, formal, coordination, delegation, negotiation, correction,
           programming, evidence, casual, humour, metalinguistic]
PER_DOMAIN = 100


def items(domain, picker) -> list:
    """The domain's items as (statement, messages, authored), the generated first."""
    fixed = []
    entries = conventional.entries_for(domain.SLUG)
    if entries:
        topic = conventional.Topic(picker, **domain.TOPIC)
        fixed += [conventional.item(i, topic, n) + (False,) for n, i in enumerate(entries)]
    for dialect in getattr(domain, "DIALECTS", ()):
        fixed += [(s, m, False) for s, m in terms.items(dialect)]
    fixed += [(s, m, False) for s, m in getattr(domain, "FIXED", ())]
    fixed += [(s, m, True) for s, m in getattr(domain, "AUTHORED", ())]
    schemas = domain.SCHEMAS
    generated = [schemas[n % len(schemas)](picker, n // len(schemas)) + (False,)
                 for n in range(PER_DOMAIN - len(fixed))]
    return generated + fixed
