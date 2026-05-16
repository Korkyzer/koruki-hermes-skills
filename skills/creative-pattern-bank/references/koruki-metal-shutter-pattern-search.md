# Koruki metal-shutter / storefront reveal pattern notes

Use these notes when Arthur asks for a site opener that feels like a real shop/storefront grille, metal shutter, curtain, blind, gate, or roll-up door.

## Intent

Arthur preferred an interactive HTML/CSS/JS or Three.js opener over a pre-rendered video when feasible. The core appeal is not just the image; it is the physical interaction: a branded metal storefront shutter opens at launch or as the user scrolls.

## Best search queries

Use `creative-pattern-bank` with query hints around the physical mechanism, not only the visual noun:

```bash
python3 scripts/build_pattern_index.py \
  --sources freefrontend,codemyui,devsnap,codrops,gsapify \
  --query-hints "storefront shutter metal roll up door scroll reveal blinds curtain gate gsap three.js" \
  --max-pages 80 \
  --out /tmp/creative-patterns.json

python3 scripts/search_patterns.py /tmp/creative-patterns.json \
  "storefront shutter roll-up door scroll reveal blinds curtain gsap" \
  --limit 15
```

Search terms that worked conceptually:
- `scroll shutter blinds gsap`
- `curtain reveal gsap`
- `venetian blinds transition`
- `garage door overlay scroll`
- `roll up door svg animation`
- `folding panels webgl three.js`

## Adaptation pattern

For a production prototype, avoid starting with video unless the interaction does not need to respond to scroll/user input.

Recommended architecture:
1. Procedural shutter in DOM/SVG: 32–48 horizontal slats, corrugated gradients/noise, logo/typography stamped across slats.
2. Scroll/source-of-truth progress: `0 = closed`, `1 = open`; support launch autoplay and scroll-linked bidirectional control.
3. Physical read: slats compress into a top roll/housing; do not just translate a flat image upward.
4. Deterministic imperfections: small friction/hiccup bands, micro tremor tied to velocity, no random jitter.
5. `prefers-reduced-motion`: static open or instant reveal, no tremor/sound.

Three.js is justified if the concept needs real depth, specular corrugated metal, lighting, or a cylindrical roll. For a first V1, DOM/CSS/SVG is usually faster, more debuggable, and easier to integrate into a normal homepage.

## Video fallback

Seedance/Kling-style video is useful for:
- a cinematic non-interactive hero loop;
- mood/reference generation;
- social teaser assets.

It is weaker for:
- scroll bidirectionality;
- responsive layouts;
- accessibility/reduced motion;
- deterministic brand/logo alignment.

If using video, generate it as an enhancement behind an HTML control layer, not as the only navigation gate.
