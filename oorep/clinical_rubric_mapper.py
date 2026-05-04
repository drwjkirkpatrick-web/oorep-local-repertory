#!/usr/bin/env python3
"""
Clinical Rubric Mapper for OOREP.

Purpose:
- Normalize patient-friendly symptom language into repertory-oriented query text.
- Retrieve reviewable rubric candidates using lexical/vector/hybrid OOREP search.
- Let accepted practitioner-reviewed rubrics drive repertorization.

Clinical integrity guardrail:
- Retrieval/normalization scores are only for finding rubric candidates.
- Final remedy scoring remains classical: sum of OOREP remedy grades for accepted rubrics.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:  # pragma: no cover - import-time fallback for external callers
    try:
        from homeopathic_repertory import HomeopathicRepertory
    except Exception:
        HomeopathicRepertory = None


WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9']+", re.IGNORECASE)


DEFAULT_SYNONYMS: Dict[str, List[str]] = {
    # Sleep / time language
    "can't sleep": ["sleep", "sleeplessness", "insomnia", "waking"],
    "cant sleep": ["sleep", "sleeplessness", "insomnia", "waking"],
    "cannot sleep": ["sleep", "sleeplessness", "insomnia", "waking"],
    "insomnia": ["sleep", "sleeplessness", "waking"],
    "sleepless": ["sleep", "sleeplessness"],
    "3am": ["night", "after midnight", "morning", "waking"],
    "3 a.m.": ["night", "after midnight", "morning", "waking"],
    "after 3": ["night", "after midnight", "morning", "waking"],
    "after midnight": ["night", "midnight", "waking"],

    # Thirst language
    "small sips": ["thirst", "small quantities", "often"],
    "little sips": ["thirst", "small quantities", "often"],
    "sip": ["thirst", "small quantities"],
    "sips": ["thirst", "small quantities"],
    "small quantities": ["thirst", "small quantities"],

    # Pain language
    "head hurts": ["head", "pain", "headache"],
    "head ache": ["head", "pain", "headache"],
    "headache": ["head", "pain", "headache"],
    "hurts": ["pain"],
    "ache": ["pain"],

    # Mental/emotional language
    "worried": ["anxiety", "fear", "mind"],
    "worry": ["anxiety", "fear", "mind"],
    "anxious": ["anxiety", "fear", "mind"],
    "anxiety": ["anxiety", "fear", "mind"],
    "about health": ["health", "about", "disease", "illness"],
    "health anxiety": ["anxiety", "health", "about"],

    # Modalities/common patient phrasing
    "worse": ["aggravation", "agg", "worse"],
    "better": ["amelioration", "amel", "better"],
    "morning": ["morning", "mornings"],
    "evening": ["evening", "night"],
    "cold drinks": ["cold", "drinks", "water"],
    "warmth": ["warm", "heat"],
}


@dataclass
class NormalizedSymptom:
    original: str
    cleaned: str
    expanded_terms: List[str]
    expanded_query: str

    def to_dict(self) -> Dict:
        return asdict(self)


class ClinicalRubricMapper:
    """Map patient symptom phrasing to practitioner-reviewable OOREP rubrics."""

    def __init__(self, repertory: Optional[HomeopathicRepertory] = None, synonyms: Optional[Dict[str, List[str]]] = None):
        if repertory is None and HomeopathicRepertory is not None:
            try:
                repertory = HomeopathicRepertory()
            except Exception:
                repertory = None
        self.repertory = repertory
        merged = dict(DEFAULT_SYNONYMS)
        if synonyms:
            merged.update(synonyms)
        self.synonyms = merged

    @staticmethod
    def _clean(text: str) -> str:
        text = (text or "").strip().lower()
        text = text.replace("’", "'")
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def _tokens(text: str) -> List[str]:
        return [t.lower() for t in WORD_RE.findall(text or "") if len(t) > 1]

    @staticmethod
    def _unique_preserve_order(items: Iterable[str]) -> List[str]:
        seen = set()
        out = []
        for item in items:
            cleaned = item.strip().lower()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                out.append(cleaned)
        return out

    def normalize_symptom(self, symptom: str) -> NormalizedSymptom:
        """Return patient text plus repertory-oriented synonym expansion."""
        cleaned = self._clean(symptom)
        expanded: List[str] = []
        expanded.extend(self._tokens(cleaned))

        # Phrase-level expansions first, so "small sips" can add "small quantities".
        for phrase, additions in self.synonyms.items():
            if phrase in cleaned:
                expanded.extend(additions)

        # Token-level expansions.
        for token in self._tokens(cleaned):
            expanded.extend(self.synonyms.get(token, []))

        expanded_terms = self._unique_preserve_order(expanded)
        expanded_query = " ".join(expanded_terms)
        return NormalizedSymptom(
            original=symptom,
            cleaned=cleaned,
            expanded_terms=expanded_terms,
            expanded_query=expanded_query,
        )

    def suggest_candidates(
        self,
        symptom: str,
        limit: int = 10,
        retrieval: str = "hybrid",
        require_remedies: bool = True,
    ) -> List[Dict]:
        """Suggest rubric candidates for practitioner review.

        By default, exclude rubrics that have no remedy links, because they cannot
        contribute to downstream repertorization.
        """
        if self.repertory is None:
            raise RuntimeError("OOREP repertory is not available")

        normalized = self.normalize_symptom(symptom)
        mode = (retrieval or "hybrid").lower().strip()
        query = normalized.expanded_query
        search_limit = max(limit * 5, limit, 25)

        if mode == "lexical":
            rubrics = self.repertory.search_rubrics(query, limit=search_limit)
        elif mode == "vector":
            rubrics = self.repertory.search_rubrics_vector(query, limit=search_limit)
        else:
            rubrics = self.repertory.search_rubrics_hybrid(query, limit=search_limit)

        candidates: List[Dict] = []
        for rubric in rubrics:
            remedies = self.repertory.get_remedies_for_rubric(int(rubric["id"]))
            remedy_count = len({r.get("abbrev") for r in remedies if r.get("abbrev")})
            if require_remedies and remedy_count == 0:
                continue
            score = rubric.get("_hybrid_score", rubric.get("_vector_score", rubric.get("_match_score", 0.0)))
            candidates.append(
                {
                    "rank": len(candidates) + 1,
                    "review_status": "pending",
                    "query_original": normalized.original,
                    "query_expanded": normalized.expanded_query,
                    "rubric_id": int(rubric["id"]),
                    "rubric": rubric.get("fullpath", ""),
                    "source": rubric.get("source", ""),
                    "retrieval": mode,
                    "retrieval_score": float(score or 0.0),
                    "remedy_count": remedy_count,
                }
            )
            if len(candidates) >= limit:
                break
        return candidates

    def suggest_case_candidates(self, symptoms: List[str], limit_per_symptom: int = 8, retrieval: str = "hybrid") -> Dict:
        """Return normalized symptoms plus candidate rubrics for a whole case."""
        return {
            "created_at": datetime.now().isoformat(),
            "retrieval": retrieval,
            "symptoms": [
                {
                    "normalized": self.normalize_symptom(symptom).to_dict(),
                    "candidates": self.suggest_candidates(symptom, limit=limit_per_symptom, retrieval=retrieval),
                }
                for symptom in symptoms
            ],
        }

    def repertorize_accepted_rubrics(self, accepted_rubrics: List[Dict], top_n: int = 20) -> List[Dict]:
        """Repertorize from practitioner-accepted rubric IDs using classical grades only."""
        if self.repertory is None:
            raise RuntimeError("OOREP repertory is not available")

        remedy_scores = defaultdict(lambda: {"score": 0, "matches": [], "_rubric_ids": set(), "remedy_name": ""})
        seen = set()
        for accepted in accepted_rubrics:
            rubric_id = int(accepted["rubric_id"])
            if rubric_id in seen:
                continue
            seen.add(rubric_id)
            rubric = self.repertory.get_rubric_by_id(rubric_id) or {}
            remedies = self.repertory.get_remedies_for_rubric(rubric_id)

            scored_remedies_for_rubric = set()
            for rem in remedies:
                abbrev = rem["abbrev"]
                if abbrev in scored_remedies_for_rubric:
                    continue
                scored_remedies_for_rubric.add(abbrev)

                weight = rem["weight"]
                remedy_scores[abbrev]["score"] += weight
                remedy_scores[abbrev]["remedy_name"] = rem["name"]
                remedy_scores[abbrev]["_rubric_ids"].add(rubric_id)
                remedy_scores[abbrev]["matches"].append(
                    {
                        "query_symptom": accepted.get("query_original"),
                        "rubric_id": rubric_id,
                        "rubric": accepted.get("rubric") or rubric.get("fullpath"),
                        "source": accepted.get("source") or rubric.get("source"),
                        "weight": weight,
                    }
                )

        sorted_results = sorted(remedy_scores.items(), key=lambda x: x[1]["score"], reverse=True)
        results: List[Dict] = []
        for abbrev, data in sorted_results[:top_n]:
            results.append(
                {
                    "abbrev": abbrev,
                    "name": data["remedy_name"],
                    "score": data["score"],
                    "match_count": len(data["_rubric_ids"]),
                    "matches": data["matches"][:8],
                }
            )
        return results

    def save_candidate_review(self, review: Dict, output_path: Optional[str] = None) -> Path:
        """Persist candidate review JSON locally for later practitioner acceptance/outcome tracking."""
        if output_path is None:
            out_dir = Path.home() / ".hermes" / "data" / "remedy_feedback" / "rubric_reviews"
            out_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(out_dir / f"rubric_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(review, indent=2, ensure_ascii=False), encoding="utf-8")
        return path


def demo() -> None:
    mapper = ClinicalRubricMapper()
    symptoms = ["can't sleep after 3am", "thirst for little sips", "anxiety about health"]
    review = mapper.suggest_case_candidates(symptoms, limit_per_symptom=5, retrieval="hybrid")
    print(json.dumps(review, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    demo()
