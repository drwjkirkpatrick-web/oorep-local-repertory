"""
Gamification Engine — Points, Streaks, and Learning Rewards

Earn points for correct remedy identification, streaks, and leaderboards.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class GamificationEngine:
    """
    Track points, streaks, and achievements for learning homeopathy.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.scores_path = self.data_dir / "gamification_scores.json"
        self.scores: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.scores_path.exists():
            with open(self.scores_path, "r", encoding="utf-8") as f:
                self.scores = json.load(f)

    def _save(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.scores_path, "w", encoding="utf-8") as f:
            json.dump(self.scores, f, indent=2)

    def record_activity(self, user_id: str, activity_type: str,
                        points: int, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if user_id not in self.scores:
            self.scores[user_id] = {"total_points": 0, "streak_days": 0, "last_active": None, "achievements": [], "history": []}

        now = datetime.utcnow().isoformat()
        user = self.scores[user_id]

        # Update streak
        if user["last_active"]:
            last = datetime.fromisoformat(user["last_active"])
            today = datetime.utcnow()
            if (today - last).days == 1:
                user["streak_days"] += 1
            elif (today - last).days > 1:
                user["streak_days"] = 1
        else:
            user["streak_days"] = 1

        user["total_points"] += points
        user["last_active"] = now
        user["history"].append({"type": activity_type, "points": points, "at": now, "meta": metadata or {}})

        # Check achievements
        self._check_achievements(user_id)
        self._save()

        return {"user_id": user_id, "points_earned": points, "total": user["total_points"], "streak": user["streak_days"]}

    def _check_achievements(self, user_id: str):
        user = self.scores[user_id]
        ach = set(user.get("achievements", []))

        if user["total_points"] >= 100 and "beginner" not in ach:
            ach.add("beginner")
        if user["total_points"] >= 500 and "intermediate" not in ach:
            ach.add("intermediate")
        if user["total_points"] >= 1000 and "expert" not in ach:
            ach.add("expert")
        if user["streak_days"] >= 7 and "week_streak" not in ach:
            ach.add("week_streak")
        if user["streak_days"] >= 30 and "month_streak" not in ach:
            ach.add("month_streak")

        user["achievements"] = list(ach)

    def get_leaderboard(self, top_n: int = 10) -> List[Dict[str, Any]]:
        users = [
            {"user_id": uid, "points": data["total_points"], "streak": data["streak_days"], "achievements": data["achievements"]}
            for uid, data in self.scores.items()
        ]
        return sorted(users, key=lambda x: -x["points"])[:top_n]

    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        user = self.scores.get(user_id, {"total_points": 0, "streak_days": 0, "achievements": []})
        return {
            "user_id": user_id,
            "total_points": user.get("total_points", 0),
            "streak_days": user.get("streak_days", 0),
            "achievements": user.get("achievements", []),
            "last_active": user.get("last_active"),
        }

    def get_achievement_definitions(self) -> List[Dict[str, Any]]:
        return [
            {"id": "beginner", "name": "Beginner", "description": "Earn 100 points", "points_required": 100},
            {"id": "intermediate", "name": "Intermediate", "description": "Earn 500 points", "points_required": 500},
            {"id": "expert", "name": "Expert", "description": "Earn 1000 points", "points_required": 1000},
            {"id": "week_streak", "name": "7-Day Streak", "description": "Study 7 days in a row", "days_required": 7},
            {"id": "month_streak", "name": "30-Day Streak", "description": "Study 30 days in a row", "days_required": 30},
        ]
