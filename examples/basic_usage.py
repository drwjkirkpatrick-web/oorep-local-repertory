#!/usr/bin/env python3
"""
Basic usage example for OOREP Local Repertory.
Copy this to get started quickly.

Prerequisites:
    pip install -r requirements.txt
    # And either:
    python scripts/extract_oorep.py   # if you have oorep.sql.gz
    # Or point to an existing data/ directory
"""

from oorep import HomeopathicRepertory, ClinicalRubricMapper


def main():
    # Initialize repertory (assumes data/ directory with extracted JSON)
    rep = HomeopathicRepertory(data_dir="data")

    # Show stats
    stats = rep.get_stats()
    print("Repertory Stats:")
    print(f"  Remedies: {stats['remedies']:,}")
    print(f"  Rubrics:  {stats['rubrics']:,}")
    print(f"  Links:    {stats['remedy_rubric_links']:,}")
    print()

    # 1. Simple lexical rubric search
    print("Lexical search: 'headache morning'")
    results = rep.search_rubrics("headache morning", limit=5)
    for r in results:
        print(f"  • {r['fullpath']}")
    print()

    # 2. Multi-symptom repertorization (with Clinical Mapper)
    symptoms = ["thirst small quantities", "anxiety about health"]
    print(f"Repertorizing symptoms: {symptoms}")
    ranked = rep.repertorize(symptoms, top_n=5, retrieval="hybrid")
    print("Top remedies:")
    for r in ranked:
        print(f"  {r['abbrev']:12} {r['name']:25}  score={r['score']}  matches={r['match_count']}")
    print()

    # 3. Clinical Rubric Mapper — practitioner review workflow
    mapper = ClinicalRubricMapper(rep)
    print("Clinical Mapper: 'can't sleep after 3am'")
    candidates = mapper.suggest_candidates("can't sleep after 3am", limit=5)
    for c in candidates:
        print(f"  [{c['review_status']}] {c['rubric']} ({c['remedy_count']} remedies)")
    print()

    # 4. Search for a specific remedy
    print("Remedy search: 'Arsenicum'")
    remedies = rep.search_remedies("Arsenicum", limit=3)
    for rm in remedies:
        print(f"  {rm['abbrev']}: {rm['name']}")


if __name__ == "__main__":
    main()