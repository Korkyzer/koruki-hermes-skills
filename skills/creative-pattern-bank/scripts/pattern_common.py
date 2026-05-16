#!/usr/bin/env python3
"""Shared helpers for Creative Pattern Bank."""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Iterable, List, Tuple
from xml.etree import ElementTree as ET

UA = "Mozilla/5.0 (compatible; Hermes-CreativePatternBank/1.0; +https://koruki.fr)"

LIB_PATTERNS = {
    "gsap": r"\b(gsap|greensock|tweenmax|scrolltrigger|splittext|morphsvg|drawsvg)\b",
    "three.js": r"\b(three\.js|three-js|threejs|webgl|glsl|shader|gltf|objloader)\b",
    "pixi.js": r"\b(pixi\.js|pixijs|pixi-js)\b",
    "react": r"\b(react\.js|react-dom|react\b|next\.js)\b",
    "vue": r"\b(vue\.js|vue\b)\b",
    "jquery": r"\b(jquery|jquery-ui)\b",
    "anime.js": r"\b(anime\.js|animejs)\b",
    "matter.js": r"\b(matter\.js|matterjs|physics)\b",
    "framer-motion": r"\b(framer-motion|framer motion|motion\.dev)\b",
    "tailwind": r"\b(tailwind)\b",
    "svg": r"\b(svg|clip-path|mask|filter|path morph)\b",
    "canvas": r"\b(canvas|2d context)\b",
    "css-only": r"\b(css-only|pure css|without javascript|no javascript|html css)\b",
}

SOURCE_PATTERNS = {
    "codepen": r"https?://(?:www\.)?codepen\.io/[^\s\"'<>]+",
    "github": r"https?://(?:www\.)?github\.com/[^\s\"'<>]+",
    "stackblitz": r"https?://(?:www\.)?stackblitz\.com/[^\s\"'<>]+",
    "codesandbox": r"https?://(?:www\.)?codesandbox\.io/[^\s\"'<>]+",
    "vercel": r"https?://[^\s\"'<>]*\.vercel\.app[^\s\"'<>]*",
    "demo": r"https?://[^\s\"'<>]*(?:demo|preview|example)[^\s\"'<>]*",
}

TAG_HINTS = [
    "scroll", "hero", "menu", "navigation", "cursor", "gallery", "card", "button",
    "form", "input", "slider", "carousel", "shader", "parallax", "reveal",
    "transition", "loader", "3d", "gooey", "liquid", "blinds", "shutter",
    "svg", "canvas", "webgl", "animation", "dashboard", "product", "e-commerce",
    "text", "typography", "hover", "drag", "accordion", "marquee", "page transition",
    "mask", "clip-path", "grid", "distortion", "particles", "image effect", "portfolio",
]


def fetch_url(url: str, timeout: int = 20, accept: str = "text/html,application/xml,application/json,*/*") -> Tuple[int, str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            return resp.status, resp.headers.get("content-type", ""), data.decode("utf-8", errors="replace")
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
    value = html.unescape(re.sub(r"<script\b.*?</script>|<style\b.*?</style>", " ", value, flags=re.I | re.S))
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    return re.sub(r"\s+", " ", value).strip()


def attr(tag: str, name: str) -> str:
    m = re.search(rf"\b{name}\s*=\s*([\"'])(.*?)\1", tag, flags=re.I | re.S)
    if m:
        return html.unescape(m.group(2))
    m = re.search(rf"\b{name}\s*=\s*([^\s>]+)", tag, flags=re.I | re.S)
    return html.unescape(m.group(1).strip('"\'')) if m else ""


def absolutize(url: str, base: str) -> str:
    return urllib.parse.urljoin(base, html.unescape(url))


def extract_meta(raw: str) -> Dict[str, str]:
    def meta_by(key: str, val: str) -> str:
        patterns = [
            rf"<meta[^>]+{key}=[\"']{re.escape(val)}[\"'][^>]+content=[\"']([^\"']*)[\"']",
            rf"<meta[^>]+content=[\"']([^\"']*)[\"'][^>]+{key}=[\"']{re.escape(val)}[\"']",
        ]
        for p in patterns:
            m = re.search(p, raw, flags=re.I | re.S)
            if m:
                return clean_text(m.group(1))
        return ""
    title_m = re.search(r"<title[^>]*>(.*?)</title>", raw, flags=re.I | re.S)
    return {
        "title": clean_text(title_m.group(1) if title_m else ""),
        "description": meta_by("name", "description"),
        "og_title": meta_by("property", "og:title"),
        "og_description": meta_by("property", "og:description"),
        "og_image": meta_by("property", "og:image"),
    }


def extract_links(raw: str, base: str) -> List[str]:
    links = []
    for href in re.findall(r"href\s*=\s*[\"']([^\"'#]+)[\"']", raw, flags=re.I):
        u = absolutize(href, base)
        if u.startswith("http"):
            links.append(u.rstrip(").,;"))
    return sorted(set(links))


def extract_images(raw: str, base: str) -> List[Dict[str, str]]:
    images = []
    for img in re.findall(r"<img\b[^>]*>", raw, flags=re.I | re.S):
        src = attr(img, "src") or attr(img, "data-src") or attr(img, "data-lazy-src")
        if src:
            images.append({"src": absolutize(src, base), "alt": clean_text(attr(img, "alt"))})
    return images[:25]


def extract_source_links(raw: str) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for name, pattern in SOURCE_PATTERNS.items():
        hits = sorted({html.unescape(x).rstrip(").,;\\") for x in re.findall(pattern, raw, flags=re.I)})
        if name == "codepen":
            hits = [u for u in hits if re.search(r"/pen/|/full/|/details/|/embed/", u)]
        if name == "github":
            hits = [u for u in hits if not re.search(r"\.(png|jpe?g|webp|gif|svg)(\?|$)", u, flags=re.I)]
        if hits:
            out[name] = hits[:30]
    return out


def detect_libraries(text: str) -> List[str]:
    low = text.lower()
    return sorted({name for name, pattern in LIB_PATTERNS.items() if re.search(pattern, low, flags=re.I)})


def detect_tags(text: str, path: str = "") -> List[str]:
    low = f"{text} {path}".lower().replace("-", " ")
    tags = [t for t in TAG_HINTS if t in low]
    return sorted(set(tags))


def blocked_reason(status: int | None, raw: str) -> str:
    low = (raw or "").lower()
    if "just a moment" in low and "cloudflare" in low:
        return "cloudflare_challenge"
    if "please wait while your request is being verified" in low or "webdrivercheck" in low:
        return "antibot_interstitial"
    if "access denied" in low and "cloudflare" in low:
        return "cloudflare_denied"
    if status in (401, 403, 429):
        return f"http_{status}"
    return ""


def parse_sitemap(xml_text: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        # tolerate web_extract-like concatenations only in emergency
        for u in re.findall(r"https?://[^<\s]+", xml_text):
            rows.append({"url": u, "lastmod": ""})
        return rows
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    for url in root.findall(".//sm:url", ns):
        loc = url.findtext("sm:loc", default="", namespaces=ns)
        lastmod = url.findtext("sm:lastmod", default="", namespaces=ns)
        if loc:
            rows.append({"url": loc.strip(), "lastmod": lastmod.strip()})
    for sm in root.findall(".//sm:sitemap", ns):
        loc = sm.findtext("sm:loc", default="", namespaces=ns)
        lastmod = sm.findtext("sm:lastmod", default="", namespaces=ns)
        if loc:
            rows.append({"url": loc.strip(), "lastmod": lastmod.strip(), "sitemap": True})
    return rows


def slug_title_from_url(url: str) -> str:
    path = urllib.parse.urlparse(url).path.strip("/").split("/")[-1]
    return clean_text(re.sub(r"[-_]+", " ", path).title()) or url


def page_record(source: str, url: str, raw: str, status: int, ctype: str, category: str = "", kind: str = "page", lastmod: str = "") -> Dict[str, Any]:
    meta = extract_meta(raw)
    links = extract_links(raw, url)
    images = extract_images(raw, url)
    sources = extract_source_links(raw)
    text_blob = " ".join([meta.get("og_title") or meta.get("title") or "", meta.get("og_description") or meta.get("description") or "", " ".join(img.get("alt", "") for img in images), " ".join(links[:80]), raw[:4000]])
    br = blocked_reason(status, raw)
    row = {
        "source": source,
        "kind": kind,
        "url": url,
        "title": meta.get("og_title") or meta.get("title") or slug_title_from_url(url),
        "description": meta.get("og_description") or meta.get("description"),
        "category": category or urllib.parse.urlparse(url).path.strip("/").split("/")[0] or "home",
        "lastmod": lastmod,
        "status": status,
        "content_type": ctype,
        "blocked": bool(br),
        "blocked_reason": br,
        "libraries": detect_libraries(text_blob),
        "tags": detect_tags(text_blob, urllib.parse.urlparse(url).path),
        "image": meta.get("og_image") or (images[0]["src"] if images else ""),
        "image_alts": [img["alt"] for img in images if img.get("alt")][:12],
        "sources": sources,
        "links": links[:120],
    }
    return enrich_record(row, raw)


def json_dump(obj: Any, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def load_index(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def tokenize(q: str) -> List[str]:
    return [t.lower() for t in re.findall(r"[a-zA-Z0-9_.+-]+", q) if len(t) > 1]


def utc_now() -> str:
    return dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"


# V2 semantic enrichment: this compensates for low-description sources like
# UIverse, CodePen, Awwwards, Dribbble, etc. by inferring our own searchable
# vocabulary from titles, URLs, code-ish text, image alt text, and optional
# vision captions merged later.
TAXONOMY = {
    "mechanics": {
        "scroll-reveal": ["scroll", "scrolltrigger", "onscroll", "intersectionobserver", "reveal on scroll"],
        "mask-reveal": ["mask", "clip-path", "clippath", "overflow hidden", "wipe", "reveal"],
        "curtain": ["curtain", "drape", "opening", "closing", "veil"],
        "blinds": ["blind", "blinds", "slats", "stripes", "horizontal", "venetian"],
        "shutter": ["shutter", "rollup", "roll-up", "garage door", "storefront", "gate", "grille"],
        "fold": ["fold", "folding", "accordion", "crease", "origami"],
        "parallax": ["parallax", "depth", "layered", "translatez"],
        "drag": ["drag", "draggable", "pointermove", "mouse move", "gesture"],
        "hover-microinteraction": ["hover", ":hover", "mouseenter", "mouseleave"],
        "page-transition": ["page transition", "barba", "swup", "transition"],
        "text-split": ["splittext", "split type", "letter", "chars", "words"],
        "physics": ["physics", "matter", "spring", "inertia", "velocity"],
        "shader-distortion": ["shader", "glsl", "distortion", "displacement", "webgl"],
    },
    "materials": {
        "metal": ["metal", "metallic", "steel", "chrome", "corrugated", "ribbed", "aluminium", "aluminum"],
        "paper": ["paper", "poster", "print", "grain", "folded paper"],
        "glass": ["glass", "frosted", "blur", "translucent", "backdrop-filter"],
        "cloth": ["cloth", "fabric", "silk", "canvas texture", "drape"],
        "neon-light": ["neon", "glow", "emissive", "light trail"],
        "liquid": ["liquid", "fluid", "gooey", "blob", "metaball"],
        "plastic": ["plastic", "rubber", "toy", "3d button"],
    },
    "structures": {
        "hero": ["hero", "landing", "intro", "header"],
        "grid": ["grid", "masonry", "gallery", "tiles"],
        "panel": ["panel", "section", "slide", "drawer"],
        "card": ["card", "pricing", "profile", "product card"],
        "navigation": ["nav", "menu", "navigation", "hamburger"],
        "loader": ["loader", "loading", "preloader", "spinner"],
        "button": ["button", "cta", "submit"],
        "form": ["input", "form", "checkbox", "toggle", "radio"],
    },
    "vibes": {
        "industrial": ["industrial", "metal", "grunge", "garage", "warehouse", "shutter", "corrugated"],
        "brutalist": ["brutalist", "raw", "bold", "poster", "mono", "black"],
        "editorial": ["editorial", "magazine", "typography", "serif", "layout"],
        "luxury": ["luxury", "premium", "elegant", "gold", "minimal"],
        "retro": ["retro", "vintage", "y2k", "90s", "2000", "crt"],
        "cyber": ["cyber", "terminal", "matrix", "hacker", "glitch"],
        "playful": ["playful", "cute", "toy", "cartoon", "bouncy"],
    },
    "code_features": {
        "css-transform": ["transform", "translate", "scale", "rotate", "matrix3d"],
        "css-mask-clip": ["clip-path", "mask-image", "mask", "overflow: hidden"],
        "css-grid": ["display:grid", "display: grid", "grid-template"],
        "css-filter": ["filter:", "backdrop-filter", "blur(", "drop-shadow"],
        "svg-path": ["<svg", "path", "viewbox", "stroke-dasharray", "strokedasharray"],
        "canvas-webgl": ["<canvas", "webgl", "getcontext", "glsl", "shader"],
        "scroll-api": ["scrolltrigger", "intersectionobserver", "scrolltimeline", "onscroll"],
        "pointer-api": ["pointermove", "mousemove", "touchmove", "drag"],
        "animation-timeline": ["@keyframes", "animation:", "transition:", "timeline", "tween"],
    },
}

LOW_METADATA_SOURCES = {"uiverse", "codepen", "dribbble", "behance", "awwwards", "siteinspire", "land-book", "one-page-love", "godly"}


def infer_values(text: str, bucket: str) -> List[str]:
    low = (text or "").lower().replace("_", " ").replace("-", " ")
    found = []
    for label, needles in TAXONOMY.get(bucket, {}).items():
        for needle in needles:
            if needle.lower().replace("-", " ") in low:
                found.append(label)
                break
    return sorted(set(found))


def description_quality(row: Dict[str, Any]) -> str:
    desc = clean_text(str(row.get("description") or ""))
    title = clean_text(str(row.get("title") or ""))
    if not desc:
        return "missing"
    if len(desc) < 45 or desc.lower() in title.lower() or title.lower() in desc.lower():
        return "thin"
    return "usable"


def enrich_record(row: Dict[str, Any], raw: str = "") -> Dict[str, Any]:
    """Add self-authored search metadata without relying on source descriptions."""
    visual = row.get("visual") or {}
    caption = " ".join(str(visual.get(k, "")) for k in ("caption", "notes", "palette", "composition"))
    text = " ".join([
        str(row.get("source") or ""), str(row.get("kind") or ""), str(row.get("url") or ""),
        str(row.get("title") or ""), str(row.get("description") or ""), str(row.get("category") or ""),
        " ".join(row.get("tags") or []), " ".join(row.get("libraries") or []),
        " ".join(row.get("image_alts") or []), caption, raw[:8000],
    ])
    row["description_quality"] = description_quality(row)
    row["mechanics"] = sorted(set(row.get("mechanics") or []) | set(infer_values(text, "mechanics")))
    row["materials"] = sorted(set(row.get("materials") or []) | set(infer_values(text, "materials")))
    row["structures"] = sorted(set(row.get("structures") or []) | set(infer_values(text, "structures")))
    row["vibes"] = sorted(set(row.get("vibes") or []) | set(infer_values(text, "vibes")))
    row["code_features"] = sorted(set(row.get("code_features") or []) | set(infer_values(text, "code_features")))
    # Promote inferred mechanics/structures into broad tags for backward-compatible search.
    promoted = set(row.get("tags") or []) | set(row["mechanics"]) | set(row["structures"])
    row["tags"] = sorted(promoted)
    row["needs_visual_caption"] = (
        row.get("source") in LOW_METADATA_SOURCES
        or row["description_quality"] in ("missing", "thin")
    ) and not visual.get("caption")
    row["search_terms"] = sorted(set(
        list(row.get("tags") or []) + list(row.get("libraries") or []) +
        row["mechanics"] + row["materials"] + row["structures"] + row["vibes"] + row["code_features"]
    ))
    return row
