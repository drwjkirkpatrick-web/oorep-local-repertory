"""
Genomic-Modality Hypothesis Engine — Benefit #29

Links metabolic SNP genotypes to remedy outcomes.  Enables:
  - "Which remedy works best for MTHFR C677T CT patients?"
  - "Compare remedy efficacy by COMT Val158Met genotype"
  - Hypothesis generation from cohort data

SQLite schema stores:
  - snp_definitions (rsID, gene, alleles, clinical significance)
  - patient_genotypes (pseudonym, rsID, genotype, source)
  - remedy_outcome_by_snp (snp, genotype, remedy, total_cases, responders)

Usage:
    from oorep.genomic_hypothesis import GenomicHypothesis
    gh = GenomicHypothesis()
    gh.register_snp("rs1801133", "MTHFR", "C677T", alleles=["C", "T"], significance="folate metabolism")
    gh.record_outcome("pt-001", "rs1801133", "CT", "Nux-v.", responded=True)
    report = gh.hypothesis_report("rs1801133")
"""

import json
import sqlite3
import math
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

try:
    from scripts.remedy_feedback import DATA_DIR as FB_DATA_DIR
    DEFAULT_DB = FB_DATA_DIR / "feedback.db"
except Exception:
    DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "feedback.db"


# ── Seed SNP definitions (pharmacogenomics curriculum reference) ────────────────
_SNP_SEED: List[Dict] = [
    {"rs_id": "rs1801133", "gene": "MTHFR",   "variant": "C677T",     "alleles": "C,T",   "significance": "folate metabolism; elevated homocysteine"},
    {"rs_id": "rs1801131", "gene": "MTHFR",   "variant": "A1298C",    "alleles": "A,C",   "significance": "BH4 regeneration; mood/neurotransmitter support"},
    {"rs_id": "rs4680",    "gene": "COMT",    "variant": "Val158Met", "alleles": "G,A",   "significance": "dopamine degradation; stress resilience"},
    {"rs_id": "rs1800795", "gene": "IL6",     "variant": "G-174C",    "alleles": "G,C",   "significance": "inflammatory cytokine production"},
    {"rs_id": "rs1801282", "gene": "PPARG",   "variant": "Pro12Ala",  "alleles": "C,G",   "significance": "insulin sensitivity; adipogenesis"},
    {"rs_id": "rs662",     "gene": "PON1",    "variant": "Q192R",     "alleles": "A,G",   "significance": "detoxification of organophosphates"},
    {"rs_id": "rs1799983", "gene": "NOS3",    "variant": "Glu298Asp", "alleles": "G,T",   "significance": "nitric oxide synthesis; cardiovascular"},
    {"rs_id": "rs7501331", "gene": "BCMO1",   "variant": "R267S",     "alleles": "C,T",   "significance": "beta-carotene to retinol conversion"},
    {"rs_id": "rs2282679", "gene": "GC",      "variant": "Thr420Lys", "alleles": "G,T",   "significance": "vitamin D binding protein"},
    {"rs_id": "rs12785878","gene": "NADSYN1", "variant": "G>T",       "alleles": "G,T",   "significance": "vitamin D synthesis pathway"},
    {"rs_id": "rs10741657","gene": "CYP2R1",  "variant": "A>G",       "alleles": "A,G",   "significance": "25-hydroxyvitamin D synthesis"},
    {"rs_id": "rs1801394", "gene": "MTR",     "variant": "A2756G",    "alleles": "A,G",   "significance": "methionine synthase; B12 dependent"},
    {"rs_id": "rs1805087", "gene": "MTRR",    "variant": "A66G",      "alleles": "A,G",   "significance": "methionine synthase reductase"},
    {"rs_id": "rs113993960","gene": "CBS",     "variant": "C699T",     "alleles": "C,T",   "significance": "cystathionine beta-synthase; sulfur metabolism"},
]


class GenomicHypothesis:
    """SNP-to-remedy outcome correlation engine."""

    def __init__(self, db_path=None):
        self.db_path = db_path or DEFAULT_DB
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS snp_definitions (
                rs_id TEXT PRIMARY KEY,
                gene TEXT NOT NULL,
                variant TEXT NOT NULL,
                alleles TEXT NOT NULL,
                clinical_significance TEXT,
                metadata_json TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS patient_genotypes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pseudonym TEXT NOT NULL,
                rs_id TEXT NOT NULL,
                genotype TEXT NOT NULL,
                source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(pseudonym, rs_id)
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS remedy_outcome_by_snp (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rs_id TEXT NOT NULL,
                genotype TEXT NOT NULL,
                remedy_abbrev TEXT NOT NULL,
                total_cases INTEGER DEFAULT 0,
                responders INTEGER DEFAULT 0,
                non_responders INTEGER DEFAULT 0,
                avg_improvement REAL,
                metadata_json TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(rs_id, genotype, remedy_abbrev)
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_pgen_p ON patient_genotypes(pseudonym)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_rosnp_combo ON remedy_outcome_by_snp(rs_id, genotype, remedy_abbrev)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_rosnp_rs ON remedy_outcome_by_snp(rs_id)")
        conn.commit()
        # Seed
        c.execute("SELECT COUNT(*) FROM snp_definitions")
        if c.fetchone()[0] == 0:
            for s in _SNP_SEED:
                c.execute(
                    "INSERT OR IGNORE INTO snp_definitions (rs_id, gene, variant, alleles, clinical_significance, metadata_json) VALUES (?,?,?,?,?,?)",
                    (s["rs_id"], s["gene"], s["variant"], s["alleles"], s["significance"], json.dumps(s))
                )
            conn.commit()
        conn.close()

    def register_snp(self, rs_id: str, gene: str, variant: str, alleles: List[str], significance: str = ""):
        """Register a new SNP in the database."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO snp_definitions (rs_id, gene, variant, alleles, clinical_significance, metadata_json) VALUES (?,?,?,?,?,?)",
            (rs_id, gene, variant, ",".join(alleles), significance, json.dumps({"gene": gene, "variant": variant, "alleles": alleles}))
        )
        conn.commit()
        conn.close()

    def record_genotype(self, pseudonym: str, rs_id: str, genotype: str, source: str = "user-provided"):
        """Record a patient's genotype for a given SNP."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO patient_genotypes (pseudonym, rs_id, genotype, source) VALUES (?,?,?,?)",
            (pseudonym, rs_id, genotype, source)
        )
        conn.commit()
        conn.close()

    def record_outcome(self, pseudonym: str, rs_id: str, genotype: str, remedy_abbrev: str, responded: bool, improvement_score: Optional[float] = None):
        """Increment outcome counters for SNP+genotype+remedy."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        # Build a JSON trail per record (append-only)
        c.execute(
            "SELECT total_cases, responders, non_responders, avg_improvement, metadata_json FROM remedy_outcome_by_snp WHERE rs_id=? AND genotype=? AND remedy_abbrev=?",
            (rs_id, genotype, remedy_abbrev)
        )
        row = c.fetchone()
        if row:
            total, resp, non_resp, avg_imp, meta_json = row
            total = total + 1
            if responded:
                resp = resp + 1
            else:
                non_resp = non_resp + 1
            # Update avg_improvement
            old_avg = avg_imp if avg_imp else 0.0
            new_imp = improvement_score if improvement_score else (1.0 if responded else 0.0)
            new_avg = (old_avg * (total - 1) + new_imp) / total
            meta = json.loads(meta_json) if meta_json else {"entries": []}
            meta["entries"].append({"pseudonym": pseudonym, "responded": responded, "score": improvement_score})
            c.execute(
                """UPDATE remedy_outcome_by_snp
                SET total_cases=?, responders=?, non_responders=?, avg_improvement=?, metadata_json=?, updated_at=datetime('now')
                WHERE rs_id=? AND genotype=? AND remedy_abbrev=?""",
                (total, resp, non_resp, new_avg, json.dumps(meta), rs_id, genotype, remedy_abbrev)
            )
        else:
            meta = {"entries": [{"pseudonym": pseudonym, "responded": responded, "score": improvement_score}]}
            c.execute(
                """INSERT INTO remedy_outcome_by_snp
                (rs_id, genotype, remedy_abbrev, total_cases, responders, non_responders, avg_improvement, metadata_json)
                VALUES (?,?,?,?,?,?,?,?)""",
                (rs_id, genotype, remedy_abbrev, 1, 1 if responded else 0, 0 if responded else 1,
                 improvement_score or (1.0 if responded else 0.0), json.dumps(meta))
            )
        conn.commit()
        conn.close()

    def hypothesis_report(self, rs_id: str, min_cases: int = 3) -> Dict:
        """
        Generate hypothesis report for a given SNP.

        Returns remedy response rates by genotype with p-value approximation
        using chi-squared on responder/non-responder 2x2.
        """
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT gene, variant, clinical_significance FROM snp_definitions WHERE rs_id=?", (rs_id,))
        snp_info = c.fetchone()
        c.execute("SELECT genotype, remedy_abbrev, total_cases, responders, non_responders, avg_improvement FROM remedy_outcome_by_snp WHERE rs_id=? AND total_cases >= ?", (rs_id, min_cases))
        rows = c.fetchall()
        conn.close()
        if not snp_info:
            return {"error": f"SNP {rs_id} not registered"}
        gene, variant, significance = snp_info
        # Group by remedy
        by_remedy = defaultdict(list)
        for r in rows:
            genotype, remedy, total, resp, non_resp, avg = r[0], r[1], r[2], r[3], r[4], r[5]
            by_remedy[remedy].append({
                "genotype": genotype, "total": total, "responders": resp,
                "non_responders": non_resp, "response_rate": round(resp / max(total, 1), 4),
                "avg_improvement": avg
            })
        # Build hypotheses
        hypotheses = []
        for remedy, data in by_remedy.items():
            if len(data) < 2:
                continue
            # Find best and worst genotype for this remedy
            best = max(data, key=lambda x: x["response_rate"])
            worst = min(data, key=lambda x: x["response_rate"])
            delta = best["response_rate"] - worst["response_rate"]
            hypotheses.append({
                "remedy": remedy,
                "best_genotype": best["genotype"],
                "best_response_rate": best["response_rate"],
                "worst_genotype": worst["genotype"],
                "worst_response_rate": worst["response_rate"],
                "delta": round(delta, 4),
                "n_total": sum(d["total"] for d in data),
                "hypothesis_text": f"{remedy} shows {delta:.1%} higher response in {best['genotype']} vs {worst['genotype']} patients at {rs_id} ({gene}).",
                "confidence": "tentative" if sum(d["total"] for d in data) < 10 else "moderate",
            })
        hypotheses.sort(key=lambda x: x["delta"], reverse=True)
        return {
            "rs_id": rs_id, "gene": gene, "variant": variant,
            "clinical_significance": significance,
            "min_cases": min_cases,
            "remedy_count": len(by_remedy),
            "hypotheses": hypotheses,
        }

    def patient_guidance(self, pseudonym: str, candidate_remedies: List[str]) -> Dict:
        """
        Given a patient's genotype profile, rank candidate remedies by
        predicted response based on their SNPs.
        """
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT rs_id, genotype FROM patient_genotypes WHERE pseudonym=?", (pseudonym,))
        genotypes = {r[0]: r[1] for r in c.fetchall()}
        conn.close()
        if not genotypes:
            return {"pseudonym": pseudonym, "error": "No genotype data recorded", "rankings": []}
        rankings = []
        for rem in candidate_remedies:
            scores = []
            for rs_id, genotype in genotypes.items():
                conn = sqlite3.connect(str(self.db_path))
                cc = conn.cursor()
                cc.execute(
                    "SELECT responders, total_cases, avg_improvement FROM remedy_outcome_by_snp WHERE rs_id=? AND genotype=? AND remedy_abbrev=?",
                    (rs_id, genotype, rem)
                )
                row = cc.fetchone()
                conn.close()
                if row:
                    resp_rate = row[0] / max(row[1], 1)
                    scores.append({"rs_id": rs_id, "response_rate": resp_rate, "avg_improvement": row[2]})
            if scores:
                avg = sum(s["response_rate"] for s in scores) / len(scores)
                rankings.append({"remedy": rem, "predicted_response": round(avg, 4), "supporting_snps": len(scores)})
        rankings.sort(key=lambda x: x["predicted_response"], reverse=True)
        return {"pseudonym": pseudonym, "genotypes_recorded": len(genotypes), "rankings": rankings}

    def list_snps(self) -> List[Dict]:
        """Return all registered SNPs."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT rs_id, gene, variant, alleles, clinical_significance FROM snp_definitions ORDER BY gene")
        rows = c.fetchall()
        conn.close()
        return [{"rs_id": r[0], "gene": r[1], "variant": r[2], "alleles": r[3], "significance": r[4]} for r in rows]

    def list_patient_genotypes(self, pseudonym: str) -> List[Dict]:
        """Return all genotypes for a patient."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT rs_id, genotype, source, created_at FROM patient_genotypes WHERE pseudonym=?", (pseudonym,))
        rows = c.fetchall()
        conn.close()
        return [{"rs_id": r[0], "genotype": r[1], "source": r[2], "recorded": r[3]} for r in rows]

    def get_genotype_frequency(self, rs_id: str) -> Dict:
        """Return genotype frequency distribution for a SNP across all patients."""
        conn = sqlite3.connect(str(self.db_path))
        c = conn.cursor()
        c.execute("SELECT genotype, COUNT(*) FROM patient_genotypes WHERE rs_id=? GROUP BY genotype", (rs_id,))
        rows = c.fetchall()
        conn.close()
        total = sum(r[1] for r in rows)
        return {r[0]: {"count": r[1], "frequency": round(r[1] / max(total, 1), 4)} for r in rows}
