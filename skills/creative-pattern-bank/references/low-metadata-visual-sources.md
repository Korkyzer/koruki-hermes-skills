# Low-Metadata Visual Sources

Some inspiration/code sites look useful but expose weak metadata. Do not rely on their native search/descriptions.

## Sources affected

- `uiverse`: component cards, sparse descriptions, often blocked to datacenter fetches.
- `codepen`: huge volume, titles/descriptions are often generic (`CSS Animation`, `Untitled`, etc.).
- `dribbble`, `behance`: strong visual signal, weak implementation metadata.
- `awwwards`, `godly`, `land-book`, `one-page-love`, `siteinspire`, `httpster`: great website references, but interactions are rarely tagged precisely.
- `pinterest`, `are.na`: moodboard-quality visual signal; poor mechanical/code signal.

## V2 indexing strategy

For each record, the bank adds its own vocabulary:

- `mechanics`: `scroll-reveal`, `mask-reveal`, `curtain`, `blinds`, `shutter`, `fold`, `parallax`, `drag`, `shader-distortion`, etc.
- `materials`: `metal`, `paper`, `glass`, `cloth`, `neon-light`, `liquid`, etc.
- `structures`: `hero`, `grid`, `panel`, `card`, `navigation`, `loader`, `button`, `form`.
- `vibes`: `industrial`, `brutalist`, `editorial`, `luxury`, `retro`, `cyber`, `playful`.
- `code_features`: `css-mask-clip`, `svg-path`, `canvas-webgl`, `scroll-api`, `pointer-api`, etc.
- `description_quality`: `missing`, `thin`, or `usable`.
- `needs_visual_caption`: true when the source/description is too weak and screenshot/vision should be used.

## Manual/vision caption merge

When you have screenshots or visual captions from browser/vision tools, merge them back into the index:

```jsonl
{"url":"https://uiverse.io/example","caption":"black metallic ribbed component with lime glow","palette":"black lime","composition":"horizontal slats"}
```

Then run:

```bash
python3 scripts/enrich_pattern_index.py /tmp/creative-patterns.json \
  --visual-annotations /tmp/pattern-visual-captions.jsonl \
  --out /tmp/creative-patterns-enriched.json
```

This lets search queries like `industrial metal shutter blinds scroll reveal` find records even if the original site had no useful description.

## Search phrasing rule

Search for the mechanism, material, and structure together:

```txt
mechanic + material + structure + tech
```

Examples:

- `shutter metal hero scroll gsap`
- `blinds mask reveal horizontal slats css`
- `fold curtain panel transition svg`
- `industrial grid hover cards metal`
