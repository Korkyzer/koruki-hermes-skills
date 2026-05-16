# Ranking Modes

`search_patterns.py` uses a hybrid score so the best references appear before merely keyword-matching pages.

```txt
final_score = relevance + weighted_quality + weighted_popularity + mode_bonus - penalties
```

## Components

- `relevance`: query match across title, mechanics, materials, structures, vibes, code features, visual captions, etc.
- `quality`: source trust, item-specific record over catalogue page, real CodePen/GitHub/demo link, usable description, image/visual availability.
- `popularity`: optional `views`, `likes`, `favorites`, `forks`, `stars` from a `stats` or `popularity` dict. Log-scaled so old popular items do not dominate.
- `mode_bonus`: mode-specific preference.
- `penalty`: catalogue/seed pages, blocked fetches, missing descriptions without visual captions, generic titles.

## Modes

- `relevant`: balanced default.
- `premium`: favors trusted/curated sources, tactile materials, refined vibes, high-quality snippets.
- `weird`: favors playful, physics, skeuomorphic, liquid, odd, characterful references.
- `production`: favors CSS-only/simple snippets with direct code and low dependency risk.
- `motion`: favors GSAP/Framer/Anime/Matter, scroll/pointer APIs, shader/canvas motion.

## Commands

```bash
python3 scripts/search_patterns.py /tmp/creative-patterns.json "toggle switch slider" --rank-mode premium --limit 12
python3 scripts/search_patterns.py /tmp/creative-patterns.json "toggle switch slider" --rank-mode weird --limit 12
python3 scripts/search_patterns.py /tmp/creative-patterns.json "toggle switch slider" --show-buckets --limit 5
```

Report `score_parts` when auditing why a result ranked high or low.
