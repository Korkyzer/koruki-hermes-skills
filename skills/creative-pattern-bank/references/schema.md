# Creative Pattern Bank Index Schema

Top-level JSON:
- `schema`: `creative-pattern-bank/v2`
- `generated_at`: ISO timestamp
- `enriched_at`: optional ISO timestamp when re-enriched after build
- `sources`: enabled source names
- `query_hints`: optional hint string
- `pages`: list of pattern records

Record fields:
- `source`: source connector name
- `kind`: `page`, `snippet`, `article`, `pattern`, or `seed`
- `url`: canonical source URL
- `title`, `description`, `category`
- `status`, `content_type`, `blocked`, `blocked_reason`
- `libraries`: detected libraries (`gsap`, `three.js`, `svg`, `css-only`, etc.)
- `tags`: backward-compatible broad effect tags; V2 also promotes inferred mechanics/structures here
- `mechanics`: inferred interaction mechanism (`scroll-reveal`, `mask-reveal`, `curtain`, `blinds`, `shutter`, `fold`, `drag`, etc.)
- `materials`: inferred surface/material (`metal`, `paper`, `glass`, `cloth`, `neon-light`, etc.)
- `structures`: inferred UI structure (`hero`, `grid`, `panel`, `card`, `navigation`, `loader`, etc.)
- `vibes`: inferred visual direction (`industrial`, `brutalist`, `editorial`, `luxury`, `retro`, etc.)
- `code_features`: detected implementation features (`css-mask-clip`, `svg-path`, `canvas-webgl`, `scroll-api`, etc.)
- `description_quality`: `missing`, `thin`, or `usable`
- `needs_visual_caption`: true when the record should be enriched with screenshot/vision caption
- `search_terms`: merged searchable terms from tags/libraries/V2 taxonomy
- `visual`: optional dict from external screenshot/vision captioning (`caption`, `palette`, `composition`, `notes`)
- `stats` / `popularity`: optional dict for extracted popularity (`views`, `likes`, `favorites`, `forks`, `stars`); search ranking uses a log-scale bonus so popularity helps but does not dominate relevance
- `score_parts`: output-only dict from `search_patterns.py` containing `relevance`, `quality`, `popularity`, `mode_bonus`, and `penalty`
- `image`, `image_alts`
- `sources`: dict of source links, e.g. `{ "codepen": [...], "github": [...] }`
- `parent_url`, `author`, `license`, `rank_hint` optional
