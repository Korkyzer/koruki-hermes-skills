#!/usr/bin/env python3
"""Inspect a pattern/source URL and resolve CodePen when possible."""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys
from pathlib import Path
from pattern_common import extract_links, extract_meta, extract_source_links, fetch_url, page_record


def try_codepen(url: str, outdir: str = "") -> dict:
    if "codepen.io" not in url:
        return {}
    script = Path(__file__).with_name("resolve_codepen_source.py")
    if not script.exists():
        return {"codepen_resolver": "missing"}
    cmd = [sys.executable, str(script), url]
    if outdir:
        cmd += ["--outdir", outdir]
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=45)
        return {"codepen_resolver_exit": p.returncode, "codepen_resolver_stdout": p.stdout[-4000:], "codepen_resolver_stderr": p.stderr[-2000:]}
    except Exception as exc:
        return {"codepen_resolver_error": str(exc)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--outdir", default="", help="For CodePen extraction output")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    status, ctype, raw = fetch_url(args.url)
    rec = page_record("inspect", args.url, raw, status, ctype)
    extra = {"meta": extract_meta(raw), "source_links": extract_source_links(raw), "links_sample": extract_links(raw, args.url)[:40]}
    cp = try_codepen(args.url, args.outdir)
    result = {**rec, **extra, **cp}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print(f"{status} {ctype} {args.url}")
    print(f"title: {rec.get('title')}")
    print(f"description: {(rec.get('description') or '')[:300]}")
    print(f"libraries: {', '.join(rec.get('libraries') or []) or '-'}")
    print(f"tags: {', '.join(rec.get('tags') or []) or '-'}")
    if rec.get("blocked"):
        print(f"blocked: {rec.get('blocked_reason')}")
    print("sources:", json.dumps(extra['source_links'], ensure_ascii=False))
    if cp:
        print("codepen resolver:")
        print(cp.get("codepen_resolver_stdout") or cp)

if __name__ == "__main__":
    main()
