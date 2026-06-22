#!/usr/bin/env python3
"""
Full MiniDungeon end-to-end run.

Runs, in order:
  1. unity-ctx scene summarize
  2. unity-ctx prefab set startLit (dry-run)
  3. uyaml scene check (--json)
  4. testplay run (EditMode)   -- real Unity, minutes
  5. testplay run (PlayMode)   -- real Unity, minutes

Captures stdout/stderr per step and writes a report under artifacts/demo-e2e/.
Exits non-zero if any step fails. For a quick, Unity-free subset use
tools/run_demo_fast.py.

    python3 tools/run_demo_e2e.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _demo_runner import FULL_STEPS, run  # noqa: E402

if __name__ == "__main__":
    sys.exit(run(FULL_STEPS, mode="full"))
