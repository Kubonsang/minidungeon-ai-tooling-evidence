#!/usr/bin/env python3
"""
Shared engine for the MiniDungeon demo runners.

Two thin entry points use this module:
  - tools/run_demo_fast.py  -> fast checks only (no Unity)
  - tools/run_demo_e2e.py   -> fast checks + testplay EditMode + PlayMode

It runs documented unity-ctx / uyaml / testplay-runner commands in order, captures
stdout/stderr per step under artifacts/demo-e2e/, writes a portfolio-safe report.md
(absolute paths replaced with <repo-root>), and returns a non-zero exit code if any
step fails.

Pass criteria:
  - Every step must exit 0.
  - `uyaml scene check` additionally requires summary.errors == 0; warnings are
    non-fatal (the tool models only GameObject/Transform, so MeshRenderer/Light/etc.
    surface as warning-only `UNKNOWN_*` codes that also appear on genuine Unity files).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACT_DIR = os.path.join(PROJECT_ROOT, "artifacts", "demo-e2e")
HOME = os.path.expanduser("~")

REPO_ROOT_PLACEHOLDER = "<repo-root>"

# Catalog of every step. kind drives result summarization:
#   "line"          -> pass = exit 0; summary = first stdout line
#   "uyaml_json"    -> pass = exit 0 AND summary.errors == 0; warnings non-fatal
#   "testplay_json" -> pass = exit 0; summary = total/passed/failed parsed from JSON
STEP_CATALOG = {
    "scene-summarize": {
        "slug": "unity-ctx-scene-summarize",
        "title": "unity-ctx scene summarize",
        "cmd": ["unity-ctx", "scene", "summarize", "Assets/Demo/Scenes/MiniDungeon.unity"],
        "kind": "line",
    },
    "prefab-set": {
        "slug": "unity-ctx-prefab-set",
        "title": "unity-ctx prefab set startLit (dry-run)",
        "cmd": ["unity-ctx", "prefab", "set", "Assets/Demo/Prefabs/Torch.prefab",
                "--project", ".", "--id", "600002", "--field", "startLit", "--value", "1"],
        "kind": "line",
    },
    "uyaml-check": {
        "slug": "uyaml-scene-check",
        "title": "uyaml scene check (--json)",
        "cmd": ["uyaml", "scene", "check", "Assets/Demo/Scenes/MiniDungeon.unity", "--json"],
        "kind": "uyaml_json",
    },
    "testplay-editmode": {
        "slug": "testplay-editmode",
        "title": "testplay run (EditMode)",
        "cmd": ["testplay", "run", "--filter", "DemoDungeon"],
        "kind": "testplay_json",
    },
    "testplay-playmode": {
        "slug": "testplay-playmode",
        "title": "testplay run (PlayMode)",
        "cmd": ["testplay", "run", "--config", "testplay.playmode.json", "--filter", "DemoDungeon"],
        "kind": "testplay_json",
    },
}

FAST_STEPS = ["scene-summarize", "prefab-set", "uyaml-check"]
FULL_STEPS = FAST_STEPS + ["testplay-editmode", "testplay-playmode"]


PYTHON_EXE = sys.executable or "python3"


def sanitize(text):
    """Make output portfolio-safe by replacing local absolute paths with placeholders."""
    if not text:
        return text
    # Normalize the local Python interpreter path to the canonical command first (so the
    # machine-specific path under /Library/Frameworks or similar never survives).
    if PYTHON_EXE and PYTHON_EXE != "python3":
        text = text.replace(PYTHON_EXE, "python3")
    text = re.sub(r"/[^\s'\"]*/python(?:3(?:\.\d+)?)?\b", "python3", text)
    # Project / home roots.
    text = text.replace(PROJECT_ROOT, REPO_ROOT_PLACEHOLDER)
    if HOME and HOME != PROJECT_ROOT:
        text = text.replace(HOME, "<home>")
    # Catch-all for any remaining machine-specific absolute paths.
    text = re.sub(r"/(?:Users|Volumes|Applications|Library/Frameworks)/[^\s'\":]+",
                  "<redacted-path>", text)
    return text


def build_env():
    """PATH augmented with the usual Go / local install dirs so the CLI tools resolve."""
    env = os.environ.copy()
    extra = [os.path.expanduser("~/go/bin"), os.path.expanduser("~/.local/bin")]
    parts = env.get("PATH", "").split(os.pathsep)
    env["PATH"] = os.pathsep.join([p for p in extra if p and p not in parts] + parts)
    return env


def clean_apple_double(env):
    """Best-effort removal of macOS ._* AppleDouble files (exFAT/FAT volumes).

    These binary sidecar files break `unity-ctx ... --project .` scans with
    "input is not valid UTF-8". Never fatal; returns how many were removed.
    """
    targets = ["Assets", "ProjectSettings", "Packages"]
    try:
        subprocess.run(["xattr", "-rc", *targets], cwd=PROJECT_ROOT, env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception:
        pass
    removed = 0
    for t in targets:
        for root, _dirs, files in os.walk(os.path.join(PROJECT_ROOT, t)):
            for name in files:
                if name.startswith("._"):
                    try:
                        os.remove(os.path.join(root, name))
                        removed += 1
                    except OSError:
                        pass
    return removed


def try_parse_json(text):
    """Parse a JSON object from command output, tolerating leading/trailing noise."""
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except ValueError:
            return None
    return None


def first_line(text):
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return "(no output)"


def uyaml_warning_breakdown(data):
    """Return {code: count} for WARN-severity issues in a uyaml --json payload."""
    by_code = {}
    for issue in (data or {}).get("issues", []) or []:
        if str(issue.get("severity", "")).upper() == "WARN":
            code = issue.get("code", "UNKNOWN")
            by_code[code] = by_code.get(code, 0) + 1
    return by_code


def capture(cmd, env):
    """Run a command from PROJECT_ROOT; return (stdout, stderr, returncode, duration_seconds)."""
    tool = cmd[0]
    started = time.time()
    if shutil.which(tool, path=env["PATH"]) is None:
        return "", "%s: not found on PATH" % tool, 127, time.time() - started
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, env=env, capture_output=True, text=True)
    return proc.stdout, proc.stderr, proc.returncode, time.time() - started


def run_step(index, step, env):
    out_path = os.path.join(ARTIFACT_DIR, "%02d_%s.stdout.log" % (index, step["slug"]))
    err_path = os.path.join(ARTIFACT_DIR, "%02d_%s.stderr.log" % (index, step["slug"]))
    cmd = step["cmd"]

    stdout, stderr, returncode, duration = capture(cmd, env)

    with open(out_path, "w", newline="\n") as f:
        f.write(sanitize(stdout))
    with open(err_path, "w", newline="\n") as f:
        f.write(sanitize(stderr))

    ok = returncode == 0
    summary = first_line(stdout) if returncode == 0 else (stderr.strip() or "exit %d" % returncode)
    note = ""
    extra = None

    if step["kind"] == "uyaml_json":
        data = try_parse_json(stdout)
        s = (data or {}).get("summary", {}) if data else {}
        errors = s.get("errors")
        warnings = s.get("warnings")
        if not ok:
            note = "process exit %d" % returncode
        elif errors is None:
            ok = False
            note = "could not parse summary.errors from --json output"
        elif errors != 0:
            ok = False
            note = "errors=%d" % errors
        else:
            note = "exit 0 and errors=0 (warnings non-fatal)"
            summary = "status=%s errors=0 warnings=%s" % ((data or {}).get("status"), warnings)
        extra = {
            "status": (data or {}).get("status") if data else None,
            "errors": errors,
            "warnings": warnings,
            "by_code": uyaml_warning_breakdown(data),
        }
    elif step["kind"] == "testplay_json" and ok:
        data = try_parse_json(stdout)
        if data:
            summary = "total=%s passed=%s failed=%s" % (
                data.get("total"), data.get("passed"), data.get("failed"))

    return {
        "index": index,
        "slug": step["slug"],
        "title": step["title"],
        "cmd": " ".join(cmd),
        "returncode": returncode,
        "duration": duration,
        "ok": ok,
        "summary": summary,
        "note": note,
        "extra": extra,
        "stdout_path": os.path.relpath(out_path, PROJECT_ROOT),
        "stderr_path": os.path.relpath(err_path, PROJECT_ROOT),
    }


def _uyaml_section(results):
    """Render the dedicated warning-summary section for the uyaml step, if present."""
    uyaml = next((r for r in results if r["extra"] is not None), None)
    if uyaml is None:
        return []
    x = uyaml["extra"]
    lines = ["## uyaml scene check — warning summary", ""]
    lines.append("Pass criteria: **process exit code 0 AND `summary.errors == 0`**. "
                 "Warnings are non-fatal.")
    lines.append("")
    lines.append("- exit code: %d %s" % (uyaml["returncode"],
                                         "(pass)" if uyaml["returncode"] == 0 else "(FAIL)"))
    lines.append("- status: %s" % x["status"])
    lines.append("- errors: %s %s" % (x["errors"], "(pass)" if x["errors"] == 0 else "(FAIL)"))
    lines.append("- warnings: %s (non-fatal)" % x["warnings"])
    by_code = x["by_code"]
    if by_code:
        lines.append("- warning types:")
        for code in sorted(by_code, key=lambda c: (-by_code[c], c)):
            lines.append("  - `%s`: %d" % (code, by_code[code]))
    lines.append("")
    lines.append("> These `UNKNOWN_*` warnings are emitted because uyaml models only GameObject "
                 "and Transform (MeshRenderer / MeshFilter / Light / BoxCollider / MonoBehaviour / "
                 "scene-settings blocks are skipped). They also appear on genuine Unity files and "
                 "do not indicate a defect.")
    lines.append("")
    return lines


def write_report(results, removed_dotfiles, mode):
    passed = sum(1 for r in results if r["ok"])
    overall = "PASS" if passed == len(results) else "FAIL"

    lines = []
    lines.append("# MiniDungeon E2E Demo Report (%s)" % mode)
    lines.append("")
    lines.append("- Generated: %s" % datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    lines.append("- Mode: %s" % mode)
    lines.append("- Project root: `%s`" % REPO_ROOT_PLACEHOLDER)
    lines.append("- Pre-step: removed %d macOS `._*` AppleDouble file(s)" % removed_dotfiles)
    lines.append("- **Overall: %s (%d/%d steps passed)**" % (overall, passed, len(results)))
    lines.append("")
    lines.append("| # | Step | Status | Exit | Duration | Result |")
    lines.append("|---|------|--------|------|----------|--------|")
    for r in results:
        status = "PASS" if r["ok"] else "FAIL"
        lines.append("| %d | %s | %s | %d | %.1fs | %s |" % (
            r["index"], r["title"], status, r["returncode"], r["duration"],
            r["summary"].replace("|", "\\|")))
    lines.append("")

    lines += _uyaml_section(results)

    lines.append("## Step details")
    for r in results:
        status = "PASS" if r["ok"] else "FAIL"
        lines.append("")
        lines.append("### %d. %s — %s" % (r["index"], r["title"], status))
        lines.append("")
        lines.append("- Command: `%s`" % r["cmd"])
        lines.append("- Exit code: %d" % r["returncode"])
        lines.append("- Duration: %.1fs" % r["duration"])
        lines.append("- Result: %s" % r["summary"])
        if r["note"]:
            lines.append("- Note: %s" % r["note"])
        lines.append("- stdout: `%s`" % r["stdout_path"])
        lines.append("- stderr: `%s`" % r["stderr_path"])
    lines.append("")

    report_path = os.path.join(ARTIFACT_DIR, "report.md")
    with open(report_path, "w", newline="\n") as f:
        f.write(sanitize("\n".join(lines)))
    return report_path, overall


def _reset_artifact_dir():
    """Clear the (flat) artifacts dir, tolerant of macOS ._* files that race on exFAT."""
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    for name in os.listdir(ARTIFACT_DIR):
        try:
            os.remove(os.path.join(ARTIFACT_DIR, name))
        except OSError:
            pass


def run(step_ids, mode):
    """Run the selected steps in order; write artifacts + report; return an exit code."""
    env = build_env()

    _reset_artifact_dir()

    removed = clean_apple_double(env)
    steps = [STEP_CATALOG[s] for s in step_ids]
    print("[e2e:%s] cleaned %d AppleDouble file(s); running %d steps..."
          % (mode, removed, len(steps)))

    results = []
    for i, step in enumerate(steps, start=1):
        print("[e2e:%s] step %d/%d: %s" % (mode, i, len(steps), step["title"]))
        r = run_step(i, step, env)
        print("         -> %s (exit %d, %.1fs) %s"
              % ("PASS" if r["ok"] else "FAIL", r["returncode"], r["duration"], r["summary"]))
        results.append(r)

    report_path, overall = write_report(results, removed, mode)
    print("[e2e:%s] report: %s" % (mode, os.path.relpath(report_path, PROJECT_ROOT)))
    print("[e2e:%s] overall: %s" % (mode, overall))
    return 0 if overall == "PASS" else 1
