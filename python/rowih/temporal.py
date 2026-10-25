"""The temporal network of a move (specification/meaning.md#time): every time the move
writes, as a start and an end on one line, under the constraints its clock values,
relations, durations, aspects and bases impose, checked for consistency; and the tense
each situation must have, read from the network's tightest bounds.

Each constraint bounds the difference of two endpoints, strictly or not, so the network
is consistent exactly when the graph of its bounds has no cycle of negative weight. A
weight is (seconds, -strict): a strict bound weighs infinitesimally less than its value,
and a cycle is negative when its weight is below (0, 0). Bounds are added in the order
the move writes its times, with all-pairs shortest paths kept current: O(n^2) for each
bound, O(c * n^2) for c bounds over n endpoints, both bounded by the message maxima.
The arithmetic is IEEE double in the same order as the TypeScript checker's."""
from __future__ import annotations

UNIT_SECONDS = {"second": 1.0, "minute": 60.0, "hour": 3600.0, "day": 86400.0,
                "week": 604800.0, "month": 2629746.0, "year": 31556952.0}

# X stands in the relation to Y: the endpoint bounds, each (left, right, strict) for
# left < right (strict) or left <= right; an equality is two bounds.
RELATIONS = {
    "before": [("xe", "ys", True)],
    "after": [("ye", "xs", True)],
    "meets": [("xe", "ys", False), ("ys", "xe", False)],
    "met-by": [("ye", "xs", False), ("xs", "ye", False)],
    "overlaps": [("xs", "ys", True), ("ys", "xe", True), ("xe", "ye", True)],
    "overlapped-by": [("ys", "xs", True), ("xs", "ye", True), ("ye", "xe", True)],
    "starts": [("xs", "ys", False), ("ys", "xs", False), ("xe", "ye", True)],
    "started-by": [("xs", "ys", False), ("ys", "xs", False), ("ye", "xe", True)],
    "during": [("ys", "xs", True), ("xe", "ye", True)],
    "contains": [("xs", "ys", True), ("ye", "xe", True)],
    "finishes": [("xe", "ye", False), ("ye", "xe", False), ("ys", "xs", True)],
    "finished-by": [("xe", "ye", False), ("ye", "xe", False), ("xs", "ys", True)],
    "equals": [("xs", "ys", False), ("ys", "xs", False), ("xe", "ye", False),
               ("ye", "xe", False)],
}

# How an aspect places the event time against the reference time, as (left, right) pairs
# of left <= right over e (event) and r (reference) endpoints.
ASPECT_BOUNDS = {
    "stative": [("es", "rs"), ("re", "ee")],
    "progressive": [("es", "rs"), ("re", "ee")],
    "continuative": [("es", "rs"), ("re", "ee")],
    "perfective": [("rs", "es"), ("ee", "re")],
    "completive": [("rs", "ee"), ("ee", "re")],
    "interrupted": [("rs", "ee"), ("ee", "re")],
    "inceptive": [("rs", "es"), ("es", "re")],
}

ASSERTION_TIMES = ("observation-time", "inference-time", "validity-interval")
SITUATION_TIMES = ("event-time", "reference-time", "execution-time")
ZERO = (0.0, 0)
INFINITE = None


def short(identifier):
    return identifier.rsplit(".", 1)[-1] if identifier else None


def seconds(number: str):
    """A number's value as (low, high), or None where it has none: an interval a~b has
    both bounds, a ratio a/b its quotient."""
    try:
        if "~" in number:
            low, high = number.split("~", 1)
            return float(low), float(high)
        if "/" in number:
            num, den = number.split("/", 1)
            v = float(num) / float(den)
            return v, v
        v = float(number)
        return v, v
    except (ValueError, ZeroDivisionError):
        return None


def add_weights(a, b):
    return (a[0] + b[0], a[1] + b[1])


class Network:
    """Endpoints and the tightest bound on each difference: dist[u][v] bounds v - u."""

    def __init__(self):
        self.nodes: list = []
        self.dist: dict = {}

    def node(self, key) -> object:
        if key not in self.dist:
            self.dist[key] = {key: ZERO}
            self.nodes.append(key)
        return key

    def get(self, u, v):
        return self.dist[u].get(v, INFINITE)

    def bound(self, u, v, c: float, strict: bool) -> bool:
        """Add v - u <= c (or < c); False, and nothing added, if that closes a cycle of
        negative weight."""
        w = (c, -1 if strict else 0)
        back = self.get(v, u)
        if back is not None and add_weights(w, back) < ZERO:
            return False
        current = self.get(u, v)
        if current is not None and current <= w:
            return True
        into_u = [(i, self.dist[i][u]) for i in self.nodes if u in self.dist[i]]
        from_v = [(j, d) for j, d in self.dist[v].items()]
        for i, du in into_u:
            row = self.dist[i]
            for j, dv in from_v:
                cand = add_weights(add_weights(du, w), dv)
                old = row.get(j, INFINITE)
                if old is None or cand < old:
                    row[j] = cand
        return True


class Temporal:
    """The network of one move, built from its tree as `tree.from_ast_move` gives it."""

    def __init__(self, lang, communication_time: float | None):
        self.lang = lang
        self.net = Network()
        self.comm = self.net.node("comm")
        self.epoch = None
        self.communication_time = communication_time
        self.named: dict = {}
        self.parents: dict = {}
        self.failure = None
        self.deadline = None
        self.ill_typed: list = []

    # ------------------------------------------------------------ building
    def build(self, t: dict) -> dict | None:
        """The part whose time closed a contradiction, or None where every time can hold
        together."""
        for c in t["constituents"]:
            self._index(c, None)
        if t.get("deadline"):
            ds, de = self.endpoints(("deadline",))
            self.point(ds, de, t["deadline"], t)
            self.deadline = (ds, de)
        world = move_world(t)
        for c in t["constituents"]:
            self._unit(c, world)
            if self.failure is not None:
                return self.failure
        return self.failure

    def _index(self, node: dict, parent):
        if not isinstance(node, dict):
            return
        k = node.get("kind")
        if k in ("assertion", "situation", "term"):
            self.parents[id(node)] = parent
            if node.get("name") is not None:
                self.named[node["name"]] = node
            for p in node["parts"]:
                if p["kind"] == "filler":
                    self._index(p["filler"], node)
                elif p["kind"] in ("assertion", "situation", "term", "readings"):
                    self._index(p, node)
        elif k == "readings":
            for r in node["readings"]:
                self._index(r, parent)

    def endpoints(self, key):
        return self.net.node(key + ("start",)), self.net.node(key + ("end",))

    def unit_times(self, unit: dict, index: str):
        s, e = self.endpoints((id(unit), index))
        self.before(s, e, False, unit)
        return s, e

    def require(self, u, v, c, strict, blame):
        """v - u <= c, or the contradiction is recorded against `blame`."""
        if self.failure is None and not self.net.bound(u, v, c, strict):
            self.failure = blame

    def before(self, a, b, strict, blame):
        """a < b (strict) or a <= b."""
        self.require(b, a, 0.0, strict, blame)

    def equal(self, u, v, c, blame):
        """v - u = c."""
        self.require(u, v, c, False, blame)
        self.require(v, u, -c, False, blame)

    def _unit(self, node: dict, world: str):
        k = node.get("kind")
        if k == "readings":
            for r in node["readings"]:
                self._unit(r, world)
            return
        if k not in ("assertion", "situation", "term"):
            return
        written = [short(p["member"]) for p in node["parts"] if p["kind"] == "value"
                   and p["member"].startswith("g.situations-and-contents.world-of-evaluation.")]
        if written:
            world = written[0]
        for p in node["parts"]:
            if p["kind"] == "time":
                s, e = self.unit_times(node, short(p["index"]))
                self.spec(s, e, p["spec"], node, p)
        if k == "assertion":
            self.assertion(node, world)
        if k == "situation":
            self.aspect(node)
        for p in node["parts"]:
            if p["kind"] == "filler":
                self._unit(p["filler"], world)
            elif p["kind"] in ("assertion", "situation", "term", "readings"):
                self._unit(p, world)

    # ------------------------------------------------------------ times
    def spec(self, s, e, spec: dict, unit: dict, blame: dict):
        k = spec["kind"]
        if k in ("now", "absolute", "offset"):
            self.point(s, e, spec, blame)
        elif k == "relation":
            self.relation(s, e, spec, unit, blame)
        elif k == "interval":
            self.endpoint(s, spec["from"], unit, blame)
            self.endpoint(e, spec["until"], unit, blame)
        elif k == "duration":
            self.duration(s, e, spec, blame)

    def clock(self, spec: dict):
        """The endpoint a clock value names and its distance from it, or None."""
        k = spec["kind"]
        if k == "now":
            return self.comm, 0.0
        if k == "absolute":
            v = seconds(spec["number"])
            if v is None or v[0] != v[1]:
                return None
            return self.epoch_node(), v[0]
        if k == "offset":
            v = seconds(spec["number"])
            if v is None or v[0] != v[1]:
                return None
            d = v[0] * UNIT_SECONDS[short(spec["unit"])]
            return self.comm, -d if short(spec["anchor"]) == "ago" else d
        return None

    def epoch_node(self):
        if self.epoch is None:
            self.epoch = self.net.node("epoch")
            if self.communication_time is not None:
                self.equal(self.epoch, self.comm, self.communication_time, None)
        return self.epoch

    def point(self, s, e, spec: dict, blame):
        placed = self.clock(spec)
        self.equal(s, e, 0.0, blame)
        if placed is not None:
            anchor, d = placed
            self.equal(anchor, s, d, blame)

    def endpoint(self, p, spec: dict, unit: dict, blame):
        """One end of an interval: a clock value, or a point in a relation."""
        if spec["kind"] == "relation":
            self.relation(p, p, spec, unit, blame)
        else:
            self.point(p, p, spec, blame)

    def reference(self, ref: dict, unit: dict, blame):
        """The endpoints a relation's reference names."""
        if ref["kind"] == "index":
            index = short(ref["index"])
            if ref.get("unit") is not None:
                target = self.named.get(ref["unit"]["name"])
                if target is None:
                    return self.endpoints(("unnamed", ref["unit"]["name"], index))
                bears = ASSERTION_TIMES if target["kind"] == "assertion" else \
                    SITUATION_TIMES if target["kind"] == "situation" else ()
                if index not in bears:
                    self.ill_typed.append((blame, target["kind"], index))
                return self.unit_times(target, index)
            return self.bare(index, unit)
        s, e = self.endpoints(("reference", id(ref)))
        self.point(s, e, ref, blame)
        return s, e

    def bare(self, index: str, unit: dict):
        """A bare index names that index of the nearest unit that bears it."""
        if index == "communication-time":
            return self.comm, self.comm
        if index == "deadline":
            return self.deadline if self.deadline else self.endpoints(("deadline",))
        node = unit
        while node is not None:
            kind = node["kind"]
            if (kind == "assertion" and index in ASSERTION_TIMES) or \
                    (kind == "situation" and index in SITUATION_TIMES):
                return self.unit_times(node, index)
            node = self.parents.get(id(node))
        return self.endpoints(("unplaced", id(unit), index))

    def relation(self, xs, xe, spec: dict, unit: dict, blame):
        ys, ye = self.reference(spec["reference"], unit, blame)
        ends = {"xs": xs, "xe": xe, "ys": ys, "ye": ye}
        for left, right, strict in RELATIONS[short(spec["relation"])]:
            self.before(ends[left], ends[right], strict, blame)

    def duration(self, s, e, spec: dict, blame):
        v = seconds(spec["number"])
        if v is None:
            return
        unit = UNIT_SECONDS[short(spec["unit"])]
        low, high = v[0] * unit, v[1] * unit
        comparator = short(spec.get("comparator")) or "exactly"
        if comparator in ("exactly", "at-least"):
            self.require(e, s, -low, False, blame)
        if comparator in ("exactly", "at-most"):
            self.require(s, e, high, False, blame)

    # ------------------------------------------------------------ the language's bounds
    def written(self, unit: dict, index: str) -> bool:
        return any(p["kind"] == "time" and short(p["index"]) == index for p in unit["parts"])

    def assertion(self, node: dict, world: str):
        """The ordered times, and observation after the start of what is observed."""
        has_obs = self.written(node, "observation-time")
        has_inf = self.written(node, "inference-time")
        if has_obs:
            os_, oe = self.unit_times(node, "observation-time")
            self.before(os_, self.comm, False, node)
        if has_inf:
            is_, ie = self.unit_times(node, "inference-time")
            self.before(is_, self.comm, False, node)
        if has_obs and has_inf:
            self.before(os_, is_, False, node)
        basis = [short(p["member"]) for p in node["parts"] if p["kind"] == "value"
                 and p["member"].startswith("g.standing.basis.")]
        if basis != ["observation"] or world != "actual":
            return
        seen = oe if has_obs else self.comm
        for p in node["parts"]:
            target = p if p["kind"] == "situation" else \
                self.named.get(p["name"]) if p["kind"] == "same" else None
            if target is None or target.get("kind") != "situation":
                continue
            if self.world_of(target, world) != "actual" or \
                    not self.written(target, "event-time"):
                continue
            es, ee = self.unit_times(target, "event-time")
            blame = next(q for q in target["parts"] if q["kind"] == "time"
                         and short(q["index"]) == "event-time")
            self.before(es, seen, False, blame)

    def world_of(self, node: dict, inherited: str) -> str:
        written = [short(p["member"]) for p in node["parts"] if p["kind"] == "value"
                   and p["member"].startswith("g.situations-and-contents.world-of-evaluation.")]
        return written[0] if written else inherited

    def aspect(self, node: dict):
        if not (self.written(node, "event-time") and self.written(node, "reference-time")):
            return
        aspect = situation_aspect(node, self.lang)
        bounds = ASPECT_BOUNDS.get(aspect)
        if not bounds:
            return
        es, ee = self.unit_times(node, "event-time")
        rs, re_ = self.unit_times(node, "reference-time")
        ends = {"es": es, "ee": ee, "rs": rs, "re": re_}
        blame = next(q for q in node["parts"] if q["kind"] == "time"
                     and short(q["index"]) == "reference-time")
        for left, right in bounds:
            self.before(ends[left], ends[right], False, blame)

    # ------------------------------------------------------------ derived tense
    def tense(self, situation: dict) -> str:
        """Past, present or future where every placement the network allows agrees, and
        undetermined otherwise."""
        if not self.written(situation, "event-time"):
            return "undetermined"
        s, e = self.unit_times(situation, "event-time")
        net = self.net
        if _below(net.get(self.comm, e)):
            return "past"
        if _below(net.get(s, self.comm)):
            return "future"
        up_s, down_e = net.get(self.comm, s), net.get(e, self.comm)
        if up_s is not None and up_s <= ZERO and down_e is not None and down_e <= ZERO:
            return "present"
        return "undetermined"


def _below(w) -> bool:
    """A bound that holds only below zero: v - u < 0 in every placement."""
    return w is not None and w < ZERO


def situation_aspect(node: dict, lang) -> str | None:
    """The aspect written, or the default the normal form gives: the root's lexical
    aspect, stative for an attitude or a reported normative state, none for a joined
    content."""
    from .formation import word_sort
    from .normal import ASPECT_OF_SORT
    parts = node["parts"]
    for p in parts:
        if p["kind"] == "value" and p["member"].startswith("g.situations-and-contents.aspect."):
            return short(p["member"])
    if any((p["kind"] == "value" and p["member"].startswith(
            "g.situations-and-contents.connective.")) or
           (p["kind"] == "filler" and short(p["role"]) == "condition") for p in parts):
        return None
    for p in parts:
        if p["kind"] == "word" and (p.get("entry") or p.get("status") == "formation"):
            # a formation's sort is the one its parts give (`inv.word-formation`)
            sort = word_sort(p, lang)
            if sort in ASPECT_OF_SORT:
                return ASPECT_OF_SORT[sort]
            break
    if any(p["kind"] == "value" and (
            p["member"].startswith("g.attitudes-and-aims.kind-of-attitude.") or
            p["member"].startswith("g.force.kind-of-normative-entry.")) for p in parts):
        return "stative"
    return None


def derived(t: dict, lang, communication_time: float | None) -> list:
    """The tense of each situation evaluated in the actual world, and whether each
    assertion is a prediction (specification/meaning.md#time), in the order the move
    writes its units; none where the move's times cannot all hold."""
    net = Temporal(lang, communication_time)
    if net.build(t) is not None:
        return []
    out = []
    counts = {"assertion": 0, "situation": 0}

    def walk(node: dict, world: str):
        k = node.get("kind")
        if k == "readings":
            for r in node["readings"]:
                walk(r, world)
            return
        if k not in ("assertion", "situation", "term"):
            return
        world = net.world_of(node, world)
        if k in counts:
            counts[k] += 1
        if k == "situation" and world == "actual":
            out.append({"unit": "situation", "ordinal": counts[k], "name": node.get("name"),
                        "tense": net.tense(node)})
        if k == "assertion":
            direct = [p if p["kind"] == "situation" else net.named.get(p.get("name"))
                      for p in node["parts"] if p["kind"] in ("situation", "same")]
            future = any(s is not None and s.get("kind") == "situation" and
                         net.world_of(s, world) == "actual" and net.tense(s) == "future"
                         for s in direct)
            out.append({"unit": "assertion", "ordinal": counts[k], "name": node.get("name"),
                        "prediction": future})
        for p in node["parts"]:
            if p["kind"] == "filler":
                walk(p["filler"], world)
            elif p["kind"] in ("assertion", "situation", "term", "readings"):
                walk(p, world)

    for c in t["constituents"]:
        if isinstance(c, dict):
            walk(c, move_world(t))
    return out


def move_world(t: dict) -> str:
    """The world a move's content is evaluated in, as the normal form gives it: a
    supposition's within the supposition, every other move's the actual world."""
    adds = t["adds"][0].rsplit(".", 1)[-1] if t.get("adds") else None
    return "within-a-supposition" if adds == "supposition" else "actual"
