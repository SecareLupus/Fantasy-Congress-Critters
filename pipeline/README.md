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
uv run critters score --congress 118   # score with rulesets/default.toml
uv run critters report                 # balance and composition of the latest run
uv run critters price                  # Session Costs for session 2 from the latest run
uv run pytest
```

Raw files land in `data/raw/` (gitignored). `load` is idempotent: each bill and its events are replaced on reload. Set `DATABASE_URL` to point somewhere other than the local container.

## Sources

| Data | Source |
| --- | --- |
| Bills, actions, co-sponsors, committee activity, amendments | GovInfo `BILLSTATUS` bulk XML |
| Members, terms, ID crosswalk, committee names | `unitedstates/congress-legislators` |
| Committee rosters over time | Every commit of `committee-membership-current.yaml` in `congress-legislators` during the Congress |
| House roll-call votes | House Clerk XML, one file per roll call (`clerk.house.gov/evs/{year}/roll{NNN}.xml`) |
| Senate roll-call votes | Voteview CSVs (`voteview.com/static/data/out/{rollcalls,votes,members}/S{congress}_*.csv`); senate.gov blocks automated downloads |
| Candidate receipts (pricing) | FEC all-candidates summary (`fec.gov/files/bulk-downloads/{cycle}/weball{yy}.zip`), the last cycle complete when the session opens |

## Tables

- `bills`, `bill_cosponsors`, `bill_subjects`, `bill_committee_activities`, `bill_actions`: source records, lightly structured. `bill_subjects` holds CRS legislative subject terms.
- `amendments`, `amendment_cosponsors`, `amendment_actions`: floor amendments to each bill, from the same BILLSTATUS file.
- `events`: normalized ontology events, the only input the scoring engine reads. Events are facts about a bill; who earns credit is decided by the engine.
- `committee_memberships`: who held which committee or subcommittee seat and role (`member`, `chair`, `ranking_member`, `vice_chair`, `ex_officio`) over which dates. `end_date` is exclusive. `first_seen`/`last_seen` are the snapshot dates behind each row.
- `roll_calls`, `member_votes`: one row per roll call and one per member position. Positions are normalized to `yea`, `nay`, `present`, `not_voting`, or `other` (Speaker elections record a name); the raw text is kept. Votes are not bill events: the scoring engine reads them directly for per-vote points and floor participation.
- `roll_call_actions` (view): bill and amendment actions that cite a roll call, from BILLSTATUS, for "what did this vote do".
- `critter_leadership`: chamber and party leadership posts (Speaker, floor leaders, whips, conference posts).
- `score_runs`, `score_items`: one run per scoring of a Congress with a ruleset, and one item per point-earning fact: an event credit, a vote, or a position held in a session. Each item records its pillar (power or productivity), category, date, source (bill, amendment, vote, or committee), and the factors behind its points.
- `critter_prices`: Session Costs priced from a scoring run: projected power and productivity, market multiplier, signing fee and weekly fee per critter.
- `critters`, `critter_terms`, `committees`: reference data.

## Scoring

`critters score` runs the engine in `scoring.py` against a ruleset (default `rulesets/default.toml`) and saves a run. Every constant lives in the ruleset; Design-Scoring §10 lists how v0.1 interprets the open rules. `critters report` prints the median power and productivity of members seated for a whole session, the productivity scale that would make the median member even, the Senate power and productivity factors that would match the median House member, the point composition by category, and the top ten critters per session.

## Pricing

`critters price` prices the critters seated on a session's first day (Design-Economy §5.2) from a scoring run, using the `[pricing]` constants in the ruleset. Projected power is the value of the seats held that day times last session's participation; projected productivity is last session's productivity per full year, pulled toward the chamber median. Donations use the last FEC cycle complete when the session opens, so a backtest uses only what was known on day one. It needs the session before it in the same run, so for a single Congress it prices session 2. It saves `critter_prices` and prints the price spread, the budget against the 75th percentile, and, when the run has that session's scores, how well price tracked points and the best and worst value.

## Normalization notes

- Committee referral, hearings, markup, reporting, and discharge come from structured committee activity, not text.
- Passage and presidential actions come from Library of Congress action codes. Codes are read per source: `E30000` means "Signed" from the Library of Congress but "Vetoed" from the House floor feed.
- Senate floor and committee actions have no codes and are matched by text (cloture, motion to proceed, ordered reported, hearings).
- The same step often appears in several feeds; events are deduplicated on type, date, chamber, committee, and member.
- Hearings recorded as held before the bill was introduced are skipped.
- A roll call's `bill_id` is the measure named in the chamber's record. Rule votes point at the rule (H.Res), not the bill it governs; use `roll_call_actions` to reach the governed bill.
- Delegates and the Resident Commissioner appear on Committee of the Whole votes (mostly amendments), so those roll calls list up to 441 members. The Clerk gives them state `XX`; it is stored as null.
- Positions are recorded as the Clerk lists them, including one for a member who died before the Congress began (A. Donald McEachin, roll 1 of 2023). Scoring should count only members seated on the vote date (`critter_terms`).
- Amendment roll calls are cited by amendment actions, not bill actions; `roll_call_actions` covers both.
- Amendment events come from Library of Congress codes on amendment actions. A Senate amendment is offered when proposed on the floor (93000), not when submitted (91000); in the 118th, 281 of 3,359 were proposed. Each amendment gets at most one offered event and one result, its final outcome. Same-day actions are not reliably ordered in the feed, so results are ordered by the roll call quoted in their text: an amendment that failed on a tie and passed on a re-vote is adopted.
- Committee-sponsored House amendments (the Rules Committee's self-executing amendments) have no member sponsor; their events have no `critter_id`.
- Past the last roll call of a year the Clerk returns 200 with a short error document, not 404; the downloader stops at the first file that isn't a roll call.
- Voteview numbers Senate roll calls across the whole Congress; `roll_number` stores the Senate's own per-session number (`clerk_rollnumber`). Voteview also records the President's position on some votes; it is skipped. Paired and announced positions were not cast and are stored as `not_voting`, with the stated side in `raw_position`.
- Committee rosters for past sessions come from snapshots of the congress-legislators roster file, which only covers current rosters. Only 20 snapshot days cover the 118th, so a seat or role change is dated by the snapshot that first shows it, often weeks late. For example, Cole is recorded as Appropriations chair from 2024-05-01, though he took over around 2024-04-10. Seats in the first snapshot (2023-02-17) are backdated to the start of the Congress. Seats are clipped to the member's term dates, so deaths and resignations are exact. A member sworn in between snapshots holds their seats from their first day.
- Committees named in bill activity but missing from the committee reference data (`hsha06`, House Administration's Oversight Subcommittee) are added from BILLSTATUS after bills load.
