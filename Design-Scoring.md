# Fantasy Congress Critters – Scoring

Documents: [Overview](README.md) | [Scoring](Design-Scoring.md) | [Economy](Design-Economy.md) | [Rulesets](Design-Rulesets.md) | [Data](Design-Data.md) | [Pages](Design-Pages.md)

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


---

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

