#!/usr/bin/env python3
"""Search a Creative Pattern Bank JSON index."""
from __future__ import annotations
import argparse, json, re
from typing import Dict, List
from pattern_common import load_index, tokenize

WEIGHTS = {
    "title": 12,
    "description": 5,
    "tags": 8,
    "libraries": 9,
    "category": 4,
    "source": 3,
    "url": 2,
    "image_alts": 2,
}


def field_text(v):
    if isinstance(v, list): return " ".join(map(str, v))
    if isinstance(v, dict): return " ".join(" ".join(map(str, x)) if isinstance(x, list) else str(x) for x in v.values())
    return str(v or "")


def score(row: Dict, terms: List[str]) -> int:
    total = 0
    hay_all = json.dumps(row, ensure_ascii=False).lower().replace("-", " ")
    for term in terms:
        t = term.lower().replace("-", " ")
        if t in hay_all:
            total += 1
        for field, weight in WEIGHTS.items():
            if t in field_text(row.get(field)).lower().replace("-", " "):
                total += weight
    # Bonus for real source/code links and for snippets over plain pages.
    srcs = row.get("sources") or {}
    if srcs.get("codepen") or srcs.get("github"):
        total += 8
    if row.get("kind") in ("snippet", "pattern", "article"):
        total += 3
    if row.get("blocked") is True:
        total -= 4
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("index")
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--source", default="", help="Filter by source name")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    idx = load_index(args.index)
    terms = tokenize(args.query)
    rows = idx.get("pages", [])
    if args.source:
        rows = [r for r in rows if r.get("source") == args.source]
    ranked = []
    for row in rows:
        s = score(row, terms)
        if s > 0:
            ranked.append((s, row))
    ranked.sort(key=lambda x: x[0], reverse=True)
    results = [{"score": s, **row} for s, row in ranked[:args.limit]]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    print(f"Query: {args.query}")
    print(f"Index: {idx.get('total_count', len(idx.get('pages', [])))} records | sources: {', '.join(idx.get('sources', []))}")
    print()
    for i, item in enumerate(results, 1):
        libs = ", ".join(item.get("libraries") or []) or "-"
        tags = ", ".join(item.get("tags") or []) or "-"
        print(f"{i}. [{item['score']}] {item.get('title')}")
        print(f"   source: {item.get('source')} / {item.get('kind')} | libs: {libs} | tags: {tags}")
        print(f"   url: {item.get('url')}")
        srcs = item.get("sources") or {}
        if srcs:
            flat = []
            for k, vals in srcs.items():
                for v in vals[:2]: flat.append(f"{k}: {v}")
            print(f"   code: {' | '.join(flat[:4])}")
        desc = (item.get("description") or "").strip()
        if desc:
            print(f"   {desc[:220]}")
        if item.get("blocked"):
            print(f"   blocked: {item.get('blocked_reason')}")
        print()

if __name__ == "__main__":
    main()
