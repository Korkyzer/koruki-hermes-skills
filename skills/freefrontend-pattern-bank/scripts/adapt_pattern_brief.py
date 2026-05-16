#!/usr/bin/env python3
"""Generate an adaptation brief from matching FreeFrontend patterns."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ff_common import load_index, tokenize
from search_freefrontend import score


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("index")
    ap.add_argument("query")
    ap.add_argument("--project", default="frontend prototype")
    ap.add_argument("--limit", type=int, default=5)
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

    print(f"# Adaptation brief — {args.project}\n")
    print(f"Query: `{args.query}`\n")
    if not rows:
        print("No matching patterns found. Rebuild the index with more pages or broaden the query.")
        return

    print("## Candidate patterns\n")
    for i, r in enumerate(rows, 1):
        print(f"### {i}. {r.get('title')} — score {r['score']}")
        print(f"- FreeFrontend: {r.get('url')}")
        src = r.get("sources") or {}
        for kind, urls in src.items():
            for u in urls[:2]:
                print(f"- Source ({kind}): {u}")
        if r.get("libraries"):
            print(f"- Libraries: {', '.join(r['libraries'])}")
        if r.get("tags"):
            print(f"- Tags: {', '.join(r['tags'])}")
        if r.get("description"):
            print(f"- Notes: {r['description'][:300]}")
        if r.get("blocked"):
            print("- Caveat: FreeFrontend detail page may require browser automation; use source links if present.")
        print()

    print("## Recommended adaptation process\n")
    print("1. Use these as motion/interaction references, not as blind copy-paste code.")
    print("2. Inspect source links with `inspect_pattern_source.py`, prioritizing CodePen/GitHub.")
    print("3. Rebuild the pattern in standalone HTML/CSS/JS with local assets and no unnecessary dependencies.")
    print("4. Preserve attribution links in README or research notes.")
    print("5. Validate reduced-motion, mobile viewport, console errors, and performance.")

    libs = sorted({lib for r in rows for lib in (r.get("libraries") or [])})
    if libs:
        print("\n## Likely implementation stack\n")
        if "gsap" in libs:
            print("- GSAP/ScrollTrigger appears relevant for scroll-driven sequencing; replace with native scroll math if zero-dependency is required.")
        if "three.js" in libs or "pixi.js" in libs:
            print("- WebGL/Pixi/Three refs are richer but heavier; use only for hero-grade effects.")
        if "css-only" in libs:
            print("- CSS-only patterns are good candidates for production-hardening and lower bundle cost.")

if __name__ == "__main__":
    main()
