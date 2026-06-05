"""
Quick integration test for clipboard commands via OOREPBridge.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "projects" / "oorep-local-repertory"))
sys.path.insert(0, str(Path.home() / ".hermes" / "skills" / "clinic" / "oorep-hermes-bridge" / "scripts"))

from oorep_bridge import OOREPBridge

bridge = OOREPBridge()

# 1. Create clipboards
print("=== CREATE ===")
r1 = bridge.handle("new clipboard morning_headache")
print(r1["formatted"])

r2 = bridge.handle("new clipboard eliminate_merc")
print(r2["formatted"])

# 2. List
print("\n=== LIST ===")
r3 = bridge.handle("list clipboards")
print(r3["formatted"])

# 3. Add rubrics (we need real rubric IDs; let's search first)
print("\n=== SEARCH RUBRIC ===")
r4 = bridge.handle("search rubric headache morning")
print(r4["formatted"][:300])

# Get first rubric ID from result
first_rubric = r4["result"][0] if r4.get("result") else None
if first_rubric:
    rid = first_rubric["id"]
    print(f"\nAdding rubric {rid} to morning_headache...")
    r5 = bridge.handle(f"add rubric {rid} to morning_headache")
    print(r5["formatted"])

# 4. Analyze (will be thin if only 1 rubric, but tests the flow)
print("\n=== ANALYZE ===")
r6 = bridge.handle("analyze clipboard morning_headache")
print(r6["formatted"][:500])

# 5. Delete
print("\n=== DELETE ===")
r7 = bridge.handle("delete clipboard morning_headache")
print(r7["formatted"])
r8 = bridge.handle("delete clipboard eliminate_merc")
print(r8["formatted"])

print("\n✅ Bridge clipboard integration test complete.")
