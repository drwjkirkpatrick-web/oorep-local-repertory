#!/usr/bin/env python3
"""
Extract OOREP PostgreSQL dump into JSON files.

This script processes the OOREP database in batches to avoid memory issues
with the 1.36M remedy-rubric links.

Usage:
    # Place oorep.sql.gz in a data/ directory, then:
    python scripts/extract_oorep.py
    # or specify paths:
    python scripts/extract_oorep.py --sql data/oorep.sql.gz --out data/
"""

import json
import gzip
import os
import argparse
from pathlib import Path


def extract_remedies(sql_path: Path, output_dir: Path) -> int:
    """Extract remedy table (2,432 rows - small enough for single pass)."""
    print("Extracting remedies...")
    remedies = []
    remedies_by_abbrev = {}
    
    with gzip.open(sql_path, "rt", encoding="utf-8") as f:
        in_copy = False
        for line in f:
            if line.startswith("COPY public.remedy "):
                in_copy = True
                continue
            if in_copy and line.strip() == "\\.":
                break
            if in_copy:
                parts = line.strip().split("\t")
                if len(parts) >= 3:
                    entry = {
                        "id": int(parts[0]),
                        "abbrev": parts[1] if parts[1] != "\\N" else None,
                        "name": parts[2] if parts[2] != "\\N" else None,
                        "alt_names": parts[3] if len(parts) > 3 and parts[3] != "\\N" else None
                    }
                    remedies.append(entry)
                    if entry["abbrev"]:
                        remedies_by_abbrev[entry["abbrev"]] = entry
    
    with open(output_dir / "remedies.json", "w", encoding="utf-8") as f:
        json.dump(remedies, f, indent=2, ensure_ascii=False)
    
    with open(output_dir / "remedies_by_abbrev.json", "w", encoding="utf-8") as f:
        json.dump(remedies_by_abbrev, f, indent=2, ensure_ascii=False)
    
    print(f"  Saved {len(remedies)} remedies")
    return len(remedies)


def extract_rubrics(sql_path: Path, output_dir: Path, batch_size: int = 20000) -> int:
    """Extract rubric table (74,785 rows) in batches."""
    print("Extracting rubrics...")
    rubrics = []
    search_index = {}
    batch_num = 0
    total = 0
    
    def flush_batch():
        nonlocal batch_num, rubrics
        if rubrics:
            with open(output_dir / f"rubrics_batch_{batch_num}.json", "w", encoding="utf-8") as f:
                json.dump(rubrics, f, indent=2, ensure_ascii=False)
            print(f"  Batch {batch_num}: {len(rubrics)} rubrics")
            rubrics = []
            batch_num += 1
    
    with gzip.open(sql_path, "rt", encoding="utf-8") as f:
        in_copy = False
        for line in f:
            if line.startswith("COPY public.rubric "):
                in_copy = True
                continue
            if in_copy and line.strip() == "\\.":
                break
            if in_copy:
                parts = line.strip().split("\t")
                if len(parts) >= 6:
                    fullpath = parts[5] if parts[5] != "\\N" else None
                    entry = {
                        "id": int(parts[1]) if parts[1] != "\\N" else None,
                        "source": parts[0] if parts[0] != "\\N" else None,
                        "fullpath": fullpath,
                        "path_parts": fullpath.split(", ") if fullpath else []
                    }
                    rubrics.append(entry)
                    total += 1
                    
                    # Build search index
                    if fullpath:
                        for word in fullpath.lower().replace(",", " ").split():
                            word = word.strip()
                            if len(word) > 2:
                                if word not in search_index:
                                    search_index[word] = []
                                search_index[word].append(entry["id"])
                    
                    if len(rubrics) >= batch_size:
                        flush_batch()
    
    flush_batch()
    
    # Save search index
    with open(output_dir / "rubric_search_index.json", "w", encoding="utf-8") as f:
        json.dump(search_index, f, indent=2, ensure_ascii=False)
    
    # Merge batches
    all_rubrics = []
    for i in range(batch_num):
        batch_file = output_dir / f"rubrics_batch_{i}.json"
        with open(batch_file, "r", encoding="utf-8") as f:
            all_rubrics.extend(json.load(f))
        batch_file.unlink()
    
    with open(output_dir / "rubrics.json", "w", encoding="utf-8") as f:
        json.dump(all_rubrics, f, indent=2, ensure_ascii=False)
    
    print(f"  Total: {total} rubrics, {len(search_index)} search terms")
    return total


def extract_rubric_remedies(sql_path: Path, output_dir: Path, batch_size: int = 150000) -> int:
    """Extract rubricremedy links (1.36M rows) in batches - memory critical."""
    print("Extracting remedy-grade links (this may take a minute)...")
    rubric_to_remedies = {}
    total = 0
    batch_num = 0
    
    def flush_batch():
        nonlocal batch_num, rubric_to_remedies
        if rubric_to_remedies:
            batch_file = output_dir / f"rubric_to_remedies_batch_{batch_num}.json"
            with open(batch_file, "w", encoding="utf-8") as f:
                json.dump(rubric_to_remedies, f, indent=2, ensure_ascii=False)
            print(f"  Batch {batch_num}: {len(rubric_to_remedies)} rubric entries")
            batch_num += 1
            rubric_to_remedies = {}
    
    with gzip.open(sql_path, "rt", encoding="utf-8") as f:
        in_copy = False
        for line in f:
            if line.startswith("COPY public.rubricremedy "):
                in_copy = True
                continue
            if in_copy and line.strip() == "\\.":
                break
            if in_copy:
                parts = line.strip().split("\t")
                if len(parts) >= 4:
                    rubric_id = int(parts[1]) if parts[1] != "\\N" else None
                    remedy_id = int(parts[2]) if parts[2] != "\\N" else None
                    weight = int(parts[3]) if parts[3] != "\\N" else 1
                    
                    if rubric_id is not None and remedy_id is not None:
                        if rubric_id not in rubric_to_remedies:
                            rubric_to_remedies[rubric_id] = []
                        rubric_to_remedies[rubric_id].append({
                            "remedy_id": remedy_id,
                            "weight": weight
                        })
                        total += 1
                        
                        if len(rubric_to_remedies) >= batch_size:
                            flush_batch()
    
    flush_batch()
    
    # Merge batches (usually just one for this data structure)
    merged = {}
    for i in range(batch_num):
        batch_file = output_dir / f"rubric_to_remedies_batch_{i}.json"
        with open(batch_file, "r", encoding="utf-8") as f:
            merged.update(json.load(f))
        batch_file.unlink()
    
    with open(output_dir / "rubric_to_remedies.json", "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    
    print(f"  Total: {total} links across {len(merged)} rubrics")
    return total


def main():
    parser = argparse.ArgumentParser(description="Extract OOREP PostgreSQL dump into JSON files")
    parser.add_argument("--sql", type=Path, default=Path("data/oorep.sql.gz"),
                        help="Path to oorep.sql.gz (default: data/oorep.sql.gz)")
    parser.add_argument("--out", type=Path, default=Path("data"),
                        help="Output directory for JSON files (default: data/)")
    parser.add_argument("--keep-sql", action="store_true",
                        help="Keep the SQL file after extraction (default: delete it)")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    sql_path = args.sql

    if not sql_path.exists():
        print(f"Error: {sql_path} not found")
        print("Download it first:")
        print('  curl -L -o data/oorep.sql.gz "https://github.com/nondeterministic/oorep/raw/master/oorep.sql.gz"')
        return 1

    print(f"Processing {sql_path}")
    print(f"Output directory: {args.out.resolve()}")
    print("-" * 50)

    remedy_count = extract_remedies(sql_path, args.out)
    rubric_count = extract_rubrics(sql_path, args.out)
    link_count = extract_rubric_remedies(sql_path, args.out)

    # Save metadata
    metadata = {
        "name": "OOREP Homeopathic Repertory",
        "version": "1.0.0",
        "source": "https://github.com/nondeterministic/oorep",
        "license": "GPL v3",
        "author": "Andreas Bauer",
        "statistics": {
            "remedies": remedy_count,
            "rubrics": rubric_count,
            "remedy_rubric_links": link_count
        }
    }

    with open(args.out / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("-" * 50)
    print("Extraction complete!")
    print(f"  Remedies: {remedy_count:,}")
    print(f"  Rubrics: {rubric_count:,}")
    print(f"  Links: {link_count:,}")

    if not args.keep_sql:
        sql_path.unlink()
        print(f"  Removed {sql_path}")

    return 0


if __name__ == "__main__":
    exit(main())
