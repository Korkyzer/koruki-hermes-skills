#!/usr/bin/env python3
"""Shared helpers for the FreeFrontend pattern bank scripts."""
from __future__ import annotations

import html
import json
import re
import time
import urllib.parse
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple
from xml.etree import ElementTree as ET

UA = "Mozilla/5.0 (compatible; Hermes-FreeFrontendPatternBank/1.0; +https://koruki.fr)"

LIB_PATTERNS = {
    "gsap": r"\b(gsap|tweenmax|scrolltrigger|splittext|morphsvg|drawsvg)\b",
    "three.js": r"\b(three\.js|three-js|threejs|webgl|glsl|shader)\b",
    "pixi.js": r"\b(pixi\.js|pixijs|pixi-js)\b",
    "react": r"\b(react\.js|react-dom|react\b)\b",
    "vue": r"\b(vue\.js|vue\b)\b",
    "jquery": r"\b(jquery|jquery-ui)\b",
    "anime.js": r"\b(anime\.js|animejs)\b",
    "matter.js": r"\b(matter\.js|matterjs)\b",
    "framer-motion": r"\b(framer-motion|framer motion)\b",
    "tailwind": r"\b(tailwind)\b",
    "bootstrap": r"\b(bootstrap)\b",
    "svg": r"\b(svg|clip-path|mask|filter)\b",
    "css-only": r"\b(css-only|pure css|without javascript|no javascript)\b",
}

SOURCE_PATTERNS = {
    "codepen": r"https?://(?:www\.)?codepen\.io/[^\s\"'<>]+",
    "github": r"https?://(?:www\.)?github\.com/[^\s\"'<>]+",
    "stackblitz": r"https?://(?:www\.)?stackblitz\.com/[^\s\"'<>]+",
    "codesandbox": r"https?://(?:www\.)?codesandbox\.io/[^\s\"'<>]+",
    "youtube": r"https?://(?:www\.)?(?:youtube\.com|youtu\.be)/[^\s\"'<>]+",
}

TAG_HINTS = [
    "scroll", "hero", "menu", "navigation", "cursor", "gallery", "card", "button",
    "form", "input", "slider", "carousel", "shader", "parallax", "reveal",
    "transition", "loader", "3d", "gooey", "liquid", "blinds", "shutter",
    "svg", "canvas", "webgl", "animation", "dashboard", "product", "e-commerce",
]


def fetch_url(url: str, timeout: int = 20, raw: bool = False) -> Tuple[int, str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xml,application/json,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            ctype = resp.headers.get("content-type", "")
            text = data.decode("utf-8", errors="replace")
            return resp.status, ctype, text
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = str(exc)
        return exc.code, exc.headers.get("content-type", "") if exc.headers else "", body or f"HTTP Error {exc.code}: {exc.reason}"
    except Exception as exc:
        return 0, "", f"ERROR: {exc}"


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    value = re.sub(r"\s+", " ", value).strip()
    return value


def extract_meta(raw: str) -> Dict[str, str]:
    def m(pattern: str) -> str:
        hit = re.search(pattern, raw, flags=re.I | re.S)
        return clean_text(hit.group(1)) if hit else ""
    return {
        "title": m(r"<title[^>]*>(.*?)</title>"),
        "description": m(r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"']([^\"']*)[\"']"),
        "og_title": m(r"<meta[^>]+property=[\"']og:title[\"'][^>]+content=[\"']([^\"']*)[\"']"),
        "og_description": m(r"<meta[^>]+property=[\"']og:description[\"'][^>]+content=[\"']([^\"']*)[\"']"),
        "og_image": m(r"<meta[^>]+property=[\"']og:image[\"'][^>]+content=[\"']([^\"']*)[\"']"),
    }


def absolutize(url: str, base: str = "https://freefrontend.com") -> str:
    return urllib.parse.urljoin(base, html.unescape(url))


def extract_links(raw: str, base: str = "https://freefrontend.com") -> List[str]:
    links = []
    for href in re.findall(r"href=[\"']([^\"'#]+)[\"']", raw, flags=re.I):
        u = absolutize(href, base)
        if u.startswith("http"):
            links.append(u)
    return sorted(set(links))


def extract_images(raw: str, base: str = "https://freefrontend.com") -> List[Dict[str, str]]:
    images = []
    for img in re.findall(r"<img\b[^>]*>", raw, flags=re.I | re.S):
        src = re.search(r"src=[\"']([^\"']+)[\"']", img, flags=re.I)
        alt = re.search(r"alt=[\"']([^\"']*)[\"']", img, flags=re.I)
        if src:
            images.append({"src": absolutize(src.group(1), base), "alt": clean_text(alt.group(1) if alt else "")})
    return images[:20]


def extract_source_links(raw: str) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for name, pattern in SOURCE_PATTERNS.items():
        hits = sorted({html.unescape(x).rstrip(").,;") for x in re.findall(pattern, raw, flags=re.I)})
        if name == "codepen":
            hits = [u for u in hits if re.search(r"/pen/|/full/|/details/|/embed/", u)]
        if name == "github":
            hits = [u for u in hits if not re.search(r"\.(png|jpe?g|webp|gif|svg)(\?|$)", u, flags=re.I)]
        if hits:
            out[name] = hits
    return out


def detect_libraries(text: str) -> List[str]:
    low = text.lower()
    libs = [name for name, pattern in LIB_PATTERNS.items() if re.search(pattern, low, flags=re.I)]
    return sorted(set(libs))


def detect_tags(text: str, path: str = "") -> List[str]:
    low = f"{text} {path}".lower()
    tags = [t for t in TAG_HINTS if re.search(r"\b" + re.escape(t) + r"\b", low)]
    return sorted(set(tags))


def parse_sitemap(xml_text: str) -> List[Dict[str, str]]:
    root = ET.fromstring(xml_text)
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    rows = []
    for url in root.findall("sm:url", ns):
        loc = url.findtext("sm:loc", default="", namespaces=ns)
        lastmod = url.findtext("sm:lastmod", default="", namespaces=ns)
        if loc:
            rows.append({"url": loc.strip(), "lastmod": lastmod.strip()})
    return rows


def path_category(url: str) -> str:
    path = urllib.parse.urlparse(url).path.strip("/")
    if not path:
        return "home"
    parts = path.split("/")
    if parts[0] == "code" and len(parts) > 1:
        return "code"
    return parts[0]


def blocked_reason(status: int | None, raw: str) -> str:
    low = (raw or "").lower()
    if "just a moment" in low and "cloudflare" in low:
        return "cloudflare_challenge"
    if "please wait while your request is being verified" in low or "webdrivercheck" in low:
        return "antibot_interstitial"
    if status in (401, 403, 429):
        return f"http_{status}"
    return ""


def is_antibot(raw: str) -> bool:
    return bool(blocked_reason(None, raw))


def json_dump(obj: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def load_index(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def tokenize(q: str) -> List[str]:
    return [t.lower() for t in re.findall(r"[a-zA-Z0-9_.+-]+", q) if len(t) > 1]
