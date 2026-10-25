"""Check that the data are what the build writes from the sources
(governance/README.md#the-regenerated-data): copy the repository's files into a temporary
directory, run the rebuild order there, and report every file the rebuild adds, changes or
removes. The data in `language/`, `lexicon/` and `corpus/` are never edited by hand; a
change edits the sources in `tools/` and commits what the rebuild writes, so a difference
here means the data and their sources disagree.

Run from the repository root: `python3 tools/check_rebuild.py`. It exits with 0 when the
rebuild changes nothing, 1 when it changes something, and 2 when a step fails."""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# the rebuild order: the language and its lexicon, the corpus and what is measured on it
ORDER = ("build_language", "build_domains", "build_corpus", "compute_maxima",
         "build_negative", "gloss_corpus", "measure_usage", "count_classes")
# a step that runs longer than this has failed; the whole order takes under a minute
STEP_TIMEOUT = 900
# directories the rebuild never reads, which hold caches of fetched files or tools
IGNORED = ("__pycache__", "cache", ".pytest_cache", "node_modules", ".git", ".venv")


class StepFailed(RuntimeError):
    """A step of the rebuild exited with an error or ran past its time."""


def _sources(root: str) -> list:
    """The files of the repository: those git tracks and those it does not ignore, so that
    a change not yet committed is rebuilt as it stands."""
    out = set()
    for args in (["ls-files", "-z"], ["ls-files", "-z", "--others", "--exclude-standard"]):
        proc = subprocess.run(["git"] + args, cwd=root, capture_output=True, check=True,
                              timeout=60)
        out.update(p for p in proc.stdout.decode("utf-8").split("\0") if p)
    return sorted(p for p in out if os.path.isfile(os.path.join(root, p)))


def _copy(source: str, target: str) -> None:
    for path in _sources(source):
        os.makedirs(os.path.dirname(os.path.join(target, path)), exist_ok=True)
        shutil.copy2(os.path.join(source, path), os.path.join(target, path))


def _files(root: str) -> dict:
    """Every file of a copy, by its path, with its bytes."""
    out = {}
    for directory, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORED]
        for f in files:
            path = os.path.join(directory, f)
            with open(path, "rb") as handle:
                out[os.path.relpath(path, root)] = handle.read()
    return out


def rebuild(source: str = ROOT, steps=ORDER, plant=None) -> dict:
    """The files the rebuild of a copy of `source` adds, changes and removes. `plant`, a
    function of the copy's root, changes the copy before the rebuild, as a test does to
    show that the check finds a difference."""
    with tempfile.TemporaryDirectory(prefix="rowih-rebuild-") as copy:
        _copy(source, copy)
        if plant is not None:
            plant(copy)
        before = _files(copy)
        for step in steps:
            try:
                proc = subprocess.run([sys.executable, os.path.join("tools", step + ".py")],
                                      cwd=copy, capture_output=True, text=True,
                                      timeout=STEP_TIMEOUT)
            except subprocess.TimeoutExpired as e:
                raise StepFailed("%s ran past %d seconds" % (step, STEP_TIMEOUT)) from e
            if proc.returncode != 0:
                raise StepFailed("%s exited with %d: %s" % (step, proc.returncode,
                                                            proc.stderr[-2000:]))
        after = _files(copy)
    return {"added": sorted(set(after) - set(before)),
            "changed": sorted(p for p in set(before) & set(after) if before[p] != after[p]),
            "removed": sorted(set(before) - set(after))}


def main() -> int:
    try:
        found = rebuild()
    except StepFailed as e:
        print("the rebuild failed: %s" % e, file=sys.stderr)
        return 2
    for kind in ("added", "changed", "removed"):
        for path in found[kind]:
            print("%s %s" % (kind, path))
    if any(found.values()):
        print("the data differ from what the sources build: rebuild in the order above "
              "and commit what it writes", file=sys.stderr)
        return 1
    print("the data are what the sources build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
