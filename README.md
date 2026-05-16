# Koruki Hermes Skills

Shared Hermes skills used by Koruki / Asa Studio.

This repo is a Hermes skill tap: install skills directly from GitHub, keep generated indexes local, and use the scripts inside each skill as small agent-facing tools.

## Quick install

```bash
hermes skills tap add Korkyzer/koruki-hermes-skills
hermes skills inspect Korkyzer/koruki-hermes-skills/skills/creative-pattern-bank
hermes skills install Korkyzer/koruki-hermes-skills/skills/creative-pattern-bank
```

Legacy FreeFrontend-only skill:

```bash
hermes skills install Korkyzer/koruki-hermes-skills/skills/freefrontend-pattern-bank
```

Note: on the current Hermes build, direct `inspect`/`install` works reliably for custom taps; `hermes skills search` may not surface custom tap results yet.

## Included skills

### `creative-pattern-bank`

A multi-source creative frontend pattern bank for finding interaction/design references and adapting them into prototypes.

Sources currently supported:

- **FreeFrontend** — broad CSS/JS snippet catalogue, strong for components and CodePen links.
- **CodeMyUI** — curated micro-interactions, buttons, SVG, GSAP, scroll effects.
- **DevSnap** — roundup pages for CSS/JS/Three.js/animation examples.
- **Codrops / Tympanus** — high-quality creative coding tutorials, WebGL, GSAP, R3F, shader, transition experiments.
- **GSAPify** — production-oriented GSAP examples and guides.
- **Uiverse seeds** — component inspiration; low metadata, useful with visual/caption enrichment.
- **Direct CodePen/GitHub source inspection** — tries to resolve CodePen source through `cdpn.io` when CodePen blocks simple fetches.

Best for:

- finding frontend inspiration without manually searching every site;
- ranking “best” options first instead of raw keyword matches;
- finding source/code links for CodePen/GitHub demos;
- building quick adaptation briefs for prototypes;
- searching weakly-described visual libraries like Uiverse/CodePen by inferred mechanics/materials/vibes;
- exploring Codrops/Tympanus creative-coding references like WebGL, R3F, shader transitions, HTML-in-Canvas, carousels, scroll effects.

### `freefrontend-pattern-bank`

Legacy FreeFrontend-only pattern bank. Kept for compatibility. Prefer `creative-pattern-bank` for new work.

## Creative Pattern Bank — usage

Run commands from the skill directory after installation:

```bash
cd ~/.hermes/skills/creative-pattern-bank
# or wherever Hermes installed it:
# hermes skills list | grep creative-pattern-bank
```

If you are running directly from this repo:

```bash
cd skills/creative-pattern-bank
```

### 1. Build a local index

The repo intentionally does **not** commit generated multi-MB JSON indexes because community skill scans can block oversized bundles. Build disposable local indexes instead.

Small focused index:

```bash
python3 scripts/build_pattern_index.py \
  --sources freefrontend,codemyui,codrops,gsapify \
  --query-hints "toggle switch slider button left right animation" \
  --per-source 8 \
  --out /tmp/creative-patterns.json
```

Broader index:

```bash
python3 scripts/build_pattern_index.py \
  --sources freefrontend,codemyui,devsnap,codrops,gsapify,uiverse \
  --max-pages 180 \
  --out /tmp/creative-patterns.json
```

Focused Codrops/Tympanus search:

```bash
python3 scripts/build_pattern_index.py \
  --sources codrops \
  --query-hints "html in canvas react three fiber webgl shader transition" \
  --per-source 12 \
  --out /tmp/codrops-patterns.json
```

### 2. Search with ranking modes

Default relevance search:

```bash
python3 scripts/search_patterns.py /tmp/creative-patterns.json \
  "toggle switch slider checkbox animated left right button" \
  --limit 12
```

Taste-filtered modes:

```bash
# Polished / high-taste refs first
python3 scripts/search_patterns.py /tmp/creative-patterns.json "toggle switch slider" \
  --rank-mode premium --limit 12

# Weird / playful / skeuomorphic / physics-heavy refs
python3 scripts/search_patterns.py /tmp/creative-patterns.json "toggle switch slider" \
  --rank-mode weird --limit 12

# Safer to ship: CSS-only/simple/direct source
python3 scripts/search_patterns.py /tmp/creative-patterns.json "toggle switch slider" \
  --rank-mode production --limit 12

# Motion-heavy: GSAP/Framer/Matter/scroll/pointer/shader
python3 scripts/search_patterns.py /tmp/creative-patterns.json "page transition canvas shader" \
  --rank-mode motion --limit 12
```

Bucket view for curation:

```bash
python3 scripts/search_patterns.py /tmp/creative-patterns.json "toggle switch slider" \
  --show-buckets --limit 5
```

Ranking combines:

- keyword relevance;
- inferred `mechanics`, `materials`, `structures`, `vibes`, `code_features`;
- source trust (`codrops` > `codemyui` > `gsapify` > `freefrontend` > etc.);
- code/source availability (`CodePen`, `GitHub`, demo links);
- description quality;
- optional popularity stats if a connector/source exposes `views`, `likes`, `favorites`, `forks`, or `stars`;
- penalties for catalogue pages, blocked fetches, generic titles, and missing descriptions.

More detail: [`skills/creative-pattern-bank/references/ranking.md`](skills/creative-pattern-bank/references/ranking.md).

### 3. Inspect a source/result

Use this when a result has a CodePen/GitHub/demo URL and you want the actual code/source links.

```bash
python3 scripts/inspect_source.py "https://codepen.io/anon/pen/KwNpBPo"
python3 scripts/inspect_source.py "https://tympanus.net/codrops/2026/05/13/exploring-the-html-in-canvas-proposal/"
```

For CodePen, the inspector first tries the bundled `resolve_codepen_source.py` helper via `cdpn.io` debug/fullpage endpoints. This often bypasses simple Cloudflare blocks for public pens.

### 4. Enrich low-description visual sources

Some sources look good but barely describe their components (`Uiverse`, raw `CodePen`, Dribbble/Behance-style sources, etc.). The skill adds its own taxonomy, but you can improve matching with screenshot/vision captions.

Visual annotations JSONL:

```jsonl
{"url":"https://uiverse.io/example","caption":"dark metallic ribbed toggle with horizontal slats and lime glow","palette":"black lime","composition":"horizontal pill slider"}
```

Merge captions back into an index:

```bash
python3 scripts/enrich_pattern_index.py /tmp/creative-patterns.json \
  --visual-annotations /tmp/pattern-visual-captions.jsonl \
  --out /tmp/creative-patterns-enriched.json
```

Then search the enriched index:

```bash
python3 scripts/search_patterns.py /tmp/creative-patterns-enriched.json \
  "industrial metal shutter horizontal slats" \
  --rank-mode premium
```

More detail: [`skills/creative-pattern-bank/references/low-metadata-visual-sources.md`](skills/creative-pattern-bank/references/low-metadata-visual-sources.md).

### 5. Generate an adaptation brief

Use this when you want the agent to turn references into implementation direction.

```bash
python3 scripts/adapt_pattern_brief.py /tmp/creative-patterns.json \
  "metal shutter scroll reveal" \
  --project "Koruki intro" \
  --limit 6
```

The brief includes source URLs, detected libraries, tags/mechanics/materials, caveats, and implementation direction.

## Example searches

### Toggle buttons

```bash
python3 scripts/build_pattern_index.py \
  --sources freefrontend,codemyui,devsnap,uiverse \
  --query-hints "toggle switch slider button on off checkbox animated left right" \
  --per-source 8 \
  --out /tmp/toggle-patterns.json

python3 scripts/search_patterns.py /tmp/toggle-patterns.json \
  "toggle switch slider checkbox animated left right button" \
  --show-buckets --limit 5
```

Good result types observed:

- mechanical / neumorphic switches;
- 3D pill sliders;
- seesaw-style toggles;
- playful skeuomorphic toggles;
- CSS-only production-safe switches.

### Metal shutter / storefront reveal

```bash
python3 scripts/build_pattern_index.py \
  --sources freefrontend,codemyui,codrops,gsapify \
  --query-hints "metal shutter blinds curtain rollup scroll reveal mask" \
  --per-source 10 \
  --out /tmp/shutter-patterns.json

python3 scripts/search_patterns.py /tmp/shutter-patterns.json \
  "industrial metal shutter blinds curtain scroll reveal mask" \
  --rank-mode motion --limit 12
```

More detail: [`skills/creative-pattern-bank/references/koruki-metal-shutter-pattern-search.md`](skills/creative-pattern-bank/references/koruki-metal-shutter-pattern-search.md).

### HTML-in-Canvas / Codrops R&D

```bash
python3 scripts/build_pattern_index.py \
  --sources codrops \
  --query-hints "html in canvas proposal react three fiber webgl page curl vanish input" \
  --per-source 12 \
  --out /tmp/html-canvas-patterns.json

python3 scripts/search_patterns.py /tmp/html-canvas-patterns.json \
  "html in canvas react three fiber webgl transition" \
  --rank-mode motion --limit 12
```

Useful references:

- Codrops article: <https://tympanus.net/codrops/2026/05/13/exploring-the-html-in-canvas-proposal/>
- Demo: <https://html-in-canvas.vercel.app/>
- Code: <https://github.com/motiontx/html-in-canvas>
- WICG proposal: <https://github.com/WICG/html-in-canvas>

Caveat: HTML-in-Canvas is experimental and currently requires Chromium/Chrome Canary flag `chrome://flags/#canvas-draw-element`.

## Output expectations for agents

When an agent uses this skill, it should **not** dump raw search output. It should return a curated shortlist:

- best overall;
- premium/polished;
- weird/fun;
- production-safe;
- motion/R&D if relevant.

For each item include:

- source name;
- direct URL;
- code/source URL if found;
- effect type;
- detected libraries;
- why it ranked / why it is useful;
- production caveat.

## Community directory

Yasu maintains a broader community directory here:

- <https://github.com/Yasuui/hermes-community-skills>
- Web view: <https://hermes-community-skills.vercel.app/>

This Koruki tap is a working source repo. To share a skill with the broader Hermes community, add it here first if needed, then submit/port the final skill into the community directory following their template and contribution rules.

Suggested Discord blurb lives in [`docs/discord-share-creative-pattern-bank.md`](docs/discord-share-creative-pattern-bank.md).

## Repo layout

Hermes taps currently scan the immediate directories under `skills/`, so each skill lives at:

```text
skills/<skill-name>/SKILL.md
```

Supporting files stay inside the skill directory under `scripts/`, `references/`, `templates/`, or `assets/`.

## Maintenance notes

- Keep generated indexes/caches out of git.
- Commit scripts/docs/reference files only.
- Run `python3 -m py_compile skills/creative-pattern-bank/scripts/*.py` before pushing script changes.
- Verify installability in a temporary `HERMES_HOME` before announcing a release:

```bash
tmp=$(mktemp -d /tmp/hermes-skill-XXXXXX)
printf 'y\n' | HERMES_HOME="$tmp" hermes skills install Korkyzer/koruki-hermes-skills/skills/creative-pattern-bank
```
