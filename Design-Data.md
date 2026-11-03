# Fantasy Congress Critters – Data, Ontology, and Normalization

Documents: [Overview](README.md) | [Scoring](Design-Scoring.md) | [Economy](Design-Economy.md) | [Rulesets](Design-Rulesets.md) | [Data](Design-Data.md) | [Pages](Design-Pages.md)

---
## 10. Data Sources, Authority, and Normalization (Draft)

This section defines how *Fantasy Congress Critters* ingests real-world data, determines authority, and converts raw records into scoreable events. The goal is **stability, reproducibility, and transparency**, not perfect historical truth.

---

### 10.1 Data Domains & Canonical Sources

For each data domain, the game designates **one canonical source of record**. Only canonical sources may directly generate scoreable events.

| Data Domain                      | Canonical Source                                              | Purpose                         |
| -------------------------------- | ------------------------------------------------------------- | ------------------------------- |
| Legislation (bills, resolutions) | Congress.gov API (Library of Congress)                        | Bill lifecycle, status, actions |
| Committees & memberships         | House Clerk member data; Senate committee membership data (current); congress-legislators history (past, see note) | Jurisdiction, gating, power     |
| Roll-call votes                  | House Clerk roll-call data; Senate: Voteview (see note)        | Participation & voting          |
| Committee schedules & hearings   | House: docs.house.gov Committee Repository; Senate: senate.gov committee hearing schedule | Hearings, markups, oversight |
| Committee recorded votes         | **Gap** (House: PDFs only, see note; Senate: not published consistently) | Committee participation multiplier |
| Fundraising & donations          | OpenFEC API                                                   | Draft pricing inputs            |
| Elections & incumbency           | House Clerk and Senate member data (seating)                  | Seating, term status            |
| Election odds                    | **Gap** (deferred with candidate drafting)                    | Candidate & future pricing      |

**Senate roll calls:** senate.gov blocks automated downloads, so Senate votes come from [Voteview](https://voteview.com) (UCLA), an open dataset built from the official record. Its tallies are checked against the Senate's own vote counts in Congress.gov bill actions. The Senate's own feed can replace it if it becomes reachable; more canonical sources can be added per domain where that makes sense.

**House committee votes:** docs.house.gov publishes each committee roll call as a separate PDF, linked from the meeting's page (file names like `CRPT-118-IF14-Vote001-20230308.pdf`; document type `CV` in the meeting XML). There is no structured feed. A survey of the 118th found about 1,500 such PDFs, and the layout differs by committee: some mark votes with X, x, y, 1 or ✓ in Yea/Nay/Present columns, and members appear as "Rep. Guthrie", "MR. JORDAN (OH)", "Mr. Graves of MO" or "Jim Baird, Indiana". About half the committees post text PDFs; the rest post scanned images (Financial Services, Judiciary, Small Business, Veterans' Affairs) or text that extracts garbled (Education and Workforce). Parsing them would need a reader per committee plus OCR, so committee seats use floor participation for now. Revisit if a structured source appears (e.g. a Congress.gov API endpoint for committee votes).

**Past committee rosters:** the official sources publish current rosters only. Rosters for past sessions (backtests) are rebuilt from the commit history of the congress-legislators membership file, which is scraped from those official sources. Snapshots are sparse (20 days across the 118th Congress), so seat changes are dated when a snapshot shows them, weeks after the real change. Departures and mid-session arrivals use exact term dates. A live season should record the official rosters daily so dates are exact.

**Committees listed late:** congress-legislators sometimes adds a committee to its roster file months after the committee is seated. The House Task Force on the Attempted Assassination of Donald J. Trump (`hszt00`) was created by H.Res. 1367 on July 24, 2024 and its 13 members were named on July 29, but the file first lists it on December 17, 2024. Those seats are backfilled to July 29 (`SEATED_BEFORE_LISTED` in `rosters.py`); the 13 members listed in December match the July appointments. Subcommittees have the same problem on a larger scale and are not backfilled: 107 of them first appear in the May 14, 2023 snapshot, after the February and March snapshots, so subcommittee seats from the start of the 118th Congress are dated May 14.

**Fundraising:** the pricing backtest uses two FEC bulk files, which carry the same figures as OpenFEC. The all-candidates summary (`weball{yy}.zip`, total receipts per candidate for a two-year cycle) drives the donations modifier, from the last cycle complete when the session opens (2022 for the 2024 session); `critters download` fetches it. Committee-to-candidate transactions (`pas224.zip`: contributions, in-kind gifts, and independent expenditures for or against a named candidate) set the price scale. Transactions repeated by amended reports are counted once, from the latest filing. Candidates are matched to critters through the FEC ids in congress-legislators, and every candidacy counts. A House member running for the Senate is priced on both campaigns (Ruben Gallego: $129M). Two members (Glenn Ivey, Keith Self) don't appear in the 2022 or 2024 files under their ids or their names; this needs a check against OpenFEC before live pricing. Until then they, like appointed members and winners of special elections after the cycle, rank at the median for donations.

The open-data `unitedstates/congress-legislators` dataset is the **secondary** source for the identifier crosswalk (bioguide, GovTrack, FEC, Wikidata) and for cross-checking memberships.

**Rule:**

> Scoring is computed **only** from canonical sources.

---

### 10.2 Secondary Sources (Fallback & Confirmation)

Secondary data sources may be used **only** for limited, non-scoring purposes:

* **Fallback** – Temporary gaps or delays in canonical data
* **Confirmation** – Detecting anomalies or obvious errors
* **Enrichment** – Adding metadata, labels, or confidence flags

Secondary sources:

* Never directly generate points
* Never override canonical records automatically
* May annotate events for debugging, UI display, or audits

**Design Principle:**

> Secondary sources annotate reality; canonical sources define it.

---

### 10.3 Internal Event Ontology (Controlled Vocabulary)

All raw data is normalized into an **internal event ontology** before scoring. This ontology is the only layer the scoring engine understands.

**Characteristics of the ontology:**

* Small, stable, and versioned
* Independent of any single external schema
* Expressive enough to support scoring rubrics

**Event Types (as implemented in `pipeline/`):**

| Group | Event types |
| --- | --- |
| Sponsorship | `BILL_INTRODUCED` (carries the sponsor; no separate sponsor event), `COSPONSOR_ADDED`, `COSPONSOR_WITHDRAWN` |
| Committee | `COMMITTEE_REFERRAL`, `COMMITTEE_HEARING_HELD`, `COMMITTEE_MARKUP`, `ORDERED_REPORTED`, `REPORTED`, `COMMITTEE_DISCHARGED`, `DISCHARGE_PETITION_FILED` |
| Floor scheduling | `PLACED_ON_CALENDAR`, `RULE_REPORTED`, `RULE_ADOPTED` (House), `MOTION_TO_PROCEED`, `CLOTURE_FILED`, `CLOTURE_INVOKED` (Senate) |
| Floor | `FLOOR_CONSIDERATION`, `PASSED_CHAMBER`, `FAILED_PASSAGE` |
| Bicameral | `CONFERENCE_APPOINTED`, `CONFERENCE_REPORT_AGREED`, `RESOLVED_DIFFERENCES` |
| Presidential | `PRESENTED_TO_PRESIDENT`, `VETOED`, `VETO_OVERRIDE_PASSED`, `VETO_OVERRIDE_FAILED`, `BECAME_LAW` |
| Amendment | `AMENDMENT_OFFERED`, `AMENDMENT_ADOPTED`, `AMENDMENT_FAILED` (carry the amendment and its sponsor) |

Committee events carry the committee or subcommittee code; parent committees come from the committee reference data. An amendment has at most one offered event and one result, its final outcome.

Roll-call votes are stored as `VOTE.*` records with one position per member, not as bill events. Scoring reads them for per-vote points (Scoring §7.1) and floor participation (Scoring §4.1).

`COMMITTEE_DISCHARGED` is usually routine (a secondary committee released so the bill can move). Discharge petitions, the procedural override in §8.3, are `DISCHARGE_PETITION_FILED`.

Each external data source is mapped **independently** into this ontology.

**Normalization Rules:**

* If a canonical source maps cleanly to an ontology event → event is created
* If a secondary source maps cleanly but canonical does not → event is *not* created
* If mapping is ambiguous → conservative interpretation or no event

**Important:**

> The ontology is never retrofitted to match a source; sources adapt to the ontology.

---

### 10.3A Internal Entity & State Ontology (Draft)

This section defines **non-event ontology domains** used to represent durable entities and stateful values. These fields are populated by canonical sources but are **not scoreable events**.

**Core Domains:**

* `CRITTER.*` – Identity, chamber, party, tenure, and status.
* `COMMITTEE.*` – Committee identity, chamber, type, membership, leadership, and tiers.
* `BILL.*` – Bill identity, metadata, sponsors, committees, and status.
* `CHAMBER.*` – Chamber leadership, party control, and aggregate activity.
* `SESSION.*` – Session identifiers, dates, chambers, and ruleset bindings.
* `RULESET.*` – Ruleset ids, versions, and types.
* `LEAGUE.*` – League configuration, participants, standings, and budgets.
* `ROSTER.*` – Player roster state, budget allocations, and scoring.
* `MARKET.*` – Listings, pricing inputs, and discount curves.
* `QUERY.*` – Structured query state for table outputs.
* `PRICING.*` – Pricing inputs, timing modifiers, and ownership discounts.
* `TRANSACTION.*` – Market and roster transaction records.
* `DATA_FRESHNESS.*` – Sync timestamps and source provenance.
* `SUBCOMMITTEE.*` – Subcommittee identity and membership; tier derived from the parent committee.
* `LEADERSHIP.*` – Chamber leadership assignments held by a critter.
* `CAUCUS.*` – Officially recognized caucuses and caucus leadership.
* `VOTE.*` – Roll-call vote records (chamber, roll call id, result, date).
* `PARTICIPATION.*` – Roll-call rates, missed votes, busyness, and reliability metrics.
* `AUTHORSHIP.*` – Primary sponsor, early/late thresholds, and dilution curve bindings for a bill.
* `SCORING.*` – Computed point totals, milestones, and per-critter attributions.
* `PLAYER.*` – Player identity.
* `BUDGET.*` – A player's available, committed, and future-year budget amounts.
* `OWNERSHIP.*` – Which players own a critter, and how many.

**Entity/State vs Event Rules:**

* Entity/state fields never generate points directly.
* Event fields remain the only scoreable layer.
* Entity/state fields may be referenced by scoring rules (e.g., committee tiers, leadership roles).

---

### 10.4 Disputes, Corrections, and Retroactivity Policy

This section defines how the game handles data disputes, corrections, and late-arriving information. The goal is to balance **fairness, transparency, and system stability**.

#### 10.4.1 Canonical Authority

* The designated canonical source for a data domain is always authoritative for scoring.
* Secondary sources may highlight discrepancies but **cannot override** canonical records automatically.

#### 10.4.2 Corrections and Updates

* If a canonical source issues a correction (e.g., reclassified action, corrected vote record):

  * The correction is applied **prospectively** from the time it is ingested.
  * Past scores are not silently recalculated.

* Large or material corrections may trigger a **manual correction window**, announced to all players.

#### 10.4.3 Retroactivity Rules

* The default rule is **no retroactive rescoring**.

* Retroactive changes are allowed only when:

  * The canonical source explicitly revises historical data, **and**
  * The change materially affects many critters or outcomes.

* Any retroactive change must be:

  * Clearly logged
  * Communicated to players
  * Applied uniformly across all leagues

#### 10.4.4 Dispute Handling

* Player disputes do not change scores directly.

* Disputes may trigger:

  * Data audits
  * Clarification of normalization rules
  * Future rubric adjustments

* Individual score adjustments in response to disputes are not permitted.

#### 10.4.5 Transparency & Auditability

* All scoreable events retain a reference to:

  * Source domain
  * Canonical source identifier
  * Ontology event type

* Where feasible, players may view:

  * Why an event scored
  * Why an expected event did not score

**Design Intent:**

* Consistency beats precision in a competitive fantasy environment
* Players should be able to reason about outcomes, even when data is imperfect
* Trust is maintained through clarity, not constant correction

---

## 10.5 Worked Example: From Raw Data to Score (Illustrative)

This example demonstrates how a single real-world legislative effort is converted into fantasy points. It is **illustrative only** and introduces no new rules.

### Scenario Setup

* **Bill:** H.R. XXXX – Example Infrastructure Reform Act
* **Session:** Regular legislative session
* **Critter A:** Member of the House Transportation & Infrastructure Committee
* **Critter B:** House Majority Leader (not on committee)

Both critters are rostered by players.

---

### Step 1: Raw Canonical Events (Simplified)

Canonical bill feed reports the following sequence:

1. Bill introduced by Critter A
2. Committee referral to Transportation & Infrastructure
3. Committee hearing held
4. Committee markup held
5. Ordered reported by committee
6. Placed on House calendar
7. Passed House

---

### Step 2: Normalization into Internal Ontology

The ingestion layer maps these to ontology events:

* `BILL_INTRODUCED`
* `COMMITTEE_HEARING_HELD`
* `COMMITTEE_MARKUP`
* `ORDERED_REPORTED`
* `PLACED_ON_CALENDAR`
* `PASSED_CHAMBER`

No secondary-only events are created.

---

### Step 3: Eligibility & Gating Checks

| Event                  | Critter A   | Critter B                                       |
| ---------------------- | ----------- | ----------------------------------------------- |
| BILL_INTRODUCED        | Full Credit | No Credit                                       |
| COMMITTEE_HEARING_HELD | Full Credit | No Credit                                       |
| COMMITTEE_MARKUP       | Full Credit | No Credit                                       |
| ORDERED_REPORTED       | Full Credit | No Credit                                       |
| PLACED_ON_CALENDAR     | Full Credit | No Credit                                       |
| PASSED_CHAMBER         | Full Credit | No Credit                                       |

Other Transportation & Infrastructure members who did not sponsor or co-sponsor the bill score nothing for its committee events. Critter B is not a sponsor or co-sponsor, so scheduling the bill and passing it earn B nothing per-bill; the Majority Leader role is rewarded through positional points.

---

### Step 4: Authorship Intensity

* Critter A is the **Author / Primary Sponsor**
* Critter B has **no authorship category**

Authorship intensity applies only to Critter A for authorship-eligible events.

---

### Step 5: Coalition Dilution

* Few co-sponsors
* Dilution curve remains shallow
* Critter A retains dominant share of authorship-based credit

---

### Step 6: Final Scoring Outcome (Conceptual)

* **Critter A** earns:

  * Multiple productivity scores across attempts and results
  * Full committee-gated credit
  * Strong authorship intensity

* **Critter B** earns:

  * No productivity from this bill (not a sponsor or co-sponsor)
  * Leadership value only through positional points

Positional / structural power for both critters is scored **separately** via the positional pipeline.

---

### Why This Example Matters

* Demonstrates committee gating in practice
* Shows leadership cannot score a bill it did not back
* Illustrates separation of power and productivity
* Confirms no retroactive or secondary-source scoring

---

