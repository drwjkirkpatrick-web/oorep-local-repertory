#!/usr/bin/env python3
"""
Local vector search for OOREP rubrics (offline, no cloud).

Approach:
- Tokenize rubric fullpath text.
- Encode into fixed-size hashed vectors (feature hashing, signed buckets).
- L2-normalize vectors and perform cosine similarity via dot product.

This is a lightweight semantic-ish vector layer that requires only numpy.
It is deterministic and works fully offline.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


class OORepVectorSearch:
    def __init__(self, data_dir: Optional[str] = None, index_dir: Optional[str] = None):
        # Grouped layout defaults:
        #   references/data/rubrics.json
        #   references/indexes/oorep_vector_*.{npz,json}
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = Path(__file__).resolve().parent.parent / "data"

        if index_dir:
            self.index_dir = Path(index_dir)
        else:
            candidate = self.data_dir.parent / "indexes"
            self.index_dir = candidate if candidate.exists() else self.data_dir

        self.rubrics_path = self.data_dir / "rubrics.json"
        self.index_path = self.index_dir / "oorep_vector_index.npz"
        self.meta_path = self.index_dir / "oorep_vector_meta.json"

        self.matrix: Optional[np.ndarray] = None  # shape: [N, D], normalized float16/32
        self.rubric_ids: Optional[np.ndarray] = None  # shape: [N]
        self.fullpaths: List[str] = []
        self.sources: List[str] = []
        self.dim: int = 384

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return TOKEN_RE.findall((text or "").lower())

    @staticmethod
    def _stable_hash(token: str) -> int:
        # FNV-1a 32-bit (deterministic across runs/processes)
        h = 2166136261
        for b in token.encode("utf-8", errors="ignore"):
            h ^= b
            h = (h * 16777619) & 0xFFFFFFFF
        return h

    @classmethod
    def _encode_hashed(cls, text: str, dim: int) -> np.ndarray:
        v = np.zeros(dim, dtype=np.float32)
        toks = cls._tokenize(text)
        if not toks:
            return v

        for tok in toks:
            h = cls._stable_hash(tok)
            idx = h % dim
            sign = 1.0 if ((h >> 1) & 1) == 0 else -1.0
            v[idx] += sign

        # L2 normalize
        n = float(np.linalg.norm(v))
        if n > 0:
            v /= n
        return v

    def build_index(
        self,
        source_filter: Optional[str] = "publicum",
        dim: int = 384,
        dtype: str = "float16",
    ) -> Dict[str, int]:
        self.dim = dim
        with open(self.rubrics_path, "r", encoding="utf-8") as f:
            rubrics = json.load(f)

        rows: List[np.ndarray] = []
        rubric_ids: List[int] = []
        fullpaths: List[str] = []
        sources: List[str] = []

        for r in rubrics:
            src = r.get("source")
            if source_filter and src != source_filter:
                continue
            fp = r.get("fullpath") or ""
            rid = int(r.get("id"))
            vec = self._encode_hashed(fp, dim=dim)
            rows.append(vec)
            rubric_ids.append(rid)
            fullpaths.append(fp)
            sources.append(src or "")

        if not rows:
            raise RuntimeError("No rubrics selected for index build.")

        mat = np.vstack(rows)
        if dtype == "float16":
            mat = mat.astype(np.float16)
        else:
            mat = mat.astype(np.float32)

        rid_arr = np.array(rubric_ids, dtype=np.int32)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(self.index_path, matrix=mat, rubric_ids=rid_arr)

        meta = {
            "version": 1,
            "method": "hashed-bow-cosine",
            "dim": dim,
            "dtype": str(mat.dtype),
            "count": int(mat.shape[0]),
            "source_filter": source_filter,
            "fullpaths": fullpaths,
            "sources": sources,
        }
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f)

        self.matrix = mat.astype(np.float32, copy=False)
        self.rubric_ids = rid_arr
        self.fullpaths = fullpaths
        self.sources = sources

        return {
            "count": int(mat.shape[0]),
            "dim": dim,
            "dtype": str(mat.dtype),
        }

    def load(self) -> None:
        if not self.index_path.exists() or not self.meta_path.exists():
            raise FileNotFoundError(
                f"Missing index files: {self.index_path.name} / {self.meta_path.name}. Build first."
            )

        npz = np.load(self.index_path)
        self.matrix = npz["matrix"].astype(np.float32, copy=False)
        self.rubric_ids = npz["rubric_ids"].astype(np.int32, copy=False)

        with open(self.meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.dim = int(meta["dim"])
        self.fullpaths = list(meta["fullpaths"])
        self.sources = list(meta["sources"])

    def search(self, query: str, top_k: int = 20) -> List[Dict]:
        if self.matrix is None or self.rubric_ids is None:
            self.load()

        q = self._encode_hashed(query, dim=self.dim)
        if float(np.linalg.norm(q)) == 0.0:
            return []

        # Cosine because both vectors are normalized
        scores = self.matrix @ q
        if top_k >= scores.shape[0]:
            idx = np.argsort(-scores)
        else:
            part = np.argpartition(scores, -top_k)[-top_k:]
            idx = part[np.argsort(-scores[part])]

        out = []
        for i in idx:
            out.append(
                {
                    "rubric_id": int(self.rubric_ids[i]),
                    "fullpath": self.fullpaths[i],
                    "source": self.sources[i],
                    "score": float(scores[i]),
                }
            )
        return out


def main() -> None:
    p = argparse.ArgumentParser(description="OORep local vector search")
    p.add_argument("--data-dir", default=str(Path(__file__).resolve().parent.parent / "data"))
    p.add_argument("--index-dir", default=str(Path(__file__).resolve().parent.parent / "indexes"))
    p.add_argument("--build", action="store_true", help="Build vector index")
    p.add_argument("--source", default="publicum", help="Source filter for build (default: publicum, empty for all)")
    p.add_argument("--dim", type=int, default=384)
    p.add_argument("--dtype", default="float16", choices=["float16", "float32"])
    p.add_argument("--query", default=None, help="Run a search query")
    p.add_argument("--top-k", type=int, default=15)
    args = p.parse_args()

    src_filter = args.source if args.source else None
    vs = OORepVectorSearch(args.data_dir, index_dir=args.index_dir)

    if args.build:
        info = vs.build_index(source_filter=src_filter, dim=args.dim, dtype=args.dtype)
        print(json.dumps({"built": True, **info}, ensure_ascii=False))

    if args.query:
        if vs.matrix is None:
            vs.load()
        res = vs.search(args.query, top_k=args.top_k)
        print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
