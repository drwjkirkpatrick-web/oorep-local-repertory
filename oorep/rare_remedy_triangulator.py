"""
Rare Remedy Triangulator

Identifies "small" or rare remedies that may be overlooked in standard
repertorization due to polychrest dominance. Uses rubric scarcity and
remedy coverage metrics to surface candidates.

Usage:
    from rare_remedy_triangulator import RareRemedyTriangulator
    
    triangulator = RareRemedyTriangulator()
    rare_candidates = triangulator.triangulate(["head pain morning", "thirst small quantities"])
"""

import json
import math
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict


@dataclass
class RareRemedySignal:
    """A rare remedy candidate with triangulation metrics."""
    remedy_abbrev: str
    remedy_name: str
    total_rubrics: int
    matching_rubrics: int
    matching_rare_rubrics: int  # Rubrics with < 10 remedies
    specificity_score: float    # Average scarcity of matching rubrics
    constellation_match: float  # Coverage ratio of input symptoms
    rarity_quotient: float      # Overall rareness metric
    adjusted_score: float       # Final ranking score
    supporting_rubrics: List[Dict]  # Top rubrics supporting this remedy


class RareRemedyTriangulator:
    """
    Triangulates rare/small remedies based on rubric scarcity and specificity.
    """
    
    # Thresholds for rarity classification
    RARE_RUBRIC_THRESHOLD = 10      # Fewer than 10 remedies = rare rubric
    SMALL_REMEDY_THRESHOLD = 50     # Fewer than 50 rubrics = small remedy
    MEDIUM_REMEDY_THRESHOLD = 150   # Fewer than 150 rubrics = medium remedy
    
    def __init__(self, data_dir: Optional[str] = None, repertory=None):
        """
        Initialize the triangulator.
        
        Args:
            data_dir: Path to repertory data directory
            repertory: Existing HomeopathicRepertory instance (optional)
        """
        if repertory is not None:
            self.rep = repertory
            self._owns_repertory = False
        else:
            try:
                from .homeopathic_repertory import HomeopathicRepertory
            except Exception:
                from homeopathic_repertory import HomeopathicRepertory
            self.rep = HomeopathicRepertory(data_dir)
            self._owns_repertory = True
        
        # Pre-compute remedy coverage stats
        self._remedy_rubric_counts: Dict[int, int] = {}
        self._rubric_remedy_counts: Dict[int, int] = {}
        
        self._compute_coverage_stats()
    
    def _compute_coverage_stats(self):
        """Pre-compute remedy and rubric coverage statistics."""
        # Count rubrics per remedy
        for rubric_id, links in self.rep.rubric_to_remedies.items():
            self._rubric_remedy_counts[rubric_id] = len(links)
            
            for link in links:
                remedy_id = link.get("remedy_id")
                if remedy_id is not None:
                    self._remedy_rubric_counts[remedy_id] = \
                        self._remedy_rubric_counts.get(remedy_id, 0) + 1
    
    def get_remedy_rubric_count(self, remedy_id: int) -> int:
        """Get total number of rubrics for a remedy."""
        return self._remedy_rubric_counts.get(remedy_id, 0)
    
    def get_rubric_remedy_count(self, rubric_id: int) -> int:
        """Get total number of remedies for a rubric."""
        return self._rubric_remedy_counts.get(rubric_id, 0)
    
    def is_rare_rubric(self, rubric_id: int) -> bool:
        """Check if a rubric is rare (few competing remedies)."""
        return self.get_rubric_remedy_count(rubric_id) < self.RARE_RUBRIC_THRESHOLD
    
    def is_small_remedy(self, remedy_id: int) -> bool:
        """Check if a remedy has limited rubric coverage."""
        return self.get_remedy_rubric_count(remedy_id) < self.SMALL_REMEDY_THRESHOLD
    
    def calculate_specificity_score(self, rubric_ids: List[int]) -> float:
        """
        Calculate average specificity (scarcity) of rubrics.
        Higher score = more specific/rare rubrics.
        """
        if not rubric_ids:
            return 0.0
        
        scores = []
        for rubric_id in rubric_ids:
            remedy_count = self.get_rubric_remedy_count(rubric_id)
            # Scarcity score: 1.0 for single-remedy rubric, decreasing as more remedies compete
            scarcity = 1.0 / math.log(remedy_count + math.e - 1)
            scores.append(scarcity)
        
        return sum(scores) / len(scores)
    
    def calculate_rarity_quotient(self, remedy_id: int, matching_rare_rubrics: int) -> float:
        """
        Calculate overall rarity quotient for a remedy.
        Combines remedy size with rare rubric coverage.
        """
        total_rubrics = self.get_remedy_rubric_count(remedy_id)
        if total_rubrics == 0:
            return 0.0
        
        # Base rarity from remedy size (smaller = rarer)
        size_rarity = 1.0 / math.log(total_rubrics + 1)
        
        # Boost from rare rubric matches
        rare_boost = math.log(matching_rare_rubrics + 1)
        
        # Combined quotient
        return size_rarity * (1 + rare_boost)
    
    def triangulate(
        self, 
        symptoms: List[str], 
        top_n: int = 10,
        min_rare_rubrics: int = 1,
        max_total_rubrics: int = 200
    ) -> List[RareRemedySignal]:
        """
        Find rare remedy candidates based on symptom constellation.
        
        Args:
            symptoms: List of symptom descriptions
            top_n: Number of top rare candidates to return
            min_rare_rubrics: Minimum rare rubrics required for inclusion
            max_total_rubrics: Maximum total rubrics for a remedy to be considered "rare"
            
        Returns:
            List of RareRemedySignal objects, ranked by adjusted_score
        """
        # Find matching rubrics for each symptom
        symptom_rubrics: Dict[str, List[Dict]] = {}
        all_rubric_ids = set()
        
        for symptom in symptoms:
            rubrics = self.rep.search_rubrics(symptom, limit=15)
            symptom_rubrics[symptom] = rubrics
            all_rubric_ids.update(r["id"] for r in rubrics)
        
        # Score remedies across all matching rubrics
        remedy_data = defaultdict(lambda: {
            "matching_rubrics": [],
            "rare_rubric_count": 0,
            "symptoms_covered": set(),
            "total_weight": 0.0,
        })
        
        for symptom, rubrics in symptom_rubrics.items():
            for rubric in rubrics:
                rubric_id = rubric["id"]
                is_rare = self.is_rare_rubric(rubric_id)
                match_score = rubric.get("_match_score", 1.0)
                
                # Get remedies for this rubric
                remedies = self.rep.get_remedies_for_rubric(rubric_id)
                
                for rem in remedies:
                    remedy_id = rem["remedy_id"]
                    abbrev = rem["abbrev"]
                    weight = rem["weight"]
                    
                    # Skip polychrests (remedies with too many rubrics)
                    total_rubrics = self.get_remedy_rubric_count(remedy_id)
                    if total_rubrics > max_total_rubrics:
                        continue
                    
                    rd = remedy_data[abbrev]
                    rd["remedy_id"] = remedy_id
                    rd["remedy_name"] = rem["name"]
                    rd["total_rubrics"] = total_rubrics
                    rd["matching_rubrics"].append({
                        "rubric_id": rubric_id,
                        "fullpath": rubric.get("fullpath"),
                        "weight": weight,
                        "is_rare": is_rare,
                        "rubric_remedy_count": self.get_rubric_remedy_count(rubric_id),
                    })
                    rd["total_weight"] += weight * match_score
                    rd["symptoms_covered"].add(symptom)
                    
                    if is_rare:
                        rd["rare_rubric_count"] += 1
        
        # Build RareRemedySignal objects
        signals = []
        
        for abbrev, data in remedy_data.items():
            # Skip if not enough rare rubrics
            if data["rare_rubric_count"] < min_rare_rubrics:
                continue
            
            matching_rubric_ids = [r["rubric_id"] for r in data["matching_rubrics"]]
            
            # Calculate metrics
            specificity = self.calculate_specificity_score(matching_rubric_ids)
            rarity_quotient = self.calculate_rarity_quotient(
                data["remedy_id"], 
                data["rare_rubric_count"]
            )
            constellation_match = len(data["symptoms_covered"]) / len(symptoms)
            
            # Adjusted score combines multiple factors
            adjusted_score = (
                data["total_weight"] * 
                specificity * 
                rarity_quotient * 
                (1 + constellation_match)
            )
            
            # Get top supporting rubrics
            supporting = sorted(
                data["matching_rubrics"],
                key=lambda x: (x["is_rare"], x["weight"]),
                reverse=True
            )[:5]
            
            signal = RareRemedySignal(
                remedy_abbrev=abbrev,
                remedy_name=data["remedy_name"],
                total_rubrics=data["total_rubrics"],
                matching_rubrics=len(data["matching_rubrics"]),
                matching_rare_rubrics=data["rare_rubric_count"],
                specificity_score=round(specificity, 3),
                constellation_match=round(constellation_match, 3),
                rarity_quotient=round(rarity_quotient, 3),
                adjusted_score=round(adjusted_score, 2),
                supporting_rubrics=[{
                    "fullpath": r["fullpath"],
                    "weight": r["weight"],
                    "is_rare": r["is_rare"],
                    "remedies_in_rubric": r["rubric_remedy_count"],
                } for r in supporting]
            )
            signals.append(signal)
        
        # Sort by adjusted score descending
        signals.sort(key=lambda x: x.adjusted_score, reverse=True)
        
        return signals[:top_n]
    
    def explain_rarity(self, remedy_abbrev: str) -> Dict:
        """
        Explain why a remedy is considered rare (for debugging/education).
        
        Args:
            remedy_abbrev: Remedy abbreviation (e.g., "Abies-c.")
            
        Returns:
            Dictionary with rarity statistics
        """
        remedy = self.rep.get_remedy_by_abbrev(remedy_abbrev)
        if not remedy:
            return {"error": f"Remedy '{remedy_abbrev}' not found"}
        
        remedy_id = remedy.get("id")
        total_rubrics = self.get_remedy_rubric_count(remedy_id)
        
        # Get all rubrics for this remedy
        rubrics = self.rep.get_rubrics_for_remedy(remedy_id)
        
        # Categorize by rarity
        rare_rubrics = []
        common_rubrics = []
        
        for r in rubrics:
            rubric_id = r["rubric_id"]
            remedy_count = self.get_rubric_remedy_count(rubric_id)
            rubric_info = {
                "fullpath": r["fullpath"],
                "weight": r["weight"],
                "remedies_in_rubric": remedy_count,
            }
            
            if remedy_count < self.RARE_RUBRIC_THRESHOLD:
                rare_rubrics.append(rubric_info)
            else:
                common_rubrics.append(rubric_info)
        
        # Classify remedy size
        if total_rubrics < self.SMALL_REMEDY_THRESHOLD:
            size_class = "small"
        elif total_rubrics < self.MEDIUM_REMEDY_THRESHOLD:
            size_class = "medium"
        else:
            size_class = "large"
        
        return {
            "remedy_abbrev": remedy_abbrev,
            "remedy_name": remedy.get("name"),
            "total_rubrics": total_rubrics,
            "size_classification": size_class,
            "rare_rubrics_count": len(rare_rubrics),
            "common_rubrics_count": len(common_rubrics),
            "rare_rubric_percentage": round(100 * len(rare_rubrics) / total_rubrics, 1) if total_rubrics > 0 else 0,
            "top_rare_rubrics": rare_rubrics[:10],
            "rarity_quotient": round(1.0 / math.log(total_rubrics + 1), 3),
        }


def triangulate_rare_remedies(symptoms: List[str], top_n: int = 10) -> List[Dict]:
    """
    Convenience function for quick rare remedy triangulation.
    
    Args:
        symptoms: List of symptom descriptions
        top_n: Number of candidates to return
        
    Returns:
        List of rare remedy candidates as dictionaries
    """
    triangulator = RareRemedyTriangulator()
    signals = triangulator.triangulate(symptoms, top_n=top_n)
    return [asdict(s) for s in signals]


if __name__ == "__main__":
    # Test the triangulator
    print("Initializing Rare Remedy Triangulator...")
    tri = RareRemedyTriangulator()
    
    print("\n" + "="*60)
    print("TEST: Triangulate rare remedies for 'head pain morning, thirst'")
    print("="*60)
    
    symptoms = ["head pain morning", "thirst small quantities"]
    results = tri.triangulate(symptoms, top_n=10)
    
    print(f"\nFound {len(results)} rare remedy candidates:\n")
    
    for i, r in enumerate(results[:5], 1):
        print(f"{i}. {r.remedy_abbrev} ({r.remedy_name})")
        print(f"   Total rubrics: {r.total_rubrics} | "
              f"Rare rubrics matched: {r.matching_rare_rubrics}")
        print(f"   Specificity: {r.specificity_score} | "
              f"Rarity quotient: {r.rarity_quotient}")
        print(f"   Adjusted score: {r.adjusted_score}")
        print(f"   Supporting: {', '.join(s['fullpath'][:40] + '...' if len(s['fullpath']) > 40 else s['fullpath'] for s in r.supporting_rubrics[:2])}")
        print()
    
    print("\n" + "="*60)
    print("TEST: Explain rarity for 'Abies-c.'")
    print("="*60)
    
    explanation = tri.explain_rarity("Abies-c.")
    print(f"\n{explanation['remedy_name']} ({explanation['remedy_abbrev']})")
    print(f"Size: {explanation['size_classification']} ({explanation['total_rubrics']} rubrics)")
    print(f"Rare rubrics: {explanation['rare_rubrics_count']} ({explanation['rare_rubric_percentage']}%)")
