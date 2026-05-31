"""
Rubric Explorer

Navigate the Kent (kent-de) rubric hierarchy using parent/child data
extracted from path_parts. Provides breadcrumbs, parent lookup, children,
siblings, ancestors, and descendants.

Usage:
    from oorep.rubric_explorer import RubricExplorer
    explorer = RubricExplorer()
    parent = explorer.get_parent_rubric(12345)
    children = explorer.get_child_rubrics(12345)
    path = explorer.explore_path(12345)
    ancestors = explorer.get_ancestors(12345)
    descendants = explorer.get_descendants(12345)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict


try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


class RubricExplorer:
    """
    Explore hierarchical rubric relationships.

    The OOREP rubrics.json already contains 'path_parts' arrays for the
    kent-de source; we build a parent/child tree from these parts.
    """

    def __init__(self, data_dir: Optional[str] = None, repertory: Optional[HomeopathicRepertory] = None):
        self.rep = repertory or HomeopathicRepertory(data_dir=data_dir)
        self._build_tree()

    def _build_tree(self):
        """
        Build internal tree structures:
        - _id_to_node: rubric_id -> {
            id, fullpath, source, path_parts, parent_id, children_ids
          }
        - _path_to_id: fullpath string (joined by "; ") -> rubric_id
        """
        self._id_to_node: Dict[int, Dict] = {}
        self._path_to_id: Dict[str, int] = {}

        # First pass: index all rubrics
        for rubric_id, rubric in self.rep.rubrics.items():
            parts = rubric.get("path_parts", []) or []
            source = rubric.get("source", "?")
            fullpath = rubric.get("fullpath", "")
            self._id_to_node[rubric_id] = {
                "id": rubric_id,
                "fullpath": fullpath,
                "source": source,
                "path_parts": parts,
                "parent_id": None,
                "children_ids": [],
            }
            # Index exact fullpath (case-sensitive) for quick parent lookup
            if fullpath:
                self._path_to_id[fullpath] = rubric_id

        # Second pass: assign parent_id by looking up parent fullpath
        for node in self._id_to_node.values():
            parts = node["path_parts"]
            if len(parts) > 1:
                # Parent fullpath = all parts but last, joined by source delimiter
                # Kent-DE uses comma-space, but some rubrics use semicolons.
                # We reconstruct using the same separator observed in fullpath.
                sep = self._detect_separator(node["fullpath"], parts)
                parent_path = sep.join(parts[:-1])
                parent_id = self._path_to_id.get(parent_path)
                if parent_id is not None and parent_id != node["id"]:
                    node["parent_id"] = parent_id
                    self._id_to_node[parent_id]["children_ids"].append(node["id"])

    @staticmethod
    def _detect_separator(fullpath: str, parts: List[str]) -> str:
        """
        Try to detect whether the rubric uses '; ' or ', ' as the separator.
        Default to '; ' if uncertain.
        """
        if "; " in fullpath:
            return "; "
        if ", " in fullpath:
            return ", "
        # Fallback: use '; ' as generic separator
        return "; "

    # ── Public API ───────────────────────────────────────────────────────────

    def get_parent_rubric(self, rubric_id: int) -> Optional[Dict]:
        """
        Return the parent rubric dict for a given rubric ID,
        or None if root-level.
        """
        node = self._id_to_node.get(rubric_id)
        if not node or node["parent_id"] is None:
            return None
        parent = self._id_to_node.get(node["parent_id"])
        if parent:
            return {
                "id": parent["id"],
                "fullpath": parent["fullpath"],
                "source": parent["source"],
            }
        return None

    def get_child_rubrics(self, rubric_id: int, limit: Optional[int] = None) -> List[Dict]:
        """
        Return immediate children of a rubric.
        """
        node = self._id_to_node.get(rubric_id)
        if not node:
            return []
        children = []
        for cid in node["children_ids"]:
            child = self._id_to_node.get(cid)
            if child:
                children.append({
                    "id": child["id"],
                    "fullpath": child["fullpath"],
                    "source": child["source"],
                })
        if limit:
            children = children[:limit]
        return children

    def get_siblings(self, rubric_id: int) -> List[Dict]:
        """
        Return sibling rubrics (same parent, excluding self).
        """
        node = self._id_to_node.get(rubric_id)
        if not node or node["parent_id"] is None:
            return []
        parent = self._id_to_node.get(node["parent_id"])
        if not parent:
            return []
        siblings = []
        for cid in parent["children_ids"]:
            if cid == rubric_id:
                continue
            child = self._id_to_node.get(cid)
            if child:
                siblings.append({
                    "id": child["id"],
                    "fullpath": child["fullpath"],
                    "source": child["source"],
                })
        return siblings

    def get_ancestors(self, rubric_id: int) -> List[Dict]:
        """
        Return ordered list from root down to the parent of this rubric.
        """
        node = self._id_to_node.get(rubric_id)
        if not node:
            return []
        ancestors: List[Dict] = []
        current_id = node["parent_id"]
        visited: Set[int] = set()
        while current_id is not None:
            if current_id in visited:
                break  # cycle guard
            visited.add(current_id)
            parent = self._id_to_node.get(current_id)
            if not parent:
                break
            ancestors.append({
                "id": parent["id"],
                "fullpath": parent["fullpath"],
                "source": parent["source"],
            })
            current_id = parent["parent_id"]
        # Reverse so root is first
        ancestors.reverse()
        return ancestors

    def get_descendants(self, rubric_id: int, max_depth: int = 10) -> List[Dict]:
        """
        Return all descendants (recursive children), limited by max_depth.
        """
        node = self._id_to_node.get(rubric_id)
        if not node:
            return []
        result: List[Dict] = []
        queue: List[Tuple[int, int]] = [(cid, 1) for cid in node["children_ids"]]
        visited: Set[int] = set()
        while queue:
            cid, depth = queue.pop(0)
            if cid in visited:
                continue
            visited.add(cid)
            child = self._id_to_node.get(cid)
            if not child:
                continue
            result.append({
                "id": child["id"],
                "fullpath": child["fullpath"],
                "source": child["source"],
                "depth": depth,
            })
            if depth < max_depth:
                for grandchild_id in child["children_ids"]:
                    queue.append((grandchild_id, depth + 1))
        # Sort by fullpath for readability
        result.sort(key=lambda x: x["fullpath"])
        return result

    def explore_path(self, rubric_id: int) -> Dict:
        """
        Return breadcrumb path from root to the rubric, including the rubric itself.

        Returns:
            Dict with keys:
                rubric_id: int
                rubric_fullpath: str
                source: str
                breadcrumb: List[str] — list of fullpath strings from root to self
        """
        node = self._id_to_node.get(rubric_id)
        if not node:
            return {
                "rubric_id": rubric_id,
                "rubric_fullpath": "?",
                "source": "?",
                "breadcrumb": [],
            }
        ancestors = self.get_ancestors(rubric_id)
        breadcrumb = [a["fullpath"] for a in ancestors] + [node["fullpath"]]
        return {
            "rubric_id": rubric_id,
            "rubric_fullpath": node["fullpath"],
            "source": node["source"],
            "breadcrumb": breadcrumb,
        }

    def get_rubric_stats(self, rubric_id: int) -> Optional[Dict]:
        """
        Return structural stats: depth, child count, descendant count.
        """
        node = self._id_to_node.get(rubric_id)
        if not node:
            return None
        ancestors = self.get_ancestors(rubric_id)
        descendants = self.get_descendants(rubric_id)
        return {
            "rubric_id": rubric_id,
            "depth": len(ancestors),
            "child_count": len(node["children_ids"]),
            "descendant_count": len(descendants),
        }
