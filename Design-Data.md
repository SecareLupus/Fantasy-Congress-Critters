# Fantasy Congress Critters – Data, Ontology, and Normalization

Documents: [Overview](README.md) | [Scoring](Design-Scoring.md) | [Economy](Design-Economy.md) | [Rulesets](Design-Rulesets.md) | [Data](Design-Data.md) | [Pages](Design-Pages.md)

---
## 10. Data Sources, Authority, and Normalization (Draft)

This section defines how *Fantasy Congress Critters* ingests real-world data, determines authority, and converts raw records into scoreable events. The goal is **stability, reproducibility, and transparency**, not perfect historical truth.

---

### 10.1 Data Domains & Canonical Sources

For each data domain, the game designates **one canonical source of record**. Only canonical sources may directly generate scoreable events.

| Data Domain                      | Canonical Source (Conceptual)   | Purpose                         |
| -------------------------------- | ------------------------------- | ------------------------------- |
| Legislation (bills, resolutions) | Official congressional bill API | Bill lifecycle, status, actions |
| Committees & memberships         | Official House / Senate records | Jurisdiction, gating, power     |
| Roll-call votes                  | Official roll-call vote feeds   | Participation & voting          |
| Committee schedules & hearings   | Official committee calendars    | Hearings, markups, oversight    |
| Fundraising & donations          | FEC filings                     | Draft pricing inputs            |
| Elections & incumbency           | Official election results       | Seating, term status            |
| Election odds                    | Chosen odds aggregator          | Candidate & future pricing      |

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

**Illustrative Event Types:**

* `BILL_INTRODUCED`
* `PRIMARY_SPONSOR_ASSIGNED`
* `COSPONSOR_ADDED`
* `COMMITTEE_HEARING_HELD`
* `COMMITTEE_MARKUP`
* `ORDERED_REPORTED`
* `PLACED_ON_CALENDAR`
* `FLOOR_CONSIDERATION`
* `AMENDMENT_OFFERED`
* `AMENDMENT_ADOPTED`
* `PASSED_CHAMBER`
* `CONFERENCE_APPOINTED`
* `SIGNED_INTO_LAW`

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
| PLACED_ON_CALENDAR     | Full Credit | Suppressed Credit (leadership agenda influence) |
| PASSED_CHAMBER         | Full Credit | Full Credit                                     |

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

  * Limited productivity from calendar placement (suppressed)
  * Full credit for chamber passage
  * No committee-derived productivity

Positional / structural power for both critters is scored **separately** via the positional pipeline.

---

### Why This Example Matters

* Demonstrates committee gating in practice
* Shows suppressed credit without bypassing jurisdiction
* Illustrates separation of power and productivity
* Confirms no retroactive or secondary-source scoring

---

