#!/usr/bin/env python3
"""Re-enrich a Creative Pattern Bank index with inferred semantics and optional visual captions.

Visual annotations JSON/JSONL format:
  {"url":"https://...", "caption":"dark ribbed metallic shutter", "palette":"navy lime"}
or a JSON array of those objects.
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict, Iterable, List

from pattern_common import enrich_record, json_dump, load_index, utc_now


def load_annotations(path: str) -> Dict[str, Dict[str, Any]]:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return {}
    rows: List[Dict[str, Any]] = []
    if text.startswith("["):
        rows = json.loads(text)
    else:
        for line in text.splitlines():
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        url = row.get("url") or row.get("source_url")
        if not url:
            continue
        visual = {k: v for k, v in row.items() if k not in ("url", "source_url") and v}
        out[url] = visual
    return out


def enrich_index(index: Dict[str, Any], annotations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    pages = []
    for row in index.get("pages", []):
        url = row.get("url", "")
        visual = annotations.get(url)
        if visual:
            current = row.get("visual") or {}
            current.update(visual)
            row["visual"] = current
        pages.append(enrich_record(row))
    index["schema"] = "creative-pattern-bank/v2"
    index["enriched_at"] = utc_now()
    index["total_count"] = len(pages)
    index["pages"] = pages
    return index


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("index", help="Input index JSON")
    ap.add_argument("--visual-annotations", default="", help="Optional JSON/JSONL captions keyed by url")
    ap.add_argument("--out", default="", help="Output path; defaults to overwriting input")
    args = ap.parse_args()

    index = load_index(args.index)
    annotations = load_annotations(args.visual_annotations)
    enriched = enrich_index(index, annotations)
    out = args.out or args.index
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json_dump(enriched, out)
    low = sum(1 for p in enriched.get("pages", []) if p.get("needs_visual_caption"))
    print(f"Wrote {enriched['total_count']} enriched records to {out} ({low} still need visual caption)")


if __name__ == "__main__":
    main()
