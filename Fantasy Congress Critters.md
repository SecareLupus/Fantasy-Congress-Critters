# Fantasy Congress Critters

## Game Design Document (Living Draft)

---

## 1. High-Level Concept

**Fantasy Congress Critters** is a fantasy sports–style game where players draft U.S. congressional actors (“Critters”) and earn points based on real-world legislative activity, influence, and participation. Players manage budgets across legislative years, weigh risk vs. reward when drafting incumbents or candidates, and are rewarded for early investment in successful legislative ideas rather than passive alignment with popular outcomes.

The core fantasy tension:

* **Predicting power** vs **predicting productivity** (power is flat positional value; productivity is earned through work and results)
* **Early conviction** vs **late bandwagoning**
* **Institutional leverage** vs **showy but empty activity**

---

## 2. What Critters *Are* vs What Critters *Do*

A central design principle is distinguishing *structural power* from *executed action*.

### 2.1 What a Critter *Is* (Positional / Structural Points)

These represent institutional leverage independent of day-to-day behavior.

**Power is a flat value per session**, determined by the critter’s positions and appointments, and **pro-rated** if a role is not held for the full session.

Critters earn positional points for:

* Committee memberships
* Subcommittee memberships
* Committee leadership (Chair, Ranking Member)
* Chamber leadership roles (Speaker, Majority/Minority Leader, Whip, etc.)
* Formal caucus leadership roles (if officially recognized)

Roll-call participation percentage for a given position acts as a **raw multiplier** on all positional points earned from that position.

**Design intent:**

* Structural points reflect *capacity to influence outcomes*, not outcomes themselves.
* Positional power is stable and predictable within a session.
* Participation determines how much of that power is actually realized.
* Structural points are capped to prevent pure role-hoarding from dominating play.

---

### 2.2 What a Critter *Does* (Action / Outcome Points)

These represent intentional effort and successful follow-through.

**Productivity rewards both attempts and results**, with attempts worth a low–to–medium amount and successful outcomes worth a high amount.

Critters earn productivity points for:

* Introducing legislation
* Sponsoring or co-sponsoring legislation
* Advancing legislation through committees
* Floor action (amendments offered, debate participation)
* Passage milestones (committee, chamber, bicameral, enactment)

Outcome points scale by:

* How far the legislation progressed
* How early the critter was involved
* How intense their participation was (Author / Primary Sponsor vs one of many co-sponsors)

**Important rule:**

> Critters do **not** receive points for outcomes they did not meaningfully pursue.

Example:

* A bill passes unanimously → only critters who introduced, sponsored, amended, or actively advanced it score points.

---

## 3. Investment Depth & Credit Assignment

Not all participation is equal.

### 3.1 Authorship vs Bandwagoning

Points scale by *degree of investment* and *timing*:

* Primary sponsor / author → highest point value
* Early co-sponsor (pre-viability) → high value
* Late co-sponsor (post-momentum) → reduced value
* Symbolic or procedural co-sponsorship → minimal value

**Design intent:** reward foresight, not opportunism.

---

### 3.2 Shared Credit & Diminishing Returns

* Multiple critters may score on the same bill
* Total available points may be capped
* Credit is distributed along an **ordinal dilution curve**

If the original sponsor or author can be identified:

* The original sponsor anchors the curve
* Early sponsors receive meaningfully higher shares
* Each additional sponsor receives a progressively smaller marginal share

**Design intent:** large coalitions reward coordination, but individual credit diminishes smoothly rather than collapsing abruptly.

---

## 4. Participation & Attendance ("Showing Up Matters")

### 4.1 Roll Call Participation

Roll-call participation percentage for a given position is a **direct multiplier** against any positional / structural points earned for that position.

* Higher participation directly increases realized power
* Missed votes reduce the value of held positions

Participation modifiers are position-specific and session-specific.

---

### 4.2 Official Busyness

**Busyness is measured strictly by official congressional work.**

Counts positively:

* Committee hearings
* Subcommittee meetings
* Markups
* Floor sessions
* Official congressional travel / delegations

Does *not* count:

* Fundraising events
* Campaign appearances
* Lobbyist meetings
* Media appearances
* Arbitrary calendar padding

**Key rule:**

> A critter’s schedule can never be gamed by non-legislative activity.

Busyness is used as a **modifier**, not a raw score:

* High busyness + high participation → bonus
* High busyness + low participation → penalty

---

## 5. Drafting & Pricing Model

> Despite the name, this is **not a zero-sum draft**. Critters may be purchased by multiple players.

### 5.1 Draft Currency

* Players acquire critters using **USD-denominated budgets**
* Critter prices float based on real-world financial and political data
* Critters may be purchased **before or during** a session

Timing modifiers apply:

* Pre-session purchases are cheapest
* Mid-session purchases are pro-rated but carry a premium due to reduced control window

---

### 5.2 Pricing Full Critters (Current Session)

Each critter has a **Session Cost**.

* Session Cost defines the total price for owning the critter for the full session
* Cost is **extracted periodically** (e.g., weekly or monthly) from the player’s available balance
* Players cannot overspend beyond their available balance

Rules:

* A critter cannot be purchased for less than a full session commitment
* If a critter leaves office mid-session (resignation, death, special election loss):

  * Periodic charges stop immediately
  * No further payments are required

Base price derived from:

* Total donations raised (cycle-adjusted)

Modifiers:

* Up for re-election this session → price increase
* Past session effectiveness vs league average → up/down adjustment
* Leadership or high-impact committee roles → premium

---

### 5.3 Drafting Candidates

Players may purchase **non-incumbent candidates** at a discount.

Candidate pricing:

* Based on public election odds (prediction markets, polling aggregates, etc.)
* Lower odds → cheaper cost
* High volatility → higher risk/reward

Candidates:

* Cost is levied against the **future legislative year’s budget**
* Score **zero points** until seated

---

### 5.4 Drafting Future Incumbents

Players may purchase incumbents **for the next legislative year** at a discount.

Rules:

* Cost is based on election odds
* Incumbency mitigates, but does not eliminate, the discount
* Incumbents are *always* more expensive than raw odds would suggest
* Cost is levied against the **future year’s budget**

**Design intent:** incumbency is safer, but never cheap.

---

## 6. Budgeting Across Legislative Years

---

## 6A. Rulesets & Engine Configuration (Draft)

Fantasy Congress Critters is designed around **pluggable rulesets**. Scoring, pricing, and eligibility logic are driven by a ruleset configuration rather than hardcoded behavior.

### 6A.1 Default Ruleset

* The **Default Ruleset** defines the canonical way the game is played.
* It is intended to be:

  * Stable
  * Backward-compatible
  * Changed rarely and deliberately

The default ruleset is used for:

* Public leagues
* Long-running dynasty leagues
* Historical comparisons

---

### 6A.2 Seasonal Rulesets

* **Seasonal Rulesets** may override or extend the default ruleset.
* They are optional and time-bound.

Examples of seasonal variations:

* Adjusted committee prestige for a specific Congress
* Experimental scoring tweaks
* Event-specific mechanics (e.g., shutdowns, impeachment periods)

Seasonal rulesets:

* Are explicitly labeled
* Apply only to sessions/leagues that opt into them
* Never retroactively alter completed sessions

---

### 6A.3 Custom League Rulesets

Custom leagues may define their own rulesets by:

* Selecting a base ruleset (default or seasonal)
* Applying a controlled set of overrides

Custom rules may affect:

* Scoring categories enabled
* Budget constraints
* Ownership limits
* Suppression or dilution behavior

**Guardrails:**

* Custom rulesets cannot violate core engine invariants (e.g., no negative scores, no retroactive scoring without consent).
* League metadata always records the active ruleset and version.

---

### 6.1 Annual Budgets

* Budgets are allocated **per legislative year**
* Players must plan across:

  * Multiple sessions
  * Both chambers
  * Future elections

---

### 6.2 Budget Allocation Rules

* Drafting critters for the current year draws from the current year’s budget
* Drafting candidates or future incumbents draws from the *future* year’s budget
* No cross-year budget borrowing

**Strategic tension:**

> Spend now for points, or invest early for dominance later.

---

## 7. Core Player Skills Rewarded

* Political foresight
* Understanding institutional power
* Risk management
* Opportunity cost evaluation
* Long-term planning across cycles

---

## 8. Session Flow & Multi-Ownership

### 8.1 Purchasing Flow

* Players may purchase critters at any time before or during a session
* Ownership is **non-exclusive**

If multiple players purchase the same critter:

* The first purchaser pays full price
* Subsequent purchasers receive **small successive discounts**, based on order of purchase
* Discounts are intentionally modest to preserve early-mover advantage

---

## 8.2 Committee Prestige & Scoring System (Draft)

## Purpose

This section defines a **playable, ex ante scoring system** for congressional committee appointments in *Fantasy Congress Critters*. It is fully compatible with the positional / structural scoring framework defined in Section 2.1.

The goal is to reflect real-world prestige and power while remaining transparent, stable, and predictable within a session.

The system uses:

* **Fixed prestige tiers set at session start**
* **Flat positional point values per session**
* **Role-based multipliers applied before participation modifiers**

---

## Core Design Principles (Committee Power)

1. **Prestige is sticky** – Standing committee value does not change mid-session.
2. **Perception > metrics** – Tiers reflect how critters *believe* power works.
3. **Roles matter** – Chairs and leadership positions multiply value.
4. **Temporary power is real** – Select committees can spike influence briefly.

---

## Committee Prestige Tiers (Ex Ante, Session-Locked)

### Tier 1 – Power Committees

*High control over money, rules, or national security; strong leadership pipeline.*

**Examples (illustrative):**

* Appropriations
* Ways & Means / Finance
* Armed Services
* Energy & Commerce
* Rules (House)

**Base Value:** [TIER_1_BASE_VALUE]

---

### Tier 2 – Major Policy Committees

*Significant jurisdiction, high visibility, but less direct control over spending or rules.*

**Examples:**

* Judiciary
* Foreign Affairs / Foreign Relations
* Homeland Security
* Budget
* Transportation & Infrastructure

**Base Value:** [TIER_2_BASE_VALUE]

---

### Tier 3 – Secondary / Specialized Committees

*Focused jurisdictions; valued by specific constituencies or regions.*

**Examples:**

* Agriculture
* Veterans’ Affairs
* Science, Space & Technology
* Natural Resources
* Small Business

**Base Value:** [TIER_3_BASE_VALUE]

---

### Tier 4 – Low-Prestige / Administrative Committees

*Narrow scope, limited agenda-setting power, or ceremonial functions.*

**Examples:**

* House Administration
* Ethics
* Joint Library / Printing

**Base Value:** [TIER_4_BASE_VALUE]

---

## Role-Based Modifiers

Applied to the committee’s base value.

| Role                | Multiplier                        | Notes                            |
| ------------------- | --------------------------------- | -------------------------------- |
| Chair               | ×[CHAIR_MULTIPLIER]               | Major prestige and control       |
| Ranking Member      | ×[RANKING_MEMBER_MULTIPLIER]      | Minority leadership              |
| Subcommittee Chair  | ×[SUBCOMMITTEE_CHAIR_MULTIPLIER]  | Applies to parent committee tier |
| Subcommittee Member | ×[SUBCOMMITTEE_MEMBER_MULTIPLIER] | Rounds down                      |
| Regular Member      | ×[REGULAR_MEMBER_MULTIPLIER]      | Base value                       |

---

## Subcommittee Rules & Structural Compatibility

* Subcommittees **do not have independent tiers**.
* Their value is always derived from the **parent committee**.
* A critter may score **both** committee and subcommittee points if applicable.

---

## Select / Special Committees (Temporary Power)

### Characteristics

* Created mid-session by event or resolution
* Temporary lifespan (defined at creation)
* High short-term visibility

### Scoring

* Assigned a **temporary tier** at creation:

  * Crisis / scandal oversight: Tier 1½ ([TEMP_TIER_1_5_BASE_VALUE])
  * Policy study / reform: Tier 2 ([TEMP_TIER_2_BASE_VALUE])
* Chairs still receive role multipliers
* Committee expires automatically when event ends

---

## Ad Hoc Committees & Task Forces

* One-off, narrative-driven bodies
* **Flat value** (no multipliers): [AD_HOC_COMMITTEE_VALUE_RANGE]
* Designed for flavor, alliances, or story arcs

---

## Mid-Session Changes & Proration

* Standing committee tiers **never change mid-session**
* Membership changes recalculate points normally
* Only a **Major Reform Event** may trigger a full tier reset

---

## Optional Advanced Rules (Future)

* Prestige decay for inactive committees
* Media spotlight bonus
* Faction synergy bonuses

---

## Summary (Committee Scoring Integration)

This system locks in committee prestige at the start of a session, uses clear tiers for playability, and allows temporary spikes of power through select committees and events—mirroring real congressional behavior while keeping scoring predictable and fair.

## 8.3 Action Scoring Rubric (Draft v0.1)

> **Action Classification Tags** Each action below is classified along three orthogonal axes used elsewhere in scoring:
>
> * **Attempt vs Result**: whether the action represents effort or a realized outcome
> * **Authorship-Eligible**: whether authorship / sponsorship intensity modifiers may apply
> * **Committee-Gated**: whether the action only scores if the critter serves on the relevant committee
>
> These tags are **categorical only** and do not imply point values.

> **Note:** All point values are symbolic placeholders (e.g. `{PTS_X}`) and will be resolved by scoring rubrics defined elsewhere.
> This rubric assumes an **event-driven scoring system**: each qualifying legislative action produces one scoreable event.

---

### Authorship Intensity Scaling (Categorical)

Authorship intensity defines **how much credit a critter receives** for an authorship-eligible action. This scale is applied *after* base action scoring and *before* coalition dilution.

These categories are **ordinal, not numeric**. Exact multipliers will be defined in a separate rubric.

**Authorship Categories:**

* **Author** – Drafted or introduced the bill text; sole or primary originator.
* **Primary Sponsor** – Official lead sponsor listed on the legislation.
* **Early Co-Sponsor** – Joined before the bill demonstrated viability (pre-hearing or pre-calendar).
* **Late Co-Sponsor** – Joined after momentum was established.
* **Procedural / Symbolic Co-Sponsor** – Joined at or near passage with minimal demonstrated investment.

**Key Rules:**

* Only actions explicitly marked *Authorship-Eligible* may reference this scale.
* A critter may only occupy **one authorship category per bill**.
* Early vs late thresholds are defined relative to the bill’s progression, not absolute dates.
* Authorship intensity **never applies to positional / structural points**.

---

### Committee Gating & Suppression Rules

This subsection defines how **committee membership gates or suppresses action scoring**. It resolves when an action scores fully, partially, or not at all based on a critter’s official assignments.

These rules apply **only to productivity / action points** and never affect positional / structural power.

#### Gating Outcomes

* **Full Credit** – Action scores normally.
* **Suppressed Credit** – Action scores at a reduced level defined by categorical rules below.
* **No Credit** – Action does not score.

#### Suppressed Credit Semantics (Categorical)

Suppressed credit represents **partial recognition of influence without full jurisdictional authority**. It is intentionally weaker than full credit but stronger than zero, and exists to model agenda-setting and indirect power.

Suppressed credit is applied **after eligibility checks** and **before authorship intensity and coalition dilution**.

**Core Semantics:**

* Suppressed credit **cannot exceed** the lowest full-credit outcome for the same action type.
* Suppressed credit **never stacks** with authorship intensity bonuses unless explicitly allowed.
* Suppressed credit may be subject to **hard caps** defined per action category.

---

#### Suppression Eligibility by Action Category

| Action Category                    | Suppression Allowed | Notes                                  |
| ---------------------------------- | ------------------- | -------------------------------------- |
| Committee hearings                 | Yes                 | Leadership agenda influence only       |
| Committee markups                  | No                  | Jurisdiction strictly enforced         |
| Ordered reported / reported        | No                  | Requires committee vote                |
| Discharge motions                  | Yes                 | Procedural override without membership |
| Floor scheduling (rules, calendar) | Yes                 | Chamber leadership only                |
| Conference committees              | Yes                 | Limited to appointed members           |
| Oversight hearings                 | No                  | Committee membership required          |
| Subpoenas                          | No                  | Chair / ranking only                   |

---

**Explicit Non-Cases (Never Suppressed):**

* Bill introduction
* Sponsorship / co-sponsorship
* Floor votes
* Amendments offered

In these cases, actions either receive **full credit** or **no credit**, never suppressed credit.

**Design Intent:**

* Preserve the importance of formal jurisdiction
* Reward indirect power without letting it dominate
* Prevent leadership roles from bypassing committee structure

#### Core Rules

1. **Committee-Gated actions** require the critter to be:

   * A member of the relevant committee or subcommittee **at the time of the action**, or
   * A formal committee leader with jurisdictional authority.
2. If the above condition is not met, the action yields **No Credit**, unless an explicit exception applies.
3. Committee membership is evaluated **per chamber** (House ≠ Senate).

#### Standard Exceptions (Explicitly Allowed)

The following actions always score at **Full Credit**, regardless of committee membership:

* Bill introduction
* Sponsorship / co-sponsorship
* Floor votes
* Floor amendments
* Passage votes

#### Leadership & Jurisdiction Overrides

* Committee Chairs and Ranking Members may score **Full Credit** for committee-gated actions even if acting outside a formal hearing or markup.
* Chamber leadership (Speaker, Majority/Minority Leaders, Whips) may receive **Suppressed Credit** for committee-gated actions when acting through agenda control rather than committee process.

#### Select / Special Committees

* Membership on a select or special committee satisfies committee-gating **only for actions under that committee’s charter**.
* Select committee authority never substitutes for standing committee jurisdiction.

#### Oversight, Subpoenas, and Investigations

* Oversight hearings and subpoenas are **always committee-gated**.
* Only committee members or leadership score these actions.
* Chairs receive enhanced authorship eligibility where applicable.

#### Design Intent

* Committees define *who is allowed to act*, not just who gets bonus points.
* Power without jurisdiction cannot be farmed for productivity.
* Leadership matters, but does not fully bypass committee structure.

---

### Scoring Pipeline (Conceptual Diagram)

The following diagram shows the **order of operations** for converting a real-world legislative event into fantasy points. This pipeline is **conceptual**, not numeric.

```
Real-World Legislative Event
        ↓
Action Identified (Rubric §8.3)
        ↓
Eligibility Checks
  • Attempt vs Result
  • Committee-Gated?
        ↓
Base Action Score
        ↓
Authorship Intensity Scaling
        ↓
Coalition Dilution Curve
        ↓
Contextual Modifiers
  • Majority / minority status
  • Leadership involvement
  • Bipartisanship (if applicable)
        ↓
Final Productivity Points
```

**Important Notes:**

* Positional / structural power is **scored separately** and never enters this pipeline.
* Participation and busyness modifiers apply **outside** this pipeline.
* Each stage may reduce or nullify downstream scoring, but never increase upstream eligibility.

---

### Positional / Structural Power Pipeline (Conceptual)

This simplified pipeline governs how **institutional roles** convert into positional points. Unlike productivity, positional power is **predictable, flat, and session-scoped**.

```
Session Start or Role Change
        ↓
Role Identified
  • Committee assignment
  • Leadership position
  • Caucus role (if applicable)
        ↓
Base Positional Value
        ↓
Role-Based Multipliers
        ↓
Proration (Partial Session)
        ↓
Roll-Call Participation Multiplier
        ↓
Final Positional Power Points
```

**Key Distinctions from Productivity Pipeline:**

* No attempt/result distinction
* No authorship or coalition logic
* No outcome dependency
* Power exists even if no work is performed

---

### Designer’s Note: Why Separate Pipelines Exist

Fantasy Congress Critters intentionally separates **power** from **productivity** into two independent scoring pipelines.

This separation exists to:

* Reward *predicting influence* separately from *predicting effort*
* Prevent institutional roles from crowding out action-based play
* Make positional scoring transparent and non-exploitable
* Allow productivity scoring to be noisy and expressive without destabilizing balance

In real legislatures, power enables action but does not guarantee it. This system mirrors that reality by ensuring:

* Power provides *opportunity*
* Productivity reflects *choices and execution*
* Players must decide which they value more, and when

---

### 1. Bill Introduction & Sponsorship Actions

### 1.1 Bill or Resolution Introduced

* **Type:** Attempt

* **Authorship-Eligible:** Yes

* **Committee-Gated:** No

* **Description:** Member introduces a bill or resolution.

* **Score:** `{PTS_BILL_INTRO}`

* **Frequency:** Common (high-volume, low individual impact)

**Data Mapping**

* Bill Status: `introducedDate`, `sponsors[]`

**Design Notes**

* Only award once per bill.
* Optional rarity modifier by bill type.

---

### 1.2 Original Sponsor

* **Type:** Attempt

* **Authorship-Eligible:** Yes (Primary)

* **Committee-Gated:** No

* **Description:** Member is listed as primary sponsor.

* **Score:** `{PTS_PRIMARY_SPONSOR}`

* **Frequency:** Common

**Data mapping**

* Sponsors array where `isByRequest == false`

---

### 1.3 Cosponsor Added

* **Type:** Attempt

* **Authorship-Eligible:** Yes (Secondary)

* **Committee-Gated:** No

* **Description:** Member formally cosponsors a bill.

* **Score:** `{PTS_COSPONSOR}`

* **Frequency:** Very common (extremely high-volume; typically low-weighted)

**Data mapping**

* `cosponsors[]`

**Notes**

* Optional cap per bill.
* Optional bipartisan bonus.

---

### 2. Committee Referral & Committee Power Actions

### 2.1 Committee Referral

* **Type:** Attempt

* **Authorship-Eligible:** No

* **Committee-Gated:** Yes

* **Description:** Bill referred to a committee where the member serves.

* **Score:** `{PTS_COMMITTEE_REFERRAL}`

**Data mapping**

* `committees[]`

---

### 2.2 Committee Hearing Held

* **Type:** Result

* **Authorship-Eligible:** No

* **Committee-Gated:** Yes

* **Description:** Committee holds a hearing on the bill.

* **Score:** `{PTS_HEARING}`

**Data mapping**

* `actions[].text` contains "Hearing"

**Notes**

* Requires keyword parsing.

---

### 2.3 Committee Markup

* **Type:** Result

* **Authorship-Eligible:** No

* **Committee-Gated:** Yes

* **Description:** Committee marks up the bill.

* **Score:** `{PTS_MARKUP}`

**Data mapping**

* `actions[].text` contains "markup"

---

### 2.4 Ordered Reported by Committee

* **Type:** Result

* **Authorship-Eligible:** No

* **Committee-Gated:** Yes

* **Description:** Committee votes to report the bill.

* **Score:** `{PTS_ORDERED_REPORTED}`

**Data mapping**

* `actions[].text` contains "Ordered to be Reported"

---

### 2.5 Reported by Committee

* **Type:** Result

* **Authorship-Eligible:** No

* **Committee-Gated:** Yes

* **Description:** Committee formally reports the bill.

* **Score:** `{PTS_REPORTED}`

**Data mapping**

* `committees[].report`

---

### 2.6 Committee Discharged

* **Description:** Committee discharged from consideration.
* **Score:** `{PTS_DISCHARGED}`

**Data mapping**

* `actions[].text` contains "Discharged"

---

### 3. Floor Scheduling & Procedural Actions

### 3.1 Placed on Calendar

* **Type:** Result

* **Authorship-Eligible:** No

* **Committee-Gated:** No

* **Score:** `{PTS_CALENDAR}`

* **Data mapping:** `actions[].text` contains "Placed on the Calendar"

---

### 3.2 Rule Reported / Agreed To (House)

* **Score:** `{PTS_RULE}`
* **Data mapping:** `actions[].text` contains "Rule"

---

### 3.3 Motion to Proceed (Senate)

* **Score:** `{PTS_MOTION_TO_PROCEED}`
* **Data mapping:** `actions[].text` contains "Motion to proceed"

---

### 3.4 Cloture Filed / Invoked

* **Score:** `{PTS_CLOTURE_FILED}`, `{PTS_CLOTURE_INVOKED}`
* **Data mapping:** `actions[].text` contains "Cloture"

---

### 4. Floor Consideration & Amendment Actions

### 4.1 Floor Consideration

* **Score:** `{PTS_FLOOR_CONSIDERATION}`
* **Data mapping:** `actions[].text` contains "Considered"

---

### 4.2 Amendment Offered

* **Type:** Attempt

* **Authorship-Eligible:** Yes

* **Committee-Gated:** No

* **Score:** `{PTS_AMENDMENT_OFFERED}`

* **Data mapping:** `actions[].text` contains "Amendment"

---

### 4.3 Amendment Agreed To

* **Type:** Result

* **Authorship-Eligible:** Yes

* **Committee-Gated:** No

* **Score:** `{PTS_AMENDMENT_PASSED}`

---

### 4.4 Amendment Rejected

* **Score:** `{PTS_AMENDMENT_FAILED}`

---

### 5. Passage & Bicameral Actions

### 5.1 Passed House / Senate

* **Type:** Result

* **Authorship-Eligible:** Yes (Diluted)

* **Committee-Gated:** No

* **Score:** `{PTS_PASS_CHAMBER}`

* **Data mapping:** `latestAction.text` contains "Passed"

---

### 5.2 Conference Committee Appointed

* **Score:** `{PTS_CONFERENCE}`
* **Data mapping:** `actions[].text` contains "Conference"

---

### 5.3 Conference Report Agreed To

* **Score:** `{PTS_CONF_REPORT}`

---

### 6. Presidential Actions

### 6.1 Presented to President

* **Score:** `{PTS_PRESENTED}`

---

### 6.2 Signed Into Law

* **Type:** Result

* **Authorship-Eligible:** Yes (Heavily Diluted)

* **Committee-Gated:** No

* **Score:** `{PTS_SIGNED_LAW}`

---

### 6.3 Vetoed

* **Score:** `{PTS_VETOED}`

---

### 6.4 Veto Override

* **Score:** `{PTS_OVERRIDE_CHAMBER}`

---

### 7. Non-Bill Legislative Actions

### 7.1 Roll Call Vote Cast

* **Score:** `{PTS_VOTE}`
* **Source:** House and Senate roll call vote data

---

### 7.2 Confirmation Vote

* **Score:** `{PTS_CONFIRM_VOTE}`

---

### 7.3 Confirmation Approved

* **Score:** `{PTS_CONFIRM_SUCCESS}`

---

### 7.4 Oversight Hearing Chaired

* **Score:** `{PTS_OVERSIGHT}`

---

### 7.5 Subpoena Issued

* **Score:** `{PTS_SUBPOENA}`

---

### 8. Implementation Notes

* Many actions require **text normalization** of `actions[].text`.
* Normalize raw events into a controlled vocabulary before scoring.
* Avoid double-counting related or causally-linked actions (e.g., markup → reported).
* Optional modifiers (applied elsewhere): majority status, committee role, election year context, bipartisan outcomes.

## 9. Session-Level Anti-Exploit Rules

These rules apply at the **session level** to prevent degenerate strategies that exploit volume, timing, or procedural churn.

### 9.1 Action Frequency Caps

* High-frequency actions (e.g., cosponsorships, votes) may be capped per critter per bill or per session.
* Caps are defined by action category, not by player ownership.

### 9.2 Diminishing Returns on Repeated Actions

* Repeated actions of the same type on the same bill may follow a diminishing returns curve.
* First meaningful action receives full eligibility; subsequent actions may be suppressed or ignored.

### 9.3 Cooldowns for Procedural Actions

* Procedural force actions (e.g., discharge, cloture) may trigger cooldowns before similar actions score again.
* Cooldowns are action-type specific and session-scoped.

### 9.4 Mid-Session Role Changes

* Gaining a committee or leadership role mid-session does not retroactively unlock suppressed or blocked actions.
* Only actions occurring **after** the role change are eligible.

### 9.5 Ownership-Neutral Enforcement

* Anti-exploit rules apply to critters, not players.
* Multiple ownership does not reset caps, cooldowns, or suppression states.

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

## 11. Open Design Questions (For Next Iteration)

* Exact numeric point formulas and caps
* Shape of ordinal dilution curves
* Amendment vs standalone bill weighting
* Handling multi-year bills
* Scoring vetoes and executive interaction
* Anti-exploit safeguards

---

## 12. How Scoring Works (Player-Facing Overview)

This section explains how *Fantasy Congress Critters* scoring works **from a player’s perspective**. It is intentionally simplified and omits internal terminology, data pipelines, and implementation details.

### 12.1 Two Ways to Score: Power and Productivity

Critters earn points in two fundamentally different ways:

**Power** reflects *who your critter is*.

* Committee assignments
* Leadership roles
* Formal positions

Power is:

* Predictable
* Mostly steady across a session
* Reduced if your critter misses votes

**Productivity** reflects *what your critter does*.

* Writing bills
* Moving legislation forward
* Voting, debating, and amending

Productivity is:

* Event-based
* Volatile
* Highly dependent on timing and involvement

Most successful teams balance both.

---

### 12.2 Why Early Action Matters

Not all participation is equal.

* Writing or sponsoring a bill early earns more credit than joining later.
* Helping a bill before it becomes popular is worth more than signing on at the end.
* Large coalitions still score, but individual credit is shared.

If you believe in an idea early — and you’re right — you’re rewarded.

---

### 12.3 Committees Matter (A Lot)

Most real legislative work happens in committees.

In the game:

* Many actions only score if your critter is on the right committee.
* Committee leadership unlocks more opportunities.
* Being powerful without jurisdiction limits what you can score.

Leadership can influence outcomes — but committees still do the work.

---

### 12.4 Showing Up Still Counts

Holding a powerful role doesn’t help if your critter doesn’t participate.

* Missing votes reduces the value of positions.
* Busy schedules only help if your critter actually attends official business.
* Fundraising and campaigning never count as "activity."

Reliability matters.

---

### 12.5 Why Scores Sometimes Lag or Feel Incomplete

Scores are based on official congressional records.

That means:

* Some actions appear hours or days after they happen.
* Not every headline-worthy moment generates points.
* Scores don’t change just because another website reports something differently.

This keeps the game fair, consistent, and predictable over time.

---

### 12.6 What Happens When Data Changes

Occasionally, official records are corrected.

When that happens:

* Scores usually update going forward, not backward.
* Large corrections are announced clearly.
* Individual disputes don’t change individual scores.

This prevents surprise rescoring and keeps competition fair.

---

### 12.7 The Core Skill the Game Rewards

*Fantasy Congress Critters* rewards players who can:

* Spot real influence early
* Understand how Congress actually works
* Balance safety and risk
* Think across multiple sessions and elections

If you can predict *who will matter* and *who will actually do the work*, you’ll do well.

---

*This overview is intended to build intuition and trust. The full rules exist to keep that intuition honest.*

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
* `committee.type` (enum: standing, select, joint, ad_hoc)
* `committee.jurisdiction` (string)
* `committee.session_id` (string)
* `committee.tier` (enum: 1, 2, 3, 4, 1.5, 2.0)
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
* `league.session_id` (string)
* `league.ruleset.id` (string)
* `league.ruleset.version` (string)
* `league.config.budget_rules` (object: annual_budget, caps, rollover_policy)
* `league.config.roster_rules` (object: roster_limit, ownership_limits)
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
* `league.session_id` -> `SESSION.ID`
* `league.ruleset.id` -> `RULESET.ID`
* `league.ruleset.version` -> `RULESET.VERSION`
* `league.config.budget_rules` -> `LEAGUE.BUDGET_RULES`
* `league.config.roster_rules` -> `LEAGUE.ROSTER_RULES`
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
* `roster.budget.committed` (number)
* `roster.budget.future_commitments` (number)
* `roster.critters[]` (array of objects: critter_id, acquisition_date, cost, session_id, status)
* `roster.scoring.total` (number)
* `roster.scoring.positional` (number)
* `roster.scoring.productivity` (number)
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
