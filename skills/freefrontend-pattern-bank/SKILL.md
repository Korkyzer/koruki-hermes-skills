---
name: freefrontend-pattern-bank
description: Build and query a local FreeFrontend pattern bank from sitemap, Pagefind/static pages, CodePen/GitHub links, and extracted metadata. Use when Arthur wants frontend inspiration, CodePen/FreeFrontend resources, interaction-pattern research, prototype references, or adapting existing web animation snippets into standalone/project-ready implementations.
---

# FreeFrontend Pattern Bank

Use this skill to turn FreeFrontend from a browsing site into an agent-usable pattern database.

## Core workflow

1. **Use the bundled V1 index first** unless freshness matters:
   ```bash
   python3 scripts/search_freefrontend.py references/freefrontend-index-v1.json "gsap scroll blinds shutter" --limit 12
   ```
   Current bundled index: ~2k records from 80 FreeFrontend listing pages, including individual snippet cards.

2. **Build/update the index** when you need fresher or broader coverage:
   ```bash
   python3 scripts/build_freefrontend_index.py --max-pages 250 --out /tmp/freefrontend-patterns.json
   ```
   For a faster pass:
   ```bash
   python3 scripts/build_freefrontend_index.py --max-pages 80 --out /tmp/freefrontend-patterns.json
   ```

3. **Search a custom index**:
   ```bash
   python3 scripts/search_freefrontend.py /tmp/freefrontend-patterns.json "gsap scroll blinds shutter" --limit 12
   ```

4. **Inspect one result/source**:
   ```bash
   python3 scripts/inspect_pattern_source.py "https://codepen.io/kjohnson/pen/wxvKp"
   ```

5. **Resolve CodePen source without codepen.io fetch when possible**:
   ```bash
   python3 scripts/resolve_codepen_source.py "https://codepen.io/anon/pen/wvMgXxN" --outdir /tmp/codepen-wvMgXxN
   ```
   This tries `https://cdpn.io/<user>/debug/<slug>` and `fullpage`, which often remain accessible even when `codepen.io` API/oEmbed returns Cloudflare 403.

6. **Generate an adaptation brief** for a project:
   ```bash
   python3 scripts/adapt_pattern_brief.py /tmp/freefrontend-patterns.json "metal shutter scroll reveal" --project "Koruki Corp intro" --limit 5
   ```

## What the scripts do

- `build_freefrontend_index.py` reads `https://freefrontend.com/sitemap.xml`, fetches listing pages, extracts both page-level metadata and individual `.snippet-card` records, then writes JSON.
- `search_freefrontend.py` ranks patterns locally with weighted term matching over title, description, path, libraries, categories, image alt text, and source links; it deduplicates repeated snippets that appear in multiple categories.
- `inspect_pattern_source.py` resolves CodePen/GitHub/FreeFrontend URLs into quick metadata. For CodePen, it checks oEmbed but also calls the V1.1 cdpn resolver so a Cloudflare-blocked oEmbed can still be source-resolved.
- `resolve_codepen_source.py` extracts public CodePen HTML/CSS/JS via `cdpn.io` debug/fullpage endpoints and can write `source.json`, `index.fragment.html`, `styles.css`, `script.js`, and a runnable `index.html`.
- `adapt_pattern_brief.py` turns top matches into a concise implementation brief for an agent.

## Practical notes

- FreeFrontend has no clean public API. Treat sitemap + static HTML + Pagefind assets as a pseudo-API.
- Some `/code/...` pages are protected by an anti-bot interstitial. Mark them as `blocked: true` and fall back to source links found from category/home pages or browser automation.
- CodePen's `codepen.io` API/oEmbed frequently returns Cloudflare 403 from datacenter IPs. Before using browser automation, run `resolve_codepen_source.py`; many public pens expose source through `cdpn.io/<user>/debug/<slug>` or `fullpage` without needing a residential IP.
- If both `cdpn.io` variants fail, the resolver returns `needs_browser: true`; then use a real browser/profile (Hermes browser tools, Mac Chrome, or user-assisted export) rather than retrying server fetch loops.
- Prefer CodePen/GitHub source links over copying from FreeFrontend pages.
- Always preserve attribution links in final prototypes or research reports.
- For production code, use the resource as reference; rewrite/adapt instead of blindly pasting unknown snippet code.

## Good search queries

- `gsap scroll reveal slats blinds`
- `three.js shader parallax hero`
- `liquid gooey radio interaction`
- `cursor trail svg morph`
- `menu transition off canvas gsap`
- `product viewer css only`

## Output standard

When reporting results to Arthur, include:
- direct FreeFrontend URL
- source URL if found (CodePen/GitHub)
- effect type and required libraries
- why it is relevant
- whether it is production-safe or only inspiration
