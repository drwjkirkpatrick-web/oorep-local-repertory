"""
Homeopathic Repertory (OOREP)
Local searchable repertory based on OOREP data.

Usage:
    from homeopathic_repertory import HomeopathicRepertory
    
    rep = HomeopathicRepertory()
    
    # Search rubrics by symptom
    results = rep.search_rubrics("headache morning")
    
    # Get remedies for a rubric
    remedies = rep.get_remedies_for_rubric(rubric_id=12345)
    
    # Search remedies by name
    remedies = rep.search_remedies("arsenic")
    
    # Repertorization (multi-symptom analysis)
    results = rep.repertorize(["head pain morning", "thirst small quantities"])
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Union
from collections import defaultdict


class HomeopathicRepertory:
    """Local searchable homeopathic repertory."""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the repertory.
        
        Args:
            data_dir: Path to data directory. Defaults to same directory as this file.
        """
        if data_dir is None:
            data_dir = Path(__file__).parent
        else:
            data_dir = Path(data_dir)
        
        self.data_dir = data_dir
        
        # Load remedies (small file, load into memory)
        with open(data_dir / "remedies.json", "r", encoding="utf-8") as f:
            self.remedies = {r["id"]: r for r in json.load(f)}
        
        with open(data_dir / "remedies_by_abbrev.json", "r", encoding="utf-8") as f:
            self.remedies_by_abbrev = json.load(f)
        
        # Load search index (8MB, load into memory)
        with open(data_dir / "rubric_search_index.json", "r", encoding="utf-8") as f:
            self.search_index = json.load(f)
        
        # Load rubrics metadata (31MB) - load on demand or keep minimal
        with open(data_dir / "rubrics.json", "r", encoding="utf-8") as f:
            rubrics_list = json.load(f)
            self.rubrics = {r["id"]: r for r in rubrics_list}
        
        # rubric_to_remedies is large (73MB) - we load it but it's indexed by rubric_id
        with open(data_dir / "rubric_to_remedies.json", "r", encoding="utf-8") as f:
            self.rubric_to_remedies = json.load(f)
        
        # Convert string keys back to integers for rubric_to_remedies
        self.rubric_to_remedies = {
            int(k): v for k, v in self.rubric_to_remedies.items()
        }
        
        self._rubric_count = len(self.rubrics)
        self._remedy_count = len(self.remedies)
    
    def get_stats(self) -> Dict:
        """Return repertory statistics."""
        total_links = sum(len(rems) for rems in self.rubric_to_remedies.values())
        return {
            "remedies": self._remedy_count,
            "rubrics": self._rubric_count,
            "remedy_rubric_links": total_links
        }
    
    def search_remedies(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Search remedies by name or abbreviation.
        
        Args:
            query: Search string
            limit: Maximum results
            
        Returns:
            List of matching remedy dictionaries
        """
        query = query.lower()
        results = []
        
        for remedy in self.remedies.values():
            name = remedy.get("name", "").lower()
            abbrev = remedy.get("abbrev", "").lower()
            
            if query in name or query in abbrev:
                results.append(remedy)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_remedy_by_abbrev(self, abbrev: str) -> Optional[Dict]:
        """Get remedy by abbreviation (e.g., 'Ars.' or 'Arsenicum')."""
        return self.remedies_by_abbrev.get(abbrev)
    
    def get_remedy_by_id(self, remedy_id: int) -> Optional[Dict]:
        """Get remedy by ID."""
        return self.remedies.get(remedy_id)
    
    def search_rubrics(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search rubrics (symptoms) by text.
        
        Args:
            query: Search string (e.g., "head pain morning")
            limit: Maximum results
            
        Returns:
            List of matching rubric dictionaries with fullpath
        """
        query_words = [w.lower() for w in query.split() if len(w) > 2]
        
        if not query_words:
            return []
        
        # Score rubrics by how many query words match
        rubric_scores = defaultdict(int)
        
        for word in query_words:
            # Exact word match
            if word in self.search_index:
                for rubric_id in self.search_index[word]:
                    rubric_scores[rubric_id] += 1
            
            # Partial matches
            for idx_word, idx_ids in self.search_index.items():
                if word in idx_word or idx_word in word:
                    for rubric_id in idx_ids:
                        rubric_scores[rubric_id] += 0.5
        
        # Sort by score (descending) and get top results
        sorted_results = sorted(rubric_scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for rubric_id, score in sorted_results[:limit]:
            if rubric_id in self.rubrics:
                rubric = self.rubrics[rubric_id].copy()
                rubric["_match_score"] = score
                results.append(rubric)
        
        return results
    
    def get_rubric_by_id(self, rubric_id: int) -> Optional[Dict]:
        """Get rubric by ID."""
        return self.rubrics.get(rubric_id)
    
    def get_remedies_for_rubric(self, rubric_id: int, limit: Optional[int] = None) -> List[Dict]:
        """
        Get all remedies with grades for a specific rubric.
        
        Args:
            rubric_id: The rubric ID
            limit: Maximum remedies to return (default: all)
            
        Returns:
            List of remedy entries with weight/grade
        """
        links = self.rubric_to_remedies.get(rubric_id, [])
        
        results = []
        for link in links:
            remedy_id = link.get("remedy_id")
            weight = link.get("weight", 1)
            
            remedy = self.remedies.get(remedy_id)
            if remedy:
                results.append({
                    "remedy_id": remedy_id,
                    "abbrev": remedy.get("abbrev"),
                    "name": remedy.get("name"),
                    "weight": weight
                })
        
        # Sort by weight (descending)
        results.sort(key=lambda x: x["weight"], reverse=True)
        
        if limit:
            results = results[:limit]
        
        return results
    
    def get_rubrics_for_remedy(self, remedy_id: int, limit: Optional[int] = None) -> List[Dict]:
        """
        Get all rubrics associated with a specific remedy.
        
        Args:
            remedy_id: The remedy ID
            limit: Maximum rubrics to return
            
        Returns:
            List of rubric entries with weight
        """
        results = []
        
        for rubric_id, links in self.rubric_to_remedies.items():
            for link in links:
                if link.get("remedy_id") == remedy_id:
                    rubric = self.rubrics.get(rubric_id)
                    if rubric:
                        results.append({
                            "rubric_id": rubric_id,
                            "fullpath": rubric.get("fullpath"),
                            "source": rubric.get("source"),
                            "weight": link.get("weight", 1)
                        })
                    break
        
        # Sort by weight (descending)
        results.sort(key=lambda x: x["weight"], reverse=True)
        
        if limit:
            results = results[:limit]
        
        return results
    
    def repertorize(self, symptoms: List[str], top_n: int = 20) -> List[Dict]:
        """
        Perform repertorization - find remedies matching multiple symptoms.
        
        Args:
            symptoms: List of symptom descriptions (e.g., ["head pain", "thirst"])
            top_n: Number of top remedies to return
            
        Returns:
            List of remedies with cumulative scores
        """
        remedy_scores = defaultdict(lambda: {"score": 0, "matches": []})
        
        for symptom in symptoms:
            rubrics = self.search_rubrics(symptom, limit=10)
            
            for rubric in rubrics:
                rubric_id = rubric["id"]
                remedies = self.get_remedies_for_rubric(rubric_id)
                
                for rem in remedies:
                    abbrev = rem["abbrev"]
                    weight = rem["weight"]
                    
                    remedy_scores[abbrev]["score"] += weight * rubric.get("_match_score", 1)
                    remedy_scores[abbrev]["remedy_name"] = rem["name"]
                    remedy_scores[abbrev]["matches"].append({
                        "symptom": rubric.get("fullpath"),
                        "weight": weight
                    })
        
        # Sort by score
        sorted_results = sorted(
            remedy_scores.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )
        
        results = []
        for abbrev, data in sorted_results[:top_n]:
            results.append({
                "abbrev": abbrev,
                "name": data["remedy_name"],
                "score": round(data["score"], 2),
                "match_count": len(data["matches"]),
                "matches": data["matches"][:5]  # Limit matches shown
            })
        
        return results


# Convenience function for quick lookup
def quick_search(symptom: str, limit: int = 10) -> List[Dict]:
    """Quick search for rubrics matching a symptom."""
    rep = HomeopathicRepertory()
    return rep.search_rubrics(symptom, limit=limit)


if __name__ == "__main__":
    # Simple test
    print("Loading repertory...")
    rep = HomeopathicRepertory()
    
    stats = rep.get_stats()
    print(f"\nRepertory loaded:")
    print(f"  Remedies: {stats['remedies']:,}")
    print(f"  Rubrics: {stats['rubrics']:,}")
    print(f"  Links: {stats['remedy_rubric_links']:,}")
    
    print("\n\nTest: Search remedies 'arsenic':")
    for r in rep.search_remedies("arsenic", limit=5):
        print(f"  {r['abbrev']}: {r['name']}")
    
    print("\n\nTest: Search rubrics 'headache morning':")
    for r in rep.search_rubrics("headache morning", limit=5):
        print(f"  {r['fullpath']}")
    
    print("\n\nTest: Repertorization 'fever, thirst':")
    for r in rep.repertorize(["fever", "thirst"], top_n=5):
        print(f"  {r['abbrev']} ({r['name']}): score {r['score']}")
