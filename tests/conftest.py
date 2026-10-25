"""Applies the planted defect named by ROWIH_MUTANT, when set, before any test runs
(`tools/run_mutants.py`). Without it the suite runs on the reference implementation."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_name = os.environ.get("ROWIH_MUTANT")
if _name:
    from mutants import MUTANTS
    MUTANTS[_name]["apply"]()
