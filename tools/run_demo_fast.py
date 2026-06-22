#!/usr/bin/env python3
"""
Fast MiniDungeon checks (no Unity required, sub-second).

Runs, in order:
  1. unity-ctx scene summarize
  2. unity-ctx prefab set startLit (dry-run)
  3. uyaml scene check (--json)

Captures stdout/stderr per step and writes a report under artifacts/demo-e2e/.
Exits non-zero if any step fails. See tools/run_demo_e2e.py for the full run that
also executes the testplay EditMode and PlayMode suites.

    python3 tools/run_demo_fast.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _demo_runner import FAST_STEPS, run  # noqa: E402

if __name__ == "__main__":
    sys.exit(run(FAST_STEPS, mode="fast"))
