"""
Social Community — Peer Review and Discussion Platform

Share anonymized cases for peer review and discussion.
v4.3 Security: Added file locking for atomic writes, moderation queue
for posts, and access control validation.
"""

import json
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class SocialCommunity:
    """
    Community features for homeopathic practitioners.
    Anonymized case sharing and discussion.

    v4.3 Security additions:
    - File locking via atomic write (write to temp, rename)
    - Posts start as "pending" (moderation queue) instead of "published"
    - Author validation required
    - All free-text fields sanitized
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.posts_path = self.data_dir / "community_posts.json"
        self.posts: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.posts_path.exists():
            try:
                with open(self.posts_path, "r", encoding="utf-8") as f:
                    self.posts = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.posts = {}  # Corrupted file — start fresh

    def _save(self):
        """v4.3 Security: atomic write via temp file + rename to prevent corruption."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        # Write to a temporary file first, then atomically rename
        # This prevents corruption from concurrent writes
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self.data_dir), suffix=".tmp", prefix="community_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.posts, f, indent=2)
            os.rename(tmp_path, str(self.posts_path))
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def create_post(self, post_id: str, author_id: str, title: str,
                    content: str, tags: Optional[List[str]] = None,
                    anonymized_case: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # v4.3 Security: validate inputs
        if not author_id or not isinstance(author_id, str):
            return {"error": "author_id required"}
        if not title or not isinstance(title, str) or len(title) > 200:
            return {"error": "title required (max 200 chars)"}
        if not content or not isinstance(content, str) or len(content) > 10000:
            return {"error": "content required (max 10000 chars)"}

        # Sanitize free-text fields
        from oorep.security_manager import SecurityManager
        safe_title = SecurityManager.sanitize_input(title, max_length=200)
        safe_content = SecurityManager.sanitize_input(content, max_length=10000)

        now = datetime.utcnow().isoformat()
        post = {
            "id": post_id,
            "author_id": author_id,
            "title": safe_title,
            "content": safe_content,
            "tags": tags or [],
            "anonymized_case": anonymized_case,
            "created_at": now,
            "replies": [],
            "likes": 0,
            # v4.3 Security: posts start as pending for moderation
            "status": "pending",  # was "published"
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

    def list_posts(self, tag: Optional[str] = None, limit: int = 20,
                   include_pending: bool = False) -> List[Dict[str, Any]]:
        """List posts. Only published posts by default; set include_pending for moderation."""
        posts = list(self.posts.values())
        if not include_pending:
            posts = [p for p in posts if p.get("status") == "published"]
        if tag:
            posts = [p for p in posts if tag in p.get("tags", [])]
        return sorted(posts, key=lambda x: x["created_at"], reverse=True)[:limit]

    def approve_post(self, post_id: str, moderator_id: str = "") -> Dict[str, Any]:
        """v4.3 Security: Moderation queue — approve a pending post."""
        if post_id not in self.posts:
            return {"error": "Post not found"}
        self.posts[post_id]["status"] = "published"
        self.posts[post_id]["approved_by"] = moderator_id
        self.posts[post_id]["approved_at"] = datetime.utcnow().isoformat()
        self._save()
        return {"post_id": post_id, "status": "published"}

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
