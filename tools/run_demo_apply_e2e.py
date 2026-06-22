#!/usr/bin/env python3
"""
Optional ACTUAL-APPLY end-to-end test for the MiniDungeon fixture.

Unlike tools/run_demo_e2e.py (which only previews the property change with a dry-run),
this test performs a real on-disk mutation and then proves it is fully reversible:

  1. Regenerate the fixture to a known baseline (offline generator).
  2. Apply a documented unity-ctx prefab property change WITH --write --ack-impact.
  3. Validate the mutated prefab with uyaml (must stay graph-clean: errors=0).
  4. Run testplay EditMode and PlayMode (project stays healthy after the write).
  5. Regenerate the fixture to restore the baseline.
  6. Confirm the working tree is clean (fixture restored byte-for-byte), or report
     the files that changed.

It is "optional" because it writes to the repo (and momentarily creates a .bak). After a
successful run the fixture is byte-identical to the baseline and the .bak is removed.

Outputs go to artifacts/demo-e2e/apply/. Exits non-zero if any step fails OR the tree is
not clean afterwards.

    python3 tools/run_demo_apply_e2e.py
"""

import hashlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _demo_runner import (  # noqa: E402
    ARTIFACT_DIR, PROJECT_ROOT, REPO_ROOT_PLACEHOLDER,
    build_env, capture, clean_apple_double, first_line, sanitize,
    try_parse_json, uyaml_warning_breakdown,
)

APPLY_DIR = os.path.join(ARTIFACT_DIR, "apply")
FIXTURE_DIR = "Assets/Demo"
TORCH_PREFAB = "Assets/Demo/Prefabs/Torch.prefab"
GENERATOR = [sys.executable, os.path.join("tools", "generate_yaml_fixtures.py")]


# --------------------------------------------------------------------------- helpers

def reset_dir(path):
    """Clear a flat artifacts dir, tolerant of macOS ._* files that race on exFAT."""
    os.makedirs(path, exist_ok=True)
    for name in os.listdir(path):
        try:
            os.remove(os.path.join(path, name))
        except OSError:
            pass


def snapshot(rel_root=FIXTURE_DIR):
    """Map every fixture file (excluding ._* and .bak) to its sha256 digest."""
    manifest = {}
    base = os.path.join(PROJECT_ROOT, rel_root)
    for root, _dirs, files in os.walk(base):
        for name in files:
            if name.startswith("._") or name.endswith(".bak") or name.endswith(".bak.meta"):
                continue
            full = os.path.join(root, name)
            try:
                with open(full, "rb") as f:
                    manifest[os.path.relpath(full, PROJECT_ROOT)] = hashlib.sha256(f.read()).hexdigest()
            except OSError:
                pass
    return manifest


def diff_manifests(before, after):
    changed, added, removed = [], [], []
    for key in sorted(set(before) | set(after)):
        if key not in after:
            removed.append(key)
        elif key not in before:
            added.append(key)
        elif before[key] != after[key]:
            changed.append(key)
    return changed, added, removed


def remove_bak_files(env):
    """Remove tool-created *.bak (and orphan *.bak.meta) files under the fixture."""
    removed = []
    base = os.path.join(PROJECT_ROOT, "Assets", "Demo")
    for root, _dirs, files in os.walk(base):
        for name in files:
            if name.endswith(".bak") or name.endswith(".bak.meta"):
                full = os.path.join(root, name)
                try:
                    os.remove(full)
                    removed.append(os.path.relpath(full, PROJECT_ROOT))
                except OSError:
                    pass
    return removed


def git_status_fixture(env):
    """Return (is_git, porcelain_lines) for the fixture path, or (False, None) if not a repo."""
    probe = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
                           cwd=PROJECT_ROOT, env=env, capture_output=True, text=True)
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        return False, None
    status = subprocess.run(["git", "status", "--porcelain", "--", FIXTURE_DIR],
                            cwd=PROJECT_ROOT, env=env, capture_output=True, text=True)
    return True, [ln for ln in status.stdout.splitlines() if ln.strip()]


def run_command_step(results, index, title, slug, cmd, env, kind="cmd"):
    """Run one command, capture sanitized logs, classify pass/fail, append a result row."""
    out_path = os.path.join(APPLY_DIR, "%02d_%s.stdout.log" % (index, slug))
    err_path = os.path.join(APPLY_DIR, "%02d_%s.stderr.log" % (index, slug))
    stdout, stderr, rc, dur = capture(cmd, env)
    with open(out_path, "w", newline="\n") as f:
        f.write(sanitize(stdout))
    with open(err_path, "w", newline="\n") as f:
        f.write(sanitize(stderr))

    ok = rc == 0
    summary = first_line(stdout) if rc == 0 else (stderr.strip() or "exit %d" % rc)
    note, extra = "", None

    if kind == "write":
        token = first_line(stdout).split(" ", 1)[0] if stdout.strip() else ""
        if ok and token != "WRITE":
            ok = False
            note = "expected WRITE prefix, got %r (BLOCKED also exits 0)" % token
        elif ok:
            note = "write committed and re-validated (.bak backup created)"
    elif kind == "uyaml_json":
        data = try_parse_json(stdout)
        s = (data or {}).get("summary", {}) if data else {}
        errors, warnings = s.get("errors"), s.get("warnings")
        if not ok:
            note = "process exit %d" % rc
        elif errors is None:
            ok = False
            note = "could not parse summary.errors from --json output"
        elif errors != 0:
            ok = False
            note = "errors=%d" % errors
        else:
            note = "exit 0 and errors=0 (warnings non-fatal)"
            summary = "status=%s errors=0 warnings=%s" % ((data or {}).get("status"), warnings)
        extra = {"status": (data or {}).get("status") if data else None,
                 "errors": errors, "warnings": warnings, "by_code": uyaml_warning_breakdown(data)}
    elif kind == "testplay_json" and ok:
        data = try_parse_json(stdout)
        if data:
            summary = "total=%s passed=%s failed=%s" % (
                data.get("total"), data.get("passed"), data.get("failed"))

    results.append({
        "index": index, "title": title, "cmd": " ".join(cmd), "returncode": rc,
        "duration": dur, "ok": ok, "summary": summary, "note": note, "extra": extra,
        "stdout_path": os.path.relpath(out_path, PROJECT_ROOT),
        "stderr_path": os.path.relpath(err_path, PROJECT_ROOT),
    })
    print("       -> %s (exit %d, %.1fs) %s" % ("PASS" if ok else "FAIL", rc, dur, summary))
    return ok


# --------------------------------------------------------------------------- report

def write_report(results, clean_info):
    from datetime import datetime, timezone
    passed = sum(1 for r in results if r["ok"]) + (1 if clean_info["clean"] else 0)
    total = len(results) + 1  # + the cleanliness check
    overall = "PASS" if passed == total else "FAIL"

    lines = ["# MiniDungeon ACTUAL-APPLY E2E Report", ""]
    lines.append("- Generated: %s" % datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    lines.append("- Project root: `%s`" % REPO_ROOT_PLACEHOLDER)
    lines.append("- Mutation: `%s` field `startLit` 0 -> 1 (real --write --ack-impact), then restored"
                 % TORCH_PREFAB)
    lines.append("- **Overall: %s (%d/%d checks passed)**" % (overall, passed, total))
    lines.append("")
    lines.append("| # | Step | Status | Exit | Duration | Result |")
    lines.append("|---|------|--------|------|----------|--------|")
    for r in results:
        lines.append("| %d | %s | %s | %d | %.1fs | %s |" % (
            r["index"], r["title"], "PASS" if r["ok"] else "FAIL", r["returncode"],
            r["duration"], r["summary"].replace("|", "\\|")))
    lines.append("| %d | Working tree clean (fixture restored) | %s | - | - | %s |" % (
        len(results) + 1, "PASS" if clean_info["clean"] else "FAIL",
        clean_info["summary"].replace("|", "\\|")))
    lines.append("")

    # uyaml warning summary
    uyaml = next((r for r in results if r["extra"] is not None), None)
    if uyaml:
        x = uyaml["extra"]
        lines += ["## uyaml prefab check — warning summary", "",
                  "Pass criteria: **process exit code 0 AND `summary.errors == 0`**. Warnings are non-fatal.",
                  "",
                  "- exit code: %d %s" % (uyaml["returncode"], "(pass)" if uyaml["returncode"] == 0 else "(FAIL)"),
                  "- status: %s" % x["status"],
                  "- errors: %s %s" % (x["errors"], "(pass)" if x["errors"] == 0 else "(FAIL)"),
                  "- warnings: %s (non-fatal)" % x["warnings"]]
        if x["by_code"]:
            lines.append("- warning types:")
            for code in sorted(x["by_code"], key=lambda c: (-x["by_code"][c], c)):
                lines.append("  - `%s`: %d" % (code, x["by_code"][code]))
        lines.append("")

    # cleanliness detail
    lines += ["## Working tree cleanliness", "",
              "Mechanism: %s" % clean_info["mechanism"], ""]
    if clean_info["bak_removed"]:
        lines.append("- removed tool-created backups: %s" % ", ".join(
            "`%s`" % p for p in clean_info["bak_removed"]))
    if clean_info["clean"]:
        lines.append("- Result: **clean** — fixture is byte-identical to the regenerated baseline.")
    else:
        lines.append("- Result: **NOT clean** — the following fixture files differ from baseline:")
        for label, items in (("changed", clean_info["changed"]),
                             ("added", clean_info["added"]),
                             ("removed", clean_info["removed"])):
            for p in items:
                lines.append("  - %s: `%s`" % (label, p))
        for ln in clean_info.get("git_lines", []):
            lines.append("  - git: `%s`" % ln)
    lines.append("")

    lines.append("## Step details")
    for r in results:
        lines.append("")
        lines.append("### %d. %s — %s" % (r["index"], r["title"], "PASS" if r["ok"] else "FAIL"))
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

    report_path = os.path.join(APPLY_DIR, "report.md")
    with open(report_path, "w", newline="\n") as f:
        f.write(sanitize("\n".join(lines)))
    return report_path, overall


# --------------------------------------------------------------------------- main

def main():
    env = build_env()
    reset_dir(APPLY_DIR)
    removed_dotfiles = clean_apple_double(env)
    print("[apply-e2e] cleaned %d AppleDouble file(s)" % removed_dotfiles)

    results = []

    # 1. Reset/regenerate to a known baseline, then snapshot it.
    print("[apply-e2e] step 1/6: regenerate baseline")
    ok1 = run_command_step(results, 1, "Regenerate baseline (offline generator)",
                           "regenerate-baseline", GENERATOR, env)
    # The generator just wrote files; on exFAT that spawns ._ sidecars that would break the
    # `unity-ctx ... --project .` scan in step 2. Drop them before snapshotting / writing.
    clean_apple_double(env)
    baseline = snapshot()
    print("[apply-e2e] baseline snapshot: %d fixture files" % len(baseline))

    # 2. Apply a documented unity-ctx prefab property change (REAL write).
    print("[apply-e2e] step 2/6: apply prefab property change (--write --ack-impact)")
    run_command_step(results, 2, "Apply unity-ctx prefab set startLit=1 (--write --ack-impact)",
                     "unity-ctx-prefab-set-write",
                     ["unity-ctx", "prefab", "set", TORCH_PREFAB, "--project", ".",
                      "--id", "600002", "--field", "startLit", "--value", "1",
                      "--write", "--ack-impact"], env, kind="write")

    # 3. Validate the mutated prefab with uyaml.
    print("[apply-e2e] step 3/6: validate mutated prefab with uyaml")
    run_command_step(results, 3, "uyaml prefab check (mutated, --json)", "uyaml-prefab-check",
                     ["uyaml", "prefab", "check", TORCH_PREFAB, "--json"], env, kind="uyaml_json")

    # Remove the unity-ctx .bak backup before the Unity import so testplay does not import it as
    # an asset (which would otherwise leave an orphan Torch.prefab.bak.meta in the working tree).
    pre_test_bak = remove_bak_files(env)
    if pre_test_bak:
        print("[apply-e2e] removed %d backup file(s) before testplay" % len(pre_test_bak))

    # 4. Run testplay EditMode and PlayMode (project stays healthy after the write).
    print("[apply-e2e] step 4/6: testplay EditMode")
    run_command_step(results, 4, "testplay run (EditMode)", "testplay-editmode",
                     ["testplay", "run", "--filter", "DemoDungeon"], env, kind="testplay_json")
    print("[apply-e2e] step 5/6: testplay PlayMode")
    run_command_step(results, 5, "testplay run (PlayMode)", "testplay-playmode",
                     ["testplay", "run", "--config", "testplay.playmode.json", "--filter", "DemoDungeon"],
                     env, kind="testplay_json")

    # 5. Regenerate to restore the baseline, then remove tool-created .bak backups.
    print("[apply-e2e] step 6/6: regenerate to restore baseline")
    run_command_step(results, 6, "Regenerate to restore baseline", "regenerate-restore",
                     GENERATOR, env)
    # Final tidy: drop fresh ._ sidecars from the restore write and any remaining .bak artifacts.
    clean_apple_double(env)
    bak_removed = pre_test_bak + remove_bak_files(env)
    if bak_removed:
        print("[apply-e2e] removed %d backup file(s) total" % len(bak_removed))

    # 6. Confirm the working tree is clean (or report changed files).
    after = snapshot()
    changed, added, removed = diff_manifests(baseline, after)
    is_git, git_lines = git_status_fixture(env)
    content_clean = not (changed or added or removed)
    git_clean = (git_lines == []) if is_git else True
    clean = bool(ok1) and content_clean and git_clean
    if is_git:
        mechanism = "`git status --porcelain -- %s` + content-hash comparison vs baseline" % FIXTURE_DIR
    else:
        mechanism = "content-hash (sha256) comparison vs baseline (not a git repository)"
    if clean:
        summary = "clean (%d files match baseline)" % len(after)
    else:
        summary = "changed=%d added=%d removed=%d git=%d" % (
            len(changed), len(added), len(removed), len(git_lines or []))
    clean_info = {"clean": clean, "summary": summary, "mechanism": mechanism,
                  "changed": changed, "added": added, "removed": removed,
                  "git_lines": git_lines or [], "bak_removed": bak_removed}
    print("[apply-e2e] working tree: %s (%s)" % ("CLEAN" if clean else "NOT CLEAN", summary))

    report_path, overall = write_report(results, clean_info)
    print("[apply-e2e] report: %s" % os.path.relpath(report_path, PROJECT_ROOT))
    print("[apply-e2e] overall: %s" % overall)
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
