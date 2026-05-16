# Discord share: Creative Pattern Bank

Copy/paste draft for the Hermes Discord:

````md
Hey folks — I’ve been building a Hermes skill for frontend/creative-coding inspiration:

https://github.com/Korkyzer/koruki-hermes-skills

Skill: `creative-pattern-bank`

It builds a local searchable index across sources like FreeFrontend, CodeMyUI, DevSnap, Codrops/Tympanus, GSAPify, Uiverse seeds, and direct CodePen/GitHub links.

The main idea: don’t just keyword-search titles/descriptions. A lot of good inspiration sites have weak metadata, so the skill enriches each result with inferred fields like:

- mechanics: `scroll-reveal`, `mask-reveal`, `fold`, `drag`, `shutter`, `blinds`, etc.
- materials: `metal`, `glass`, `paper`, `neon-light`, etc.
- structures: `hero`, `grid`, `panel`, `card`, `navigation`, etc.
- vibes: `industrial`, `brutalist`, `editorial`, `retro`, `playful`, etc.
- code features: `css-mask-clip`, `svg-path`, `canvas-webgl`, `scroll-api`, etc.

It also has ranking modes so agents can return curated shortlists instead of raw search dumps:

```bash
python3 scripts/search_patterns.py /tmp/creative-patterns.json "toggle switch slider" --rank-mode premium --limit 12
python3 scripts/search_patterns.py /tmp/creative-patterns.json "toggle switch slider" --show-buckets --limit 5
```

Modes: `relevant`, `premium`, `weird`, `production`, `motion`.

Example use cases:

- find polished toggle/button references;
- find weird/fun skeuomorphic interactions;
- find production-safe CSS-only snippets;
- search Codrops/Tympanus for WebGL/R3F/shader/page-transition ideas;
- inspect CodePen/GitHub source links;
- generate adaptation briefs for prototypes.

Install:

```bash
hermes skills tap add Korkyzer/koruki-hermes-skills
hermes skills install Korkyzer/koruki-hermes-skills/skills/creative-pattern-bank
```

I kept generated JSON indexes out of the repo so the community scan stays light/safe; you rebuild indexes locally with `build_pattern_index.py`.
````

Shorter version:

````md
I made a Hermes skill tap for frontend/creative-coding pattern search:
https://github.com/Korkyzer/koruki-hermes-skills

`creative-pattern-bank` indexes FreeFrontend, CodeMyUI, DevSnap, Codrops/Tympanus, GSAPify, Uiverse seeds, and CodePen/GitHub links.

It enriches weakly-described visual sources with inferred mechanics/materials/vibes/code features, then ranks results with modes like `premium`, `weird`, `production`, and `motion`.

Install:
```bash
hermes skills tap add Korkyzer/koruki-hermes-skills
hermes skills install Korkyzer/koruki-hermes-skills/skills/creative-pattern-bank
```
````
