#!/usr/bin/env python3
"""Generate an implementation/adaptation brief from top pattern matches."""
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path


def run_search(index: str, query: str, limit: int) -> list:
    script = Path(__file__).with_name("search_patterns.py")
    p = subprocess.run([sys.executable, str(script), index, query, "--limit", str(limit), "--json"], text=True, capture_output=True, check=True)
    return json.loads(p.stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("index")
    ap.add_argument("query")
    ap.add_argument("--project", default="frontend prototype")
    ap.add_argument("--limit", type=int, default=6)
    args = ap.parse_args()
    rows = run_search(args.index, args.query, args.limit)
    print(f"# Adaptation brief: {args.project}")
    print(f"\nQuery: `{args.query}`\n")
    print("## Relevant references")
    for i, r in enumerate(rows, 1):
        print(f"\n### {i}. {r.get('title')} — {r.get('source')}")
        print(f"- URL: {r.get('url')}")
        srcs = r.get('sources') or {}
        if srcs:
            flat=[]
            for k, vals in srcs.items():
                for v in vals[:2]: flat.append(f"{k}: {v}")
            print(f"- Source/code: {' | '.join(flat[:4])}")
        print(f"- Libraries: {', '.join(r.get('libraries') or []) or 'unknown / CSS'}")
        print(f"- Tags: {', '.join(r.get('tags') or []) or '-'}")
        if r.get('description'):
            print(f"- Why useful: {r.get('description')[:240]}")
        if r.get('blocked'):
            print(f"- Caveat: fetch blocked ({r.get('blocked_reason')}); use browser or source link.")
    print("\n## Implementation direction")
    print("- Treat references as motion/design inspiration, not copy-paste production code.")
    print("- Preserve attribution links in research notes or internal prototype comments.")
    print("- Prefer a standalone HTML/CSS/JS spike first; port to framework only after motion feels right.")
    print("- Add `prefers-reduced-motion` fallback and avoid scroll-jank: transform/opacity first, layout changes sparingly.")

if __name__ == "__main__":
    main()
