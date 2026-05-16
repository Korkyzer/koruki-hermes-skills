---
name: creative-pattern-bank
description: Build and query a multi-source creative frontend pattern bank from FreeFrontend, CodeMyUI, DevSnap, Codrops/Tympanus, GSAPify, Uiverse seeds, and direct CodePen/GitHub links. Use when Arthur wants frontend inspiration, interaction patterns, GSAP/Three.js/CSS examples, CodePen-style source discovery, scroll/hero/menu/cursor/loader effects, or adaptation briefs for custom web prototypes.
---

# Creative Pattern Bank

Use this skill to find and adapt frontend interaction patterns across multiple curated sources instead of searching each site manually.

## Core workflow

1. Build a local V2 index. Start small when speed matters:
   ```bash
   python3 scripts/build_pattern_index.py --sources freefrontend,codemyui,devsnap,codrops,gsapify --max-pages 80 --out /tmp/creative-patterns.json
   ```
   For a focused query, use `--query-hints` to bias source selection:
   ```bash
   python3 scripts/build_pattern_index.py --query-hints "metal shutter scroll gsap blinds" --max-pages 80 --out /tmp/creative-patterns.json
   ```

2. Search/rank the index:
   ```bash
   python3 scripts/search_patterns.py /tmp/creative-patterns.json "metal shutter scroll reveal gsap" --limit 12
   ```
   Search now uses self-authored V2 fields (`mechanics`, `materials`, `structures`, `vibes`, `code_features`) so it still works when the source has weak descriptions.

   Use ranking modes when Arthur wants the best options first:
   ```bash
   python3 scripts/search_patterns.py /tmp/creative-patterns.json "toggle switch slider" --rank-mode premium --limit 12
   python3 scripts/search_patterns.py /tmp/creative-patterns.json "toggle switch slider" --show-buckets --limit 5
   ```
   Modes: `relevant`, `premium`, `weird`, `production`, `motion`. The hybrid rank combines relevance, source trust, code/source availability, description quality, optional popularity stats, and mode-specific bonuses.

3. For low-metadata visual sources, merge screenshot/vision captions when available:
   ```bash
   python3 scripts/enrich_pattern_index.py /tmp/creative-patterns.json \
     --visual-annotations /tmp/pattern-visual-captions.jsonl \
     --out /tmp/creative-patterns-enriched.json
   ```
   See `references/low-metadata-visual-sources.md` for the JSONL format and source caveats.

4. Inspect a result/source URL:
   ```bash
   python3 scripts/inspect_source.py "https://codepen.io/anon/pen/wvMgXxN"
   ```
   For CodePen, the inspector tries the bundled `resolve_codepen_source.py` first via `cdpn.io` debug/fullpage endpoints.

5. Generate an adaptation brief:
   ```bash
   python3 scripts/adapt_pattern_brief.py /tmp/creative-patterns.json "metal shutter scroll reveal" --project "Koruki intro" --limit 6
   ```

## Sources

- `freefrontend`: broad snippet catalogue; best for CSS/JS component breadth.
- `codemyui`: handpicked micro-interactions, GSAP, SVG, scroll effects.
- `devsnap`: broad open-source CodePen/demo roundups, especially CSS and Three.js.
- `codrops`: highest creative quality; tutorials, WebGL, GSAP, case studies, Webzibition.
- `gsapify`: production-ready GSAP recipe pages and examples.
- `uiverse`: component inspiration; currently seed/search-page based because the site blocks simple sitemap fetches.

## V2 low-description handling

For sources like UIverse/CodePen where titles/descriptions are weak, every record is enriched with our own taxonomy:

- `mechanics`: motion/interaction (`shutter`, `blinds`, `mask-reveal`, `scroll-reveal`, `fold`, etc.)
- `materials`: surface feel (`metal`, `paper`, `glass`, `cloth`, `neon-light`, etc.)
- `structures`: UI role (`hero`, `grid`, `panel`, `card`, `navigation`, etc.)
- `vibes`: design direction (`industrial`, `brutalist`, `editorial`, `luxury`, `retro`, etc.)
- `code_features`: implementation clues (`css-mask-clip`, `svg-path`, `canvas-webgl`, `scroll-api`, etc.)

If `needs_visual_caption: true`, treat native metadata as insufficient: grab/describe a screenshot externally and merge captions with `enrich_pattern_index.py`. For UIverse/CodePen-style sources, do not rely on source descriptions alone; search must combine mechanism + material + structure + tech (e.g. `shutter metal hero scroll gsap`) and use the V2 inferred fields first.

## Practical notes

- Treat indexes as disposable generated artifacts. Do not commit multi-MB generated JSON into public taps; rebuild locally.
- For physical storefront/reveal concepts (metal shutter, curtain, blinds, gate, roll-up door), search for the underlying mechanism as well as the object name; see `references/koruki-metal-shutter-pattern-search.md` for query hints and adaptation rules.
- Prefer source links (CodePen/GitHub/demo repo) over copying from aggregator pages.
- Preserve attribution links in final prototypes/reports.
- Use inspiration as reference; rewrite/adapt before production.
- If a source blocks datacenter fetches, mark records as `blocked` and fall back to web search, browser automation, or a direct source URL.

## Output standard

When reporting patterns to Arthur, include source, direct URL, code/source URL if found, effect type, libraries, why relevant, and production-safety caveat.
