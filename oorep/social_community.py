"""
Social Community — Peer Review and Discussion Platform

Share anonymized cases for peer review and discussion.
Scaffold — requires moderation and privacy controls.
"""

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class SocialCommunity:
    """
    Community features for homeopathic practitioners.
    Anonymized case sharing and discussion.
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.posts_path = self.data_dir / "community_posts.json"
        self.posts: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.posts_path.exists():
            with open(self.posts_path, "r", encoding="utf-8") as f:
                self.posts = json.load(f)

    def _save(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.posts_path, "w", encoding="utf-8") as f:
            json.dump(self.posts, f, indent=2)

    def create_post(self, post_id: str, author_id: str, title: str,
                    content: str, tags: Optional[List[str]] = None,
                    anonymized_case: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        now = datetime.utcnow().isoformat()
        post = {
            "id": post_id,
            "author_id": author_id,
            "title": title,
            "content": content,
            "tags": tags or [],
            "anonymized_case": anonymized_case,
            "created_at": now,
            "replies": [],
            "likes": 0,
            "status": "published",
        }
        self.posts[post_id] = post
        self._save()
        return post

    def add_reply(self, post_id: str, author_id: str, content: str) -> Dict[str, Any]:
        if post_id not in self.posts:
            return {"error": "Post not found"}
        reply = {
            "author_id": author_id,
            "content": content,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.posts[post_id]["replies"].append(reply)
        self._save()
        return reply

    def like_post(self, post_id: str) -> Dict[str, Any]:
        if post_id in self.posts:
            self.posts[post_id]["likes"] += 1
            self._save()
        return {"post_id": post_id, "likes": self.posts.get(post_id, {}).get("likes", 0)}

    def list_posts(self, tag: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        posts = list(self.posts.values())
        if tag:
            posts = [p for p in posts if tag in p.get("tags", [])]
        return sorted(posts, key=lambda x: x["created_at"], reverse=True)[:limit]

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        return self.posts.get(post_id)

    def anonymize_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove all PII from a case before sharing."""
        safe = {
            "symptoms": case_data.get("symptoms", []),
            "modalities": case_data.get("modalities", []),
            "prescribed_remedy": case_data.get("prescribed_remedy"),
            "outcome": case_data.get("outcome"),
            "age_range": case_data.get("age_range"),  # "20-30" not exact
            "gender": case_data.get("gender"),
        }
        return safe

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_posts": len(self.posts),
            "total_replies": sum(len(p.get("replies", [])) for p in self.posts.values()),
            "total_likes": sum(p.get("likes", 0) for p in self.posts.values()),
            "note": "Community features require moderation setup for production use.",
        }
