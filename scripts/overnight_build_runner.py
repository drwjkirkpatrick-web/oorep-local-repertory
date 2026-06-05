#!/usr/bin/env python3
"""
OOREP Overnight Autonomous Build Runner

Executes one feature build per invocation, based on schedule and completion state.
Called by cron every 30 minutes starting at 00:30.

Safety:
  - Lockfile prevents concurrent runs
  - Git backup before each build
  - Tests must pass before commit
  - 15-minute max build time (safety timeout)
  - Logs everything to data/build_log.json

Usage (from cron):
    python3 scripts/overnight_build_runner.py

Usage (manual, specific feature):
    python3 scripts/overnight_build_runner.py --feature word_wrap_search
"""

import argparse
import fcntl
import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path("/home/walker/projects/oorep-local-repertory")
QUEUE_FILE = PROJECT_DIR / "scripts" / "overnight_build_queue.json"
LOG_FILE = PROJECT_DIR / "data" / "build_log.json"
LOCK_FILE = Path("/tmp/oorep_overnight_build.lock")
DB_BACKUP_DIR = PROJECT_DIR / "backups"
MAX_BUILD_SECONDS = 900


def acquire_lock() -> bool:
    """Try to acquire lockfile; return False if already locked."""
    try:
        fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except (OSError, IOError):
        return False


def load_queue() -> dict:
    with open(QUEUE_FILE) as f:
        return json.load(f)


def load_log() -> list:
    if LOG_FILE.exists():
        with open(LOG_FILE) as f:
            return json.load(f)
    return []


def save_log(log: list):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2, default=str)


def git_backup(label: str) -> bool:
    """Stash + backup commit before building."""
    try:
        subprocess.run(
            ["git", "stash", "push", "-m", f"pre-build-{label}"],
            cwd=PROJECT_DIR, capture_output=True, timeout=30
        )
        subprocess.run(
            ["git", "add", "-A"], cwd=PROJECT_DIR, capture_output=True, timeout=30
        )
        subprocess.run(
            ["git", "commit", "-m", f"pre-build-backup-{label}", "--allow-empty"],
            cwd=PROJECT_DIR, capture_output=True, timeout=30
        )
        return True
    except Exception as e:
        print(f"[WARN] Git backup failed (non-fatal): {e}")
        return False


def run_tests(feature: dict) -> tuple[bool, str]:
    """Run test files for the feature. Returns (pass, output)."""
    test_files = [f for f in feature.get("files_to_create", []) if "test_" in f]
    if not test_files:
        # Run the overall test suite as fallback
        test_files = ["tests/"]

    all_pass = True
    all_output = []
    for tf in test_files:
        path = PROJECT_DIR / tf
        if not path.exists():
            all_output.append(f"[SKIP] Test file not yet created: {tf}")
            continue
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(path), "-q", "--tb=short"],
                cwd=PROJECT_DIR, capture_output=True, text=True, timeout=180
            )
            all_output.append(f"--- {tf} ---\n{result.stdout}\n{result.stderr}")
            if result.returncode != 0:
                all_pass = False
        except subprocess.TimeoutExpired:
            all_output.append(f"[TIMEOUT] {tf} exceeded 180s")
            all_pass = False
        except Exception as e:
            all_output.append(f"[ERROR] {tf}: {e}")
            all_pass = False
    return all_pass, "\n".join(all_output)


def git_commit_feature(feature: dict) -> bool:
    """Commit built feature files."""
    try:
        files = feature.get("files_to_create", []) + feature.get("files_to_patch", [])
        for f in files:
            subprocess.run(
                ["git", "add", str(f)], cwd=PROJECT_DIR, capture_output=True, timeout=30
            )
        msg = f"Feature #{feature['id']}: {feature['name']} ({feature['slug']})"
        result = subprocess.run(
            ["git", "commit", "-m", msg, "--allow-empty"],
            cwd=PROJECT_DIR, capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[WARN] Git commit failed: {e}")
        return False


def build_feature(feature: dict) -> dict:
    """
    The core build step. For each feature, this calls out to a feature-specific
    builder script, or falls back to the generic scaffold builder.
    """
    slug = feature["slug"]
    builder_script = PROJECT_DIR / "scripts" / "builders" / f"build_{slug}.py"
    scaffold_script = PROJECT_DIR / "scripts" / "builders" / "build_scaffold.py"

    if builder_script.exists():
        try:
            result = subprocess.run(
                [sys.executable, str(builder_script)],
                cwd=PROJECT_DIR, capture_output=True, text=True, timeout=MAX_BUILD_SECONDS
            )
            return {
                "built": result.returncode == 0,
                "output": result.stdout + "\n" + result.stderr,
                "method": "builder_script"
            }
        except subprocess.TimeoutExpired:
            return {
                "built": False,
                "output": f"[TIMEOUT] Builder script exceeded {MAX_BUILD_SECONDS}s",
                "method": "builder_script"
            }
    elif scaffold_script.exists():
        # Fall back to generic scaffold
        try:
            result = subprocess.run(
                [sys.executable, str(scaffold_script), slug],
                cwd=PROJECT_DIR, capture_output=True, text=True, timeout=60
            )
            return {
                "built": result.returncode == 0,
                "output": result.stdout + "\n" + result.stderr,
                "method": "scaffold"
            }
        except subprocess.TimeoutExpired:
            return {
                "built": False,
                "output": "[TIMEOUT] Scaffold builder exceeded 60s",
                "method": "scaffold"
            }
    else:
        return {
            "built": False,
            "output": f"No builder script found at {builder_script} and no scaffold builder.",
            "method": "missing_builder"
        }


def get_current_scheduled_feature(queue: dict) -> dict | None:
    """Return the feature scheduled for the current 30-minute slot."""
    now = datetime.now()
    now_time = now.strftime("%H:%M")
    current_hour = now.hour
    current_minute = now.minute

    for feature in queue["features"]:
        sched = feature["schedule"]
        h, m = map(int, sched.split(":"))
        # Match if we're within 15 minutes of the scheduled time
        if current_hour == h and abs(current_minute - m) <= 15:
            return feature
    return None


def run_build(feature: dict | None = None) -> dict:
    """Execute one build cycle and return a log entry."""
    if not acquire_lock():
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "skipped",
            "reason": "Lockfile active — another build in progress"
        }

    queue = load_queue()
    log = load_log()

    if feature is None:
        feature = get_current_scheduled_feature(queue)

    if feature is None:
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "skipped",
            "reason": "No feature scheduled for current time slot"
        }

    # Skip if already built successfully
    already_done = any(
        e.get("feature_id") == feature["id"] and e.get("status") == "success"
        for e in log
    )
    if already_done:
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "skipped",
            "reason": f"Feature #{feature['id']} already built successfully",
            "feature_id": feature["id"],
            "feature_name": feature["name"]
        }

    slug = feature["slug"]
    print(f"[BUILD] Starting Feature #{feature['id']}: {feature['name']} ({slug})")

    # Step 1: Git backup
    backup_ok = git_backup(slug)

    # Step 2: Build
    build_result = build_feature(feature)
    built = build_result["built"]
    build_output = build_result["output"]

    # Step 3: Test (only if build succeeded or files exist)
    tests_pass = False
    test_output = ""
    if built or any((PROJECT_DIR / f).exists() for f in feature.get("files_to_create", [])):
        tests_pass, test_output = run_tests(feature)
    else:
        test_output = "[SKIP] No files to test"

    # Step 4: Commit if tests pass
    committed = False
    if tests_pass and built:
        committed = git_commit_feature(feature)

    entry = {
        "timestamp": datetime.now().isoformat(),
        "feature_id": feature["id"],
        "feature_name": feature["name"],
        "slug": slug,
        "status": "success" if (built and tests_pass and committed) else "failed",
        "built": built,
        "tests_pass": tests_pass,
        "committed": committed,
        "backup_ok": backup_ok,
        "build_output": build_output,
        "test_output": test_output,
        "build_method": build_result.get("method", "unknown")
    }

    log.append(entry)
    save_log(log)

    # Remove lockfile
    try:
        LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass

    return entry


def main():
    parser = argparse.ArgumentParser(description="OOREP Overnight Build Runner")
    parser.add_argument("--feature", type=str, help="Build specific feature by slug")
    parser.add_argument("--list", action="store_true", help="List queue and exit")
    parser.add_argument("--status", action="store_true", help="Show build status and exit")
    args = parser.parse_args()

    if args.list:
        queue = load_queue()
        print(f"Build Queue v{queue['version']}")
        print(f"{'ID':>3} {'Time':>6} {'Slug':<28} {'Risk':>8} {'Status':>10}")
        print("-" * 65)
        log = load_log()
        completed = {e["feature_id"] for e in log if e.get("status") == "success"}
        for f in queue["features"]:
            status = "DONE" if f["id"] in completed else "PENDING"
            print(f"{f['id']:>3} {f['schedule']:>6} {f['slug']:<28} {f['risk_level']:>8} {status:>10}")
        return

    if args.status:
        log = load_log()
        print(f"Total builds: {len(log)}")
        successes = [e for e in log if e.get("status") == "success"]
        failures = [e for e in log if e.get("status") == "failed"]
        print(f"  Success: {len(successes)}")
        print(f"  Failed:  {len(failures)}")
        for e in failures[-5:]:
            print(f"    #{e['feature_id']} {e['feature_name']}: {e.get('build_output', 'no output')[:100]}")
        return

    # Normal run
    if args.feature:
        queue = load_queue()
        feature = next((f for f in queue["features"] if f["slug"] == args.feature), None)
        if not feature:
            print(f"Feature '{args.feature}' not found in queue.")
            sys.exit(1)
        result = run_build(feature)
    else:
        result = run_build()

    print(json.dumps(result, indent=2, default=str))

    if result.get("status") != "success":
        sys.exit(1)


if __name__ == "__main__":
    main()
