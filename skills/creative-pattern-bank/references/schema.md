# Creative Pattern Bank Index Schema

Top-level JSON:
- `schema`: `creative-pattern-bank/v1`
- `generated_at`: ISO timestamp
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
- `tags`: effect tags (`scroll`, `hero`, `menu`, `cursor`, `loader`, etc.)
- `image`, `image_alts`
- `sources`: dict of source links, e.g. `{ "codepen": [...], "github": [...] }`
- `parent_url`, `author`, `license`, `rank_hint` optional
