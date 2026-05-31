"""
Cron Tasks — Benefits #33 (Follow-up Alerts), #42 (Vector Auto-Rebuild), #43 (GitHub Backup)

A self-contained scheduler module that provides cron-ready CLI entrypoints
for OOREP maintenance:

  1. Vector Auto-Rebuild (#42)
     - Compares rubrics.json mtime against vector index mtime.
     - Rebuilds FNV-1a vector index when stale.

  2. GitHub Backup (#43)
     - Generates a timestamped snapshot of JSON + SQLite data.
     - Commits and pushes to remote (requires git config + auth).

  3. Follow-up Alerts (#33)
     - Scans upcoming follow-up dates in SQLite.
     - Emits alert records (intended for Hermes cron delivery or email).

Usage (from crontab):
    python -m oorep.cron_tasks --check-followups
    python -m oorep.cron_tasks --rebuild-vector
    python -m oorep.cron_tasks --github-backup

Or as a library:
    from oorep.cron_tasks import CronTasks
    ct = CronTasks()
    alerts = ct.check_followups(days_ahead=1)
    rebuilt = ct.rebuild_vector_if_stale()
    pushed = ct.github_backup()
"""

import json
import os
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_INDEXES_DIR = PROJECT_ROOT / "indexes"
INDEX_FILE = DEFAULT_INDEXES_DIR / "oorep_vector_index.npz"
RUBRICS_FILE = DEFAULT_DATA_DIR / "rubrics.json"
REMEDIES_FILE = DEFAULT_DATA_DIR / "remedies.json"

try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = DEFAULT_DATA_DIR / "feedback.db"


class CronTasks:
    """Maintenance cron tasks for OOREP."""

    def __init__(self, db_path=None, data_dir=None, indexes_dir=None, rubrics_file=None):
        self.db_path = db_path or DEFAULT_DB
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.indexes_dir = indexes_dir or DEFAULT_INDEXES_DIR
        self.rubrics_file = rubrics_file or RUBRICS_FILE

    # ── #42 Vector Auto-Rebuild ────────────────────────────────────────────────

    def rebuild_vector_if_stale(self, force=False) -> Dict:
        """
        Rebuild the FNV-1a vector index if rubrics.json is newer.

        Returns:
            dict: {"rebuilt": bool, "rubrics_count": int, "reason": str}
        """
        rubrics_mtime = self._mtime(self.rubrics_file)
        index_mtime = self._mtime(INDEX_FILE)
        if not force and rubrics_mtime and index_mtime and rubrics_mtime <= index_mtime:
            return {"rebuilt": False, "rubrics_count": None, "reason": "Vector index is current"}
        # Import and rebuild
        try:
            from oorep.oorep_vector_search import OORepVectorSearch
            vs = OORepVectorSearch(
                index_dir=str(self.indexes_dir),
            )
            vs.build_index()
            return {"rebuilt": True, "rubrics_count": None, "reason": "Index rebuilt from rubrics.json"}
        except Exception as e:
            return {"rebuilt": False, "reason": f"Exception during rebuild: {e}"}

    def _mtime(self, fpath: Path) -> Optional[float]:
        return os.path.getmtime(fpath) if fpath.exists() else None

    # ── #43 GitHub Backup ──────────────────────────────────────────────────────

    def github_backup(self, dry_run=False) -> Dict:
        """
        Create a backup snapshot and push to GitHub.

        Steps:
          1. Verify working tree is clean or commit changes.
          2. Create timestamped .tar.gz of data/ and indexes/.
          3. Place in backups/ directory.
          4. git add, commit, push.

        Returns:
            dict: {"success": bool, "backup_path": str, "git_output": str}
        """
        backup_dir = PROJECT_ROOT / "backups"
        backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"oorep_snapshot_{timestamp}.tar.gz"
        backup_path = backup_dir / backup_name

        # Build tarball
        with tarfile.open(backup_path, "w:gz") as tar:
            if self.data_dir.exists():
                tar.add(self.data_dir, arcname="data")
            if self.indexes_dir.exists():
                tar.add(self.indexes_dir, arcname="indexes")

        if dry_run:
            return {"success": True, "backup_path": str(backup_path), "git_output": "DRY RUN"}

        # Git commit and push
        git_dir = str(PROJECT_ROOT)
        try:
            subprocess.run(["git", "-C", git_dir, "add", "-A"], check=True, capture_output=True)
            subprocess.run(
                ["git", "-C", git_dir, "commit", "-m", f"cron: auto-backup {timestamp}"],
                check=False,
                capture_output=True,
            )  # may fail if nothing to commit — that's okay
            result = subprocess.run(
                ["git", "-C", git_dir, "push", "origin", "main"],
                check=True,
                capture_output=True,
                text=True,
            )
            return {"success": True, "backup_path": str(backup_path), "git_output": result.stdout}
        except subprocess.CalledProcessError as e:
            return {"success": False, "backup_path": str(backup_path), "git_output": e.stderr or e.stdout}

    # ── #33 Follow-up Alerts ───────────────────────────────────────────────────

    def check_followups(self, days_ahead: int = 1, pseudonym: Optional[str] = None) -> List[Dict]:
        """
        Scan prescriptions table for follow-ups due within days_ahead.

        Returns list of alert dicts with keys:
            prescription_id, remedy, potency, pseudonym, next_followup, days_until
        """
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        # Ensure patients table exists
        try:
            c.execute("SELECT id FROM patients LIMIT 1")
        except sqlite3.OperationalError:
            conn.close()
            return []
        now = datetime.now()
        future = now + timedelta(days=days_ahead)
        sql = """
            SELECT pr.id, pr.remedy, pr.potency, pr.prescriber_ack, pt.pseudonym, pr.next_followup
            FROM prescriptions pr
            JOIN patients pt ON pr.patient_id = pt.id
            WHERE pr.next_followup IS NOT NULL
            AND datetime(pr.next_followup) <= ?
            AND datetime(pr.next_followup) >= ?
        """
        params = [future.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')]
        if pseudonym:
            sql += " AND pt.pseudonym = ?"
            params.append(pseudonym)
        sql += " ORDER BY pr.next_followup ASC"
        c.execute(sql, params)
        rows = c.fetchall()
        conn.close()
        alerts = []
        for r in rows:
            due = datetime.strptime(r[5], '%Y-%m-%d %H:%M:%S') if r[5] and 'T' in r[5] or':' in r[5] else None
            days_until = None
            if due:
                try:
                    days_until = max(0, (due - now).days)
                except Exception:
                    days_until = None
            alerts.append({
                "prescription_id": r[0], "remedy": r[1], "potency": r[2],
                "prescriber_ack": r[3], "pseudonym": r[4],
                "next_followup": r[5], "days_until": days_until,
            })
        return alerts

    def mark_followup_sent(self, prescription_id: int) -> bool:
        """Mark a prescription followup as alerted (updates next_followup by +7 days to avoid re-alert)."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        new_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        c.execute("UPDATE prescriptions SET next_followup = ? WHERE id = ?", (new_date, prescription_id))
        conn.commit()
        conn.close()
        return True


def _cli():
    import argparse
    parser = argparse.ArgumentParser(description="OOREP Cron Tasks")
    parser.add_argument("--check-followups", action="store_true", help="Check due followups")
    parser.add_argument("--rebuild-vector", action="store_true", help="Rebuild vector index if stale")
    parser.add_argument("--github-backup", action="store_true", help="Run GitHub backup")
    parser.add_argument("--days-ahead", type=int, default=1, help="Followup lookahead days")
    parser.add_argument("--dry-run", action="store_true", help="Dry run for backup")
    args = parser.parse_args()
    ct = CronTasks()
    if args.check_followups:
        alerts = ct.check_followups(days_ahead=args.days_ahead)
        print(json.dumps({"alerts": alerts, "count": len(alerts)}, indent=2))
    elif args.rebuild_vector:
        result = ct.rebuild_vector_if_stale(force=True)
        print(json.dumps(result, indent=2))
    elif args.github_backup:
        result = ct.github_backup(dry_run=args.dry_run)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    _cli()
