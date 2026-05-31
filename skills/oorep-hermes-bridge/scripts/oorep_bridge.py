#!/usr/bin/env python3
"""
OOREP-Hermes Bridge: Natural-language command router for homeopathic repertory.

Translates conversational requests into OOREP API calls.
Handles repertorization, remedy lookup, comparison, rare remedy surfacing,
and patient case retrieval.

Usage:
    from oorep_hermes_bridge import OOREPBridge
    bridge = OOREPBridge()
    response = bridge.handle("repertorize dry cough evening, throat pit pressing")
"""

from __future__ import annotations

import json
import re
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from collections import defaultdict

# Import OOREP from the local repository
REPO_BASE = Path.home() / "projects" / "oorep-local-repertory"
DATA_DIR = REPO_BASE / "data"
sys.path.insert(0, str(REPO_BASE))

try:
    from oorep.homeopathic_repertory import HomeopathicRepertory
    from oorep.clinical_rubric_mapper import ClinicalRubricMapper
    from oorep.rare_remedy_triangulator import RareRemedyTriangulator
    from oorep.cycles_and_segments import CyclesAndSegmentsEngine
    OOREP_AVAILABLE = True
except ImportError as e:
    OOREP_AVAILABLE = False
    OOREP_ERROR = str(e)

# Import case memory if available
_CASE_MEMORY_AVAILABLE = False
try:
    _BRIDGE_DIR = Path(__file__).resolve().parent
    if str(_BRIDGE_DIR) not in sys.path:
        sys.path.insert(0, str(_BRIDGE_DIR))
    from case_memory import CaseMemoryStore
    _CASE_MEMORY_AVAILABLE = True
except ImportError:
    pass


class OOREPBridgeError(Exception):
    """Custom exception for bridge errors."""
    pass


class OOREPBridge:
    """
    Natural-language bridge to OOREP homeopathic repertory.

    Handles commands like:
      - "repertorize [symptoms]"
      - "what remedy is [name/abbrev]?"
      - "compare [remedyA] and [remedyB]"
      - "rare remedy for [symptoms]"
      - "patient [pseudonym]" / "case [pseudonym]"
    """

    def __init__(self, data_dir: Optional[str] = None):
        if not OOREP_AVAILABLE:
            raise OOREPBridgeError(f"OOREP not available: {OOREP_ERROR}")

        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.rep = HomeopathicRepertory(str(self.data_dir))
        self.mapper = ClinicalRubricMapper(self.rep)
        self.triangulator = RareRemedyTriangulator(repertory=self.rep)
        self.cycles_engine = CyclesAndSegmentsEngine()
        self.case_memory = CaseMemoryStore() if _CASE_MEMORY_AVAILABLE else None

        # Command patterns
        self._patterns = [
            (r"(?i)^\s*rep(?:ertorize)?[:\s]+(.+)", "repertorize"),
            (r"(?i)(?:repertorize|which remedy for|what remedy matches|find remedy for)[:\s]*(.+)", "repertorize"),
            (r"(?i)^\s*compare\s+([A-Za-z\-\.\s]+)\s+(?:and|vs\.?)\s+([A-Za-z\-\.\s]+)$", "compare"),
            (r"(?i)^\s*(?:rare remedy|uncommon remedy|small remedy|find rare)(?:\s+for)?[:\s]*(.+)?$", "rare"),
            (r"(?i)^\s*(?:what is|show me|tell me about|profile for)\s+([A-Za-z\-\.\s]+?)(?:\s+profile)?$", "profile"),
            (r"(?i)^\s*(?:patient|case|prescription for)\s+([A-Za-z0-9\-_]+)$", "patient"),
            (r"(?i)^\s*(?:timeline|history)\s+(?:for\s+)?([A-Za-z0-9\-_]+)$", "timeline"),
            (r"(?i)^\s*(?:summary|overview)\s+(?:for\s+)?([A-Za-z0-9\-_]+)$", "summary"),
            (r"(?i)^\s*(?:pattern|recurring|constitutional)\s+(?:for\s+)?([A-Za-z0-9\-_]+)$", "pattern"),
            (r"(?i)^\s*(?:suppression|suppress|suppressed)\s+(?:for\s+)?([A-Za-z0-9\-_]+)$", "suppression"),
            (r"(?i)^\s*(?:search rubric|find rubric|look up rubric)[:\s]*(.+)$", "search_rubric"),
            (r"(?i)^\s*(?:what remedy is|remedy abbrev|abbreviation)\s+([A-Za-z0-9\-\.]+)[\.\?\!]*$", "abbrev_lookup"),
            (r"(?i)^\s*(?:cycle|cycles|segments)(?:\s+of)?[:\s]+([A-Za-z\-\.\s]+)$", "cycle"),
            (r"(?i)^\s*(?:match case|case match|analyze case)[:\s]*(.+)$", "match_case"),
            (r"(?i)^\s*(?:map of hierarchy|hierarchy|pediatric hierarchy)$", "hierarchy"),
        ]

    def handle(self, message: str) -> Dict[str, Any]:
        """
        Parse a natural-language message and route to the appropriate OOREP command.

        Returns a dict with:
          - type: command type
          - result: structured results
          - formatted: human-readable string (for Telegram/CLI)
        """
        message = message.strip()
        if not message:
            return {"type": "empty", "result": None, "formatted": "Please provide a homeopathic query."}

        # Try each pattern in order
        for pattern, cmd_type in self._patterns:
            match = re.match(pattern, message)
            if match:
                return self._dispatch(cmd_type, match, message)

        # Fallback: repertorize only if message looks like symptom descriptions.
        # Short messages (2-4 words) get repertorized by default.
        # Longer messages need at least one symptom keyword to avoid garbage input.
        SYMPTOM_KEYWORDS = {"cough", "fever", "pain", "headache", "thirst", "sleep",
                            "nausea", "vomit", "diarrhea", "constipation", "rash", "itch",
                            "swelling", "swollen", "sore", "ache", "burning", "cold", "hot",
                            "warm", "chill", "sweat", "perspiration", "tired", "weak",
                            "anxious", "worried", "sad", "angry", "irritable", "hoarseness",
                            "dry", "wet", "throat", "chest", "coryza", "cramps", "convulsions",
                            "delirium", "dyspnea", "eructations", "flatulence", "flatus",
                            "larynx", "mucus", "pulsation", "respiration", "stomach",
                            "suppuration", "trembling", "twitching", "vertigo", "voice",
                            "worse", "better", "morning", "evening", "night", "afternoon"}
        words = message.lower().split()
        if (len(words) >= 2 and not message.endswith("?")
                and not any(kw in message.lower() for kw in ["what", "how", "who", "when", "where",
                                                              "why", "which", "compare", "profile",
                                                              "patient", "case", "search", "rare"])):
            if len(words) <= 4 or any(w.rstrip(",.;:()[]") in SYMPTOM_KEYWORDS for w in words):
                return self._do_repertorize(message)
        return {
            "type": "unknown",
            "result": None,
            "formatted": (
                "I'm not sure how to interpret that. Try:\n"
                "• Repertorize dry cough, hoarseness\n"
                "• Compare Bromum and Hepar sulph\n"
                "• Profile for Arsenicum album\n"
                "• Rare remedy for hoarse voice, croup\n"
                "• Cycles of Stramonium\n"
                "• Match case fear of death, violent outbursts\n"
                "• Map of hierarchy\n"
                "• Patient MrsJ2024\n"
                "• Summary for MrsJ2024\n"
                "• Timeline for MrsJ2024\n"
                "• Pattern for MrsJ2024\n"
                "• Suppression for MrsJ2024"
            ),
        }

    def _dispatch(self, cmd_type: str, match, full_message: str) -> Dict[str, Any]:
        if cmd_type == "repertorize":
            symptoms_text = match.group(1).strip() if match.lastindex >= 1 else full_message
            return self._do_repertorize(symptoms_text)

        elif cmd_type == "compare":
            rem_a = match.group(1).strip()
            rem_b = match.group(2).strip()
            return self._do_compare(rem_a, rem_b)

        elif cmd_type == "rare":
            symptoms_text = match.group(1).strip() if match.lastindex >= 1 else ""
            return self._do_rare(symptoms_text)

        elif cmd_type == "profile":
            remedy_name = match.group(1).strip()
            return self._do_profile(remedy_name)

        elif cmd_type == "patient":
            pseudonym = match.group(1).strip()
            return self._do_patient(pseudonym)

        elif cmd_type == "timeline":
            pseudonym = match.group(1).strip()
            return self._do_timeline(pseudonym)

        elif cmd_type == "summary":
            pseudonym = match.group(1).strip()
            return self._do_summary(pseudonym)

        elif cmd_type == "pattern":
            pseudonym = match.group(1).strip()
            return self._do_pattern(pseudonym)

        elif cmd_type == "suppression":
            pseudonym = match.group(1).strip()
            return self._do_suppression(pseudonym)

        elif cmd_type == "search_rubric":
            query = match.group(1).strip()
            return self._do_search_rubric(query)

        elif cmd_type == "abbrev_lookup":
            abbrev = match.group(1).strip()
            return self._do_abbrev_lookup(abbrev)

        elif cmd_type == "cycle":
            remedy_name = match.group(1).strip()
            return self._do_cycle(remedy_name)

        elif cmd_type == "match_case":
            case_text = match.group(1).strip()
            return self._do_match_case(case_text)

        elif cmd_type == "hierarchy":
            return self._do_hierarchy()

        return {"type": "unknown", "result": None, "formatted": "Unrecognized command type."}

    def _do_repertorize(self, symptoms_text: str) -> Dict[str, Any]:
        """Run repertorization on comma-separated or natural symptom text."""
        # Split on commas, semicolons, or obvious conjunctions
        symptoms = [s.strip() for s in re.split(r"[,;]|\band\b|\bplus\b", symptoms_text) if s.strip()]
        if not symptoms:
            symptoms = [symptoms_text]

        results = self.rep.repertorize(
            symptoms,
            top_n=20,
            retrieval="hybrid",
            rubrics_per_symptom=10,
            use_clinical_mapper=True,
        )

        formatted = self._format_repertorization(symptoms, results)
        return {
            "type": "repertorize",
            "symptoms": symptoms,
            "result": results,
            "formatted": formatted,
        }

    def _do_compare(self, rem_a: str, rem_b: str) -> Dict[str, Any]:
        """Compare two remedies by rubric overlap."""
        # Resolve remedy IDs
        remedy_a = self._resolve_remedy(rem_a)
        remedy_b = self._resolve_remedy(rem_b)

        if remedy_a is None:
            return {"type": "compare", "error": f"Unknown remedy: {rem_a}", "formatted": f"❌ Could not find remedy: {rem_a}"}
        if remedy_b is None:
            return {"type": "compare", "error": f"Unknown remedy: {rem_b}", "formatted": f"❌ Could not find remedy: {rem_b}"}

        # Get rubrics for each
        rubrics_a = self.rep.get_rubrics_for_remedy(remedy_a["id"], limit=None)
        rubrics_b = self.rep.get_rubrics_for_remedy(remedy_b["id"], limit=None)

        a_ids = {r["rubric_id"]: r for r in rubrics_a}
        b_ids = {r["rubric_id"]: r for r in rubrics_b}

        overlap = []
        only_a = []
        only_b = []

        for rid, ra in a_ids.items():
            if rid in b_ids:
                rb = b_ids[rid]
                overlap.append({
                    "rubric_id": rid,
                    "rubric": ra["fullpath"],
                    f"{remedy_a['abbrev']}_weight": ra["weight"],
                    f"{remedy_b['abbrev']}_weight": rb["weight"],
                })
            else:
                only_a.append(ra)

        for rid, rb in b_ids.items():
            if rid not in a_ids:
                only_b.append(rb)

        # Sort overlap by combined weight
        overlap.sort(key=lambda x: x[f"{remedy_a['abbrev']}_weight"] + x[f"{remedy_b['abbrev']}_weight"], reverse=True)

        formatted = self._format_comparison(remedy_a, remedy_b, overlap, only_a, only_b)
        return {
            "type": "compare",
            "remedy_a": remedy_a,
            "remedy_b": remedy_b,
            "overlap": overlap,
            "only_a": only_a,
            "only_b": only_b,
            "formatted": formatted,
        }

    def _do_rare(self, symptoms_text: str) -> Dict[str, Any]:
        """Surface rare/small remedies for a symptom set."""
        if not symptoms_text:
            return {"type": "rare", "error": "No symptoms provided", "formatted": "Please provide symptoms for rare remedy triangulation."}

        symptoms = [s.strip() for s in re.split(r"[,;]|\band\b|\bplus\b", symptoms_text) if s.strip()]
        if not symptoms:
            symptoms = [symptoms_text]

        # Use max_total_rubrics=5000 to surface small-to-medium remedies while excluding true polychrests
        results = self.triangulator.triangulate(symptoms, top_n=15, max_total_rubrics=5000)

        formatted = self._format_rare_results(symptoms, results)
        return {
            "type": "rare",
            "symptoms": symptoms,
            "result": results,
            "formatted": formatted,
        }

    def _do_profile(self, remedy_name: str) -> Dict[str, Any]:
        """Generate full remedy profile from repertory data."""
        remedy = self._resolve_remedy(remedy_name)
        if remedy is None:
            return {"type": "profile", "error": f"Unknown remedy: {remedy_name}", "formatted": f"❌ Could not find remedy: {remedy_name}"}

        rubrics = self.rep.get_rubrics_for_remedy(remedy["id"], limit=None)

        # Group by top-level category
        chapters = defaultdict(list)
        weight3 = []
        for r in rubrics:
            fp = r.get("fullpath", "")
            top = fp.split("::")[0].strip() if "::" in fp else fp.split(" - ")[0].strip()
            chapters[top].append(r)
            if r["weight"] == 3:
                weight3.append(r)

        # Sort categories by count
        sorted_chapters = sorted(chapters.items(), key=lambda x: -len(x[1]))

        formatted = self._format_profile(remedy, sorted_chapters, weight3)
        return {
            "type": "profile",
            "remedy": remedy,
            "chapters": sorted_chapters,
            "weight3_rubrics": weight3,
            "formatted": formatted,
        }

    def _do_patient(self, pseudonym: str) -> Dict[str, Any]:
        """Retrieve patient case from memory."""
        if self.case_memory is None:
            return {
                "type": "patient",
                "error": "Case memory not available",
                "formatted": "📋 Case memory module is not loaded. Check that case_memory.py is in the skill path.",
            }

        cases = self.case_memory.get_cases_for_patient(pseudonym)
        if not cases:
            return {
                "type": "patient",
                "pseudonym": pseudonym,
                "result": [],
                "formatted": f"📋 No cases found for '{pseudonym}'. Use the prescription tracker to add cases.",
            }

        formatted = self._format_patient_cases(pseudonym, cases)
        return {
            "type": "patient",
            "pseudonym": pseudonym,
            "result": cases,
            "formatted": formatted,
        }

    def _do_timeline(self, pseudonym: str) -> Dict[str, Any]:
        """Retrieve chronological timeline for a patient."""
        if self.case_memory is None:
            return {
                "type": "timeline",
                "error": "Case memory not available",
                "formatted": "📋 Case memory module is not loaded. Check that case_memory.py is in the skill path.",
            }

        timeline = self.case_memory.get_patient_timeline(pseudonym)
        if not timeline:
            return {
                "type": "timeline",
                "pseudonym": pseudonym,
                "result": [],
                "formatted": f"📋 No timeline found for '{pseudonym}'. Add prescriptions to build a timeline.",
            }

        formatted = self._format_timeline(pseudonym, timeline)
        return {
            "type": "timeline",
            "pseudonym": pseudonym,
            "result": timeline,
            "formatted": formatted,
        }

    def _do_summary(self, pseudonym: str) -> Dict[str, Any]:
        """Retrieve high-level patient summary."""
        if self.case_memory is None:
            return {
                "type": "summary",
                "error": "Case memory not available",
                "formatted": "📋 Case memory module is not loaded.",
            }

        summary = self.case_memory.get_patient_summary(pseudonym)
        if summary.get("total_cases", 0) == 0:
            return {
                "type": "summary",
                "pseudonym": pseudonym,
                "result": summary,
                "formatted": f"📋 No cases found for '{pseudonym}'.",
            }

        formatted = self._format_patient_summary(pseudonym, summary)
        return {
            "type": "summary",
            "pseudonym": pseudonym,
            "result": summary,
            "formatted": formatted,
        }

    def _do_pattern(self, pseudonym: str) -> Dict[str, Any]:
        """Find recurring rubrics (constitutional patterns) for a patient."""
        if self.case_memory is None:
            return {
                "type": "pattern",
                "error": "Case memory not available",
                "formatted": "📋 Case memory module is not loaded.",
            }

        patterns = self.case_memory.find_recurring_rubrics(pseudonym)
        if patterns.get("total_cases", 0) == 0:
            return {
                "type": "pattern",
                "pseudonym": pseudonym,
                "result": patterns,
                "formatted": f"📋 No cases found for '{pseudonym}'.",
            }

        formatted = self._format_patterns(pseudonym, patterns)
        return {
            "type": "pattern",
            "pseudonym": pseudonym,
            "result": patterns,
            "formatted": formatted,
        }

    def _do_suppression(self, pseudonym: str) -> Dict[str, Any]:
        """Retrieve suppression history for a patient."""
        if self.case_memory is None:
            return {
                "type": "suppression",
                "error": "Case memory not available",
                "formatted": "📋 Case memory module is not loaded.",
            }

        history = self.case_memory.get_suppression_history(pseudonym)
        formatted = self._format_suppression(pseudonym, history)
        return {
            "type": "suppression",
            "pseudonym": pseudonym,
            "result": history,
            "formatted": formatted,
        }

    def _do_search_rubric(self, query: str) -> Dict[str, Any]:
        """Search for rubrics by text."""
        results = self.rep.search_rubrics_hybrid(query, limit=20)
        formatted = self._format_rubric_search(query, results)
        return {
            "type": "search_rubric",
            "query": query,
            "result": results,
            "formatted": formatted,
        }

    def _do_abbrev_lookup(self, abbrev: str) -> Dict[str, Any]:
        """Look up remedy by abbreviation."""
        abbrev = abbrev.rstrip(".").lower()
        # Try exact match first
        for r in self.rep.remedies.values():
            if r.get("abbrev", "").lower().rstrip(".") == abbrev:
                name = r.get("name", "Unknown")
                return {
                    "type": "abbrev_lookup",
                    "abbrev": r.get("abbrev"),
                    "name": name,
                    "formatted": f"💊 **{r.get('abbrev')}** → {name}",
                }

        # Try partial
        matches = self.rep.search_remedies(abbrev, limit=5)
        if matches:
            formatted = "🔍 Possible matches:\n"
            for m in matches:
                formatted += f"  • **{m['abbrev']}**: {m['name']}\n"
            return {"type": "abbrev_lookup", "query": abbrev, "result": matches, "formatted": formatted}

        return {"type": "abbrev_lookup", "error": f"Unknown: {abbrev}", "formatted": f"❌ No remedy found for '{abbrev}'"}

    def _do_cycle(self, remedy_name: str) -> Dict[str, Any]:
        """Return the Cycles & Segments description for a remedy."""
        cycle = self.cycles_engine.get_cycle(remedy_name)
        if cycle is None:
            return {
                "type": "cycle",
                "error": f"No cycle data for: {remedy_name}",
                "formatted": f"❌ No cycle/segments data found for **{remedy_name}**.",
            }
        formatted = self._format_cycle(cycle)
        return {
            "type": "cycle",
            "remedy": remedy_name,
            "result": cycle.to_dict(),
            "formatted": formatted,
        }

    def _do_match_case(self, case_text: str) -> Dict[str, Any]:
        """Match a natural-language case to all registered cycles."""
        symptoms = [s.strip() for s in re.split(r"[,;]|\band\b|\bplus\b", case_text) if s.strip()]
        suggestions = self.cycles_engine.suggest_cycles_for_case(symptoms, limit=5)
        formatted = self._format_case_match(case_text, symptoms, suggestions)
        return {
            "type": "match_case",
            "symptoms": symptoms,
            "result": [
                {"remedy": name, "coverage": cov, "match": match}
                for name, cov, match in suggestions
            ],
            "formatted": formatted,
        }

    def _do_hierarchy(self) -> Dict[str, Any]:
        """Return the Map of Hierarchy overview."""
        hierarchy = self.cycles_engine.get_map_of_hierarchy()
        formatted = self._format_hierarchy(hierarchy)
        return {
            "type": "hierarchy",
            "result": hierarchy,
            "formatted": formatted,
        }

    def _resolve_remedy(self, name: str) -> Optional[Dict]:
        """Resolve a remedy name/abbrev/alias to its full record."""
        name_clean = name.strip().lower().rstrip(".")

        # By ID
        if name_clean.isdigit():
            return self.rep.get_remedy_by_id(int(name_clean))

        # By abbreviation (exact)
        result = self.rep.get_remedy_by_abbrev(name.strip())
        if result:
            return result

        # By full name (exact)
        for m in self.rep.remedies.values():
            if m.get("name", "").lower() == name_clean:
                return m

        # By abbreviation (exact after stripping dot and case)
        for m in self.rep.remedies.values():
            if m.get("abbrev", "").lower().rstrip(".") == name_clean:
                return m

        # Partial match: the query is a prefix of the remedy name
        # (e.g. "Hepar sulph" -> "Hepar Sulphur")
        for m in self.rep.remedies.values():
            full_name = m.get("name", "").lower()
            if full_name.startswith(name_clean + " ") or name_clean.startswith(full_name.split()[0].lower() + " "):
                if name_clean in full_name or full_name in name_clean:
                    return m

        # Best partial match from search
        matches = self.rep.search_remedies(name.strip(), limit=5)
        if matches:
            return matches[0]

        return None

    # ─────────────────── Formatters ───────────────────

    def _format_repertorization(self, symptoms: List[str], results: List[Dict]) -> str:
        lines = [
            f"🔬 **Repertorization** ({len(symptoms)} symptom{'s' if len(symptoms) > 1 else ''})",
            f"   {'; '.join(symptoms)}",
            "",
            "Top remedies (classical grade scoring):",
            "",
        ]
        for i, r in enumerate(results[:10], 1):
            lines.append(f"{i:2d}. **{r['abbrev']}** ({r['name']}) — Score: {r['score']} | Rubrics: {r['match_count']}")
            # Show top 3 rubrics
            for m in r.get("matches", [])[:3]:
                lines.append(f"      └─ {m.get('rubric', 'N/A')} [weight {m.get('weight', 1)}]")

        if len(results) > 10:
            lines.append(f"\n...and {len(results) - 10} more remedies.")

        lines.append("\n⚠️ *Requires practitioner review before prescription.*")
        return "\n".join(lines)

    def _format_comparison(self, rem_a: Dict, rem_b: Dict, overlap: List[Dict], only_a: List[Dict], only_b: List[Dict]) -> str:
        lines = [
            f"⚖️ **Remedy Comparison: {rem_a['abbrev']} vs. {rem_b['abbrev']}**",
            f"",
            f"| Feature | {rem_a['abbrev']} | {rem_b['abbrev']} |",
            f"|---------|{'-'*len(rem_a['abbrev'])}|{'-'*len(rem_b['abbrev'])}|",
            f"| Full name | {rem_a['name']} | {rem_b['name']} |",
            f"| Total rubrics | {len(only_a) + len(overlap)} | {len(only_b) + len(overlap)} |",
            f"| Shared rubrics | {len(overlap)} | {len(overlap)} |",
            f"",
            f"**Top Shared Rubrics (by combined weight):**",
        ]
        for o in overlap[:10]:
            w_a = o.get(f"{rem_a['abbrev']}_weight", 1)
            w_b = o.get(f"{rem_b['abbrev']}_weight", 1)
            lines.append(f"  • {o['rubric']} [{rem_a['abbrev']}: {w_a}, {rem_b['abbrev']}: {w_b}]")

        lines.append(f"\n**Unique to {rem_a['abbrev']} ({len(only_a)} rubrics):**")
        for o in sorted(only_a, key=lambda x: -x["weight"])[:5]:
            lines.append(f"  [{o['weight']}] {o['fullpath']}")

        lines.append(f"\n**Unique to {rem_b['abbrev']} ({len(only_b)} rubrics):**")
        for o in sorted(only_b, key=lambda x: -x["weight"])[:5]:
            lines.append(f"  [{o['weight']}] {o['fullpath']}")

        return "\n".join(lines)

    def _format_rare_results(self, symptoms: List[str], results: List) -> str:
        lines = [
            f"🌿 **Rare Remedy Triangulation** ({len(symptoms)} symptoms)",
            f"   {'; '.join(symptoms)}",
            "",
            "Top rare/small remedy candidates:",
            "",
        ]
        for i, r in enumerate(results[:15], 1):
            lines.append(
                f"{i:2d}. **{r.remedy_abbrev}** ({r.remedy_name})"
                f" — Rarity: {r.rarity_quotient:.3f} | Specificity: {r.specificity_score:.3f}"
                f" | Matching rubrics: {r.matching_rubrics}/{r.total_rubrics}"
            )
            # Supporting rubrics
            for sr in r.supporting_rubrics[:3]:
                rubric_display = sr.get('fullpath') or sr.get('rubric', 'N/A')
                lines.append(f"      └─ {rubric_display} [weight {sr.get('weight', 1)}]")

        lines.append("\n💡 These are *small* or *rare* remedies — verify materia medica before use.")
        return "\n".join(lines)

    def _format_profile(self, remedy: Dict, chapters: List, weight3: List[Dict]) -> str:
        lines = [
            f"💊 **Remedy Profile: {remedy['name']}** ({remedy.get('abbrev', 'N/A')})",
            f"   ID: {remedy['id']} | Alternative names: {remedy.get('alt_names', 'None')}",
            "",
            f"**Affinity Areas** (by rubric count):",
        ]
        for chapter, rubrics in chapters[:15]:
            w3_count = sum(1 for r in rubrics if r["weight"] == 3)
            lines.append(f"  {len(rubrics):4d} rubrics | W3={w3_count:3d} | {chapter}")

        lines.append(f"\n**Characteristic Weight-3 Rubrics ({len(weight3)} total):**")
        # Show all weight-3 rubrics sorted by system
        for r in sorted(weight3, key=lambda x: x.get("fullpath", ""))[:25]:
            lines.append(f"  [{r['weight']}] {r.get('fullpath', 'N/A')}")

        if len(weight3) > 25:
            lines.append(f"  ...and {len(weight3) - 25} more weight-3 rubrics.")

        return "\n".join(lines)

    def _format_patient_cases(self, pseudonym: str, cases: List[Dict]) -> str:
        lines = [f"📋 **Patient: {pseudonym}**", "", f"Cases: {len(cases)}"]
        for c in sorted(cases, key=lambda x: x.get("date", ""), reverse=True):
            lines.append(
                f"\n📅 {c.get('date', 'Unknown')} | {c.get('remedy', 'N/A')} {c.get('potency', '')}"
            )
            lines.append(f"   Status: {c.get('status', 'Unknown')}")
            lines.append(f"   Outcome: {c.get('outcome', 'Pending')}")
            if c.get("notes"):
                lines.append(f"   Notes: {c['notes'][:100]}")
        return "\n".join(lines)

    def _format_timeline(self, pseudonym: str, timeline: List[Dict]) -> str:
        lines = [f"📅 **Patient Timeline: {pseudonym}**", f"Events: {len(timeline)}", ""]
        for e in timeline:
            emoji = {"prescription": "💊", "followup": "🔄", "outcome": "🏁"}.get(e.get("type"), "•")
            date_str = e.get("date", "Unknown")
            lines.append(f"{emoji} {date_str} — {e.get('description', '')}")
            # Add minimal data preview
            data = e.get("data", {})
            if e["type"] == "prescription" and data.get("rubric_ids"):
                lines.append(f"    └─ {len(data['rubric_ids'])} rubrics | status: {data.get('status')}")
            elif e["type"] == "followup" and data.get("note"):
                lines.append(f"    └─ {data['note'][:60]}")
        return "\n".join(lines)

    def _format_patient_summary(self, pseudonym: str, summary: Dict) -> str:
        lines = [
            f"📊 **Patient Summary: {pseudonym}**",
            "",
            f"**Cases**: {summary['total_cases']} total",
            f"  ├─ Active: {summary['active']}",
            f"  ├─ Pending review: {summary['pending_review']}",
            f"  └─ Completed: {summary['completed']}",
        ]
        if summary.get("outcome_distribution"):
            lines.append(f"\n**Outcome Distribution**:")
            for outcome, count in summary["outcome_distribution"].items():
                lines.append(f"  {outcome}: {count}")
        if summary.get("most_common_remedies"):
            lines.append(f"\n**Frequent Remedies**:")
            for r in summary["most_common_remedies"][:5]:
                lines.append(f"  • {r['remedy']} — {r['count']} case(s)")
        if summary.get("constitutional_signal"):
            lines.append(f"\n🧬 *Constitutional pattern detected — recurring rubrics across cases.*")
        lines.append(f"\nFirst visit: {summary['first_visit'] or 'N/A'}")
        lines.append(f"Latest visit: {summary['latest_visit'] or 'N/A'}")
        return "\n".join(lines)

    def _format_patterns(self, pseudonym: str, patterns: Dict) -> str:
        lines = [
            f"🧬 **Constitutional Analysis: {pseudonym}**",
            f"Total cases: {patterns['total_cases']}",
            "",
        ]
        recurring = patterns.get("recurring_rubrics", [])
        if recurring:
            lines.append("**Recurring Rubrics** (appear in ≥30% of cases):")
            for r in recurring[:15]:
                lines.append(f"  • {r['rubric']} — {r['count']}/{patterns['total_cases']} ({r['percentage']}%)")
        else:
            lines.append("No strong recurring rubric patterns yet. More cases may reveal constitutional themes.")

        remedies = patterns.get("recurring_remedies", [])
        if remedies:
            lines.append(f"\n**Returning Remedies**:")
            for r in remedies:
                lines.append(f"  • {r['remedy']} — {r['count']} case(s)")
        return "\n".join(lines)

    def _format_suppression(self, pseudonym: str, history: List[Dict]) -> str:
        lines = [f"🚫 **Suppression History: {pseudonym}**", ""]
        if not history:
            lines.append("No recorded suppression events for this patient.")
            return "\n".join(lines)
        for e in history:
            lines.append(f"📅 {e.get('date', 'Unknown')} | {e.get('type', 'Unknown')}")
            lines.append(f"   Substance: {e.get('substance', 'N/A')}")
            if e.get("suppressed_symptoms"):
                lines.append(f"   Suppressed symptoms: {', '.join(e['suppressed_symptoms'])}")
            if e.get("notes"):
                lines.append(f"   Notes: {e['notes']}")
        return "\n".join(lines)

    def _format_rubric_search(self, query: str, results: List[Dict]) -> str:
        lines = [f"🔍 **Rubric Search**: \"{query}\"", "", f"Found {len(results)} matching rubrics:", ""]
        for i, r in enumerate(results[:15], 1):
            score = r.get("_hybrid_score", r.get("_match_score", 0))
            src = r.get("source", "unknown")
            lines.append(f"{i:2d}. [{src}] {r.get('fullpath', 'N/A')} (score: {score:.3f})")
        return "\n".join(lines)

    def _format_cycle(self, cycle) -> str:
        lines = [
            f"🔄 **Cycles & Segments: {cycle.remedy_name}** ({cycle.remedy_abbrev})",
            "",
            f"*One-sentence essence:*",
            f"  {cycle.sentence}",
            "",
        ]
        if cycle.map_of_hierarchy_phase:
            lines.append(f"*Map of Hierarchy — Phase {cycle.map_of_hierarchy_phase}*")
            lines.append("")
        lines.append("*Cycle segments:*")
        for seg in cycle.segments:
            arrow = f" → {seg.next_segment}" if seg.next_segment else ""
            lines.append(f"  • **{seg.name}**{arrow}")
            if seg.description:
                lines.append(f"    {seg.description}")
            if seg.symptoms:
                lines.append(f"    Symptoms: {', '.join(seg.symptoms[:5])}")
            lines.append("")
        if cycle.references:
            lines.append("*References:*")
            for ref in cycle.references:
                lines.append(f"  • {ref}")
        return "\n".join(lines)

    def _format_case_match(self, case_text: str, symptoms: List[str], suggestions) -> str:
        lines = [
            f"🧩 **Case-to-Cycle Match**",
            f"Symptoms: {', '.join(symptoms)}",
            "",
            "Top matching cycles:",
        ]
        for i, (name, coverage, match) in enumerate(suggestions[:5], 1):
            lines.append(f"{i}. **{name}** — coverage: {coverage:.1%}")
            if match.get("matched_segments"):
                lines.append(f"   Matched: {', '.join(match['matched_segments'])}")
            if match.get("missing_segments"):
                lines.append(f"   Missing: {', '.join(match['missing_segments'])}")
            lines.append("")
        return "\n".join(lines)

    def _format_hierarchy(self, hierarchy: Dict[int, List[str]]) -> str:
        lines = [
            "🏛️ **Map of Hierarchy** (Pediatric Behavioral Remedies)",
            "After Herscu & Rothenberg, NESH.",
            "",
        ]
        phase_names = {
            1: "Phase 1 — Polychrests",
            2: "Phase 2 — Nosodes",
            3: "Phase 3 — Transition Remedies (conscious ↔ unconscious doorway)",
            4: "Phase 4 — Deep Pathology (uncontrolled passions / increasing dullness)",
        }
        for phase in sorted(hierarchy.keys()):
            title = phase_names.get(phase, f"Phase {phase}")
            lines.append(f"**{title}**")
            for r in hierarchy[phase]:
                lines.append(f"  • {r}")
            lines.append("")
        return "\n".join(lines)


def quick_handle(message: str) -> str:
    """One-shot: parse message and return formatted string."""
    bridge = OOREPBridge()
    result = bridge.handle(message)
    return result.get("formatted", "No result.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        msg = " ".join(sys.argv[1:])
    else:
        msg = "Repertorize dry cough evening, throat pit pressing"
    print(quick_handle(msg))
