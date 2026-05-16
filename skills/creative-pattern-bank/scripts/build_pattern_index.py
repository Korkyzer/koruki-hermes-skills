#!/usr/bin/env python3
"""Build a multi-source creative frontend pattern index."""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from typing import Dict, Iterable, List

from pattern_common import (
    absolutize, clean_text, detect_libraries, detect_tags, extract_links,
    extract_source_links, fetch_url, json_dump, page_record, parse_sitemap,
    slug_title_from_url, utc_now
)

SOURCE_DEFAULTS = ["freefrontend", "codemyui", "devsnap", "codrops", "gsapify", "uiverse"]


def extract_freefrontend_cards(parent_url: str, parent_category: str, raw: str, lastmod: str) -> List[Dict]:
    cards: List[Dict] = []
    chunks = re.split(r"<div class=snippet-card", raw)
    for chunk in chunks[1:]:
        chunk = "<div class=snippet-card" + chunk
        title_m = re.search(r"<h3[^>]*>(.*?)</h3>", chunk, flags=re.I | re.S)
        desc_m = re.search(r"itemprop=description[^>]*.*?<p>(.*?)</p>", chunk, flags=re.I | re.S)
        img_m = re.search(r"<img[^>]+src=([^\s>]+)[^>]*", chunk, flags=re.I | re.S)
        alt_m = re.search(r"<img[^>]+alt=\"([^\"]*)\"", chunk, flags=re.I | re.S)
        codepen_m = re.search(r"https?://codepen\.io/[^\s\"'<>]+/pen/[^\s\"'<>]+", chunk, flags=re.I)
        license_m = re.search(r"<span class=meta-label>License:</span>\s*<span class=meta-value>(.*?)</span>", chunk, flags=re.I | re.S)
        author_m = re.search(r"class=author-name-link>(.*?)</a>", chunk, flags=re.I | re.S)
        if not title_m and not codepen_m:
            continue
        title = clean_text(title_m.group(1) if title_m else "")
        desc = clean_text(desc_m.group(1) if desc_m else "")
        img = absolutize(img_m.group(1).strip('"\''), parent_url) if img_m else ""
        source_url = codepen_m.group(0).rstrip(").,;") if codepen_m else ""
        text_blob = " ".join([title, desc, alt_m.group(1) if alt_m else "", source_url])
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or (source_url.split("/")[-1] if source_url else "snippet")
        cards.append({
            "source": "freefrontend", "kind": "snippet", "url": f"{parent_url}#{slug}",
            "title": title or slug, "description": desc, "category": parent_category,
            "lastmod": lastmod, "status": 200, "content_type": "text/html#snippet-card",
            "blocked": False, "blocked_reason": "", "libraries": detect_libraries(text_blob),
            "tags": detect_tags(text_blob, parent_url), "image": img,
            "image_alts": [clean_text(alt_m.group(1))] if alt_m else [],
            "sources": {"codepen": [source_url]} if source_url else {}, "parent_url": parent_url,
            "author": clean_text(author_m.group(1) if author_m else ""),
            "license": clean_text(license_m.group(1) if license_m else ""),
        })
    return cards


def build_freefrontend(max_pages: int, delay: float, hints: str) -> List[Dict]:
    status, _, xml = fetch_url("https://freefrontend.com/sitemap.xml", timeout=30)
    if status != 200:
        return []
    rows = [r for r in parse_sitemap(xml) if not r.get("sitemap")]
    rows = [r for r in rows if "/code/" not in r["url"]]
    rows.sort(key=lambda r: score_url(r["url"], hints), reverse=True)
    out: List[Dict] = []
    for i, row in enumerate(rows[:max_pages], 1):
        url = row["url"]
        st, ctype, raw = fetch_url(url)
        rec = page_record("freefrontend", url, raw, st, ctype, lastmod=row.get("lastmod", ""))
        out.append(rec)
        if st == 200 and not rec.get("blocked"):
            out.extend(extract_freefrontend_cards(url, rec.get("category", ""), raw, row.get("lastmod", "")))
        print(f"[freefrontend {i}/{min(max_pages,len(rows))}] {st} {url}", file=sys.stderr)
        if delay: time.sleep(delay)
    return out


def build_sitemap_source(name: str, sitemap_url: str, max_pages: int, delay: float, hints: str, include: str = "") -> List[Dict]:
    st, _, xml = fetch_url(sitemap_url, timeout=30)
    if st != 200:
        print(f"[{name}] sitemap failed status={st}", file=sys.stderr)
        return []
    rows = parse_sitemap(xml)
    # If sitemap index, fetch child sitemaps selectively.
    child_sitemaps = [r["url"] for r in rows if r.get("sitemap")]
    if child_sitemaps:
        expanded = []
        for sm in child_sitemaps:
            if include and not re.search(include, sm, flags=re.I):
                continue
            cst, _, cxml = fetch_url(sm, timeout=30)
            if cst == 200:
                expanded.extend([r for r in parse_sitemap(cxml) if not r.get("sitemap")])
        rows = expanded
    else:
        rows = [r for r in rows if not r.get("sitemap")]
    if include:
        rows = [r for r in rows if re.search(include, r["url"], flags=re.I)] or rows
    rows = [r for r in rows if not re.search(r"privacy|terms|contact|about|wp-content|feed", r["url"], flags=re.I)]
    rows.sort(key=lambda r: score_url(r["url"], hints), reverse=True)
    out = []
    for i, row in enumerate(rows[:max_pages], 1):
        url = row["url"]
        status, ctype, raw = fetch_url(url)
        out.append(page_record(name, url, raw, status, ctype, lastmod=row.get("lastmod", "")))
        out.extend(extract_article_cards(name, url, raw))
        print(f"[{name} {i}/{min(max_pages,len(rows))}] {status} {url}", file=sys.stderr)
        if delay: time.sleep(delay)
    return out


def extract_article_cards(source: str, parent_url: str, raw: str) -> List[Dict]:
    """Generic card extractor for article/listing pages."""
    cards: List[Dict] = []
    # Prefer article blocks, fallback to meaningful anchors.
    blocks = re.findall(r"<article\b.*?</article>", raw, flags=re.I | re.S)
    if not blocks:
        # Extract anchors with human titles; avoid nav/noise.
        for a in re.findall(r"<a\b[^>]*href=[\"'][^\"']+[\"'][^>]*>.*?</a>", raw, flags=re.I | re.S)[:120]:
            href_m = re.search(r"href=[\"']([^\"']+)[\"']", a, flags=re.I)
            href = absolutize(href_m.group(1), parent_url) if href_m else ""
            title = clean_text(a)
            if not href.startswith("http") or len(title) < 8 or len(title) > 140:
                continue
            if re.search(r"privacy|terms|contact|category|tag|author|#", href, flags=re.I):
                continue
            text = f"{title} {href}"
            cards.append({
                "source": source, "kind": "pattern", "url": href, "title": title,
                "description": f"Discovered from {parent_url}", "category": source,
                "status": None, "content_type": "text/html#link", "blocked": None, "blocked_reason": "",
                "libraries": detect_libraries(text), "tags": detect_tags(text, href), "image": "", "image_alts": [],
                "sources": extract_source_links(a), "parent_url": parent_url,
            })
        return dedupe(cards, key="url")[:40]
    for block in blocks[:60]:
        href_m = re.search(r"href=[\"']([^\"']+)[\"']", block, flags=re.I)
        href = absolutize(href_m.group(1), parent_url) if href_m else parent_url
        title_m = re.search(r"<h[1-4][^>]*>(.*?)</h[1-4]>", block, flags=re.I | re.S)
        title = clean_text(title_m.group(1) if title_m else "") or slug_title_from_url(href)
        desc_m = re.search(r"<p[^>]*>(.*?)</p>", block, flags=re.I | re.S)
        desc = clean_text(desc_m.group(1) if desc_m else "")
        img_m = re.search(r"<img\b[^>]*src=[\"']([^\"']+)[\"'][^>]*>", block, flags=re.I | re.S)
        img = absolutize(img_m.group(1), parent_url) if img_m else ""
        text = f"{title} {desc} {href} {block[:1500]}"
        cards.append({
            "source": source, "kind": "article", "url": href, "title": title,
            "description": desc, "category": source, "status": None, "content_type": "text/html#article",
            "blocked": None, "blocked_reason": "", "libraries": detect_libraries(text),
            "tags": detect_tags(text, href), "image": img, "image_alts": [],
            "sources": extract_source_links(block), "parent_url": parent_url,
        })
    return dedupe(cards, key="url")


def build_codemyui(max_pages: int, delay: float, hints: str) -> List[Dict]:
    return build_sitemap_source("codemyui", "https://codemyui.com/sitemap.xml", max_pages, delay, hints, include=r"post-sitemap|post_tag|gsap|scroll|animation|image|menu|hover|button")


def build_devsnap(max_pages: int, delay: float, hints: str) -> List[Dict]:
    return build_sitemap_source("devsnap", "https://devsnap.me/sitemap.xml", max_pages, delay, hints, include=r"css|javascript|three-js|animation|scroll|hover|menu|button|image|parallax|page-transitions")


def build_codrops(max_pages: int, delay: float, hints: str) -> List[Dict]:
    return build_sitemap_source("codrops", "https://tympanus.net/codrops/sitemap.xml", max_pages, delay, hints, include=r"post-sitemap|webzibition|tutorial|case|gsap|three|webgl|shader|scroll")


def build_gsapify(max_pages: int, delay: float, hints: str) -> List[Dict]:
    return build_sitemap_source("gsapify", "https://gsapify.com/sitemap.xml", max_pages, delay, hints, include=r"gsap|animation|scroll|text|examples|templates")


def build_uiverse(max_pages: int, delay: float, hints: str) -> List[Dict]:
    seeds = [
        "https://uiverse.io/", "https://uiverse.io/buttons", "https://uiverse.io/cards",
        "https://uiverse.io/loaders", "https://uiverse.io/checkboxes", "https://uiverse.io/toggles",
        "https://uiverse.io/inputs", "https://uiverse.io/radio-buttons",
    ]
    out = []
    for i, url in enumerate(seeds[:max_pages], 1):
        st, ctype, raw = fetch_url(url)
        rec = page_record("uiverse", url, raw, st, ctype, category="components")
        if st in (401,403,429):
            rec.update({"kind":"seed", "title": slug_title_from_url(url), "description":"Uiverse seed URL; simple fetch may be blocked, use browser/search fallback."})
        out.append(rec)
        out.extend(extract_article_cards("uiverse", url, raw))
        print(f"[uiverse {i}/{min(max_pages,len(seeds))}] {st} {url}", file=sys.stderr)
        if delay: time.sleep(delay)
    return out


def score_url(url: str, hints: str) -> int:
    if not hints:
        return 0
    low = url.lower().replace("-", " ")
    terms = [t for t in re.findall(r"[a-z0-9]+", hints.lower()) if len(t) > 2]
    return sum(10 for t in terms if t in low)


def dedupe(rows: List[Dict], key: str = "url") -> List[Dict]:
    seen = set(); out = []
    for r in rows:
        k = r.get(key) or r.get("url") or r.get("title")
        if not k or k in seen:
            continue
        seen.add(k); out.append(r)
    return out


def build(sources: List[str], max_pages: int, per_source: int, delay: float, hints: str) -> Dict:
    builders = {
        "freefrontend": build_freefrontend,
        "codemyui": build_codemyui,
        "devsnap": build_devsnap,
        "codrops": build_codrops,
        "gsapify": build_gsapify,
        "uiverse": build_uiverse,
    }
    pages: List[Dict] = []
    budget = per_source or max(1, max_pages // max(1, len(sources)))
    for source in sources:
        fn = builders.get(source)
        if not fn:
            print(f"Unknown source: {source}", file=sys.stderr)
            continue
        try:
            pages.extend(fn(budget, delay, hints))
        except Exception as exc:
            print(f"[{source}] failed: {exc}", file=sys.stderr)
    pages = dedupe(pages, key="url")
    return {"schema": "creative-pattern-bank/v1", "generated_at": utc_now(), "sources": sources, "query_hints": hints, "total_count": len(pages), "pages": pages}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default=",".join(SOURCE_DEFAULTS), help="Comma-separated sources")
    ap.add_argument("--max-pages", type=int, default=120, help="Total-ish page budget")
    ap.add_argument("--per-source", type=int, default=0, help="Override max pages per source")
    ap.add_argument("--query-hints", default="", help="Bias URL ordering toward these terms")
    ap.add_argument("--delay", type=float, default=0.05)
    ap.add_argument("--out", default="creative-patterns.json")
    args = ap.parse_args()
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    index = build(sources, args.max_pages, args.per_source, args.delay, args.query_hints)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    json_dump(index, args.out)
    print(f"Wrote {index['total_count']} records to {args.out}")

if __name__ == "__main__":
    main()
