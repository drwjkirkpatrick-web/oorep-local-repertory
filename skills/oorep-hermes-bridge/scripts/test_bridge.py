#!/usr/bin/env python3
"""
OOREP-Hermes Bridge: Integration Test Suite

Validates all natural-language commands:
- Repertorization
- Remedy lookup / abbreviation decoding
- Profile generation
- Remedy comparison
- Rare remedy triangulation
- Rubric search
"""

import sys
sys.path.insert(0, '/home/walker/.hermes/skills/clinic/oorep-hermes-bridge/scripts')
sys.path.insert(0, '/home/walker/projects/oorep-local-repertory')
from oorep_bridge import OOREPBridge

bridge = OOREPBridge(data_dir='/home/walker/projects/oorep-local-repertory/data')

passed = 0
failed = 0

def test(name, msg, check_fn):
    global passed, failed
    try:
        result = bridge.handle(msg)
        assert check_fn(result), f"Check failed for: {name}"
        print(f"  ✓ {name}")
        passed += 1
    except Exception as e:
        print(f"  ✗ {name}: {e}")
        failed += 1

print("")
print("═══════════════════════════════════════════════════════")
print("  OOREP-Hermes Bridge   Integration Test Suite")
print("═══════════════════════════════════════════════════════\n")

# Test 1: Repertorization via natural language
test(
    "Repertorize command",
    "repertorize dry cough evening, hoarseness",
    lambda r: r['type'] == 'repertorize' and r['result'][0]['score'] > 0
)

# Test 2: Alternative repertorization phrasing
test(
    "Alternative repertorize phrasing",
    "which remedy for dry cough and hoarseness",
    lambda r: r['type'] == 'repertorize' and len(r['result']) > 0
)

# Test 3: Remedy abbreviation lookup
test(
    "Abbreviation lookup",
    "what remedy is Brom?",
    lambda r: r['type'] == 'abbrev_lookup' and 'Bromum' in r['formatted']
)

# Test 4: Profile generation - full name
test(
    "Profile by full name",
    "profile for Bromum",
    lambda r: r['type'] == 'profile' and 'Bromum' in r['formatted']
)

# Test 5: Profile generation - alternative phrasing
test(
    "Profile by 'what is'",
    "what is Bromum",
    lambda r: r['type'] == 'profile' and 'Bromum' in r['formatted']
)

# Test 6: Remedy comparison
test(
    "Remedy comparison",
    "compare Bromum and Hepar Sulphur",
    lambda r: r['type'] == 'compare' and 'Top Shared Rubrics' in r['formatted']
)

# Test 7: Rare remedy triangulation
test(
    "Rare remedy triangulation",
    "rare remedy for hoarse voice, croup",
    lambda r: r['type'] == 'rare' and len(r['result']) > 0
)

# Test 8: Rubric search
test(
    "Rubric search",
    "search rubric throat pit pressing",
    lambda r: r['type'] == 'search_rubric' and 'throat-pit' in r['formatted']
)

# Test 9: Patient case (no case memory since DB is empty)
test(
    "Patient case lookup (empty DB)",
    "patient TestPatient99",
    lambda r: r['type'] == 'patient' and 'No cases found' in r['formatted']
)

# Test 10: Fallback repertorization (no explicit command)
test(
    "Fallback repertorization",
    "dry cough hoarseness",
    lambda r: r['type'] == 'repertorize' and len(r['result']) > 0
)

# Test 11: Unknown command handling
test(
    "Unknown command fallback",
    "blah blah random text 12345",
    lambda r: r['type'] == 'unknown'
)

# Test 12: Empty input
test(
    "Empty input",
    " ",
    lambda r: r['type'] == 'empty'
)

print()
print(f"═══════════════════════════════════════════════════════")
print(f"  Results: {passed} passed, {failed} failed")
print(f"═══════════════════════════════════════════════════════")

if failed > 0:
    sys.exit(1)
print("\n  ✅ ALL TESTS PASSED")
