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
| House roll-call votes | House Clerk XML, one file per roll call (`clerk.house.gov/evs/{year}/roll{NNN}.xml`) |
| Senate roll-call votes | Voteview CSVs (`voteview.com/static/data/out/{rollcalls,votes,members}/S{congress}_*.csv`); senate.gov blocks automated downloads |

## Tables

- `bills`, `bill_cosponsors`, `bill_committee_activities`, `bill_actions`: source records, lightly structured.
- `events`: normalized ontology events, the only input the scoring engine reads. Events are facts about a bill; who earns credit is decided by the engine.
- `roll_calls`, `member_votes`: one row per roll call and one per member position. Positions are normalized to `yea`, `nay`, `present`, `not_voting`, or `other` (Speaker elections record a name); the raw text is kept. Votes are not bill events: the scoring engine reads them directly for per-vote points and floor participation.
- `roll_call_actions` (view): bill actions that cite a roll call, from BILLSTATUS, for "what did this vote do".
- `critters`, `critter_terms`, `committees`: reference data.

## Normalization notes

- Committee referral, hearings, markup, reporting, and discharge come from structured committee activity, not text.
- Passage and presidential actions come from Library of Congress action codes. Codes are read per source: `E30000` means "Signed" from the Library of Congress but "Vetoed" from the House floor feed.
- Senate floor and committee actions have no codes and are matched by text (cloture, motion to proceed, ordered reported, hearings).
- The same step often appears in several feeds; events are deduplicated on type, date, chamber, committee, and member.
- Hearings recorded as held before the bill was introduced are skipped.
- A roll call's `bill_id` is the measure named in the chamber's record. Rule votes point at the rule (H.Res), not the bill it governs; use `roll_call_actions` to reach the governed bill.
- Delegates and the Resident Commissioner appear on Committee of the Whole votes (mostly amendments), so those roll calls list up to 441 members. The Clerk gives them state `XX`; it is stored as null.
- Positions are recorded as the Clerk lists them, including one for a member who died before the Congress began (A. Donald McEachin, roll 1 of 2023). Scoring should count only members seated on the vote date (`critter_terms`).
- Amendment roll calls (about 550 in the 118th) are not cited by bill actions; BILLSTATUS links them from amendment records, which are not parsed yet.
- Past the last roll call of a year the Clerk returns 200 with a short error document, not 404; the downloader stops at the first file that isn't a roll call.
- Voteview numbers Senate roll calls across the whole Congress; `roll_number` stores the Senate's own per-session number (`clerk_rollnumber`). Voteview also records the President's position on some votes; it is skipped. Paired and announced positions were not cast and are stored as `not_voting`, with the stated side in `raw_position`.
