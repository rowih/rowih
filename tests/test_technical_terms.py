"""The technical terms of version 1.0
(specification/dialects.md#dialects-registers-and-technical-terms): five new terms for
each of the eleven communities, in each dialect's next release, which bring the technical
terms to 110; each read by its composition, and in the five dialects that give compressed
forms each given a form a reader holds only from the new release."""
from rowih import data, dialects
from rowih.lexer import segment

LANG = data.load()
TECHNICAL = ["mathematics", "programming", "machine-learning", "robotics", "science",
             "philosophy", "linguistics", "security", "databases", "planning", "negotiation"]
WITH_FORMS = ["mathematics", "programming", "robotics", "science", "security"]


def releases_of(slug):
    return sorted((r for r in data.dialect_releases().values() if r["dialect"] == slug),
                  key=lambda r: [int(x) for x in r["version"].split(".")])


def current(release):
    return [t for t in release["terms"] if not t["version"]["deprecated"]]


def reformed(release) -> set:
    """The terms a release forms again on a root that replaces a redesigned one, with
    their forms."""
    return {x["replaced by"] for x in release["terms"] + release.get("forms", [])
            if x.get("replaced by")}


def as_released(x: dict, version: str) -> dict:
    """A term or form as the release before `version` released it, without the
    deprecation `version` adds."""
    if x["version"]["deprecated"] != version:
        return x
    out = {k: v for k, v in x.items() if k != "replaced by"}
    out["version"] = dict(x["version"], deprecated=None)
    return out


def test_each_technical_community_has_ten_terms_and_110_in_all():
    latest = {slug: releases_of(slug)[-1] for slug in TECHNICAL}
    assert {slug: len(current(r)) for slug, r in latest.items()} == dict.fromkeys(TECHNICAL, 10)
    assert sum(len(current(r)) for r in latest.values()) == 110
    assert len(current(releases_of("conversation")[-1])) == 5
    for slug, r in latest.items():
        assert r["formed from lexicon"] == "1.0" and r["digest"] == dialects.digest(r)


def test_every_new_term_is_its_stems_read_by_composition():
    for slug in TECHNICAL:
        latest = releases_of(slug)[-1]
        new = [t for t in latest["terms"] if t["version"]["introduced"] == latest["version"]]
        assert len([t for t in new if t["machine identifier"] not in reformed(latest)]) == 5
        for t in new:
            morphemes = segment(t["orthographic form"], LANG)
            assert morphemes is not None, (slug, t["term"])
            stems = [m.identifier for m in morphemes if m != "linker"]
            assert stems == [i for stem in t["formed from"] for i in stem], (slug, t["term"])


def test_earlier_releases_are_kept_as_released():
    for slug in TECHNICAL:
        earlier, latest = releases_of(slug)[-2], releases_of(slug)[-1]
        assert earlier["digest"] == dialects.digest(earlier)
        v = latest["version"]
        assert [as_released(t, v) for t in latest["terms"][:len(earlier["terms"])]] \
            == earlier["terms"]
        assert [as_released(f, v) for f in latest.get("forms", [])[
            :len(earlier.get("forms", []))]] == earlier.get("forms", [])


def test_a_new_compressed_form_is_read_only_under_the_new_release():
    for slug in WITH_FORMS:
        earlier, latest = releases_of(slug)[-2], releases_of(slug)[-1]
        new = latest["forms"][len(earlier["forms"]):]
        assert len([f for f in new if f["machine identifier"] not in reformed(latest)]) == 5
        with_new = data.load(dialects=((latest["number"], latest["version"]),))
        with_old = data.load(dialects=((earlier["number"], earlier["version"]),))
        for f in new:
            form = f["orthographic form"]
            assert len(form) == 5 and form[0] == "r" and form not in LANG.by_form
            assert with_new.by_form[form].kind == "dialect"
            assert form not in with_old.by_form
            term = next(t for t in latest["terms"] if t["machine identifier"]
                        == f["expansion"]["term"])
            assert term["term"] == f["key"] and term["version"]["introduced"] == latest["version"]
