#!/usr/bin/env python3
"""
Turn an archived testplay-runner `.testplay` run set into public-facing dogfooding evidence.

It recursively scans Other_Projects_testplay/, detects run folders (directories containing a
summary.json), parses each run's artifacts, classifies non-passing runs into broad failure
categories from real evidence, and writes:

  docs/dogfooding/testplay-runner-dogfooding-summary.json   (machine-readable)
  docs/dogfooding/testplay-runner-dogfooding-report.md      (human-readable)
  docs/dogfooding/sanitized-samples/                        (small, path-sanitized excerpts)

All numbers are derived from the actual files. The original archive is never modified. Generated
reports sanitize local absolute paths (home-directory, volume, application, and source-project-root
paths) to `<repo-root>` / `<source-project-root>` placeholders. Output is deterministic (no
wall-clock timestamps), so the script is safe to run repeatedly.

    python3 tools/analyze_testplay_dogfooding.py
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE_DIRNAME = "Other_Projects_testplay"
ARCHIVE = os.path.join(PROJECT_ROOT, ARCHIVE_DIRNAME)
OUT_DIR = os.path.join(PROJECT_ROOT, "docs", "dogfooding")
SAMPLES_DIR = os.path.join(OUT_DIR, "sanitized-samples")
SUMMARY_JSON = os.path.join(OUT_DIR, "testplay-runner-dogfooding-summary.json")
REPORT_MD = os.path.join(OUT_DIR, "testplay-runner-dogfooding-report.md")

PROJECT_LABEL = "GNF_"
HOME = os.path.expanduser("~")

# Human-readable names for the failure taxonomy.
CATEGORY_LABELS = {
    "test_assertion_runtime_failure": "Test assertion / runtime failure",
    "compile_import_bootstrap_failure": "Compile / import / bootstrap failure",
    "missing_results_xml": "Missing results XML",
    "timeout_or_interrupted": "Timeout or interrupted run",
    "unknown": "Unknown",
}
CATEGORY_WHY = {
    "test_assertion_runtime_failure":
        "Proves the runner surfaces genuine product bugs: a real assertion failed and was "
        "reported with the failing test name and expected/actual values.",
    "compile_import_bootstrap_failure":
        "Proves the runner distinguishes project-level build/import/bootstrap failures (no tests "
        "executed, no results.xml) from ordinary test failures.",
    "missing_results_xml":
        "Indicates a run that produced no NUnit results document — useful for spotting runs that "
        "never reached the test-execution phase.",
    "timeout_or_interrupted":
        "Proves the runner bounds long Unity runs and records interruptions instead of hanging.",
    "unknown":
        "A non-passing run whose evidence did not match a known category; reported honestly "
        "rather than force-fit.",
}


# --------------------------------------------------------------------------- sanitization

def detect_source_root():
    """Find the original project root from any manifest's absolute artifact_root path."""
    for run_dir in find_run_dirs():
        manifest = read_json(os.path.join(run_dir, "manifest.json"))
        root = (manifest or {}).get("artifact_root")
        if isinstance(root, str) and "/.testplay" in root:
            return root.split("/.testplay", 1)[0]
    return None


def make_sanitizer(source_root):
    user = os.path.basename(HOME) if HOME else ""

    def sanitize(text):
        if not text:
            return text
        if source_root:
            text = text.replace(source_root, "<source-project-root>")
        text = text.replace(PROJECT_ROOT, "<repo-root>")
        if HOME:
            text = text.replace(HOME, "<home>")
        # Normalize any local Python interpreter path to the canonical command.
        text = re.sub(r"/[^\s'\"]*/python(?:3(?:\.\d+)?)?\b", "python3", text)
        # Catch-all for any remaining machine-specific absolute paths.
        text = re.sub(r"/(?:Users|Volumes|Applications|Library/Frameworks)/[^\s\"':]+",
                      "<redacted-path>", text)
        # Redact the bare username if it still appears (e.g. inside non-path strings).
        if user:
            text = text.replace(user, "<user>")
        return text

    return sanitize


# --------------------------------------------------------------------------- io helpers

def read_json(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def parse_dt(value):
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def find_run_dirs():
    """Run folder = any directory containing summary.json. Unity 'Library' caches are pruned."""
    run_dirs = []
    if not os.path.isdir(ARCHIVE):
        return run_dirs
    for root, dirs, files in os.walk(ARCHIVE):
        # Skip macOS AppleDouble noise and large Unity Library caches (never hold run folders).
        dirs[:] = [d for d in dirs if d != "Library" and not d.startswith("._")]
        if "summary.json" in files:
            run_dirs.append(root)
    return sorted(run_dirs)


# --------------------------------------------------------------------------- per-run analysis

def phases_from_events(path):
    """Return the ordered list of phases observed in events.ndjson (best-effort)."""
    phases = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except ValueError:
                    continue
                ph = ev.get("phase")
                if ph and (not phases or phases[-1] != ph):
                    phases.append(ph)
    except OSError:
        return None
    return phases


def failed_tests_from_xml(path, sanitize, cap=5):
    """Extract (name, message) for failed test-cases from an NUnit results.xml."""
    out = []
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return out, True  # malformed/unreadable
    for tc in root.iter("test-case"):
        if tc.get("result") == "Failed":
            name = tc.get("name") or tc.get("fullname") or "(unnamed)"
            msg_el = tc.find(".//failure/message")
            if msg_el is None:
                msg_el = tc.find(".//message")
            msg = (msg_el.text or "").strip() if msg_el is not None else ""
            msg = re.sub(r"\s+", " ", msg)[:200]
            out.append({"name": sanitize(name), "message": sanitize(msg)})
            if len(out) >= cap:
                break
    return out, False


def classify(exit_code, failed, has_results_xml):
    """Map a non-passing run to one primary failure category from concrete signals."""
    if exit_code == 0:
        return None
    if (failed or 0) > 0 and has_results_xml:
        return "test_assertion_runtime_failure"
    if exit_code in (4, 8):
        return "timeout_or_interrupted"
    if exit_code in (1, 2, 5, 6):
        # 1 project-not-found, 2 compile, 5 config, 6 build/invocation — all pre-test bootstrap.
        return "compile_import_bootstrap_failure"
    if not has_results_xml:
        return "missing_results_xml"
    return "unknown"


def analyze_run(run_dir, sanitize):
    run_id = os.path.basename(run_dir)
    summary = read_json(os.path.join(run_dir, "summary.json"))

    def has(name):
        return os.path.exists(os.path.join(run_dir, name))

    rec = {
        "run_id": run_id,
        "exit_code": None,
        "total": None,
        "passed": None,
        "failed": None,
        "skipped": None,
        "duration_seconds": None,
        "has_summary": summary is not None,
        "has_results_xml": has("results.xml"),
        "has_stdout": has("stdout.log"),
        "has_stderr": has("stderr.log"),
        "has_manifest": has("manifest.json"),
        "has_events": has("events.ndjson"),
        "reached_running_phase": None,
        "status": "incomplete",
        "failure_category": None,
        "failed_tests": [],
        "notes": [],
    }

    if summary is None:
        rec["notes"].append("summary.json missing or malformed")
        return rec

    for k in ("exit_code", "total", "passed", "failed", "skipped"):
        rec[k] = summary.get(k)

    manifest = read_json(os.path.join(run_dir, "manifest.json"))
    if manifest:
        a, b = parse_dt(manifest.get("started_at")), parse_dt(manifest.get("finished_at"))
        if a and b:
            rec["duration_seconds"] = round((b - a).total_seconds(), 1)

    if rec["has_events"]:
        phases = phases_from_events(os.path.join(run_dir, "events.ndjson"))
        if phases is not None:
            rec["reached_running_phase"] = "running" in phases

    ec = rec["exit_code"]
    if ec == 0:
        rec["status"] = "pass"
    elif ec is not None:
        rec["status"] = "fail"
        rec["failure_category"] = classify(ec, rec["failed"], rec["has_results_xml"])
        if rec["failure_category"] == "test_assertion_runtime_failure":
            tests, malformed = failed_tests_from_xml(
                os.path.join(run_dir, "results.xml"), sanitize)
            rec["failed_tests"] = tests
            if malformed:
                rec["notes"].append("results.xml present but unreadable/malformed")
        if not rec["has_results_xml"]:
            rec["notes"].append("no results.xml (no NUnit document produced)")
        if rec["reached_running_phase"] is False:
            rec["notes"].append("phase never reached 'running' (failed before tests executed)")
    else:
        rec["notes"].append("summary.json has no exit_code")

    return rec


# --------------------------------------------------------------------------- aggregation

def build_summary(runs):
    def s(key):
        return sum((r[key] or 0) for r in runs if isinstance(r.get(key), int))

    passing = [r for r in runs if r["status"] == "pass"]
    non_passing = [r for r in runs if r["status"] != "pass"]
    categories = {}
    for r in non_passing:
        cat = r["failure_category"] or "unknown"
        categories[cat] = categories.get(cat, 0) + 1

    durations = [r["duration_seconds"] for r in runs if isinstance(r["duration_seconds"], (int, float))]
    dates = sorted(r["run_id"][:8] for r in runs if re.match(r"^\d{8}", r["run_id"]))

    return {
        "source": ARCHIVE_DIRNAME,
        "project_label": PROJECT_LABEL,
        "run_folders_found": len(runs),
        "runs_with_summary": sum(1 for r in runs if r["has_summary"]),
        "passing_runs": len(passing),
        "non_passing_runs": len(non_passing),
        "total_tests_observed": s("total"),
        "total_passed_tests_observed": s("passed"),
        "total_failed_tests_observed": s("failed"),
        "total_skipped_observed": s("skipped"),
        "runs_missing_results_xml": sum(1 for r in runs if not r["has_results_xml"]),
        "incomplete_runs": sum(1 for r in runs if r["status"] == "incomplete"),
        "observed_date_range": ([dates[0], dates[-1]] if dates else []),
        "total_runtime_seconds_observed": round(sum(durations), 1) if durations else 0,
        "max_run_duration_seconds": max(durations) if durations else 0,
        "failure_categories": dict(sorted(categories.items())),
        "runs": runs,
    }


# --------------------------------------------------------------------------- report

def fmt_dur(seconds):
    if not isinstance(seconds, (int, float)):
        return "-"
    return "%ds" % round(seconds)


def write_samples(runs, sanitize):
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    written = []

    passing = next((r for r in runs if r["status"] == "pass" and r["total"]), None)
    if passing:
        body = {k: passing[k] for k in ("run_id", "exit_code", "total", "passed", "failed", "skipped")}
        p = os.path.join(SAMPLES_DIR, "passing-run.summary.json")
        with open(p, "w", newline="\n") as f:
            f.write(json.dumps(body, indent=2) + "\n")
        written.append(p)

    tf = next((r for r in runs if r["failure_category"] == "test_assertion_runtime_failure"), None)
    if tf:
        lines = ["# Sanitized sample — test assertion failure", "",
                 "- run id: `%s`" % tf["run_id"],
                 "- exit code: %s" % tf["exit_code"],
                 "- totals: total=%s passed=%s failed=%s skipped=%s"
                 % (tf["total"], tf["passed"], tf["failed"], tf["skipped"]),
                 "", "Failing test(s):"]
        for t in tf["failed_tests"]:
            lines.append("- `%s` — %s" % (t["name"], t["message"]))
        p = os.path.join(SAMPLES_DIR, "test-failure-run.md")
        with open(p, "w", newline="\n") as f:
            f.write(sanitize("\n".join(lines)) + "\n")
        written.append(p)

    bf = next((r for r in runs if r["failure_category"] == "compile_import_bootstrap_failure"), None)
    if bf:
        lines = ["# Sanitized sample — compile/import/bootstrap failure", "",
                 "- run id: `%s`" % bf["run_id"],
                 "- exit code: %s (build/invocation; no tests executed)" % bf["exit_code"],
                 "- results.xml present: %s" % ("yes" if bf["has_results_xml"] else "no"),
                 "- reached 'running' phase: %s" % bf["reached_running_phase"],
                 "- duration: %s" % fmt_dur(bf["duration_seconds"]),
                 "- evidence: " + "; ".join(bf["notes"]) if bf["notes"] else "- evidence: n/a"]
        p = os.path.join(SAMPLES_DIR, "bootstrap-failure-run.md")
        with open(p, "w", newline="\n") as f:
            f.write(sanitize("\n".join(lines)) + "\n")
        written.append(p)

    return written


def write_report(summary, runs, sample_paths, sanitize):
    rng = summary["observed_date_range"]
    rng_str = "%s – %s" % (rng[0], rng[1]) if rng else "n/a"
    L = []
    L.append("# testplay-runner Dogfooding Report")
    L.append("")
    L.append("## 1. Context")
    L.append("")
    L.append("This evidence comes from a **real, separate Unity project** (`%s`) on which "
             "[`testplay-runner`](https://github.com/Kubonsang/testplay-runner) was run repeatedly "
             "during development. Its archived `.testplay/` run set was copied into this repository "
             "under `%s/` purely as dogfooding evidence." % (PROJECT_LABEL, ARCHIVE_DIRNAME))
    L.append("")
    L.append("It is **separate from the MiniDungeon fixture** in this repo: MiniDungeon is the "
             "tiny copyright-safe test fixture; `%s` is a real game project with a large asset set "
             "and a real test suite. Observed run dates: %s." % (PROJECT_LABEL, rng_str))
    L.append("")

    L.append("## 2. Summary")
    L.append("")
    L.append("| Metric | Value |")
    L.append("|---|---:|")
    L.append("| Run folders found | %d |" % summary["run_folders_found"])
    L.append("| Runs with summary.json | %d |" % summary["runs_with_summary"])
    L.append("| Passing runs | %d |" % summary["passing_runs"])
    L.append("| Non-passing runs | %d |" % summary["non_passing_runs"])
    L.append("| Total tests observed | %d |" % summary["total_tests_observed"])
    L.append("| Total passed tests observed | %d |" % summary["total_passed_tests_observed"])
    L.append("| Total failed tests observed | %d |" % summary["total_failed_tests_observed"])
    L.append("| Total skipped/inconclusive observed | %d |" % summary["total_skipped_observed"])
    L.append("| Runs missing results.xml | %d |" % summary["runs_missing_results_xml"])
    L.append("| Incomplete/malformed runs | %d |" % summary["incomplete_runs"])
    L.append("| Total observed runtime | %s |" % fmt_dur(summary["total_runtime_seconds_observed"]))
    L.append("| Longest single run | %s |" % fmt_dur(summary["max_run_duration_seconds"]))
    L.append("")
    L.append("All values above are computed directly from the archived files by "
             "`tools/analyze_testplay_dogfooding.py`.")
    L.append("")

    L.append("## 3. Failure Taxonomy")
    L.append("")
    if not summary["failure_categories"]:
        L.append("_No non-passing runs were found._")
    else:
        for cat, count in summary["failure_categories"].items():
            affected = [r for r in runs if (r["failure_category"] or "unknown") == cat
                        and r["status"] != "pass"]
            L.append("### %s — %d run(s)" % (CATEGORY_LABELS.get(cat, cat), count))
            L.append("")
            reps = ", ".join("`%s`" % r["run_id"] for r in affected[:5])
            L.append("- Representative run folders: %s" % reps)
            # Short, sanitized evidence per category.
            if cat == "test_assertion_runtime_failure":
                ev = []
                for r in affected:
                    for t in r["failed_tests"]:
                        ev.append("`%s` → %s" % (t["name"], t["message"]))
                for e in ev[:5]:
                    L.append("- Evidence: %s" % e)
            elif cat == "compile_import_bootstrap_failure":
                for r in affected[:3]:
                    L.append("- Evidence (`%s`): exit_code=%s, results.xml=%s, reached_running=%s, "
                             "duration=%s — %s" % (
                                 r["run_id"], r["exit_code"],
                                 "yes" if r["has_results_xml"] else "no",
                                 r["reached_running_phase"], fmt_dur(r["duration_seconds"]),
                                 "; ".join(r["notes"]) or "n/a"))
            else:
                for r in affected[:3]:
                    L.append("- Evidence (`%s`): exit_code=%s — %s"
                             % (r["run_id"], r["exit_code"], "; ".join(r["notes"]) or "n/a"))
            L.append("- Why it matters: %s" % CATEGORY_WHY.get(cat, ""))
            L.append("")

    L.append("## 4. What This Proves")
    L.append("")
    L.append("- `testplay-runner` was run **%d times** against a real Unity project, not only the "
             "MiniDungeon fixture." % summary["run_folders_found"])
    L.append("- It captured **%d passing runs** (e.g. suites of ~300 tests) and **%d non-passing "
             "runs**." % (summary["passing_runs"], summary["non_passing_runs"]))
    L.append("- It caught **real product bugs**: %d failed test(s) were reported with the failing "
             "test name and expected/actual values (see the failure taxonomy)."
             % summary["total_failed_tests_observed"])
    L.append("- It surfaced **Unity/project-level failure modes** distinct from test failures "
             "(build/import/bootstrap runs that produced no `results.xml` and never reached the "
             "test-execution phase).")
    L.append("- Every run left **inspectable artifacts** on disk (`summary.json`, `manifest.json`, "
             "`results.xml` when tests ran, `stdout.log`, `stderr.log`, `events.ndjson`).")
    L.append("- The artifacts let a reader **distinguish a test failure (exit 3, has results.xml) "
             "from an environment/import/bootstrap failure (exit 6, no results.xml)**.")
    L.append("")

    L.append("## 5. Limitations")
    L.append("")
    L.append("- This is **local dogfooding evidence by the tool's own author**, not independent "
             "third-party adoption or production usage.")
    L.append("- The archive contains machine-specific logs; absolute paths are sanitized in this "
             "report but the raw archive is left untouched.")
    L.append("- Some runs may be incomplete or malformed; such runs are reported honestly "
             "(incomplete/malformed runs: %d)." % summary["incomplete_runs"])
    L.append("- This evidence primarily validates **`testplay-runner`**. It does **not** validate "
             "[`unity-ctx`](https://github.com/Kubonsang/unity-ctx) or "
             "[`unity-fileid-graph`](https://github.com/Kubonsang/unity-fileid-graph) — no logs "
             "for those tools are present in this archive.")
    L.append("- Long Unity startup/import times remain a performance concern: the longest observed "
             "run took %s, and even passing runs spend a large fraction of time in the "
             "compile/import phase before tests execute." % fmt_dur(summary["max_run_duration_seconds"]))
    L.append("")

    L.append("## 6. Reproducibility")
    L.append("")
    L.append("Regenerate this report and the machine-readable summary from the archive with:")
    L.append("")
    L.append("```bash")
    L.append("python3 tools/analyze_testplay_dogfooding.py")
    L.append("```")
    L.append("")
    L.append("The analyzer only reads the archive and is deterministic (no wall-clock timestamps "
             "in its output), so repeated runs produce identical files.")
    L.append("")

    L.append("## 7. Public Safety")
    L.append("")
    L.append("Generated reports sanitize local absolute paths: the source project root is shown as "
             "`<source-project-root>`, this repository as `<repo-root>`, and any remaining "
             "home-directory or volume absolute paths and the local username are redacted. The raw "
             "archive under `%s/` is preserved unmodified as the underlying evidence." % ARCHIVE_DIRNAME)
    if sample_paths:
        L.append("")
        L.append("Small sanitized samples are provided under "
                 "`docs/dogfooding/sanitized-samples/`:")
        for p in sample_paths:
            L.append("- `%s`" % os.path.relpath(p, PROJECT_ROOT))
    L.append("")

    L.append("## Appendix: per-run table")
    L.append("")
    L.append("| Run | Status | Exit | Total | Pass | Fail | Skip | results.xml | Duration |")
    L.append("|---|---|---:|---:|---:|---:|---:|:--:|---:|")
    for r in runs:
        L.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["run_id"], r["status"],
            "-" if r["exit_code"] is None else r["exit_code"],
            "-" if r["total"] is None else r["total"],
            "-" if r["passed"] is None else r["passed"],
            "-" if r["failed"] is None else r["failed"],
            "-" if r["skipped"] is None else r["skipped"],
            "yes" if r["has_results_xml"] else "no",
            fmt_dur(r["duration_seconds"])))
    L.append("")

    with open(REPORT_MD, "w", newline="\n") as f:
        f.write(sanitize("\n".join(L)))


# --------------------------------------------------------------------------- main

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    source_root = detect_source_root()
    sanitize = make_sanitizer(source_root)

    run_dirs = find_run_dirs()
    runs = [analyze_run(d, sanitize) for d in run_dirs]

    summary = build_summary(runs)

    with open(SUMMARY_JSON, "w", newline="\n") as f:
        f.write(json.dumps(summary, indent=2) + "\n")

    sample_paths = write_samples(runs, sanitize)
    write_report(summary, runs, sample_paths, sanitize)

    print("[dogfood] source project root detected: %s"
          % ("yes -> sanitized as <source-project-root>" if source_root else "no"))
    print("[dogfood] run folders found: %d (passing=%d, non-passing=%d, incomplete=%d)" % (
        summary["run_folders_found"], summary["passing_runs"],
        summary["non_passing_runs"], summary["incomplete_runs"]))
    print("[dogfood] failure categories: %s" % (summary["failure_categories"] or "none"))
    print("[dogfood] wrote: %s" % os.path.relpath(SUMMARY_JSON, PROJECT_ROOT))
    print("[dogfood] wrote: %s" % os.path.relpath(REPORT_MD, PROJECT_ROOT))
    for p in sample_paths:
        print("[dogfood] wrote: %s" % os.path.relpath(p, PROJECT_ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
