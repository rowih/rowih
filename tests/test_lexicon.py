"""The lexicon checks (specification/conformance.md#the-conformance-suite), each run first
against a planted defect so that a check which cannot fail is not counted."""
import copy
import dataclasses

from rowih import data, lexicon_checks as lc

LANG = data.load()


def codes(findings):
    return {code for code, _ in findings}


def with_word(lang, form, protected=False):
    """A copy of the language with one more word of the given form."""
    planted = copy.copy(lang)
    planted.by_form = dict(lang.by_form)
    planted.by_form[form] = dataclasses.replace(next(iter(lang.by_form.values())), form=form,
                                                protected=protected, identifier="planted")
    return planted


def test_release_passes_every_check():
    assert lc.check_release(LANG) == []


def test_release_counts():
    # the core's 54 classes, the declared loss of language 0.5, the register of language
    # 0.6, and the protocol statement and its parts of language 0.9
    assert len(LANG.grammar["classes"]) == 58
    # the core's 262 members, the first entry of language 0.3, the five declared losses,
    # the eight registers, the authentication field and the six words of the protocol
    # statement of language 0.9, and the six of version negotiation of language 0.10;
    # every member states the release that introduced it
    assert sum(len(c["members"]) for c in LANG.grammar["classes"]) == 289
    assert all("introduced" in m for c in LANG.grammar["classes"] for m in c["members"])
    later = [m["identifier"] for c in LANG.grammar["classes"] for m in c["members"]
             if m["introduced"] != "0.1"]
    registers = ["g.ambiguity-and-figures.register." + m for m in (
        "raw", "protocol", "standard", "explanatory", "formal", "casual", "playful",
        "ceremonial")]
    assert later == ["g.message.message-field.first-entry",
                     "g.message.message-field.authentication"] + [
        "g.ambiguity-and-figures.declared-loss." + m for m in (
            "register", "diction", "stance", "relation-between-participants", "wording")] + \
        registers + ["g.protocol.protocol-statement." + m for m in (
            "holds", "send-again", "not-held", "understands", "lacks")] + [
                "g.protocol.statement-part." + m for m in (
                    "channel", "serials", "entries", "language-version", "lexicon-version",
                    "protocol-version", "lacking-features")]
    grammar_critical = [m for c in LANG.grammar["classes"] if c["critical dimension"]
                        for m in c["members"]]
    assert len(grammar_critical) == 151
    # the grammar's members first, in the order of the grammar, then the appended words
    assert LANG.grammar["critical forms"][:151] == [m["identifier"] for m in grammar_critical]
    # release 0.3 appends the idiom mark and its 25 act words
    assert LANG.grammar["critical forms"][189] == \
        "g.ambiguity-and-figures.idiom-selection.idiom-entry"
    acts = [i for i, e in LANG.entries.items() if e["grammatical category"] == "act word"]
    assert LANG.grammar["critical forms"][190:215] == acts and len(acts) == 25
    # release 0.4 appends the eight registers, two of which are precision-bound by
    # default, release 0.6 the message serial, and release 0.7 the dialect word, neither
    # of whose codes moves the modulus
    assert LANG.grammar["critical forms"][215:223] == registers
    assert LANG.grammar["critical forms"][223:225] == ["g.structure.message-serial",
                                                       "g.structure.dialect"]
    # lexicon 1.0 appends its ten units of measure, and major version 1 takes the largest
    # prime the 346 admissible forms of the h code allow
    units = [i for i, e in LANG.entries.items() if e["grammatical category"] == "unit of measure"
             and e["version"]["introduced"] == "1.0"]
    assert LANG.grammar["critical forms"][225:] == units and len(units) == 10
    assert len(LANG.grammar["critical forms"]) == 235
    assert LANG.grammar["move check word"]["admissible forms"] == 346
    assert LANG.modulus == 337
    # a register-marked synonym names its base's concept again, and a conventional sense
    # extends its root's, so neither is a root of its own; the core has 50 to 100 roots,
    # and later releases grow toward the 500 of version 1.0, release 0.5 adding four,
    # release 0.6 three and release 0.7 four
    def roots(lang):
        return [e for e in lang.entries.values() if (
            e["grammatical category"].endswith("root")
            or e["grammatical category"] in ("unit of measure", "discourse relation"))
            and "synonym of" not in e and data.in_force(lang, e)]
    assert 50 <= len(roots(data.load("0.1"))) <= 100
    assert len(roots(data.load("0.7"))) == 108
    assert [e["key"] for e in roots(data.load("0.7"))][-11:] == [
        "analogous", "confine", "elegant", "clumsy", "forget", "authenticate", "acknowledge",
        "version", "feature", "dialect", "deprecate"]
    # lexicon 1.0 reaches 500 roots, every one of its own a long root of seven symbols
    # opened by nu
    assert len(roots(LANG)) == 500
    added = [e for e in roots(LANG) if e["version"]["introduced"] == "1.0"]
    # the two that replace released roots the resemblance audit redesigned, which are
    # deprecated in lexicon 1.0
    assert len(added) == 394
    assert sorted(e["key"] for e in added if "replaces" in e) == ["assent", "move"]
    assert all(len(e["orthographic form"]) == 7 and e["orthographic form"].startswith("nu")
               for e in added)
    assert all(len(e["orthographic form"]) == 5 for e in roots(LANG) if e not in added)


def test_word_one_edit_from_another_is_found():
    lowering = LANG.form_of("g.force.change-made.lowering")
    other = LANG.form_of("g.reference.person.self")
    planted = with_word(LANG, other[:-1] + ("a" if other[-1] != "a" else "e"))
    assert "distance-below-two" in codes(lc.check_release(planted))
    assert lowering not in {w for _, w in lc.check_release(planted)}


def test_protected_word_two_edits_from_another_is_found():
    lowering = LANG.form_of("g.force.change-made.lowering")
    near = lowering[:2] + ("a" if lowering[2] != "a" else "e") + lowering[3:4] + (
        "a" if lowering[4] != "a" else "e") + lowering[5:]
    assert lc.levenshtein(near, lowering) == 2
    planted = with_word(LANG, near)
    assert "protected-distance-below-three" in codes(lc.check_release(planted))


def test_vowel_initial_word_is_found():
    planted = with_word(LANG, "apaka")
    assert "not-consonant-initial" in codes(lc.check_release(planted))


def test_dangling_suffix_test_finds_a_planted_collision():
    assert lc.check_decodability(["a", "ab", "ba"]) == ["a"]
    assert lc.check_decodability(["0", "10", "110", "111"]) == []


def test_lexicon_is_not_decodable_once_a_collision_is_planted():
    # A word that is the concatenation of two words makes the code ambiguous.
    first = LANG.form_of("g.structure.term")
    second = LANG.form_of("g.structure.end-term")
    planted = with_word(LANG, first + second)
    assert "not-uniquely-decodable" in codes(lc.check_release(planted))


def test_modulus_rule_is_checked():
    planted = copy.copy(LANG)
    planted.modulus = 163
    assert "modulus-not-by-rule" in codes(lc.check_release(planted))


def test_least_prime_modulus_is_refused_in_major_version_1():
    # the rule of major version 0 would give 239 for lexicon 1.0's 235 critical forms,
    # which leaves no release of the major version room for a critical form
    planted = copy.copy(LANG)
    planted.modulus = 239
    planted.move_check_forms = LANG.move_check_forms[:239]
    findings = lc.check_release(planted)
    assert ("modulus-not-by-rule", "239 337") in findings
    assert "move-check-forms-not-modulus" not in codes(findings)
    # lexicon 0.7, of major version 0, keeps the least prime its 225 critical forms gave;
    # the checks of its idioms generate under the current release, so only the modulus is
    # read here
    old = data.load("0.7")
    assert old.modulus == 227 and len(old.move_check_forms) == 227
    assert old.move_check_forms == LANG.move_check_forms[:227]
    assert "modulus-not-by-rule" not in codes(lc.check_release(old))


def test_word_longer_than_its_opening_fixes_is_found():
    # a numeral opened by the long root's syllable would be four symbols where nu fixes
    # seven
    planted = copy.copy(LANG)
    planted.by_form = dict(LANG.by_form)
    numeral = LANG.items["g.numbers.numeral.zero"]
    planted.by_form["noba"] = dataclasses.replace(numeral, form="noba", identifier="planted")
    assert lc.check_release(planted) == []
    planted.by_form = dict(LANG.by_form)
    planted.by_form["nuda"] = dataclasses.replace(numeral, form="nuda", identifier="planted")
    assert "length-not-fixed-by-opening" in codes(lc.check_release(planted))


def test_every_entry_field_is_checked():
    planted = copy.copy(LANG)
    planted.entries = dict(LANG.entries)
    ident = sorted(planted.entries)[0]
    planted.entries[ident] = {k: v for k, v in planted.entries[ident].items() if k != "sort"}
    assert "entry-field-missing" in codes(lc.check_release(planted))
