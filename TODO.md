# TODO

## Incomplete or underspecified items

- Define numeric values for scoring placeholders (`[TIER_*_BASE_VALUE]`, `{PTS_*}`)
- Complete budgeting across legislative years in Section 6: cross-year mechanics, carryover rules, and caps
- [x] Specify pricing formulas for session costs and re-election premiums (candidate odds-based pricing still deferred)
- Decide mid-session repricing for new purchases (how a critter's Session Cost moves once the session is under way)
- Decide whether chamber balance should hold every session (Design-Scoring §11): in 2025 the busier Senate out-earned the House on productivity
- Flag announced departures in the market (members leaving for the administration or retiring mid-session)
- [x] Turn the pricing backtest into code: a `critters price` command with the constants in the ruleset
- [x] Finalize committee prestige tier mapping (House and Senate) and base values
- [x] Define authorship multipliers and dilution curve shape/parameters
- Quantify anti-exploit caps, decay rates, and cooldown durations
- [x] Name canonical data sources/APIs (gaps: Senate committee votes, election odds)
- [x] Define update cadences and failure handling per source (`critters update`, daily; Design-Data §10.4.3A)
- Decide whether corrections to settled weeks carry forward into the next unsettled week, or wait for a manual correction window (today: reported as drift, not applied)
- Host the daily update (scheduler, alerting on a non-zero exit) once there is a production server
- [x] Read-only website: leagues, standings, rosters, market and critter pages (`web/`, `critters serve`)
- [x] Website accounts: invite codes and passwords, sessions, rosters owned by accounts, joining official leagues (`critters invite`, `critters account`)
- Password reset without an admin (needs an email sender), if the beta outgrows hand resets
- [x] Trading from the website: buy from the market, drop from the roster
- [x] Game master pages: create a league from a preset, change its settings before it starts, join links for private leagues, remove players before the start, invite codes for GameMakers
- Choose a ruleset when creating a league on the website (today: the default ruleset)
- Choose a fallback for the committee participation multiplier where committees don't publish recorded votes (most Senate committees)
- Choose an election odds source (deferred with candidate drafting)
- Add concrete normalization mappings for action text parsing, including edge cases,
- Specify ruleset versioning and governance (approval, freezing, deprecation)
- Define multi-ownership discount schedule and guardrails (deferred; flat price at launch)
- [x] League settings as a per-league entity set by game masters, with GameMaker presets (Design-Rulesets §6A.7)
- Head-to-head matchups: scheduling and weekly scoring for leagues that choose them
- [x] Rosters, purchases, drops and standings within a league (cumulative standings; `critters league buy`, `drop`, `roster`, `standings`)
- Decide whether a critter earns points for bill progress after leaving office: scoring credits departed sponsors and co-sponsors (562 points to 13 members who left in 2024); rosters already stop counting them
- Price critters seated mid-session (special elections, appointments): they have no Session Cost, so they can't be bought
- [x] Decide who scores bill committee and floor scheduling actions (sponsor/co-sponsors only)
- [x] Set authorship stage cutoffs

## Suggested next steps

1) Lock scoring constants: set numeric values for action points, tier bases, authorship multipliers, and dilution curve parameters (PARTIALLY DONE: multipliers and tiers set)
2) Finish budget rules: annual budget amounts, rollover policy, and penalties/caps (annual amount DONE)
3) Specify pricing formulas: session cost equation, odds-based candidate pricing, and reelection premiums (session cost and re-election DONE; candidates deferred)
4) Finalize committee tier map: explicit committee-to-tier list for both chambers (DONE)
5) Define anti-exploit parameters: caps, cooldowns, and diminishing-return formulas
6) Pin data sources and schemas: canonical APIs, odds source, update cadence/latency
7) Create ruleset versioning policy: versioning, seasonal publication, and deprecation rules (DONE)
8) Run a scoring sanity pass: test with a few recent bills and tune constants

## Ontology coverage checklist (draft)

- Entity domains defined for all schema fields (`CRITTER`, `COMMITTEE`, `BILL`, `CHAMBER`, `SESSION`, `RULESET`, `LEAGUE`, `ROSTER`, `MARKET`, `QUERY`, `PRICING`, `TRANSACTION`, `DATA_FRESHNESS`).
- Event domains used only for scoreable actions (`EVENT.*`) and separated from entity/state values.
- Every page schema field mapped to exactly one ontology token.
- Fields that are cross-cutting (pricing, freshness, transactions) use shared ontology tokens across pages.
- Any schema field lacking a clear ontology token is listed and resolved before source mapping.
