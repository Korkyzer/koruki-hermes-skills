#!/usr/bin/env python3
"""Search a FreeFrontend pattern-bank JSON index."""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Dict, List, Tuple

from ff_common import load_index, tokenize

WEIGHTS = {
    "title": 8,
    "tags": 6,
    "libraries": 5,
    "description": 4,
    "url": 3,
    "image_alts": 2,
    "sources": 2,
}


def field_text(page: Dict, field: str) -> str:
    v = page.get(field)
    if isinstance(v, str):
        return v.lower()
    if isinstance(v, list):
        return " ".join(str(x) for x in v).lower()
    if isinstance(v, dict):
        return " ".join(" ".join(vals) if isinstance(vals, list) else str(vals) for vals in v.values()).lower()
    return ""


def score(page: Dict, terms: List[str]) -> Tuple[int, List[str]]:
    total = 0
    reasons = []
    for field, weight in WEIGHTS.items():
        text = field_text(page, field)
        hits = [t for t in terms if t in text]
        if hits:
            total += weight * len(hits)
            reasons.append(f"{field}:{','.join(hits)}")
    # bonus for source-rich/code records
    if page.get("sources"):
        total += 3
    if page.get("category") == "code":
        total += 1
    return total, reasons


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("index")
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    idx = load_index(args.index)
    terms = tokenize(args.query)
    rows = []
    for page in idx.get("pages", []):
        s, reasons = score(page, terms)
        if s > 0:
            rows.append({"score": s, "reasons": reasons, **page})
    rows.sort(key=lambda r: (r["score"], bool(r.get("sources")), r.get("lastmod") or ""), reverse=True)
    deduped = []
    seen = set()
    for r in rows:
        src = r.get("sources") or {}
        first_source = ""
        for urls in src.values():
            if urls:
                first_source = urls[0]
                break
        key = first_source or (r.get("title", "").lower(), r.get("description", "")[:80].lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    rows = deduped[: args.limit]

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    print(f"Query: {args.query} | matches: {len(rows)} | index records: {idx.get('total_count')}")
    for i, r in enumerate(rows, 1):
        libs = ", ".join(r.get("libraries") or []) or "—"
        tags = ", ".join(r.get("tags") or []) or "—"
        srcs = []
        for kind, urls in (r.get("sources") or {}).items():
            if urls:
                srcs.append(f"{kind}:{urls[0]}")
        print(f"\n{i}. [{r['score']}] {r.get('title')}")
        print(f"   URL: {r.get('url')}")
        print(f"   Libs: {libs} | Tags: {tags}")
        if r.get("description"):
            print(f"   {r['description'][:240]}")
        if srcs:
            print(f"   Source: {' | '.join(srcs[:3])}")
        print(f"   Why: {'; '.join(r.get('reasons', [])[:5])}")

if __name__ == "__main__":
    main()
