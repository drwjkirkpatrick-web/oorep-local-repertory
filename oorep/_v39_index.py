"""
Shared index builder for OOREP v3.9 modules.

Builds the (remedy_abbrev → {rubric_id: max_grade}) index that most
of the new statistical modules depend on. Uses the HomeopathicRepertory's
native data: rubric_to_remedies[rid] = [{remedy_id, weight}, ...] and
remedies[remedy_id] = {abbrev, name, ...}.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Optional

try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory


def build_remedy_grade_index(
    repertory: Optional[HomeopathicRepertory] = None,
) -> Dict[str, Dict[int, int]]:
    """
    Build the forward index: abbrev → {rubric_id: max_grade}.

    Looks up remedy abbreviation from the repertory's remedy table by id.
    """
    rep = repertory or HomeopathicRepertory()
    index: Dict[str, Dict[int, int]] = defaultdict(dict)
    for rubric_id, links in rep.rubric_to_remedies.items():
        for link in links:
            remedy_id = link.get("remedy_id")
            weight = link.get("weight", 1)
            if remedy_id is None:
                continue
            # Look up the remedy to get its abbreviation
            remedy = rep.remedies.get(remedy_id)
            if not remedy:
                continue
            abbrev = remedy.get("abbrev")
            if not abbrev:
                continue
            existing = index[abbrev].get(rubric_id, 0)
            if weight > existing:
                index[abbrev][rubric_id] = weight
    return dict(index)
