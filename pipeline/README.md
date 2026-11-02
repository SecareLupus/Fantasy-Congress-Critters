# Data Pipeline

Downloads official congressional data, normalizes it into the event ontology ([Design-Data §10.3](../Design-Data.md)), and loads it into Postgres for the scoring engine.

## Setup

From the repo root, start Postgres:

```bash
docker compose up -d db
```

Then, from `pipeline/`:

```bash
uv sync
uv run critters download --congress 118
uv run critters load --congress 118
uv run pytest
```

Raw files land in `data/raw/` (gitignored). `load` is idempotent: each bill and its events are replaced on reload. Set `DATABASE_URL` to point somewhere other than the local container.

## Sources

| Data | Source |
| --- | --- |
| Bills, actions, co-sponsors, committee activity | GovInfo `BILLSTATUS` bulk XML |
| Members, terms, ID crosswalk, committee names | `unitedstates/congress-legislators` |

## Tables

- `bills`, `bill_cosponsors`, `bill_committee_activities`, `bill_actions`: source records, lightly structured.
- `events`: normalized ontology events, the only input the scoring engine reads. Events are facts about a bill; who earns credit is decided by the engine.
- `critters`, `critter_terms`, `committees`: reference data.

## Normalization notes

- Committee referral, hearings, markup, reporting, and discharge come from structured committee activity, not text.
- Passage and presidential actions come from Library of Congress action codes. Codes are read per source: `E30000` means "Signed" from the Library of Congress but "Vetoed" from the House floor feed.
- Senate floor and committee actions have no codes and are matched by text (cloture, motion to proceed, ordered reported, hearings).
- The same step often appears in several feeds; events are deduplicated on type, date, chamber, committee, and member.
- Hearings recorded as held before the bill was introduced are skipped.
