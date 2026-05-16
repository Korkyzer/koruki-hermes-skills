# Koruki Hermes Skills

Shared Hermes skills used by Koruki / Asa Studio.

## Install as a Hermes tap

```bash
hermes skills tap add Korkyzer/koruki-hermes-skills
hermes skills inspect Korkyzer/koruki-hermes-skills/skills/creative-pattern-bank
hermes skills install Korkyzer/koruki-hermes-skills/skills/creative-pattern-bank
```

Legacy FreeFrontend-only skill:

```bash
hermes skills install Korkyzer/koruki-hermes-skills/skills/freefrontend-pattern-bank
```

Note: on the current Hermes build, direct `inspect`/`install` works reliably for custom taps; `skills search` may not surface custom tap results yet.

## Included skills

- `creative-pattern-bank` — multi-source creative frontend pattern bank: FreeFrontend, CodeMyUI, DevSnap, Codrops, GSAPify, Uiverse seeds, CodePen/GitHub source inspection.
- `freefrontend-pattern-bank` — legacy FreeFrontend-only pattern bank with CodePen source inspection helpers.

## Repo layout

Hermes taps currently scan the immediate directories under `skills/`, so each skill lives at:

```text
skills/<skill-name>/SKILL.md
```

Supporting files stay inside the skill directory under `scripts/`, `references/`, `templates/`, or `assets/`.

## Update the FreeFrontend index

The full prebuilt FreeFrontend JSON index is intentionally not committed here: Hermes Hub security scan blocks oversized community skills. After installing/loading the skill, rebuild locally with:

```bash
python ~/.hermes/skills/freefrontend-pattern-bank/scripts/build_freefrontend_index.py --max-pages 80 --out /tmp/freefrontend-patterns.json
```

Then search it:

```bash
python ~/.hermes/skills/freefrontend-pattern-bank/scripts/search_freefrontend.py /tmp/freefrontend-patterns.json "metal shutter scroll reveal"
```

If installed under a category/path, adjust the path accordingly.
