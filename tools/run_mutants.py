"""Run every planted defect of `tests/mutants.py` against the test files it names, each in
its own process (specification/conformance.md#the-planted-defects). A mutant is caught
when those tests fail; one that survives is a gap in the suite. Writes
`corpus/reports/mutants.json`. Run from the repository root: `python3 tools/run_mutants.py
[workers]`. Exit status: 1 when a planted defect survives, 0 when every one is caught."""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tests"))
sys.path.insert(0, os.path.join(ROOT, "python"))

from mutants import DEFERRED, FAILURES, FAILURES_DEFERRED, MUTANTS  # noqa: E402


def run(name):
    m = MUTANTS[name]
    env = dict(os.environ, ROWIH_MUTANT=name)
    proc = subprocess.run([os.path.join(ROOT, ".venv", "bin", "python"), "-m", "pytest", "-q",
                           "-x", "-p", "no:cacheprovider"] + m["tests"],
                          cwd=ROOT, env=env, capture_output=True, text=True, timeout=1800)
    tail = proc.stdout.strip().splitlines()[-1:] if proc.stdout else []
    return name, proc.returncode, tail


def failed(report: dict) -> bool:
    """Whether a run's report shows a planted defect that its tests did not catch."""
    return report["caught"] != report["mutants"]


def main() -> int:
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    results = {}
    with ThreadPoolExecutor(workers) as pool:
        for name, code, tail in pool.map(run, sorted(MUTANTS)):
            caught = code == 1
            results[name] = {"invariant": MUTANTS[name]["invariant"],
                             "description": MUTANTS[name]["description"],
                             "tests": MUTANTS[name]["tests"], "caught": caught,
                             "exit": code, "summary": tail}
            print("%-32s %s %s" % (name, "caught" if caught else "SURVIVED(%d)" % code,
                                   tail), flush=True)
    failures = {key: {"mutant": name, "caught": results[name]["caught"] if name else None,
                      "deferred": FAILURES_DEFERRED.get(key)}
                for key, name in FAILURES.items()}
    report = {"mutants": len(results), "caught": sum(r["caught"] for r in results.values()),
              "results": results, "deferred": DEFERRED, "failures": failures}
    with open(os.path.join(ROOT, "corpus", "reports", "mutants.json"), "w",
              encoding="utf-8") as f:
        json.dump(report, f, indent=1)
        f.write("\n")
    print("%d of %d caught; %d invariants deferred" % (report["caught"], report["mutants"],
                                                         len(DEFERRED)))
    covered = [k for k, v in failures.items() if v["caught"]]
    print("failures of an implementation's origin: %d of %d planted and caught, %d deferred"
          % (len(covered), len(failures), len(FAILURES_DEFERRED)))
    return 1 if failed(report) else 0


if __name__ == "__main__":
    sys.exit(main())
