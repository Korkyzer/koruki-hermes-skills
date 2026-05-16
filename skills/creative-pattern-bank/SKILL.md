---
name: creative-pattern-bank
description: Build and query a multi-source creative frontend pattern bank from FreeFrontend, CodeMyUI, DevSnap, Codrops/Tympanus, GSAPify, Uiverse seeds, and direct CodePen/GitHub links. Use when Arthur wants frontend inspiration, interaction patterns, GSAP/Three.js/CSS examples, CodePen-style source discovery, scroll/hero/menu/cursor/loader effects, or adaptation briefs for custom web prototypes.
---

# Creative Pattern Bank

Use this skill to find and adapt frontend interaction patterns across multiple curated sources instead of searching each site manually.

## Core workflow

1. Build a local index. Start small when speed matters:
   ```bash
   python3 scripts/build_pattern_index.py --sources freefrontend,codemyui,devsnap,codrops,gsapify --max-pages 80 --out /tmp/creative-patterns.json
   ```
   For a focused query, use `--query-hints` to bias source selection:
   ```bash
   python3 scripts/build_pattern_index.py --query-hints "metal shutter scroll gsap blinds" --max-pages 80 --out /tmp/creative-patterns.json
   ```

2. Search the index:
   ```bash
   python3 scripts/search_patterns.py /tmp/creative-patterns.json "metal shutter scroll reveal gsap" --limit 12
   ```

3. Inspect a result/source URL:
   ```bash
   python3 scripts/inspect_source.py "https://codepen.io/anon/pen/wvMgXxN"
   ```
   For CodePen, the inspector tries the bundled `resolve_codepen_source.py` first via `cdpn.io` debug/fullpage endpoints.

4. Generate an adaptation brief:
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

## Practical notes

- Treat indexes as disposable generated artifacts. Do not commit multi-MB generated JSON into public taps; rebuild locally.
- Prefer source links (CodePen/GitHub/demo repo) over copying from aggregator pages.
- Preserve attribution links in final prototypes/reports.
- Use inspiration as reference; rewrite/adapt before production.
- If a source blocks datacenter fetches, mark records as `blocked` and fall back to web search, browser automation, or a direct source URL.

## Output standard

When reporting patterns to Arthur, include source, direct URL, code/source URL if found, effect type, libraries, why relevant, and production-safety caveat.
