# TODO

## Incomplete or underspecified items

- Define numeric values for scoring placeholders (`[TIER_*_BASE_VALUE]`, `{PTS_*}`) in `Fantasy Congress Critters.md`.
- Complete budgeting across legislative years in Section 6: cross-year mechanics, carryover rules, and caps in `Fantasy Congress Critters.md`.
- Specify pricing formulas for session costs, candidate odds-based pricing, and reelection premiums in `Fantasy Congress Critters.md`.
- Finalize committee prestige tier mapping (House and Senate) and base values in `Fantasy Congress Critters.md`.
- Define authorship multipliers and dilution curve shape/parameters in `Fantasy Congress Critters.md`.
- Quantify anti-exploit caps, decay rates, and cooldown durations in `Fantasy Congress Critters.md`.
- Name canonical data sources/APIs, update cadences, and failure handling in `Fantasy Congress Critters.md`.
- Add concrete normalization mappings for action text parsing, including edge cases, in `Fantasy Congress Critters.md`.
- Specify ruleset versioning and governance (approval, freezing, deprecation) in `Fantasy Congress Critters.md`.
- Define multi-ownership discount schedule and guardrails in `Fantasy Congress Critters.md`.

## Suggested next steps

1) Lock scoring constants: set numeric values for action points, tier bases, authorship multipliers, and dilution curve parameters in `Fantasy Congress Critters.md`.
2) Finish budget rules: annual budget amounts, rollover policy, and penalties/caps in `Fantasy Congress Critters.md`.
3) Specify pricing formulas: session cost equation, odds-based candidate pricing, and reelection premiums in `Fantasy Congress Critters.md`.
4) Finalize committee tier map: explicit committee-to-tier list for both chambers in `Fantasy Congress Critters.md`.
5) Define anti-exploit parameters: caps, cooldowns, and diminishing-return formulas in `Fantasy Congress Critters.md`.
6) Pin data sources and schemas: canonical APIs, odds source, update cadence/latency in `Fantasy Congress Critters.md`.
7) Create ruleset versioning policy: versioning, seasonal publication, and deprecation rules in `Fantasy Congress Critters.md`.
8) Run a scoring sanity pass: test with a few recent bills and tune constants in `Fantasy Congress Critters.md`.

## Ontology coverage checklist (draft)

- Entity domains defined for all schema fields (`CRITTER`, `COMMITTEE`, `BILL`, `CHAMBER`, `SESSION`, `RULESET`, `LEAGUE`, `ROSTER`, `MARKET`, `QUERY`, `PRICING`, `TRANSACTION`, `DATA_FRESHNESS`).
- Event domains used only for scoreable actions (`EVENT.*`) and separated from entity/state values.
- Every page schema field mapped to exactly one ontology token.
- Fields that are cross-cutting (pricing, freshness, transactions) use shared ontology tokens across pages.
- Any schema field lacking a clear ontology token is listed and resolved before source mapping.
