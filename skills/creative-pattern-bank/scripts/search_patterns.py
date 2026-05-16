#!/usr/bin/env python3
"""Search/rank a Creative Pattern Bank JSON index."""
from __future__ import annotations
import argparse, json, math, re
from typing import Dict, List, Tuple
from pattern_common import load_index, tokenize

WEIGHTS = {
    "title": 12,
    "description": 5,
    "tags": 8,
    "libraries": 9,
    "mechanics": 13,
    "materials": 10,
    "structures": 7,
    "vibes": 6,
    "code_features": 9,
    "search_terms": 6,
    "visual": 8,
    "category": 4,
    "source": 3,
    "url": 2,
    "image_alts": 2,
}

SOURCE_TRUST = {
    "codrops": 25,
    "codemyui": 18,
    "gsapify": 16,
    "freefrontend": 14,
    "devsnap": 10,
    "uiverse": 8,
    "codepen": 6,
}

GENERIC_TITLE_RE = re.compile(r"^(css|html|js|javascript|animation|button|switch|toggle|untitled|demo|example)\s*\d*$", re.I)

MODE_PROFILE = {
    "relevant": {"relevance": 1.0, "quality": 0.35, "popularity": 0.25},
    "premium": {"relevance": 1.0, "quality": 0.85, "popularity": 0.25, "premium": 1.0},
    "weird": {"relevance": 0.85, "quality": 0.45, "popularity": 0.20, "weird": 1.0},
    "production": {"relevance": 0.95, "quality": 0.75, "popularity": 0.15, "production": 1.0},
    "motion": {"relevance": 1.0, "quality": 0.60, "popularity": 0.20, "motion": 1.0},
}


def field_text(v):
    if isinstance(v, list): return " ".join(map(str, v))
    if isinstance(v, dict): return " ".join(" ".join(map(str, x)) if isinstance(x, list) else str(x) for x in v.values())
    return str(v or "")


def number_from_any(row: Dict, keys: List[str]) -> int:
    for key in keys:
        val = row.get(key)
        if val is None and isinstance(row.get("stats"), dict):
            val = row["stats"].get(key)
        if val is None and isinstance(row.get("popularity"), dict):
            val = row["popularity"].get(key)
        if isinstance(val, (int, float)):
            return int(val)
        if isinstance(val, str):
            m = re.search(r"([0-9][0-9,._ ]*)", val)
            if m:
                try: return int(re.sub(r"[^0-9]", "", m.group(1)))
                except Exception: pass
    return 0


def relevance_score(row: Dict, terms: List[str]) -> int:
    total = 0
    hay_all = json.dumps(row, ensure_ascii=False).lower().replace("-", " ")
    for term in terms:
        t = term.lower().replace("-", " ")
        if t in hay_all:
            total += 1
        for field, weight in WEIGHTS.items():
            if t in field_text(row.get(field)).lower().replace("-", " "):
                total += weight
    return total


def popularity_score(row: Dict) -> int:
    views = number_from_any(row, ["views", "view_count", "plays"])
    likes = number_from_any(row, ["likes", "favorites", "favourites", "hearts", "upvotes"])
    forks = number_from_any(row, ["forks", "remixes"])
    stars = number_from_any(row, ["stars", "stargazers"])
    # Log scale: useful bonus without letting ancient popular-but-ugly items dominate.
    return int(math.log10(views + 1) * 4 + math.log10(likes + 1) * 8 + math.log10(forks + 1) * 5 + math.log10(stars + 1) * 8)


def quality_score(row: Dict) -> int:
    srcs = row.get("sources") or {}
    title = (row.get("title") or "").strip()
    desc_quality = row.get("description_quality") or "usable"
    score = SOURCE_TRUST.get(row.get("source"), 4)
    if row.get("kind") in ("snippet", "pattern", "article"):
        score += 10
    if row.get("kind") in ("page", "seed"):
        score -= 14
    if srcs.get("codepen") or srcs.get("github") or srcs.get("demo"):
        score += 15
    if row.get("image") or row.get("visual"):
        score += 5
    if desc_quality == "usable":
        score += 6
    elif desc_quality == "thin":
        score -= 3
    else:
        score -= 7
    if row.get("blocked") is True:
        score -= 12
    if row.get("needs_visual_caption"):
        score -= 4
    if GENERIC_TITLE_RE.match(title):
        score -= 6
    return score


def mode_bonus(row: Dict, mode: str) -> int:
    libs = set(row.get("libraries") or [])
    mech = set(row.get("mechanics") or [])
    mats = set(row.get("materials") or [])
    vibes = set(row.get("vibes") or [])
    code = set(row.get("code_features") or [])
    tags = set(row.get("tags") or [])
    srcs = row.get("sources") or {}
    bonus = 0
    if mode == "premium":
        if {"glass", "metal", "paper", "neon-light"} & mats: bonus += 8
        if {"industrial", "brutalist", "editorial", "luxury"} & vibes: bonus += 8
        if {"hover-microinteraction", "mask-reveal", "text-split"} & mech: bonus += 5
        if row.get("source") in ("codrops", "codemyui", "freefrontend"): bonus += 6
    elif mode == "weird":
        weird_terms = {"physics", "liquid", "gooey", "parallax", "shader-distortion", "fold", "drag", "playful"}
        bonus += 12 * len((mech | mats | vibes | tags) & weird_terms)
        if "matter.js" in libs or "canvas" in libs: bonus += 8
        title_desc = f"{row.get('title','')} {row.get('description','')}".lower()
        if re.search(r"egg|seesaw|bulb|star|rabbit|skeuo|mechanical|futuristic", title_desc): bonus += 14
    elif mode == "production":
        if srcs.get("codepen") or srcs.get("github"): bonus += 10
        if "css-only" in libs: bonus += 12
        if not ({"gsap", "three.js", "matter.js", "react", "vue", "jquery"} & libs): bonus += 6
        if row.get("blocked") is not True: bonus += 6
        if row.get("kind") == "snippet": bonus += 8
    elif mode == "motion":
        if {"gsap", "framer-motion", "anime.js", "matter.js"} & libs: bonus += 14
        if {"scroll-reveal", "drag", "physics", "shader-distortion", "page-transition", "fold"} & mech: bonus += 10
        if {"scroll-api", "pointer-api", "animation-timeline", "canvas-webgl"} & code: bonus += 8
    return bonus


def penalties(row: Dict) -> int:
    p = 0
    url = row.get("url", "")
    if row.get("kind") in ("page", "seed") and "#" not in url:
        p += 18
    if row.get("blocked") is True:
        p += 8
    if row.get("description_quality") == "missing" and not row.get("visual"):
        p += 5
    return p


def score_parts(row: Dict, terms: List[str], mode: str = "relevant") -> Dict[str, int]:
    rel = relevance_score(row, terms)
    q = quality_score(row)
    pop = popularity_score(row)
    mb = mode_bonus(row, mode)
    pen = penalties(row)
    profile = MODE_PROFILE.get(mode, MODE_PROFILE["relevant"])
    final = int(rel * profile.get("relevance", 1.0) + q * profile.get("quality", 0.35) + pop * profile.get("popularity", 0.25) + mb - pen)
    return {"score": final, "relevance": rel, "quality": q, "popularity": pop, "mode_bonus": mb, "penalty": pen}


def score(row: Dict, terms: List[str]) -> int:
    """Backward-compatible score used by adapt_pattern_brief."""
    return score_parts(row, terms, "relevant")["score"]


def result_key(row: Dict) -> str:
    srcs = row.get("sources") or {}
    for key in ("codepen", "github", "demo"):
        vals = srcs.get(key) or []
        if vals:
            return f"{key}:{vals[0]}".lower()
    title = re.sub(r"\s+", " ", (row.get("title") or "").strip().lower())
    if title:
        return f"title:{title}"
    return f"url:{row.get('url','')}".lower()


def rank(rows: List[Dict], terms: List[str], mode: str, limit: int) -> List[Dict]:
    ranked: List[Tuple[int, Dict]] = []
    for row in rows:
        parts = score_parts(row, terms, mode)
        if parts["relevance"] > 0 or parts["score"] > 0:
            ranked.append((parts["score"], {"score_parts": parts, **row}))
    ranked.sort(key=lambda x: x[0], reverse=True)
    unique = []
    seen = set()
    for s, row in ranked:
        k = result_key(row)
        if k in seen:
            continue
        seen.add(k)
        unique.append({"score": s, **row})
        if len(unique) >= limit:
            break
    return unique


def print_results(results: List[Dict], args, idx):
    print(f"Query: {args.query}")
    print(f"Rank mode: {args.rank_mode}")
    print(f"Index: {idx.get('total_count', len(idx.get('pages', [])))} records | sources: {', '.join(idx.get('sources', []))}")
    print()
    for i, item in enumerate(results, 1):
        libs = ", ".join(item.get("libraries") or []) or "-"
        tags = ", ".join(item.get("tags") or []) or "-"
        mech = ", ".join(item.get("mechanics") or []) or "-"
        mat = ", ".join((item.get("materials") or []) + (item.get("vibes") or [])) or "-"
        parts = item.get("score_parts") or {}
        print(f"{i}. [{item['score']}] {item.get('title')}")
        print(f"   source: {item.get('source')} / {item.get('kind')} | libs: {libs}")
        print(f"   parts: rel {parts.get('relevance', '-')}, quality {parts.get('quality', '-')}, pop {parts.get('popularity', '-')}, mode {parts.get('mode_bonus', '-')}, penalty {parts.get('penalty', '-')}")
        print(f"   mechanics: {mech} | material/vibe: {mat}")
        print(f"   tags: {tags}")
        print(f"   url: {item.get('url')}")
        srcs = item.get("sources") or {}
        if srcs:
            flat = []
            for k, vals in srcs.items():
                for v in vals[:2]: flat.append(f"{k}: {v}")
            print(f"   code: {' | '.join(flat[:4])}")
        desc = (item.get("description") or "").strip()
        if desc:
            print(f"   {desc[:220]}")
        if item.get("blocked"):
            print(f"   blocked: {item.get('blocked_reason')}")
        print()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("index")
    ap.add_argument("query")
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--source", default="", help="Filter by source name")
    ap.add_argument("--rank-mode", choices=sorted(MODE_PROFILE), default="relevant")
    ap.add_argument("--show-buckets", action="store_true", help="Show best overall + premium/weird/production/motion buckets")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    idx = load_index(args.index)
    terms = tokenize(args.query)
    rows = idx.get("pages", [])
    if args.source:
        rows = [r for r in rows if r.get("source") == args.source]

    if args.show_buckets:
        buckets = {mode: rank(rows, terms, mode, args.limit) for mode in ["relevant", "premium", "weird", "production", "motion"]}
        if args.json:
            print(json.dumps(buckets, ensure_ascii=False, indent=2))
            return
        for mode, results in buckets.items():
            print(f"\n## {mode.upper()}\n")
            print_results(results, argparse.Namespace(query=args.query, rank_mode=mode), idx)
        return

    results = rank(rows, terms, args.rank_mode, args.limit)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return
    print_results(results, args, idx)

if __name__ == "__main__":
    main()
