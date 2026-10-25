"""The run of the planted defects (specification/conformance.md#the-planted-defects,
`tools/run_mutants.py`), which the gate requires to catch every defect it plants."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import run_mutants  # noqa: E402


def test_a_run_fails_where_a_planted_defect_survives():
    assert not run_mutants.failed({"mutants": 3, "caught": 3})
    assert run_mutants.failed({"mutants": 3, "caught": 2})
