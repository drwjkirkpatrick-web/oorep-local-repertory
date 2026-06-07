"""
Case Complexity Scorer — Coverage Gap & Symptom Entropy Analysis (Module #68)

Quantifies how difficult a case is to repertorize:
  - Rubric coverage ratio (symptoms matched / total symptoms)
  - Symptom entropy (diversity of symptom types)
  - Redundancy score (how many symptoms map to the same rubrics)
  - Phantom rubric exposure (low-information rubrics in the analysis)
  - Composite complexity score (0–1, higher = harder)

Dashboard visual: Complexity gauge + breakdown bars

Usage:
    from oorep.case_complexity_scorer import CaseComplexityScorer
    scorer = CaseComplexityScorer(repertory)
    complexity = scorer.score_case(symptoms=["anxiety", "insomnia", "thirstless"])
"""

import math
from typing import Any, Dict, List, Optional, Set
from collections import Counter, defaultdict


class CaseComplexityScorer:
    """Quantify case complexity for repertorization."""

    def __init__(self, repertory: Optional[Any] = None):
        self.rep = repertory
        self._stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "can", "this", "that", "these", "those",
        }

    def score_case(self, symptoms: List[str], rubric_matches: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Score case complexity.

        Parameters
        ----------
        symptoms: list of free-text symptom descriptions
        rubric_matches: optional list of matched rubric IDs
        """
        n_symptoms = len(symptoms)
        if n_symptoms == 0:
            return {"complexity_score": 0, "interpretation": "No symptoms provided"}

        # Tokenize all symptoms
        all_tokens = []
        symptom_tokens = []
        for s in symptoms:
            tokens = self._tokenize(s)
            symptom_tokens.append(tokens)
            all_tokens.extend(tokens)

        # Symptom entropy — diversity of vocabulary
        token_counts = Counter(all_tokens)
        total_tokens = len(all_tokens)
        entropy = 0.0
        for count in token_counts.values():
            p = count / total_tokens
            if p > 0:
                entropy -= p * math.log2(p)
        max_entropy = math.log2(len(token_counts)) if token_counts else 1
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0

        # Redundancy — how many symptoms share tokens
        overlap_scores = []
        for i in range(n_symptoms):
            for j in range(i + 1, n_symptoms):
                overlap = len(set(symptom_tokens[i]) & set(symptom_tokens[j]))
                total_unique = len(set(symptom_tokens[i]) | set(symptom_tokens[j]))
                if total_unique > 0:
                    overlap_scores.append(overlap / total_unique)
        redundancy = sum(overlap_scores) / len(overlap_scores) if overlap_scores else 0

        # Coverage ratio
        coverage = len(rubric_matches) / n_symptoms if rubric_matches else 0.5
        coverage_penalty = max(0, 1 - coverage)

        # Symptom specificity (longer, more detailed = more specific = lower complexity)
        avg_length = sum(len(t) for t in symptom_tokens) / n_symptoms if n_symptoms > 0 else 0
        specificity = min(1, avg_length / 10)  # Normalize

        # Composite: higher entropy + lower coverage + higher redundancy = harder
        complexity = (
            normalized_entropy * 0.3 +
            coverage_penalty * 0.35 +
            redundancy * 0.2 +
            (1 - specificity) * 0.15
        )

        return {
            "complexity_score": round(min(1, complexity), 4),
            "interpretation": self._interpret(complexity),
            "components": {
                "symptom_entropy": round(normalized_entropy, 4),
                "coverage_ratio": round(coverage, 4),
                "coverage_penalty": round(coverage_penalty, 4),
                "symptom_redundancy": round(redundancy, 4),
                "symptom_specificity": round(specificity, 4),
                "n_symptoms": n_symptoms,
                "unique_tokens": len(token_counts),
                "total_tokens": total_tokens,
            },
            "rubric_matches": rubric_matches or [],
        }

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        return [
            word.lower().strip(".,;:!?()[]{}")
            for word in text.split()
            if word.lower().strip(".,;:!?()[]{}") not in self._stopwords
            and len(word) > 2
        ]

    @staticmethod
    def _interpret(score: float) -> str:
        if score < 0.3:
            return "Straightforward case — good rubric coverage"
        if score < 0.5:
            return "Moderate complexity — some gaps or redundancy"
        if score < 0.7:
            return "Complex case — significant gaps or vague symptoms"
        return "Very complex case — poor coverage, vague or overlapping symptoms"

    def get_feature_overview(self) -> Dict[str, Any]:
        return {
            "feature_id": 68,
            "feature_name": "Case Complexity Scorer",
            "version": "1.0",
            "supports": ["complexity_score", "entropy", "coverage", "redundancy", "specificity"],
            "pure_python": True,
        }
