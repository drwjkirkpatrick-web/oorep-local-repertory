"""
Test grade_mode feature in repertorize().
Run as standalone script: python tests/test_grade_mode.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path("/home/walker/projects/oorep-local-repertory/oorep")))

from homeopathic_repertory import HomeopathicRepertory

if __name__ == "__main__":
    print("Loading repertory...")
    rep = HomeopathicRepertory()
    print("Loaded.")

    symptoms = ["headache morning", "thirst small quantities", "anxiety night"]

    # Full mode (default)
    print("\n--- FULL mode ---")
    results_full = rep.repertorize(symptoms, top_n=10, grade_mode="full")
    for r in results_full[:5]:
        grades = r.get("grade_distribution", {})
        print(f"  {r['abbrev']} ({r['name']}): score={r['score']} | matches={r['match_count']} | grades={grades}")

    # Classical mode (exclude grade-1)
    print("\n--- CLASSICAL mode (no grade-1) ---")
    results_classical = rep.repertorize(symptoms, top_n=10, grade_mode="classical")
    for r in results_classical[:5]:
        grades = r.get("grade_distribution", {})
        print(f"  {r['abbrev']} ({r['name']}): score={r['score']} | matches={r['match_count']} | grades={grades}")

    # Custom Kent-style weights
    print("\n--- CUSTOM weights {1:1, 2:3, 3:6} ---")
    results_custom = rep.repertorize(symptoms, top_n=10, grade_mode="full", grade_weights={1: 1.0, 2: 3.0, 3: 6.0})
    for r in results_custom[:5]:
        grades = r.get("grade_distribution", {})
        print(f"  {r['abbrev']} ({r['name']}): score={r['score']} | matches={r['match_count']} | grades={grades}")

    print("\n✅ Grade mode tests complete.")
