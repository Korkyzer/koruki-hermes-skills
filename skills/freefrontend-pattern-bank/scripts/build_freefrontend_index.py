#!/usr/bin/env python3
"""Build a local JSON index of FreeFrontend resources."""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
import time
import urllib.parse
from typing import Dict, List


def extract_snippet_cards(parent_url: str, parent_category: str, raw: str, lastmod: str) -> List[Dict]:
    """Extract individual FreeFrontend snippet cards from category/listing pages."""
    cards: List[Dict] = []
    chunks = re.split(r"<div class=snippet-card", raw)
    for chunk in chunks[1:]:
        chunk = "<div class=snippet-card" + chunk
        # Stop at next card-ish boundary if the split was too greedy.
        # Regex extraction below is deliberately tolerant of Hugo's unquoted attrs.
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
        img = ""
        if img_m:
            raw_src = img_m.group(1).strip('"\'')
            img = urllib.parse.urljoin(parent_url, raw_src)
        source_url = codepen_m.group(0).rstrip(").,;") if codepen_m else ""
        text_blob = " ".join([title, desc, alt_m.group(1) if alt_m else "", source_url])
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or (source_url.split("/")[-1] if source_url else "snippet")
        cards.append({
            "kind": "snippet",
            "url": f"{parent_url}#{slug}",
            "title": title or slug,
            "description": desc,
            "category": parent_category,
            "lastmod": lastmod,
            "status": 200,
            "content_type": "text/html#snippet-card",
            "blocked": False,
            "libraries": detect_libraries(text_blob),
            "tags": detect_tags(text_blob, urllib.parse.urlparse(parent_url).path),
            "image": img,
            "image_alts": [clean_text(alt_m.group(1))] if alt_m else [],
            "sources": {"codepen": [source_url]} if source_url else {},
            "freefrontend_links": [parent_url],
            "code_links": [],
            "parent_url": parent_url,
            "author": clean_text(author_m.group(1) if author_m else ""),
            "license": clean_text(license_m.group(1) if license_m else ""),
        })
    return cards

from ff_common import (
    clean_text, detect_libraries, detect_tags, extract_images, extract_links,
    extract_meta, extract_source_links, fetch_url, is_antibot, json_dump,
    parse_sitemap, path_category
)


def summarize_page(url: str, lastmod: str, raw: str, status: int, ctype: str) -> Dict:
    meta = extract_meta(raw)
    links = extract_links(raw, url)
    images = extract_images(raw, url)
    sources = extract_source_links(raw)
    text_blob = " ".join([
        meta.get("og_title") or meta.get("title") or "",
        meta.get("og_description") or meta.get("description") or "",
        " ".join(img.get("alt", "") for img in images),
        " ".join(links[:80]),
    ])
    title = meta.get("og_title") or meta.get("title") or clean_text(urllib.parse.urlparse(url).path.strip("/").replace("-", " ").title())
    desc = meta.get("og_description") or meta.get("description")
    page_links = [u for u in links if u.startswith("https://freefrontend.com/")]
    code_links = [u for u in page_links if "/code/" in u]
    return {
        "url": url,
        "title": title,
        "description": desc,
        "category": path_category(url),
        "lastmod": lastmod,
        "status": status,
        "content_type": ctype,
        "blocked": is_antibot(raw),
        "libraries": detect_libraries(text_blob + " " + raw[:5000]),
        "tags": detect_tags(text_blob, urllib.parse.urlparse(url).path),
        "image": meta.get("og_image") or (images[0]["src"] if images else ""),
        "image_alts": [img["alt"] for img in images if img.get("alt")][:12],
        "sources": sources,
        "freefrontend_links": page_links[:120],
        "code_links": code_links[:80],
    }


def build(max_pages: int, delay: float, sitemap_url: str, include_code: bool) -> Dict:
    status, ctype, xml = fetch_url(sitemap_url, timeout=30)
    if status != 200:
        raise SystemExit(f"Could not fetch sitemap: status={status} body={xml[:200]}")
    sitemap = parse_sitemap(xml)

    # Prioritize home/category pages first; code pages are often protected but still useful later.
    seed = []
    for row in sitemap:
        u = row["url"]
        cat = path_category(u)
        if include_code or cat != "code":
            seed.append(row)
    seed.sort(key=lambda r: (path_category(r["url"]) == "code", r.get("lastmod", "")), reverse=True)

    seen = set()
    queue = seed[:]
    pages: List[Dict] = []
    discovered_code: Dict[str, str] = {}

    fetched = 0
    while queue and fetched < max_pages:
        row = queue.pop(0)
        url = row["url"]
        if url in seen:
            continue
        seen.add(url)
        status, ctype, raw = fetch_url(url)
        fetched += 1
        lastmod = row.get("lastmod", "")
        page = summarize_page(url, lastmod, raw, status, ctype)
        pages.append(page)
        if status == 200 and not page.get("blocked"):
            cards = extract_snippet_cards(url, page.get("category", ""), raw, lastmod)
            pages.extend(cards)
            if cards:
                print(f"    extracted snippet cards: {len(cards)}", file=sys.stderr)
        for cu in page.get("code_links", []):
            discovered_code.setdefault(cu, url)
            if include_code and cu not in seen and all(x["url"] != cu for x in queue):
                queue.append({"url": cu, "lastmod": row.get("lastmod", "")})
        print(f"[{fetched:04d}/{max_pages}] {status} {url} codes={len(page.get('code_links', []))} blocked={page['blocked']}", file=sys.stderr)
        if delay:
            time.sleep(delay)

    # Add discovered code links as lightweight records if not fetched.
    known = {p["url"] for p in pages}
    for cu, parent in sorted(discovered_code.items()):
        if cu not in known:
            slug = urllib.parse.urlparse(cu).path.rstrip("/").split("/")[-1]
            pages.append({
                "url": cu,
                "title": clean_text(slug.replace("-", " ").title()),
                "description": "Discovered from FreeFrontend listing page; fetch may require browser due anti-bot.",
                "category": "code",
                "lastmod": "",
                "status": None,
                "content_type": "",
                "blocked": None,
                "libraries": detect_libraries(slug),
                "tags": detect_tags(slug, slug),
                "image": "",
                "image_alts": [],
                "sources": {},
                "freefrontend_links": [],
                "code_links": [],
                "discovered_from": parent,
            })

    return {
        "schema": "freefrontend-pattern-bank/v1",
        "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "sitemap_url": sitemap_url,
        "sitemap_count": len(sitemap),
        "fetched_count": len([p for p in pages if p.get("status") is not None]),
        "total_count": len(pages),
        "pages": pages,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=180, help="Max pages to fetch from sitemap/listings")
    ap.add_argument("--out", default="freefrontend-patterns.json")
    ap.add_argument("--sitemap", default="https://freefrontend.com/sitemap.xml")
    ap.add_argument("--delay", type=float, default=0.05)
    ap.add_argument("--include-code", action="store_true", help="Try fetching /code/ pages too; many are anti-bot protected")
    args = ap.parse_args()

    index = build(args.max_pages, args.delay, args.sitemap, args.include_code)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    json_dump(index, args.out)
    print(f"Wrote {index['total_count']} records to {args.out}")

if __name__ == "__main__":
    main()
