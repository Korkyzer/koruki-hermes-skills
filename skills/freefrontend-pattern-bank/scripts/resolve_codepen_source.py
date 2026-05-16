#!/usr/bin/env python3
"""Resolve a CodePen URL through cdpn.io debug/fullpage endpoints and optionally save source files.

This avoids the common Cloudflare 403 on codepen.io itself for many public pens.
It does not bypass private pens or paid/disabled embeds.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.parse
from pathlib import Path
from typing import Dict, List

from ff_common import blocked_reason, clean_text, fetch_url, json_dump


def parse_codepen_url(url: str) -> tuple[str, str]:
    m = re.search(r"codepen\.io/([^/]+)/(?:pen|full|details|embed)/([^/?#]+)", url)
    if not m:
        raise SystemExit(f"Not a CodePen pen/full/details/embed URL: {url}")
    return m.group(1), m.group(2)


def extract_between(raw: str, pattern: str) -> str:
    m = re.search(pattern, raw, flags=re.I | re.S)
    return m.group(1).strip() if m else ""


def extract_all(raw: str, pattern: str) -> List[str]:
    return [x.strip() for x in re.findall(pattern, raw, flags=re.I | re.S)]


def resolve(url: str) -> Dict:
    user, slug = parse_codepen_url(url)
    candidates = [
        f"https://cdpn.io/{user}/debug/{slug}",
        f"https://cdpn.io/{user}/fullpage/{slug}",
    ]
    attempts = []
    chosen = ""
    raw = ""
    status = 0
    ctype = ""
    for candidate in candidates:
        status, ctype, body = fetch_url(candidate, timeout=25)
        reason = blocked_reason(status, body)
        attempts.append({"url": candidate, "status": status, "content_type": ctype, "blocked_reason": reason})
        if status == 200 and not reason and "<html" in body.lower():
            chosen = candidate
            raw = body
            break
    if not chosen:
        return {
            "type": "codepen-source",
            "url": url,
            "ok": False,
            "needs_browser": True,
            "reason": attempts[-1]["blocked_reason"] if attempts else "unresolved",
            "attempts": attempts,
            "browser_hint": "Open the CodePen in a real browser or use Hermes browser tools; cdpn.io debug/fullpage did not return source.",
        }

    canonical = extract_between(raw, r"<link[^>]+rel=[\"']canonical[\"'][^>]+href=[\"']([^\"']+)[\"']")
    title = clean_text(extract_between(raw, r"<title[^>]*>(.*?)</title>"))
    styles = extract_all(raw, r"<style[^>]*>(.*?)</style>")
    rendered_js = extract_between(raw, r"<script[^>]+id=[\"']rendered-js[\"'][^>]*>(.*?)</script>")
    scripts = [urllib.parse.urljoin(chosen, u) for u in extract_all(raw, r"<script[^>]+src=[\"']([^\"']+)[\"'][^>]*>")]
    stylesheets = [urllib.parse.urljoin(chosen, u) for u in extract_all(raw, r"<link[^>]+rel=[\"']stylesheet[\"'][^>]+href=[\"']([^\"']+)[\"'][^>]*>")]
    body = extract_between(raw, r"<body[^>]*>(.*?)</body>")
    # Remove external and rendered script tags from body payload to leave HTML structure.
    html_body = re.sub(r"<script\b.*?</script>", "", body, flags=re.I | re.S).strip()

    return {
        "type": "codepen-source",
        "url": url,
        "ok": True,
        "needs_browser": False,
        "resolved_url": chosen,
        "canonical_url": canonical,
        "title": title,
        "slug": slug,
        "user_from_url": user,
        "stylesheets": stylesheets,
        "external_scripts": scripts,
        "html": html_body,
        "css": "\n\n".join(styles).strip(),
        "js": rendered_js.strip(),
        "attempts": attempts,
    }


def write_outputs(result: Dict, outdir: str) -> Dict:
    path = Path(outdir)
    path.mkdir(parents=True, exist_ok=True)
    json_dump(result, str(path / "source.json"))
    if result.get("ok"):
        (path / "index.fragment.html").write_text(result.get("html", ""), encoding="utf-8")
        (path / "styles.css").write_text(result.get("css", ""), encoding="utf-8")
        (path / "script.js").write_text(result.get("js", ""), encoding="utf-8")
        external_css = "\n".join(f'<link rel="stylesheet" href="{u}">' for u in result.get("stylesheets", []))
        external_js = "\n".join(f'<script src="{u}"></script>' for u in result.get("external_scripts", []))
        standalone = f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>{result.get('title') or 'CodePen resolved source'}</title>
{external_css}
<link rel=\"stylesheet\" href=\"./styles.css\">
</head>
<body>
{result.get('html','')}
{external_js}
<script src=\"./script.js\"></script>
</body>
</html>
"""
        (path / "index.html").write_text(standalone, encoding="utf-8")
    return {"outdir": str(path), "files": sorted(p.name for p in path.iterdir())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--outdir", help="Write source.json + extracted HTML/CSS/JS/standalone index.html")
    args = ap.parse_args()
    result = resolve(args.url)
    if args.outdir:
        result["written"] = write_outputs(result, args.outdir)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
