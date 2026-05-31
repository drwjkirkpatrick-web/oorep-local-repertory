"""
Rubric Gap Analyzer — Benefit #40

Identifies symptoms that do NOT map cleanly to existing rubrics, scores rubric
differentiation quality, and suggests wording for new rubric entries.  Bridges
clinical free-text symptoms to structured repertory coverage.

Usage:
    from oorep.rubric_gap_analyzer import RubricGapAnalyzer
    analyzer = RubricGapAnalyzer()

    # Analyze mapping quality of symptoms to chosen rubrics
    gaps = analyzer.analyze_mapping("burning headache worse night", mapped_rubrics=[...])

    # Find symptoms with poor rubric coverage
    uncovered = analyzer.find_uncovered_symptoms(common_symptoms=["anxiety dreams"])

    # Suggest new rubric text
    suggestions = analyzer.suggest_new_rubric_text(uncovered)

    # Score a specific rubric's differentiation
    score = analyzer.score_rubric_quality(rubric_id=12345)

    # Full gap report
    report = analyzer.generate_gap_report()
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict

try:
    from .homeopathic_repertory import HomeopathicRepertory
except Exception:
    from homeopathic_repertory import HomeopathicRepertory

try:
    from .phantom_rubric_analyzer import PhantomRubricAnalyzer
except Exception:
    from phantom_rubric_analyzer import PhantomRubricAnalyzer


class RubricGapAnalyzer:
    """
    Detects and reports gaps between free-text clinical symptoms and formal
    repertory rubrics.

    Combines lexical matching heuristics with PhantomRubricAnalyzer
    differentiation metrics to answer:
      1. Which symptoms have low-confidence rubric matches?
      2. Which symptoms lack rubric coverage entirely?
      3. How well does a given rubric differentiate remedies?
      4. What new rubric wording might fill the gap?
    """

    # Lexical stop-words that should not be treated as symptom tokens
    STOP_WORDS: Set[str] = {
        "the", "and", "with", "for", "from", "that", "this", "was", "is",
        "are", "were", "been", "have", "has", "had", "not", "but", "on",
        "at", "to", "in", "of", "a", "an", "as", "by", "or", "be",
    }

    # Confidence thresholds
    LOW_CONFIDENCE_THRESHOLD = 0.3
    HIGH_CONFIDENCE_THRESHOLD = 0.7

    def __init__(
        self,
        data_dir: Optional[str] = None,
        repertory: Optional[HomeopathicRepertory] = None,
        phantom_analyzer: Optional[PhantomRubricAnalyzer] = None,
    ):
        """
        Args:
            data_dir: Path to repertory data directory.
            repertory: Existing HomeopathicRepertory instance.
            phantom_analyzer: Existing PhantomRubricAnalyzer for scoring.
        """
        self.rep = repertory or HomeopathicRepertory(data_dir)
        self.phantom = phantom_analyzer or PhantomRubricAnalyzer(self.rep)

        # Build inverted keyword index from rubric fullpaths
        self._rubric_keyword_index: Dict[str, Set[int]] = defaultdict(set)
        self._build_keyword_index()

    def _build_keyword_index(self) -> None:
        """
        Index all rubric fullpath words so we can quickly find candidate rubrics.
        """
        for rubric_id, rubric in self.rep.rubrics.items():
            fullpath = rubric.get("fullpath", "")
            words = self._tokenize(fullpath)
            for w in words:
                self._rubric_keyword_index[w].add(rubric_id)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Lowercase tokenization suitable for rubric-path comparison."""
        return [
            w.lower().strip(".,;:-")
            for w in (text or "").split()
            if len(w) > 2
        ]

    def _stop_filter(self, words: List[str]) -> List[str]:
        """Remove stop words from a token list."""
        return [w for w in words if w not in self.STOP_WORDS]

    # ── Mapping Analysis ────────────────────────────────────────────────────

    def analyze_mapping(
        self, symptoms_text: str, mapped_rubrics: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare free-text symptoms to mapped rubrics and flag low-confidence mappings.

        Args:
            symptoms_text: Clinician's symptom description.
            mapped_rubrics: List of chosen rubric dicts (with at least ``fullpath``).

        Returns:
            Dict with keys:
              - token_coverage: fraction of symptom tokens covered by mapped rubrics
              - rubric_confidences: per-rubric confidence score
              - low_confidence_rubrics: rubrics scoring ≤ LOW_CONFIDENCE_THRESHOLD
              - missing_tokens: symptom tokens with NO rubric coverage
              - overall_confidence: aggregate mapping quality
        """
        symptom_tokens = set(self._stop_filter(self._tokenize(symptoms_text)))
        if not symptom_tokens:
            return {
                "token_coverage": 0.0,
                "rubric_confidences": [],
                "low_confidence_rubrics": [],
                "missing_tokens": [],
                "overall_confidence": 0.0,
            }

        # Aggregate all keyword tokens from mapped rubrics
        covered_tokens: Set[str] = set()
        rubric_confidences = []

        for rubric in mapped_rubrics:
            rid = rubric.get("rubric_id")
            fp = rubric.get("fullpath", "")
            rubric_tokens = set(self._stop_filter(self._tokenize(fp)))
            overlap = symptom_tokens & rubric_tokens
            covered_tokens |= overlap
            # Confidence = Jaccard overlap of symptom tokens with rubric tokens
            union = symptom_tokens | rubric_tokens
            confidence = round(len(overlap) / len(union), 4) if union else 0.0
            rubric_confidences.append({
                "rubric_id": rid,
                "fullpath": fp,
                "confidence": confidence,
                "matched_tokens": list(overlap),
            })

        token_coverage = round(len(covered_tokens) / len(symptom_tokens), 4) if symptom_tokens else 0.0
        low_confidence = [r for r in rubric_confidences if r["confidence"] <= self.LOW_CONFIDENCE_THRESHOLD]
        missing = list(symptom_tokens - covered_tokens)
        # Overall confidence: weighted average of per-rubric confidences, penalized by missing tokens
        avg_conf = sum(r["confidence"] for r in rubric_confidences) / len(rubric_confidences) if rubric_confidences else 0.0
        overall = round(avg_conf * token_coverage, 4)

        return {
            "token_coverage": token_coverage,
            "rubric_confidences": rubric_confidences,
            "low_confidence_rubrics": low_confidence,
            "missing_tokens": missing,
            "overall_confidence": overall,
        }

    # ── Uncovered Symptoms ──────────────────────────────────────────────────

    def find_uncovered_symptoms(
        self,
        common_symptoms: List[str],
        existing_rubrics: Optional[List[Dict[str, Any]]] = None,
        require_full_coverage: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Identify symptoms that are not well represented in the repertory.

        For each symptom phrase, this method measures how many rubric keyword
        matches exist.  If ``require_full_coverage`` is True, symptoms with
        no overlapping rubric fullpath are flagged.

        Args:
            common_symptoms: Free-text symptom phrases from case records.
            existing_rubrics: Optional list of already-selected rubrics to ignore.
            require_full_coverage: If False, returns ANY low-match symptoms.

        Returns:
            List of dicts with keys: symptom_text, match_count, best_rubric_matches,
            uncovered_reason.
        """
        existing_rids: Set[int] = set()
        if existing_rubrics:
            for r in existing_rubrics:
                rid = r.get("rubric_id")
                if isinstance(rid, int):
                    existing_rids.add(rid)

        uncovered = []
        for symptom in common_symptoms:
            tokens = set(self._stop_filter(self._tokenize(symptom)))
            if not tokens:
                continue
            # Find all rubrics that share at least one keyword token
            candidate_rids: Set[int] = set()
            for t in tokens:
                candidate_rids |= self._rubric_keyword_index.get(t, set())
            candidate_rids -= existing_rids

            match_count = len(candidate_rids)
            if require_full_coverage and match_count == 0:
                uncovered.append({
                    "symptom_text": symptom,
                    "match_count": 0,
                    "best_rubric_matches": [],
                    "uncovered_reason": "No rubric fullpath contains any symptom keyword",
                })
            elif not require_full_coverage and match_count < 3:
                # Show top 3 match candidates when partial coverage exists
                best = []
                for rid in list(candidate_rids)[:3]:
                    rubric = self.rep.get_rubric_by_id(rid)
                    if rubric:
                        best.append({
                            "rubric_id": rid,
                            "fullpath": rubric.get("fullpath", "?"),
                        })
                uncovered.append({
                    "symptom_text": symptom,
                    "match_count": match_count,
                    "best_rubric_matches": best,
                    "uncovered_reason": f"Only {match_count} candidate rubrics found",
                })
        return uncovered

    # ── New Rubric Suggestions ──────────────────────────────────────────────

    def suggest_new_rubric_text(
        self, uncovered_symptoms: List[Dict[str, Any]], target_chapter: str = "General"
    ) -> List[Dict[str, Any]]:
        """
        Propose rubric wording for uncovered symptoms.

        Suggestions are generated by normalizing symptom text into a hierarchical
        rubric path.  The optional ``target_chapter`` prefix guides the suggested
        nesting.

        Returns:
            List of dicts with keys: suggested_fullpath, source_symptom,
            rationale, confidence_estimate.
        """
        suggestions = []
        for entry in uncovered_symptoms:
            symptom = entry.get("symptom_text", "")
            if not symptom:
                continue
            # Normalization heuristic: strip "with", "and" joins → " > " nesting
            parts = [p.strip().lower() for p in symptom.split(",")]
            if len(parts) > 1:
                nested = " > ".join(parts[:3])
            else:
                nested = parts[0]
            suggested = f"{target_chapter} > {nested}"
            rationale = (
                f"No existing rubric covers the symptom phrase '{symptom}'. "
                f"Suggested wording nests under '{target_chapter}' to align "
                f"with standard chapter conventions."
            )
            suggestions.append({
                "suggested_fullpath": suggested,
                "source_symptom": symptom,
                "rationale": rationale,
                "confidence_estimate": "low (requires materia medica validation)",
            })
        return suggestions

    # ── Rubric Quality Scoring ──────────────────────────────────────────────

    def score_rubric_quality(
        self, rubric_id: int, include_phantom: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Compute a composite quality score for a single rubric.

        Quality is defined by **differentiation power** — how well the rubric
        separates remedies rather than returning the same polycrest list.

        Args:
            rubric_id: Numeric rubric ID.
            include_phantom: Whether to embed PhantomRubricAnalyzer metrics.

        Returns:
            Dict with quality score, gini, entropy, hhi, remedy_count, and flag
            status; or None if rubric not found.
        """
        rubric = self.rep.get_rubric_by_id(rubric_id)
        if not rubric:
            return None

        remedies = self.rep.get_remedies_for_rubric(rubric_id)
        total_remedies = len(remedies)
        if total_remedies == 0:
            return {
                "rubric_id": rubric_id,
                "fullpath": rubric.get("fullpath", "?"),
                "quality_score": 0.0,
                "flag": "Empty rubric",
            }

        weights = [r["weight"] for r in remedies]
        total_weight = sum(weights)
        # Normalized entropy (0–1 scale)
        raw_entropy = self._entropy(weights)
        max_entropy = math.log2(total_remedies) if total_remedies > 1 else 1.0
        normalized_entropy = raw_entropy / max_entropy if max_entropy > 0 else 0.0

        # Gini coefficient (already 0–1)
        gini = self._gini(weights)
        # Herfindahl (already 0–1)
        hhi = self._herfindahl(weights)
        # Remedy-to-weight ratio: penalize very sparse rubrics
        remedy_weight_balance = total_remedies / len(weights) if len(weights) else 1.0

        # Composite quality score: higher entropy + lower Gini + lower HHI = better
        quality_score = round(
            (normalized_entropy * 0.4) + ((1 - gini) * 0.3) + ((1 - hhi) * 0.3),
            4,
        )

        result = {
            "rubric_id": rubric_id,
            "fullpath": rubric.get("fullpath", "?"),
            "source": rubric.get("source", "?"),
            "quality_score": quality_score,
            "remedy_count": total_remedies,
            "gini": round(gini, 4),
            "entropy_bits": round(raw_entropy, 3),
            "herfindahl": round(hhi, 4),
            "flag": None,
        }

        if include_phantom:
            phantom_report = self.phantom.analyze_rubric(rubric_id)
            if phantom_report:
                result["phantom_flag_reason"] = phantom_report.flag_reason
                result["is_flagged"] = phantom_report.is_flagged
                if phantom_report.is_flagged:
                    result["flag"] = "Poor differentiation (phantom rubric)"

        return result

    # ── Gap Report ──────────────────────────────────────────────────────────

    def generate_gap_report(
        self,
        symptom_samples: Optional[List[str]] = None,
        sample_size: int = 100,
    ) -> Dict[str, Any]:
        """
        Comprehensive report of symptoms and rubric quality across the repertory.

        Optionally analyses a provided list of symptom phrases; otherwise
        performs a light statistical survey of rubric keywords.

        Args:
            symptom_samples: List of free-text symptom phrases to check.
            sample_size: Number of rubrics to sample for quality scoring if no
                         symptom list is provided.

        Returns:
            Dict with keys:
              - total_rubrics: count of rubrics in repertory
              - uncovered_symptoms (if symptom_samples provided)
              - quality_distribution: histogram of quality scores
              - low_quality_rubrics: rubrics with quality_score < 0.4
              - suggestions: proposed new rubrics for uncovered symptoms
              - overall_coverage_estimate
        """
        total_rubrics = len(self.rep.rubrics_list)
        report: Dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
            "total_rubrics": total_rubrics,
        }

        if symptom_samples:
            uncovered = self.find_uncovered_symptoms(symptom_samples)
            report["uncovered_symptoms"] = uncovered
            report["suggestions"] = self.suggest_new_rubric_text(uncovered)
            covered_count = len(symptom_samples) - len(uncovered)
            report["overall_coverage_estimate"] = round(
                covered_count / len(symptom_samples), 3
            ) if symptom_samples else 0.0
        else:
            report["uncovered_symptoms"] = []
            report["suggestions"] = []
            report["overall_coverage_estimate"] = None

        # Sample rubric quality scores
        rubric_quality_scores: Dict[str, float] = {}
        low_quality: List[Dict] = []
        bins = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
        ids = list(self.rep.rubric_to_remedies.keys())
        if sample_size and len(ids) > sample_size:
            ids = random.sample(ids, sample_size)

        for rid in ids:
            score_data = self.score_rubric_quality(rid, include_phantom=False)
            if not score_data:
                continue
            score = score_data["quality_score"]
            rubric_quality_scores[score_data.get("fullpath", "?")] = score
            if score < 0.4:
                low_quality.append({
                    "rubric_id": rid,
                    "fullpath": score_data.get("fullpath", "?"),
                    "quality_score": score,
                    "flag": score_data.get("flag"),
                })
            for label, (lo, hi) in [
                ("0.0-0.2", (0.0, 0.2)),
                ("0.2-0.4", (0.2, 0.4)),
                ("0.4-0.6", (0.4, 0.6)),
                ("0.6-0.8", (0.6, 0.8)),
                ("0.8-1.0", (0.8, 1.0)),
            ]:
                if lo <= score <= hi:
                    bins[label] += 1
                    break

        report["quality_distribution"] = bins
        report["low_quality_rubrics"] = low_quality
        report["average_quality_score"] = round(
            sum(rubric_quality_scores.values()) / len(rubric_quality_scores), 4
        ) if rubric_quality_scores else 0.0
        return report

    # ── Static math utilities (mirroring PhantomRubricAnalyzer for independence)

    @staticmethod
    def _gini(values: List[float]) -> float:
        if not values or sum(values) == 0:
            return 0.0
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        cumsum = 0.0
        for i, v in enumerate(sorted_vals, start=1):
            cumsum += (2 * i - n - 1) * v
        denominator = n * sum(sorted_vals)
        return abs(cumsum) / denominator if denominator else 0.0

    @staticmethod
    def _entropy(values: List[float]) -> float:
        total = sum(values)
        if total == 0:
            return 0.0
        bits = 0.0
        for v in values:
            if v > 0:
                p = v / total
                bits -= p * math.log2(p)
        return round(bits, 3)

    @staticmethod
    def _herfindahl(values: List[float]) -> float:
        total = sum(values)
        if total == 0:
            return 0.0
        return round(sum((v / total) ** 2 for v in values), 4)


from datetime import datetime  # noqa: E402  (used in generate_gap_report)
import random  # noqa: E402
