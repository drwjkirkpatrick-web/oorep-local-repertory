#!/usr/bin/env python3
"""
Cycle Builder — Interactive CLI for constructing Cycles & Segments data.

Usage:
    python build_cycle.py --interactive       # Build a new cycle interactively
    python build_cycle.py --template NAME     # Emit a JSON template for NAME
    python build_cycle.py --validate FILE     # Validate a cycle JSON file
    python build_cycle.py --list              # List built-in cycles in data/cycles/

Each cycle is a directed graph of segments. Every segment must have:
  - name: unique label within the cycle
  - description: narrative of the defensive reaction
  - symptoms: representative rubric-like symptoms
  - generalizations: Boenninghausen-style broad categories
  - next_segment: name of the next segment (or first segment name to loop)

The cycle should be a closed loop (cycle_loop=true) unless it is a terminal
progression (e.g., acute disease that resolves or kills).

Authoritative sources:
  - Herscu, P. (1996). Stramonium. NESH Press.
  - Herscu, P. & Rothenberg, A. NESH curriculum and NEJH articles.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Default data directory relative to this script
DEFAULT_CYCLES_DIR = Path(__file__).parent.parent / "data" / "cycles"


def _input_nonempty(prompt: str) -> str:
    while True:
        val = input(prompt).strip()
        if val:
            return val
        print("  (required — please enter a value)")


def _input_list(prompt: str, sentinel: str = "done") -> List[str]:
    print(f"  Enter items one per line. Type '{sentinel}' when finished.")
    items: List[str] = []
    while True:
        item = input(f"    {prompt} ").strip()
        if item.lower() == sentinel.lower():
            break
        if item:
            items.append(item)
    return items


def _input_yes_no(prompt: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    resp = input(f"{prompt} {suffix} ").strip().lower()
    if not resp:
        return default
    return resp.startswith("y")


def interactive_builder(cycles_dir: Path) -> None:
    """Build a cycle interactively via CLI."""
    print("=" * 60)
    print("  Cycle & Segment Builder — Interactive Mode")
    print("=" * 60)
    print()

    remedy_name = _input_nonempty("Remedy name (e.g., 'Vipera'): ")
    remedy_abbrev = _input_nonempty("Abbreviation (e.g., 'Vip.'): ")

    print("\nOne-sentence essence: attempt to capture EVERY symptom in a single sentence.")
    print("Example for Stramonium:")
    print('  "Driven by confusion, fears, and vulnerability, Stramonium is engaged..."')
    sentence = _input_nonempty("Essence: ")

    hierarchy_phase: Optional[int] = None
    if _input_yes_no("Assign Map of Hierarchy phase?"):
        while True:
            phase_str = input("  Phase (1=Polychrests, 2=Nosodes, 3=Transition, 4=Deep Pathology): ").strip()
            if phase_str in ("1", "2", "3", "4"):
                hierarchy_phase = int(phase_str)
                break
            print("  Please enter 1, 2, 3, or 4.")

    print("\n--- Segments ---")
    print("Each segment is a station in the cycle. Enter at least 3 segments.")
    print("The last segment's 'next' should be the first segment's name to close the loop.")
    print()

    segments: List[Dict[str, Any]] = []
    while True:
        print(f"\n-- Segment #{len(segments) + 1} --")
        name = _input_nonempty("Segment name (e.g., 'Fear of death'): ")
        description = _input_nonempty("Description: ")
        symptoms = _input_list("Symptom")
        generalizations = _input_list("Generalization")

        if segments:
            default_next = segments[0]["name"]
            print(f"  Next segment after '{name}'? (default: '{default_next}')")
        else:
            default_next = ""
            print("  Next segment after this one? (enter name of segment #2 later)")
        next_seg = input(f"    Next segment {f'[{default_next}]' if default_next else ''}: ").strip()
        if not next_seg and default_next:
            next_seg = default_next

        segments.append(
            {
                "name": name,
                "description": description,
                "symptoms": symptoms,
                "generalizations": generalizations,
                "next_segment": next_seg or None,
            }
        )

        if not _input_yes_no("Add another segment?", default=True):
            break

    # Warn about loop closure
    if len(segments) >= 2:
        last = segments[-1]
        first = segments[0]
        if last["next_segment"] != first["name"]:
            print(f"\n⚠️  Warning: last segment ('{last['name']}') does not loop back to first ('{first['name']}').")
            if _input_yes_no("Close the loop now?"):
                last["next_segment"] = first["name"]

    references = _input_list("Reference citation")
    if not references:
        references = ["Herscu, P. NESH curriculum materials."]

    cycle: Dict[str, Any] = {
        "remedy_name": remedy_name,
        "remedy_abbrev": remedy_abbrev,
        "sentence": sentence,
        "cycle_loop": True,
        "map_of_hierarchy_phase": hierarchy_phase,
        "references": references,
        "segments": segments,
    }

    # Write
    cycles_dir.mkdir(parents=True, exist_ok=True)
    filename = cycles_dir / f"{remedy_name.lower().replace(' ', '_')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(cycle, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved to {filename}")
    print(f"   Segments: {len(segments)} | Loop: {cycle['cycle_loop']}")


def emit_template(remedy_name: str, cycles_dir: Path) -> None:
    """Emit a JSON template for a named remedy."""
    abbrev = input("Abbreviation (e.g., 'Vip.'): ").strip() or "XXX."
    template: Dict[str, Any] = {
        "remedy_name": remedy_name,
        "remedy_abbrev": abbrev,
        "sentence": "",
        "cycle_loop": True,
        "map_of_hierarchy_phase": None,
        "references": [],
        "segments": [
            {
                "name": "Segment 1",
                "description": "",
                "symptoms": [],
                "generalizations": [],
                "next_segment": "Segment 2",
            },
            {
                "name": "Segment 2",
                "description": "",
                "symptoms": [],
                "generalizations": [],
                "next_segment": "Segment 1",
            },
        ],
    }
    cycles_dir.mkdir(parents=True, exist_ok=True)
    filename = cycles_dir / f"{remedy_name.lower().replace(' ', '_')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    print(f"📝 Template saved to {filename}")


def validate_cycle(path: Path) -> List[str]:
    """Validate a cycle JSON file. Returns list of error strings."""
    errors: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]

    required_top = ["remedy_name", "remedy_abbrev", "sentence", "segments"]
    for key in required_top:
        if key not in data:
            errors.append(f"Missing top-level key: '{key}'")

    segments = data.get("segments", [])
    if not isinstance(segments, list):
        errors.append("'segments' must be a list")
    elif len(segments) < 2:
        errors.append(f"Cycle must have at least 2 segments (found {len(segments)})")
    else:
        names = [s.get("name", "") for s in segments]
        if len(set(names)) != len(names):
            errors.append("Duplicate segment names detected")

        # Check that every next_segment points to a real name
        for seg in segments:
            nxt = seg.get("next_segment")
            if nxt and nxt not in names:
                errors.append(f"Segment '{seg.get('name')}' points to unknown next_segment '{nxt}'")

        # Check loop closure
        last_next = segments[-1].get("next_segment")
        first_name = segments[0].get("name")
        if data.get("cycle_loop", True):
            if last_next != first_name:
                errors.append(
                    f"Loop not closed: last segment ('{segments[-1].get('name')}') "
                    f"next='{last_next}' != first ('{first_name}')"
                )

    return errors


def validate_all(cycles_dir: Path) -> bool:
    """Validate all JSON files in the cycles directory."""
    ok = True
    for f in sorted(cycles_dir.glob("*.json")):
        errs = validate_cycle(f)
        if errs:
            ok = False
            print(f"❌ {f.name}")
            for e in errs:
                print(f"   - {e}")
        else:
            print(f"✅ {f.name}")
    return ok


def list_cycles(cycles_dir: Path) -> None:
    """List all cycle files with segment counts."""
    files = sorted(cycles_dir.glob("*.json"))
    if not files:
        print("No cycle files found.")
        return
    print(f"{'File':<30} {'Remedy':<20} {'Segments':>8} {'Loop':>6}")
    print("-" * 66)
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        remedy = data.get("remedy_name", "?")
        segs = len(data.get("segments", []))
        loop = "yes" if data.get("cycle_loop") else "no"
        print(f"{f.name:<30} {remedy:<20} {segs:>8} {loop:>6}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build and validate Cycles & Segments JSON files.")
    parser.add_argument("--dir", type=Path, default=DEFAULT_CYCLES_DIR, help="Cycles directory")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--interactive", action="store_true", help="Interactive builder")
    group.add_argument("--template", type=str, metavar="NAME", help="Emit template for remedy")
    group.add_argument("--validate", type=Path, metavar="FILE", help="Validate one file")
    group.add_argument("--validate-all", action="store_true", help="Validate all files in dir")
    group.add_argument("--list", action="store_true", help="List all cycle files")
    args = parser.parse_args()

    cycles_dir: Path = args.dir
    cycles_dir.mkdir(parents=True, exist_ok=True)

    if args.interactive:
        interactive_builder(cycles_dir)
    elif args.template:
        emit_template(args.template, cycles_dir)
    elif args.validate:
        errs = validate_cycle(args.validate)
        if errs:
            print(f"❌ Validation failed for {args.validate.name}")
            for e in errs:
                print(f"   - {e}")
            sys.exit(1)
        else:
            print(f"✅ {args.validate.name} is valid.")
    elif args.validate_all:
        if not validate_all(cycles_dir):
            sys.exit(1)
        print("\nAll cycles passed validation.")
    elif args.list:
        list_cycles(cycles_dir)


if __name__ == "__main__":
    main()
