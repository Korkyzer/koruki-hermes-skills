#!/usr/bin/env python3
"""Inspect a FreeFrontend/CodePen/GitHub source URL and print structured metadata."""
from __future__ import annotations

import argparse
import json
import re
import urllib.parse
import urllib.request

from ff_common import blocked_reason, clean_text, detect_libraries, detect_tags, extract_meta, extract_source_links, fetch_url
from resolve_codepen_source import resolve as resolve_codepen


def inspect_codepen(url: str) -> dict:
    api = "https://codepen.io/api/oembed?" + urllib.parse.urlencode({"url": url, "format": "json"})
    status, ctype, raw = fetch_url(api)
    data = {}
    if status == 200:
        try:
            data = json.loads(raw)
        except Exception:
            data = {"raw": raw[:500]}
    m = re.search(r"codepen\.io/([^/]+)/(?:pen|full|details|embed)/([^/?#]+)", url)
    user, slug = (m.group(1), m.group(2)) if m else ("", "")
    source = resolve_codepen(url) if user and slug else {"ok": False, "needs_browser": True, "reason": "unparseable_codepen_url"}
    source_summary = {
        "ok": source.get("ok", False),
        "needs_browser": source.get("needs_browser", True),
        "reason": "" if source.get("ok") else (source.get("reason") or blocked_reason(status, raw)),
        "resolved_url": source.get("resolved_url", ""),
        "canonical_url": source.get("canonical_url", ""),
        "has_html": bool(source.get("html")),
        "has_css": bool(source.get("css")),
        "has_js": bool(source.get("js")),
        "external_scripts": source.get("external_scripts", []),
        "stylesheets": source.get("stylesheets", []),
    }
    return {
        "type": "codepen",
        "url": url,
        "oembed_status": status,
        "oembed_blocked_reason": blocked_reason(status, raw),
        "title": data.get("title", "") or source.get("title", ""),
        "author_name": data.get("author_name", ""),
        "author_url": data.get("author_url", ""),
        "thumbnail_url": data.get("thumbnail_url", ""),
        "html_embed": data.get("html", ""),
        "debug_url": f"https://cdpn.io/{user}/debug/{slug}" if user and slug else "",
        "full_page_url": f"https://codepen.io/{user}/full/{slug}" if user and slug else "",
        "details_url": f"https://codepen.io/{user}/details/{slug}" if user and slug else "",
        "source": source_summary,
    }


def inspect_github(url: str) -> dict:
    m = re.search(r"github\.com/([^/]+)/([^/#?]+)", url)
    owner, repo = (m.group(1), m.group(2).replace(".git", "")) if m else ("", "")
    api = f"https://api.github.com/repos/{owner}/{repo}" if owner and repo else ""
    status, ctype, raw = fetch_url(api) if api else (0, "", "")
    data = {}
    if status == 200:
        try:
            data = json.loads(raw)
        except Exception:
            pass
    return {
        "type": "github",
        "url": url,
        "api_status": status,
        "full_name": data.get("full_name", f"{owner}/{repo}" if owner else ""),
        "description": data.get("description", ""),
        "language": data.get("language", ""),
        "stars": data.get("stargazers_count"),
        "default_branch": data.get("default_branch", ""),
        "clone_url": data.get("clone_url", ""),
        "html_url": data.get("html_url", url),
    }


def inspect_generic(url: str) -> dict:
    status, ctype, raw = fetch_url(url)
    meta = extract_meta(raw)
    blob = " ".join(meta.values()) + " " + raw[:5000]
    return {
        "type": "freefrontend" if "freefrontend.com" in url else "web",
        "url": url,
        "status": status,
        "content_type": ctype,
        "title": meta.get("og_title") or meta.get("title"),
        "description": meta.get("og_description") or meta.get("description"),
        "image": meta.get("og_image"),
        "blocked": bool(blocked_reason(status, raw)),
        "blocked_reason": blocked_reason(status, raw),
        "libraries": detect_libraries(blob),
        "tags": detect_tags(blob, urllib.parse.urlparse(url).path),
        "sources": extract_source_links(raw),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    args = ap.parse_args()
    url = args.url
    if "codepen.io" in url:
        out = inspect_codepen(url)
    elif "github.com" in url:
        out = inspect_github(url)
    else:
        out = inspect_generic(url)
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
