# Fantasy Congress Critters – Pages and Schemas

Documents: [Overview](README.md) | [Scoring](Design-Scoring.md) | [Economy](Design-Economy.md) | [Rulesets](Design-Rulesets.md) | [Data](Design-Data.md) | [Pages](Design-Pages.md)

---
## 13. Page Inventory & Data Requirements (Draft)

This section enumerates the core pages required by the game, independent of UI layout. Each page definition lists **required data**, **derived data**, and **update cadence**.

---

### 13.1 Critter Page

**Purpose:** Canonical reference for a single congressional critter.

**Required Data:**

* Identity (name, chamber, party, district/state)
* Tenure timeline
* Current roles and committee assignments

**Derived / Computed:**

* Positional power summary
* Productivity timeline
* Participation and reliability metrics
* Fantasy ownership and session cost

**Custom Schema (Draft):**

* `critter.id` (string, stable internal id)
* `critter.slug` (string)
* `critter.name` (string)
* `critter.chamber` (enum: House, Senate)
* `critter.party` (enum)
* `critter.state` (string)
* `critter.district` (string, nullable)
* `critter.identifiers.bioguide` (string, nullable)
* `critter.identifiers.govtrack` (string, nullable)
* `critter.identifiers.fec` (string, nullable)
* `critter.identifiers.wikidata` (string, nullable)
* `critter.tenure[]` (array of objects: start_date, end_date, seat_type, end_reason)
* `critter.status.current` (enum: active, resigned, deceased, retired, candidate)
* `critter.roles.leadership[]` (array of objects: role, start_date, end_date)
* `critter.roles.committees[]` (array of objects: committee_id, role, start_date, end_date)
* `critter.roles.subcommittees[]` (array of objects: subcommittee_id, role, start_date, end_date)
* `critter.roles.caucuses[]` (array of objects: caucus_id, role, start_date, end_date)
* `critter.metrics.roll_call_rate` (number, 0-1)
* `critter.metrics.busyness_score` (number)
* `critter.metrics.reliability_score` (number)
* `critter.metrics.missed_votes` (number)
* `critter.scoring.positional.total` (number)
* `critter.scoring.productivity.total` (number)
* `critter.scoring.total` (number)
* `critter.scoring.by_session[]` (array of objects: session_id, positional, productivity, total)
* `critter.ownership.owners_count` (number)
* `critter.ownership.owners[]` (array of objects: player_id, league_id)
* `critter.ownership.session_cost` (number)
* `critter.ownership.price_history[]` (array of objects: date, price)
* `critter.data_freshness.last_synced_at` (datetime)
* `critter.data_freshness.sources[]` (array of strings)

**Internal Ontology Mapping (Draft):**

* `critter.id` -> `CRITTER.ID`
* `critter.slug` -> `CRITTER.SLUG`
* `critter.name` -> `CRITTER.NAME`
* `critter.chamber` -> `CRITTER.CHAMBER`
* `critter.party` -> `CRITTER.PARTY`
* `critter.state` -> `CRITTER.STATE`
* `critter.district` -> `CRITTER.DISTRICT`
* `critter.identifiers.bioguide` -> `CRITTER.IDENTIFIER.BIOGUIDE`
* `critter.identifiers.govtrack` -> `CRITTER.IDENTIFIER.GOVTRACK`
* `critter.identifiers.fec` -> `CRITTER.IDENTIFIER.FEC`
* `critter.identifiers.wikidata` -> `CRITTER.IDENTIFIER.WIKIDATA`
* `critter.tenure[]` -> `CRITTER.TENURE`
* `critter.status.current` -> `CRITTER.STATUS`
* `critter.roles.leadership[]` -> `LEADERSHIP.ASSIGNMENT`
* `critter.roles.committees[]` -> `COMMITTEE.MEMBERSHIP`
* `critter.roles.subcommittees[]` -> `SUBCOMMITTEE.MEMBERSHIP`
* `critter.roles.caucuses[]` -> `CAUCUS.MEMBERSHIP`
* `critter.metrics.roll_call_rate` -> `PARTICIPATION.ROLL_CALL_RATE`
* `critter.metrics.busyness_score` -> `PARTICIPATION.BUSYNESS_SCORE`
* `critter.metrics.reliability_score` -> `PARTICIPATION.RELIABILITY_SCORE`
* `critter.metrics.missed_votes` -> `PARTICIPATION.MISSED_VOTES`
* `critter.scoring.positional.total` -> `SCORING.POSITIONAL_TOTAL`
* `critter.scoring.productivity.total` -> `SCORING.PRODUCTIVITY_TOTAL`
* `critter.scoring.total` -> `SCORING.TOTAL`
* `critter.scoring.by_session[]` -> `SCORING.BY_SESSION`
* `critter.ownership.owners_count` -> `OWNERSHIP.OWNERS_COUNT`
* `critter.ownership.owners[]` -> `OWNERSHIP.RECORD`
* `critter.ownership.session_cost` -> `PRICING.SESSION_COST`
* `critter.ownership.price_history[]` -> `PRICING.PRICE_HISTORY`
* `critter.data_freshness.last_synced_at` -> `DATA_FRESHNESS.LAST_SYNCED_AT`
* `critter.data_freshness.sources[]` -> `DATA_FRESHNESS.SOURCES`

**Update Cadence:** Event-driven + daily refresh

---

### 13.2 Committee Page

**Purpose:** Explain committee jurisdiction, membership, and fantasy relevance.

**Required Data:**

* Committee identity and chamber
* Jurisdiction description
* Membership roster

**Derived / Computed:**

* Prestige tier (session-locked)
* Typical scoring opportunities
* Recent committee activity

**Custom Schema (Draft):**

* `committee.id` (string, stable internal id)
* `committee.name` (string)
* `committee.chamber` (enum: House, Senate, Joint)
* `committee.type` (enum: standing, permanent_select, select, joint, ad_hoc; permanent_select covers permanent select and special committees, tiered like standing)
* `committee.jurisdiction` (string)
* `committee.session_id` (string)
* `committee.tier` (enum: 1, 1.5, 2, 3, 4; tiers on a `select` committee are temporary tiers with their own base values)
* `committee.leadership[]` (array of objects: critter_id, role, start_date, end_date)
* `committee.members[]` (array of objects: critter_id, role, start_date, end_date)
* `committee.subcommittees[]` (array of objects: subcommittee_id, name, leadership[], members[])
* `committee.activity.hearings_count` (number)
* `committee.activity.markups_count` (number)
* `committee.activity.reports_count` (number)
* `committee.activity.last_event_date` (date)
* `committee.scoring.gated_actions[]` (array of strings)
* `committee.scoring.typical_opportunities[]` (array of strings)
* `committee.data_freshness.last_synced_at` (datetime)
* `committee.data_freshness.sources[]` (array of strings)

**Internal Ontology Mapping (Draft):**

* `committee.id` -> `COMMITTEE.ID`
* `committee.name` -> `COMMITTEE.NAME`
* `committee.chamber` -> `COMMITTEE.CHAMBER`
* `committee.type` -> `COMMITTEE.TYPE`
* `committee.jurisdiction` -> `COMMITTEE.JURISDICTION`
* `committee.session_id` -> `SESSION.ID`
* `committee.tier` -> `COMMITTEE.TIER`
* `committee.leadership[]` -> `COMMITTEE.LEADERSHIP_ASSIGNMENT`
* `committee.members[]` -> `COMMITTEE.MEMBERSHIP`
* `committee.subcommittees[]` -> `SUBCOMMITTEE`
* `committee.activity.hearings_count` -> `COMMITTEE.ACTIVITY.HEARINGS_COUNT`
* `committee.activity.markups_count` -> `COMMITTEE.ACTIVITY.MARKUPS_COUNT`
* `committee.activity.reports_count` -> `COMMITTEE.ACTIVITY.REPORTS_COUNT`
* `committee.activity.last_event_date` -> `COMMITTEE.ACTIVITY.LAST_EVENT_DATE`
* `committee.scoring.gated_actions[]` -> `COMMITTEE.SCORING_PROFILE.GATED_ACTIONS`
* `committee.scoring.typical_opportunities[]` -> `COMMITTEE.SCORING_PROFILE.OPPORTUNITIES`
* `committee.data_freshness.last_synced_at` -> `DATA_FRESHNESS.LAST_SYNCED_AT`
* `committee.data_freshness.sources[]` -> `DATA_FRESHNESS.SOURCES`

**Update Cadence:** Session start + event-driven

---

### 13.3 Bill Page

**Purpose:** Transparency into legislative progress and scoring attribution.

**Required Data:**

* Bill identity and text metadata
* Sponsors and cosponsors
* Status and actions

**Derived / Computed:**

* Normalized event timeline
* Scoring-relevant milestones
* Dilution and authorship context

**Custom Schema (Draft):**

* `bill.id` (string: congress + type + number)
* `bill.congress` (number)
* `bill.type` (string)
* `bill.number` (string)
* `bill.title` (string)
* `bill.short_title` (string, nullable)
* `bill.summary` (string, nullable)
* `bill.introduced_date` (date)
* `bill.sponsor.id` (string)
* `bill.sponsor.role` (string)
* `bill.cosponsors[]` (array of objects: critter_id, joined_date, is_original)
* `bill.committees[]` (array of objects: committee_id, referral_date, report_date)
* `bill.status.stage` (string)
* `bill.status.latest_action_text` (string)
* `bill.status.latest_action_date` (date)
* `bill.actions[]` (array of objects: date, text, source, chamber)
* `bill.votes[]` (array of objects: chamber, roll_call_id, result, date)
* `bill.normalized_events[]` (array of objects: event_type, date, source_id)
* `bill.scoring.milestones[]` (array of objects: event_type, date, points)
* `bill.scoring.by_critter[]` (array of objects: critter_id, points, rationale)
* `bill.authorship.primary_sponsor_id` (string)
* `bill.authorship.early_thresholds` (object)
* `bill.authorship.dilution_curve_id` (string)
* `bill.metadata.policy_area` (string, nullable)
* `bill.metadata.subjects[]` (array of strings)
* `bill.data_freshness.last_synced_at` (datetime)
* `bill.data_freshness.sources[]` (array of strings)

**Internal Ontology Mapping (Draft):**

* `bill.id` -> `BILL.ID`
* `bill.congress` -> `BILL.CONGRESS`
* `bill.type` -> `BILL.TYPE`
* `bill.number` -> `BILL.NUMBER`
* `bill.title` -> `BILL.TITLE`
* `bill.short_title` -> `BILL.SHORT_TITLE`
* `bill.summary` -> `BILL.SUMMARY`
* `bill.introduced_date` -> `EVENT.BILL_INTRODUCED.DATE`
* `bill.sponsor.id` -> `BILL.SPONSOR_ID`
* `bill.sponsor.role` -> `BILL.SPONSOR_ROLE`
* `bill.cosponsors[]` -> `BILL.COSPONSOR_ASSIGNMENT`
* `bill.committees[]` -> `BILL.COMMITTEE_REFERRAL`
* `bill.status.stage` -> `BILL.STATUS.STAGE`
* `bill.status.latest_action_text` -> `BILL.STATUS.LATEST_ACTION_TEXT`
* `bill.status.latest_action_date` -> `BILL.STATUS.LATEST_ACTION_DATE`
* `bill.actions[]` -> `BILL.ACTION_RAW`
* `bill.votes[]` -> `VOTE.RECORD`
* `bill.normalized_events[]` -> `EVENT.NORMALIZED`
* `bill.scoring.milestones[]` -> `SCORING.MILESTONES`
* `bill.scoring.by_critter[]` -> `SCORING.BY_CRITTER`
* `bill.authorship.primary_sponsor_id` -> `AUTHORSHIP.PRIMARY_SPONSOR_ID`
* `bill.authorship.early_thresholds` -> `AUTHORSHIP.EARLY_THRESHOLDS`
* `bill.authorship.dilution_curve_id` -> `AUTHORSHIP.DILUTION_CURVE_ID`
* `bill.metadata.policy_area` -> `BILL.POLICY_AREA`
* `bill.metadata.subjects[]` -> `BILL.SUBJECTS`
* `bill.data_freshness.last_synced_at` -> `DATA_FRESHNESS.LAST_SYNCED_AT`
* `bill.data_freshness.sources[]` -> `DATA_FRESHNESS.SOURCES`

**Update Cadence:** Event-driven

---

### 13.4 Chamber Page (House / Senate)

**Purpose:** Macro-level context and comparison.

**Required Data:**

* Leadership
* Party control
* Session metadata

**Derived / Computed:**

* Aggregate productivity
* Participation averages
* Committee distribution

**Custom Schema (Draft):**

* `chamber.id` (enum: House, Senate)
* `chamber.session_id` (string)
* `chamber.leadership[]` (array of objects: critter_id, role, start_date, end_date)
* `chamber.party_control.majority_party` (enum)
* `chamber.party_control.seat_counts` (object: by_party)
* `chamber.membership.total_seats` (number)
* `chamber.membership.vacancies` (number)
* `chamber.committees[]` (array of objects: committee_id, tier)
* `chamber.activity.bills_introduced` (number)
* `chamber.activity.bills_passed` (number)
* `chamber.activity.votes_held` (number)
* `chamber.productivity.total_events` (number)
* `chamber.productivity.by_category` (object)
* `chamber.participation.roll_call_average` (number)
* `chamber.participation.attendance_distribution` (object)
* `chamber.data_freshness.last_synced_at` (datetime)
* `chamber.data_freshness.sources[]` (array of strings)

**Internal Ontology Mapping (Draft):**

* `chamber.id` -> `CHAMBER.ID`
* `chamber.session_id` -> `SESSION.ID`
* `chamber.leadership[]` -> `CHAMBER.LEADERSHIP_ASSIGNMENT`
* `chamber.party_control.majority_party` -> `CHAMBER.PARTY_CONTROL.MAJORITY_PARTY`
* `chamber.party_control.seat_counts` -> `CHAMBER.PARTY_CONTROL.SEAT_COUNTS`
* `chamber.membership.total_seats` -> `CHAMBER.MEMBERSHIP.TOTAL_SEATS`
* `chamber.membership.vacancies` -> `CHAMBER.MEMBERSHIP.VACANCIES`
* `chamber.committees[]` -> `CHAMBER.COMMITTEES`
* `chamber.activity.bills_introduced` -> `CHAMBER.ACTIVITY.BILLS_INTRODUCED`
* `chamber.activity.bills_passed` -> `CHAMBER.ACTIVITY.BILLS_PASSED`
* `chamber.activity.votes_held` -> `CHAMBER.ACTIVITY.VOTES_HELD`
* `chamber.productivity.total_events` -> `CHAMBER.PRODUCTIVITY.TOTAL_EVENTS`
* `chamber.productivity.by_category` -> `CHAMBER.PRODUCTIVITY.BY_CATEGORY`
* `chamber.participation.roll_call_average` -> `CHAMBER.PARTICIPATION.ROLL_CALL_AVERAGE`
* `chamber.participation.attendance_distribution` -> `CHAMBER.PARTICIPATION.ATTENDANCE_DISTRIBUTION`
* `chamber.data_freshness.last_synced_at` -> `DATA_FRESHNESS.LAST_SYNCED_AT`
* `chamber.data_freshness.sources[]` -> `DATA_FRESHNESS.SOURCES`

**Update Cadence:** Session start + daily refresh

---

### 13.5 Session Page

**Purpose:** Historical and ruleset context for a legislative session.

**Required Data:**

* Session dates
* Chambers included
* Active ruleset and version

**Derived / Computed:**

* Locked committee tiers
* Notable events summary

**Custom Schema (Draft):**

* `session.id` (string: congress + session)
* `session.congress` (number)
* `session.number` (number)
* `session.start_date` (date)
* `session.end_date` (date)
* `session.chambers[]` (array: House, Senate)
* `session.ruleset.id` (string)
* `session.ruleset.version` (string)
* `session.ruleset.type` (enum: default, seasonal, custom)
* `session.committee_tiers` (object: committee_id -> tier)
* `session.notable_events[]` (array of objects: date, event_type, description)
* `session.pricing_snapshot.donation_cycle` (string)
* `session.pricing_snapshot.odds_source` (string)
* `session.pricing_snapshot.baseline_date` (date)
* `session.data_freshness.last_synced_at` (datetime)
* `session.data_freshness.sources[]` (array of strings)

**Internal Ontology Mapping (Draft):**

* `session.id` -> `SESSION.ID`
* `session.congress` -> `SESSION.CONGRESS`
* `session.number` -> `SESSION.NUMBER`
* `session.start_date` -> `SESSION.START_DATE`
* `session.end_date` -> `SESSION.END_DATE`
* `session.chambers[]` -> `SESSION.CHAMBERS`
* `session.ruleset.id` -> `RULESET.ID`
* `session.ruleset.version` -> `RULESET.VERSION`
* `session.ruleset.type` -> `RULESET.TYPE`
* `session.committee_tiers` -> `COMMITTEE.TIER_SNAPSHOT`
* `session.notable_events[]` -> `SESSION.NOTABLE_EVENT`
* `session.pricing_snapshot.donation_cycle` -> `PRICING.SNAPSHOT.DONATION_CYCLE`
* `session.pricing_snapshot.odds_source` -> `PRICING.SNAPSHOT.ODDS_SOURCE`
* `session.pricing_snapshot.baseline_date` -> `PRICING.SNAPSHOT.BASELINE_DATE`
* `session.data_freshness.last_synced_at` -> `DATA_FRESHNESS.LAST_SYNCED_AT`
* `session.data_freshness.sources[]` -> `DATA_FRESHNESS.SOURCES`

**Update Cadence:** Session lifecycle

---

### 13.6 League Page

**Purpose:** Competitive context for players.

**Required Data:**

* League configuration
* Ruleset reference
* Participants

**Derived / Computed:**

* Standings
* Budget usage
* Score trends

**Custom Schema (Draft):**

* `league.id` (string)
* `league.name` (string)
* `league.type` (enum: session, annual, representative, presidential, senatorial, standard_private, flexible_private)
* `league.start_date` (date)
* `league.end_date` (date)
* `league.session_ids[]` (array of strings; leagues may span several sessions)
* `league.ruleset.id` (string)
* `league.ruleset.version` (string)
* `league.config.budget_rules` (object: annual_budget; caps and rollover_policy to come)
* `league.config.roster_rules` (object: roster_limit, chamber_slots {house, senate} or null; ownership_limits to come)
* `league.config.win_condition` (enum: cumulative, head_to_head)
* `league.config.drop_cost` (object: extra_fee, points_penalty; on top of the signing fee, which is always lost)
* `league.preset` (string: the preset the settings started from)
* `league.created_by` (object: game master and role [gamemaker, commissioner])
* `league.participants[]` (array of objects: player_id, display_name, joined_at)
* `league.standings[]` (array of objects: player_id, points, rank)
* `league.budgets[]` (array of objects: player_id, available, committed)
* `league.score_trends[]` (array of objects: date, player_id, total_points)
* `league.transactions[]` (array of objects: txn_id, player_id, critter_id, date, amount, type)
* `league.data_freshness.last_synced_at` (datetime)
* `league.data_freshness.sources[]` (array of strings)

**Internal Ontology Mapping (Draft):**

* `league.id` -> `LEAGUE.ID`
* `league.name` -> `LEAGUE.NAME`
* `league.type` -> `LEAGUE.TYPE`
* `league.start_date` -> `LEAGUE.START_DATE`
* `league.end_date` -> `LEAGUE.END_DATE`
* `league.session_ids[]` -> `SESSION.ID`
* `league.ruleset.id` -> `RULESET.ID`
* `league.ruleset.version` -> `RULESET.VERSION`
* `league.config.budget_rules` -> `LEAGUE.BUDGET_RULES`
* `league.config.roster_rules` -> `LEAGUE.ROSTER_RULES`
* `league.config.win_condition` -> `LEAGUE.WIN_CONDITION`
* `league.config.drop_cost` -> `LEAGUE.DROP_COST`
* `league.preset` -> `LEAGUE.PRESET`
* `league.created_by` -> `LEAGUE.GAME_MASTER`
* `league.participants[]` -> `LEAGUE.PARTICIPANT`
* `league.standings[]` -> `LEAGUE.STANDINGS`
* `league.budgets[]` -> `LEAGUE.BUDGET_STATE`
* `league.score_trends[]` -> `LEAGUE.SCORE_TREND`
* `league.transactions[]` -> `TRANSACTION.RECORD`
* `league.data_freshness.last_synced_at` -> `DATA_FRESHNESS.LAST_SYNCED_AT`
* `league.data_freshness.sources[]` -> `DATA_FRESHNESS.SOURCES`

**Update Cadence:** Event-driven

---

### 13.7 Roster Page

**Purpose:** Player team management and analysis.

**Required Data:**

* Owned critters
* Budget commitments

**Derived / Computed:**

* Power vs productivity breakdown
* Risk indicators
* Opportunity analysis

**Custom Schema (Draft):**

* `roster.id` (string)
* `roster.league_id` (string)
* `roster.player_id` (string)
* `roster.budget.available` (number)
* `roster.budget.committed` (number: spent this legislative year, signing fees, drop fees and weekly fees charged)
* `roster.budget.future_commitments` (number: weekly fees reserved for the weeks to come)
* `roster.critters[]` (array of objects: critter_id, acquisition_date, cost, session_id, first_week, status (enum: held, dropped, left_office))
* `roster.scoring.total` (number)
* `roster.scoring.positional` (number)
* `roster.scoring.productivity` (number)
* `roster.scoring.penalties` (number, player-level deductions such as a points-based drop cost; total = positional + productivity − penalties)
* `roster.scoring.by_critter[]` (array of objects: critter_id, points)
* `roster.risk.reelection_odds` (number)
* `roster.risk.volatility_score` (number)
* `roster.risk.flags[]` (array of strings)
* `roster.analysis.power_vs_productivity` (object)
* `roster.analysis.opportunity_flags[]` (array of strings)
* `roster.transactions[]` (array of objects: txn_id, date, type, amount)
* `roster.data_freshness.last_synced_at` (datetime)
* `roster.data_freshness.sources[]` (array of strings)

**Internal Ontology Mapping (Draft):**

* `roster.id` -> `ROSTER.ID`
* `roster.league_id` -> `LEAGUE.ID`
* `roster.player_id` -> `PLAYER.ID`
* `roster.budget.available` -> `BUDGET.AVAILABLE`
* `roster.budget.committed` -> `BUDGET.COMMITTED`
* `roster.budget.future_commitments` -> `BUDGET.FUTURE_COMMITMENTS`
* `roster.critters[]` -> `ROSTER.CRITTER_OWNERSHIP`
* `roster.scoring.total` -> `ROSTER.SCORING.TOTAL`
* `roster.scoring.positional` -> `ROSTER.SCORING.POSITIONAL`
* `roster.scoring.productivity` -> `ROSTER.SCORING.PRODUCTIVITY`
* `roster.scoring.penalties` -> `ROSTER.SCORING.PENALTIES`
* `roster.scoring.by_critter[]` -> `ROSTER.SCORING.BY_CRITTER`
* `roster.risk.reelection_odds` -> `ROSTER.RISK.REELECTION_ODDS`
* `roster.risk.volatility_score` -> `ROSTER.RISK.VOLATILITY_SCORE`
* `roster.risk.flags[]` -> `ROSTER.RISK.FLAGS`
* `roster.analysis.power_vs_productivity` -> `ROSTER.ANALYSIS.POWER_VS_PRODUCTIVITY`
* `roster.analysis.opportunity_flags[]` -> `ROSTER.ANALYSIS.OPPORTUNITY_FLAGS`
* `roster.transactions[]` -> `TRANSACTION.RECORD`
* `roster.data_freshness.last_synced_at` -> `DATA_FRESHNESS.LAST_SYNCED_AT`
* `roster.data_freshness.sources[]` -> `DATA_FRESHNESS.SOURCES`

**Update Cadence:** Real-time

---

### 13.8 Market / Acquisition Page

**Purpose:** Discover and acquire critters.

**Required Data:**

* Available critters
* Pricing inputs

**Derived / Computed:**

* Timing modifiers
* Ownership discounts

**Custom Schema (Draft):**

* `market.id` (string)
* `market.session_id` (string)
* `market.as_of` (datetime)
* `market.available_critters[]` (array of objects: critter_id, price, price_trend, owners_count)
* `market.available_candidates[]` (array of objects: candidate_id, race_id, odds, price)
* `market.pricing_inputs` (object: donations, odds, leadership_premium)
* `market.timing_modifiers` (object: pre_session_discount, mid_session_premium)
* `market.ownership_discounts` (object: curve_id, max_discount)
* `market.filters` (object: chamber, party, committee, price_range)
* `market.data_freshness.last_synced_at` (datetime)
* `market.data_freshness.sources[]` (array of strings)

**Internal Ontology Mapping (Draft):**

* `market.id` -> `MARKET.ID`
* `market.session_id` -> `SESSION.ID`
* `market.as_of` -> `MARKET.AS_OF`
* `market.available_critters[]` -> `MARKET.CRITTER_LISTING`
* `market.available_candidates[]` -> `MARKET.CANDIDATE_LISTING`
* `market.pricing_inputs` -> `PRICING.INPUTS`
* `market.timing_modifiers` -> `PRICING.TIMING_MODIFIERS`
* `market.ownership_discounts` -> `PRICING.OWNERSHIP_DISCOUNTS`
* `market.filters` -> `MARKET.FILTERS`
* `market.data_freshness.last_synced_at` -> `DATA_FRESHNESS.LAST_SYNCED_AT`
* `market.data_freshness.sources[]` -> `DATA_FRESHNESS.SOURCES`
**Update Cadence:** Real-time

---

### 13.9 Query & Tables Pages

**Purpose:** Exploration and analysis.

**Examples:**

* All critters sortable by value
* Bills by committee
* Critters up for reelection

**Custom Schema (Draft):**

* `query.id` (string)
* `query.entity_type` (enum: critter, bill, committee, vote)
* `query.title` (string)
* `query.columns[]` (array of objects: column_id, label, data_type)
* `query.filters[]` (array of objects: field, operator, value)
* `query.sort.field` (string)
* `query.sort.direction` (enum: asc, desc)
* `query.pagination.limit` (number)
* `query.pagination.offset` (number)
* `query.pagination.total` (number)
* `query.results[]` (array of objects: row_id, cells[])
* `query.updated_at` (datetime)
* `query.data_freshness.last_synced_at` (datetime)

**Internal Ontology Mapping (Draft):**

* `query.id` -> `QUERY.ID`
* `query.entity_type` -> `QUERY.ENTITY_TYPE`
* `query.title` -> `QUERY.TITLE`
* `query.columns[]` -> `QUERY.COLUMNS`
* `query.filters[]` -> `QUERY.FILTERS`
* `query.sort.field` -> `QUERY.SORT.FIELD`
* `query.sort.direction` -> `QUERY.SORT.DIRECTION`
* `query.pagination.limit` -> `QUERY.PAGINATION.LIMIT`
* `query.pagination.offset` -> `QUERY.PAGINATION.OFFSET`
* `query.pagination.total` -> `QUERY.PAGINATION.TOTAL`
* `query.results[]` -> `QUERY.RESULTS`
* `query.updated_at` -> `QUERY.UPDATED_AT`
* `query.data_freshness.last_synced_at` -> `DATA_FRESHNESS.LAST_SYNCED_AT`

**Update Cadence:** On demand

---
