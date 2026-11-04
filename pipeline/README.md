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
uv run critters league preset save standard --file presets/standard.toml --by <you>
uv run critters league create --name "2026 Session" --type session --congress 119 --session 2 --by <you>
uv run critters league join 1 <player>
uv run critters league buy 1 <player> Cornyn Neguse   # bioguide ids or parts of names
uv run critters league standings 1
uv run critters update                 # once a day during a season: new data, rescore, settle weeks
uv run critters status                 # when each source last updated, and what failed
uv run critters serve                  # the web API on http://127.0.0.1:8000 (see web/README.md)
uv run critters invite create --by <you> --uses 5   # invite codes for website accounts
uv run critters account list           # website accounts; account update resets passwords, roles
uv run pytest
```

Raw files land in `data/raw/` (gitignored). `load` is idempotent: each bill and its events are replaced on reload. Set `DATABASE_URL` to point somewhere other than the local container.

## Sources

| Data | Source |
| --- | --- |
| Bills, actions, co-sponsors, committee activity, amendments | GovInfo `BILLSTATUS` bulk XML |
| Members, terms, ID crosswalk, committee names | `unitedstates/congress-legislators` |
| Committee rosters over time | During a live season, the chambers' own lists, recorded by `critters update` whenever a seat changes: the House Clerk's `MemberData.xml` and senate.gov's `committee_memberships_{code}.xml`. Before that, every commit of `committee-membership-current.yaml` in `congress-legislators` during the Congress |
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
- `weekly_points`: a run's points per critter and settlement week, for standings. A seat is split across the weeks it was held at each week's participation, so a critter's weeks add up to their items.
- `critter_prices`: Session Costs priced from a scoring run: projected power and productivity, market multiplier, signing fee and weekly fee per critter.
- `league_presets`, `leagues`: settings presets authored by GameMakers, and leagues with their resolved settings and a frozen copy of their ruleset.
- `rosters`, `transactions`: a player's roster in a league, and its purchases (with the price paid and the weeks reserved) and drops.
- `source_syncs`: every attempt by `critters update` to bring a source up to date, with what changed, the newest data afterward, and the error if it failed.
- `settled_weeks`, `settled_points`: weeks whose points are final for every league using a ruleset, and those points.
- `invites`, `accounts`, `sessions`: website accounts, the invite codes that made them, and signed-in browsers (only a hash of each session token). A roster joined on the site points at its account, and a league made on the site at its owner.
- `critters`, `critter_terms`, `committees`: reference data.

## Scoring

`critters score` runs the engine in `scoring.py` against a ruleset (default `rulesets/default.toml`) and saves a run. Votes, and the attendance multiplier on seats, settle by week: each of a session's 52 weeks pays by that week's participation, so a week's points are final when it ends. Every constant lives in the ruleset; Design-Scoring §10 lists how v0.1 interprets the open rules. `critters report` prints the median power and productivity of members seated for a whole session, the productivity scale that would make the median member even, the Senate power and productivity factors that would match the median House member, the point composition by category, and the top ten critters per session.

## Pricing

`critters price` prices the critters seated on a session's first day (Design-Economy §5.2) from a scoring run, using the `[pricing]` constants in the ruleset. Projected power is the value of the seats held that day times last session's participation; projected productivity is last session's productivity per full year, pulled toward the chamber median. Donations use the last FEC cycle complete when the session opens, so a backtest uses only what was known on day one. Session 2 reads session 1 of the same run; session 1 reads session 2 of the previous Congress's latest run (or `--prev-run`). A new Congress seats its committees weeks after it convenes: priced before its rosters are posted, committee seats are projected from the last Congress (chairs and ranking members swap where the majority changed; newcomers get the freshman median) at a discount, and `--as-of` prices on a later date instead. It saves `critter_prices` and prints the price spread, the budget against the 75th percentile, and, when the run has that session's scores, how well price tracked points and the best and worst value.

## Leagues

League rules are settings on each league, set by a game master (Design-Rulesets §6A.7), not constants in the code or the ruleset. `leagues.py` defines which settings exist and their limits; values come from presets (`presets/standard.toml`, loaded with `critters league preset save`) and from the game master's `--set path=value` overrides at `critters league create`. A league keeps its own copy of the settings and of its ruleset, and both are frozen once it starts (`critters league update` refuses after that). Official league types need `--role gamemaker`. A private league gets a join code (`critters league show` prints it). `critters price --league ID` prices with the league's ruleset and checks its budget. Creating and updating leagues goes through `play.create_league` and `play.update_league`, shared with the website.

Players trade with `critters league join`, `buy`, `drop`, `roster` and `standings` (`ledger.py`, Design-Economy §5.2). Each takes `--on DATE` (default today), so a past season can be replayed; a roster's transactions can't be dated before its last one. A league scores and prices from the latest run of each Congress scored with exactly its frozen ruleset (`critters score --league ID` makes one), and its sessions must be priced in that run.

- Each legislative year has its own budget. A purchase spends the signing fee and reserves the weekly fee for every league week left in the session; made during a week, it is held from the next week.
- A drop takes effect the next week: the critter scores through the week already paid for, and the rest of the reservation returns. The league's `drop_cost` adds a fee and a points penalty.
- A critter whose service ends mid-session leaves the roster with no drop cost: later weeks aren't charged and the slot frees.
- Points count for the weeks held once each week has ended. Standings rank by total points; head-to-head isn't built yet.

## Live updates

`critters update` keeps a season current; run it once a day from a scheduler (`live.py`). It updates the Congress in session, and for the first 30 days of a new Congress the previous one too, so its last week can settle. Each source is updated on its own and logged in `source_syncs`, so one failure doesn't stop the rest; the command exits non-zero if any failed, and `critters status` shows when each last succeeded and why the last attempt failed. Downloads retry timeouts and server errors, and send the last ETag so unchanged files aren't fetched again. Two updates can't run at once.

| Source | What `update` does |
| --- | --- |
| `legislators` | Refetches the congress-legislators files and reloads members, terms and committees when they change |
| `rosters` | Reads both chambers' committee lists and saves a snapshot (`data/raw/rosters/official/{congress}/`) when any seat changed; from the first one, these replace the congress-legislators history. The Senate lists names and states, matched to sitting senators (accents folded; Darline Graham Nordone is listed as Graham). Sides follow the caucus. Until the House Clerk lists the new Congress, House seats are left out. A list less than 80% the size of the last is refused as a glitch |
| `billstatus` | GovInfo rebuilds the BILLSTATUS zips daily; changed zips are fetched and bills whose update date changed are reloaded |
| `house_votes` | Fetches House roll calls past the last one on disk |
| `senate_votes` | Refetches Voteview's files and reloads the Senate roll calls when they change. Voteview's 119th files held the Senate's September 30 votes by 07:00 UTC the next morning |

When anything changed, the Congress is rescored with each ruleset in play (`rulesets/default.toml` and the rulesets of leagues not yet over) as a live run. A new live run replaces the last one of the same Congress and ruleset, which is deleted unless prices or purchases point at it. Leagues price from the latest run that has prices for the session, so live runs don't change prices.

Then weeks settle (Design-Data §10.4). A week settles, in order, once it has been over for three days, every source has synced since then, and every roll call that bill actions cite before the week ended is loaded (none were missing in the 118th or 119th, so a gap means a source is behind). Its points are copied to `settled_points` and are final for every league with that ruleset: standings count settled weeks from there and later weeks from the latest run. Later corrections to a settled week aren't applied; `update` reports them as drift (weeks, critters and points), for a manual correction window if they matter.

To schedule it, a crontab line such as:

```
30 9 * * * cd /path/to/pipeline && uv run critters update >> ../data/update.log 2>&1
```

## Web API

`critters serve` runs the API behind the site (`api.py`, FastAPI): leagues with their standings, rosters, a league's market, critters and where their points came from, and data freshness from `source_syncs`; accounts, joining a league, and buying and dropping critters (`play.buy` and `play.drop`, the same code as `critters league buy` and `drop`, which lock the roster until the trade commits so two at once can't both spend the balance). Every view takes `?on=DATE` to show the game as it stood that day, so the 2024 backtest can be browsed. It shares the league logic in `play.py` with the `league` commands, so the site and the command line agree. Weeks still to come are left out of a critter's points: a live run scores them at today's seats and attendance, which aren't points yet. When `web/dist` exists (`npm run build` in `web/`), `serve` also serves the site. See [web/README.md](../web/README.md) for development.

### Accounts

The beta is invite-only (`auth.py`). `critters invite create` makes codes, each good for `--uses` accounts with its `--role` (player, commissioner or gamemaker) until it expires (`--days`, default 30); `critters invite list` shows which accounts each made. Someone with a code creates an account on the site's sign-up page (`/signup?invite=CODE` fills it in). There's no email, so a forgotten password is reset by hand: `critters account update NAME --reset-password` prints a temporary one and signs the account out everywhere. `--disable` blocks an account.

- Passwords are hashed with scrypt; at least 10 characters. Usernames are 3 to 24 letters, digits, hyphens or underscores, unique ignoring case, and are the player name in standings.
- Signing in sets an HttpOnly, SameSite=Lax cookie with a random token, good for 30 days; the database keeps only its SHA-256. Set `CRITTERS_SECURE_COOKIE=1` when serving over HTTPS.
- Requests that change anything must be JSON, which browsers won't send across sites without asking, so other sites can't act for a signed-in player.
- Ten failed sign-ins for a username or from an address within 15 minutes block it for the rest of the window (in memory, per process).
- A signed-in player can join an official league that hasn't ended, on today's date. A private league needs its join code, which comes in the link its game master shares.
- Any account can make a private league on the site and becomes its commissioner; GameMaker accounts can also make official ones. Site leagues score with `rulesets/default.toml` and record their owner (`leagues.owner_account_id`).
- A league's game master (its owner, or any GameMaker for an official league) changes its name and settings and removes players until it starts, and can replace a private league's join code, which stops the old link working.
- Private leagues are unlisted: the league list shows them only to their players and game master.
- GameMakers make invite codes on the site too (`/invites`), the same as `critters invite create`.
- A player buys and drops for their own roster only, always on today's date; browsing with `?on=` never trades.

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
