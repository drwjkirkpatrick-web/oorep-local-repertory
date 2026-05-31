#!/usr/bin/env python3
"""
Auto Cycle Builder — Repertory-Derived Cycles & Segments for OOREP.

Generates cycle JSON files for remedies by analyzing their rubric profiles.
Uses a heuristic segmentation of the remedy's rubrics into a directed cycle
that approximates the Herscu method. Output is compatible with the existing
CyclesAndSegmentsEngine auto-loader (data/cycles/*.json).

Methodology:
1. Collect all rubrics for the remedy (with weights).
2. Group by top-level repertory chapter (Mind, Generalities, Head, etc.).
3. Identify the 4-6 most dominant chapters by weighted rubric count.
4. Map each chapter to a cycle segment using a thematic template.
5. Sample actual rubric text as symptoms.
6. Derive Boenninghausen-style generalizations from symptom keywords.
7. Compose a one-sentence essence from the top 3 themes.
8. Emit validated JSON with closed-loop transitions.

Attribution: These are *repertory-derived approximations* of remedy cycles,
NOT verified against Herscu's published work. Marked as "OOREP auto-derived"
in references for transparency. They are intended as a working scaffold that
can be refined by clinical review or replaced with authoritative cycles
when available.

Usage:
    python auto_cycle_builder.py --batch 0 50      # remedies 0-49
    python auto_cycle_builder.py --batch 50 100
    python auto_cycle_builder.py --remedy "Sulphur" # single remedy
    python auto_cycle_builder.py --all             # all 1000 (slow)
    python auto_cycle_builder.py --validate        # validate all generated
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ── Paths ────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
CYCLES_DIR = REPO_ROOT / "data" / "cycles"
TOP_1000_PATH = DATA_DIR / "top_1000_remedies.json"

# Ensure we can import the OOREP repertory module
sys.path.insert(0, str(REPO_ROOT))

from oorep.homeopathic_repertory import HomeopathicRepertory  # noqa: E402

# ── Segment name templates ───────────────────────────────────────────────────
# Maps repertory chapter keywords to cycle segment archetypes.
CHAPTER_TO_SEGMENT = {
    # English
    "mind": ("Core mental state / inner conflict", "The mental-emotional kernel of the remedy — its characteristic consciousness pattern."),
    "head": ("Cephalic disturbance", "Symptoms localized to the head — pain, confusion, pressure, heat."),
    "eye": ("Visual and ocular strain", "Eye symptoms, vision changes, periorbital conditions."),
    "ear": ("Auditory disturbance", "Hearing changes, ear pain, tinnitus, otitis."),
    "nose": ("Nasal and olfactory state", "Coryza, obstruction, sneezing, smell changes."),
    "face": ("Facial expression and symptoms", "Facial color, eruptions, neuralgia, appearance."),
    "mouth": ("Oral disturbance", "Taste, saliva, tongue, ulcers, bleeding gums."),
    "throat": ("Pharyngeal reaction", "Sore throat, hoarseness, swallowing, larynx."),
    "external throat": ("External throat state", "External throat symptoms, glands, cervical region."),
    "stomach": ("Gastric center", "Nausea, appetite, thirst, vomiting, stomach pain."),
    "abdomen": ("Abdominal state", "Pain, bloating, liver, flatulence, hernia."),
    "rectum": ("Rectal and anal expression", "Diarrhea, constipation, hemorrhoids, urging."),
    "stool": ("Stool pattern", "Stool character, consistency, color, urging."),
    "urinary": ("Urinary function", "Kidney, bladder, urine character, retention."),
    "urine": ("Urine character", "Urine color, quantity, sediment, odor."),
    "bladder": ("Bladder state", "Bladder symptoms, retention, pain, incontinence."),
    "kidneys": ("Renal function", "Kidney pain, stones, suppression, albuminuria."),
    "genitalia": ("Genital and sexual state", "Libido, eruptions, menses, discharges."),
    "genitalia female": ("Female genital state", "Menses, leucorrhea, pregnancy, uterine symptoms."),
    "genitalia male": ("Male genital state", "Erections, emissions, prostate, testicular symptoms."),
    "respiration": ("Respiratory rhythm", "Dyspnea, cough, asthma, suffocation."),
    "cough": ("Cough pattern", "Cough character, time, aggravation, expectation."),
    "expectoration": ("Expectoration state", "Mucus color, consistency, quantity, taste."),
    "chest": ("Thoracic condition", "Heart, lungs, oppression, palpitation, pain."),
    "heart & circulation": ("Cardiac rhythm", "Palpitation, angina, pulse, hypertension."),
    "back": ("Spinal and dorsal strain", "Back pain, curvature, coccyx, weakness."),
    "extremities": ("Limb expression", "Pain, paralysis, cramps, varices, nails."),
    "sleep": ("Sleep and dream pattern", "Insomnia, position, dreams, unrefreshing sleep."),
    "skin": ("Cutaneous manifestation", "Eruptions, itching, discoloration, ulcers."),
    "fever": ("Febrile dynamic", "Chill, heat, sweat, stages, periodicity."),
    "chill": ("Chill pattern", "Chill stages, time, character, shaking."),
    "perspiration": ("Perspiration state", "Sweat character, time, odor, staining."),
    "generalities": ("Constitutional vulnerability", "General sensations, food modalities, concomitants."),
    "food": ("Nutritional reaction", "Desires, aversions, aggravation from specific foods."),
    "blood": ("Blood state", "Hemorrhage, anemia, coagulation, circulation."),
    "teeth": ("Dental state", "Toothache, caries, grinding, dentition."),
    "vision": ("Visual function", "Vision changes, blindness, diplopia, colors."),
    "hearing": ("Auditory function", "Hearing loss, noises, sensitivity, deafness."),
    "vertigo": ("Vertiginous state", "Dizziness, falling, turning, nausea with vertigo."),
    "allgemeines": ("Constitutional vulnerability", "General sensations, food modalities, concomitants."),
    "appetite": ("Appetite state", "Appetite changes, cravings, aversions."),
    "atmung": ("Respiratory rhythm", "Dyspnea, cough, asthma, suffocation."),
    "auge": ("Visual and ocular strain", "Eye symptoms, vision changes, periorbital conditions."),
    "auswurf": ("Expectoration state", "Mucus color, consistency, quantity, taste."),
    "bauch": ("Abdominal state", "Pain, bloating, liver, flatulence, hernia."),
    "blase": ("Bladder state", "Bladder symptoms, retention, pain, incontinence."),
    "brust": ("Thoracic condition", "Heart, lungs, oppression, palpitation, pain."),
    "fieber": ("Febrile dynamic", "Chill, heat, sweat, stages, periodicity."),
    "frost": ("Chill pattern", "Chill stages, time, character, shaking."),
    "gehör": ("Auditory disturbance", "Hearing changes, ear pain, tinnitus, otitis."),
    "gemüt": ("Core mental state / inner conflict", "The mental-emotional kernel of the remedy — its characteristic consciousness pattern."),
    "geschlechtsorgane männlich": ("Male genital state", "Erections, emissions, prostate, testicular symptoms."),
    "geschlechtsorgane weiblich": ("Female genital state", "Menses, leucorrhea, pregnancy, uterine symptoms."),
    "gesicht": ("Facial expression and symptoms", "Facial color, eruptions, neuralgia, appearance."),
    "hals": ("Pharyngeal reaction", "Sore throat, hoarseness, swallowing, larynx."),
    "hals-außenseite": ("External throat state", "External throat symptoms, glands, cervical region."),
    "harnröhre": ("Urethral state", "Urethral discharge, pain, burning during urination."),
    "haut": ("Cutaneous manifestation", "Eruptions, itching, discoloration, ulcers."),
    "husten": ("Cough pattern", "Cough character, time, aggravation, expectation."),
    "kehlkopf und luftröhre": ("Laryngeal state", "Larynx, trachea, croup, hoarseness."),
    "kopf": ("Cephalic disturbance", "Symptoms localized to the head — pain, confusion, pressure, heat."),
    "larynx and trachea": ("Laryngeal state", "Larynx, trachea, croup, hoarseness."),
    "magen": ("Gastric center", "Nausea, appetite, thirst, vomiting, stomach pain."),
    "mastdarm": ("Rectal and anal expression", "Diarrhea, constipation, hemorrhoids, urging."),
    "mund": ("Oral disturbance", "Taste, saliva, tongue, ulcers, bleeding gums."),
    "nase": ("Nasal and olfactory state", "Coryza, obstruction, sneezing, smell changes."),
    "nieren": ("Renal function", "Kidney pain, stones, suppression, albuminuria."),
    "ohr": ("Auditory disturbance", "Hearing changes, ear pain, tinnitus, otitis."),
    "prostata": ("Prostatic state", "Prostate symptoms, urination difficulty, discharge."),
    "prostate gland": ("Prostatic state", "Prostate symptoms, urination difficulty, discharge."),
    "rücken": ("Spinal and dorsal strain", "Back pain, curvature, coccyx, weakness."),
    "schlaf": ("Sleep and dream pattern", "Insomnia, position, dreams, unrefreshing sleep."),
    "schweiß": ("Perspiration state", "Sweat character, time, odor, staining."),
    "schwindel": ("Vertiginous state", "Dizziness, falling, turning, nausea with vertigo."),
    "sehen": ("Visual function", "Vision changes, blindness, diplopia, colors."),
    "stuhl": ("Stool pattern", "Stool character, consistency, color, urging."),
    "urethra": ("Urethral state", "Urethral discharge, pain, burning during urination."),
    "urin": ("Urine character", "Urine color, quantity, sediment, odor."),
    "zähne": ("Dental state", "Toothache, caries, grinding, dentition."),
    "clinical": ("Clinical condition", "Disease names, pathology, clinical presentations."),
}

# Mental sub-themes for finer MIND segmentation
MIND_KEYWORDS = {
    "fear": ["fear", "terrified", "dread", "anxious", "apprehension", "panic", "fright", "scared"],
    "anger": ["anger", "rage", "irritable", "violent", "fury", "quarrelsome", "cursing", "malicious"],
    "sadness": ["sad", "weeping", "grief", "depression", "melancholy", "discontented", "disappointed"],
    "confusion": ["confusion", "forgetful", "dull", "stupid", "idiotic", "imbecility", "mistakes"],
    "mania": ["mania", "delirium", "insanity", "madness", "excitement", "ecstasy", "religious"],
    "withdrawal": ["indifference", " apathy", "aversion", "sits", "silent", "reserved", "timid"],
}


def get_rubrics_for_remedy(rep: HomeopathicRepertory, remedy_id: int) -> List[Dict]:
    """Return all rubric entries for a remedy with full paths and weights via the repertory API."""
    return rep.get_rubrics_for_remedy(remedy_id, limit=None)


def parse_chapter(fullpath: str) -> str:
    """Extract top-level chapter from a rubric fullpath."""
    # Fullpaths are like "Extremities, coldness" or "Head, congestion, vertex"
    # The first comma-delimited part is the chapter
    if "," in fullpath:
        chapter = fullpath.split(",")[0].strip().lower()
    elif "::" in fullpath:
        chapter = fullpath.split("::")[0].strip().lower()
    elif " - " in fullpath:
        chapter = fullpath.split(" - ")[0].strip().lower()
    else:
        chapter = fullpath.split()[0].strip().lower() if fullpath else "unknown"
    # Clean trailing comma artifacts
    chapter = chapter.rstrip(",")
    return chapter


def score_chapters(rubric_entries: List[Dict]) -> List[Tuple[str, float]]:
    """Return chapters sorted by weighted rubric count."""
    scores = Counter()
    for e in rubric_entries:
        chapter = parse_chapter(e["fullpath"])
        scores[chapter] += e.get("weight", 1)
    return scores.most_common()


def mind_subtheme(rubric_entries: List[Dict]) -> str:
    """Determine the dominant mental sub-theme from MIND rubrics."""
    mind_text = " ".join(
        (e.get("fullpath", "") + " " + e.get("text", "")).lower()
        for e in rubric_entries
        if parse_chapter(e.get("fullpath", "")) == "mind"
    )
    if not mind_text:
        return "mental dullness"

    scores = {}
    for theme, keywords in MIND_KEYWORDS.items():
        scores[theme] = sum(mind_text.count(kw) for kw in keywords)

    best = max(scores, key=scores.get) if scores else None
    return best if best and scores[best] > 0 else "mental disturbance"


def sample_symptoms(rubric_entries: List[Dict], chapter: str, limit: int = 8) -> List[str]:
    """Sample actual rubric texts as symptoms for a chapter."""
    matches = [e for e in rubric_entries if parse_chapter(e.get("fullpath", "")) == chapter]
    # Prefer weight 3, then weight 2, then weight 1
    matches.sort(key=lambda e: -e.get("weight", 1))
    out = []
    seen = set()
    for e in matches[:limit * 2]:
        text = e.get("text", "").strip()
        if not text:
            # Use the fullpath as the rubric text
            text = e.get("fullpath", "")
        # Skip bare chapter names (no comma and short — e.g. just "Extremities")
        if "," not in text and len(text) < 25:
            continue
        # Clean and dedupe
        clean = text.lower().strip(",.;:")
        if clean not in seen and 3 < len(text) < 120:
            seen.add(clean)
            out.append(text)
        if len(out) >= limit:
            break
    return out


def derive_generalizations(symptoms: List[str]) -> List[str]:
    """Derive Boenninghausen-style generalizations from symptom keywords."""
    # Simple keyword extraction
    all_text = " ".join(symptoms).lower()
    words = re.findall(r"[a-z]{4,}", all_text)
    stopwords = {"from", "with", "without", "better", "worse", "morning", "evening", "night", "pain", "sensation"}
    freq = Counter(w for w in words if w not in stopwords)
    return [w for w, _ in freq.most_common(5)]


def compose_essence(top_chapters: List[Tuple[str, float]], remedy_name: str) -> str:
    """Compose a one-sentence essence from the top 3 chapter themes."""
    if len(top_chapters) >= 3:
        c1, c2, c3 = top_chapters[0][0], top_chapters[1][0], top_chapters[2][0]
    elif len(top_chapters) == 2:
        c1, c2, c3 = top_chapters[0][0], top_chapters[1][0], "general disturbance"
    else:
        c1 = top_chapters[0][0] if top_chapters else "general"
        c2, c3 = "constitutional", "general"

    # Make them sound more clinical
    c1 = c1.replace("generalities", "constitutional vulnerability").replace("extremities", "limb expression")
    c2 = c2.replace("generalities", "general state").replace("extremities", "limb disturbance")
    c3 = c3.replace("generalities", "general condition").replace("extremities", "limb symptoms")

    sentence = (
        f"Driven by {c1}, {remedy_name} manifests a dynamic cycle through "
        f"{c2} and {c3}, looping back to its constitutional core."
    )
    return sentence


def build_cycle_for_remedy(
    rep: HomeopathicRepertory,
    remedy: Dict,
) -> Optional[Dict[str, Any]]:
    """Build a cycle dict for a single remedy. Returns None if insufficient rubrics."""
    rid = remedy["id"]
    name = remedy.get("name", "")
    abbrev = remedy.get("abbrev", "")

    entries = get_rubrics_for_remedy(rep, rid)
    if len(entries) < 5:
        return None

    top_chapters = score_chapters(entries)

    # Select 4-6 segments from top chapters
    num_segments = min(6, max(4, len(top_chapters)))
    selected = top_chapters[:num_segments]

    # If MIND is present, use the sub-theme for the first segment
    has_mind = any(ch == "mind" for ch, _ in selected)
    segments = []

    for i, (chapter, score) in enumerate(selected):
        # Get segment template
        seg_name, seg_desc_template = CHAPTER_TO_SEGMENT.get(
            chapter, (f"{chapter.title()} state", f"Characteristic {chapter} symptoms.")
        )

        # Refine MIND segment
        if chapter == "mind":
            subtheme = mind_subtheme(entries)
            seg_name = f"Mental {subtheme}"
            seg_desc = f"The remedy's dominant mental pattern: {subtheme}. {seg_desc_template}"
        else:
            seg_desc = seg_desc_template

        symptoms = sample_symptoms(entries, chapter, limit=8)
        if not symptoms:
            symptoms = [f"{chapter} symptoms characteristic of {name}"]

        generalizations = derive_generalizations(symptoms)
        if not generalizations:
            generalizations = [chapter]

        # Next segment: the next one in selected list, or first to close loop
        if i < len(selected) - 1:
            next_ch = selected[i + 1][0]
            next_name, _ = CHAPTER_TO_SEGMENT.get(next_ch, (next_ch.title(), ""))
            if next_ch == "mind":
                next_name = f"Mental {mind_subtheme(entries)}"
        else:
            # Loop back to first
            first_ch = selected[0][0]
            next_name, _ = CHAPTER_TO_SEGMENT.get(first_ch, (first_ch.title(), ""))
            if first_ch == "mind":
                next_name = f"Mental {mind_subtheme(entries)}"

        segments.append({
            "name": seg_name,
            "description": seg_desc,
            "symptoms": symptoms,
            "generalizations": generalizations,
            "next_segment": next_name,
        })

    # Compose essence
    essence = compose_essence(selected, name)

    cycle = {
        "remedy_name": name,
        "remedy_abbrev": abbrev,
        "sentence": essence,
        "cycle_loop": True,
        "map_of_hierarchy_phase": None,  # Auto-derived cycles don't claim hierarchy
        "references": [
            "OOREP auto-derived cycle. Segments generated from repertory rubric analysis.",
            "NOT verified against Herscu published cycles. Intended as working scaffold.",
        ],
        "segments": segments,
    }
    return cycle


def save_cycle(cycle: Dict[str, Any], cycles_dir: Path) -> Path:
    """Save cycle to JSON file."""
    filename = cycles_dir / f"{cycle['remedy_name'].lower().replace(' ', '_')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(cycle, f, indent=2, ensure_ascii=False)
    return filename


def validate_cycle_file(path: Path) -> List[str]:
    """Validate a cycle JSON. Returns list of error strings."""
    errors = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]

    for key in ("remedy_name", "remedy_abbrev", "sentence", "segments"):
        if key not in data:
            errors.append(f"Missing key: {key}")

    segments = data.get("segments", [])
    if len(segments) < 2:
        errors.append(f"Need ≥2 segments, found {len(segments)}")

    names = [s.get("name", "") for s in segments]
    if len(set(names)) != len(names):
        errors.append("Duplicate segment names")

    for seg in segments:
        nxt = seg.get("next_segment")
        if nxt and nxt not in names:
            errors.append(f"'{seg.get('name')}' → unknown '{nxt}'")

    if data.get("cycle_loop", True) and len(segments) >= 2:
        last_next = segments[-1].get("next_segment")
        first_name = segments[0].get("name")
        if last_next != first_name:
            errors.append(f"Loop broken: last→'{last_next}' != first→'{first_name}'")

    return errors


def batch_build(start: int, end: int, dry_run: bool = False) -> Tuple[int, int]:
    """Build cycles for remedies[start:end] from top-1000 list. Returns (built, skipped)."""
    with open(TOP_1000_PATH, "r", encoding="utf-8") as f:
        top_1000 = json.load(f)

    rep = HomeopathicRepertory(str(DATA_DIR))
    remedies_list = rep.remedies
    remedies_map = {r["id"]: r for rid, r in remedies_list.items()}

    CYCLES_DIR.mkdir(parents=True, exist_ok=True)

    built = 0
    skipped = 0
    for i, stat in enumerate(top_1000[start:end], start=start):
        rid = stat["id"]
        remedy = remedies_map.get(rid)
        if not remedy:
            skipped += 1
            continue

        # Skip if already exists
        filename = CYCLES_DIR / f"{remedy['name'].lower().replace(' ', '_')}.json"
        if filename.exists():
            skipped += 1
            continue

        cycle = build_cycle_for_remedy(rep, remedy)
        if cycle is None:
            print(f"  [{i:4d}] SKIP {remedy['name']} — insufficient rubrics")
            skipped += 1
            continue

        if not dry_run:
            save_cycle(cycle, CYCLES_DIR)
            # Validate immediately
            errs = validate_cycle_file(filename)
            if errs:
                print(f"  [{i:4d}] WARN {remedy['name']}: {errs}")
            else:
                print(f"  [{i:4d}] OK   {remedy['name']} ({len(cycle['segments'])} segments)")
        else:
            print(f"  [{i:4d}] DRY  {remedy['name']} ({len(cycle['segments'])} segments)")

        built += 1

    return built, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-build Cycles & Segments from repertory rubrics.")
    parser.add_argument("--batch", nargs=2, type=int, metavar=("START", "END"), help="Build batch range")
    parser.add_argument("--remedy", type=str, help="Build single remedy by name")
    parser.add_argument("--all", action="store_true", help="Build all 1000 (use with care)")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't write")
    parser.add_argument("--validate", action="store_true", help="Validate all JSON in data/cycles")
    parser.add_argument("--list-built", action="store_true", help="List existing + remaining")
    args = parser.parse_args()

    if args.validate:
        ok = True
        for f in sorted(CYCLES_DIR.glob("*.json")):
            errs = validate_cycle_file(f)
            if errs:
                ok = False
                print(f"❌ {f.name}: {errs}")
            else:
                print(f"✅ {f.name}")
        if ok:
            print("\nAll cycles passed validation.")
        return

    if args.list_built:
        with open(TOP_1000_PATH, "r", encoding="utf-8") as f:
            top_1000 = json.load(f)
        existing = {f.stem for f in CYCLES_DIR.glob("*.json")}
        print(f"Existing: {len(existing)} | Remaining: {1000 - len(existing)}")
        for i, stat in enumerate(top_1000):
            slug = stat["name"].lower().replace(" ", "_")
            status = "✅" if slug in existing else "⬜"
            print(f"{status} {i+1:4d}. {stat['name']}")
        return

    if args.remedy:
        rep = HomeopathicRepertory(str(DATA_DIR))
        for rid, r in rep.remedies.items():
            if r["name"].lower() == args.remedy.lower():
                cycle = build_cycle_for_remedy(rep, r)
                if cycle:
                    print(json.dumps(cycle, indent=2, ensure_ascii=False))
                else:
                    print("Insufficient rubrics.")
                return
        print(f"Remedy '{args.remedy}' not found.")
        return

    if args.batch:
        start, end = args.batch
        print(f"Building batch {start}–{end} ...")
        built, skipped = batch_build(start, end, dry_run=args.dry_run)
        print(f"\nDone: {built} built, {skipped} skipped")
        return

    if args.all:
        print("Building all 1000 remedies...")
        built, skipped = batch_build(0, 1000, dry_run=args.dry_run)
        print(f"\nDone: {built} built, {skipped} skipped")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
