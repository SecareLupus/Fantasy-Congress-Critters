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

Roll-call participation percentage for a given position acts as a **raw multiplier** on all positional points earned from that position (see §4.1 for which votes count).

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

* Introducing (sponsoring) legislation
* Co-sponsoring legislation
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
* Credit is distributed along an **ordinal dilution curve**
* Each critter's share is computed independently; later joiners never reduce an earlier joiner's share

If the original sponsor or author can be identified:

* The original sponsor anchors the curve
* Early sponsors receive meaningfully higher shares
* Each additional sponsor receives a progressively smaller marginal share

**Design intent:** large coalitions reward coordination, but individual credit diminishes smoothly rather than collapsing abruptly.

**Ordinal Dilution Formula:**
`CreditShare(rank) = 1 / (rank^0.5)`
Where `rank` is the order in which the critter joined the coalition (Sponsor = 1, first co-sponsor = 2, etc.).

* Co-sponsors who join on the same date share a rank (e.g., all original co-sponsors are rank 2; the next date's joiners are rank 2 + the number of original co-sponsors).
* Total credit per bill is not capped. Co-sponsors come only from the bill's chamber, which bounds the total naturally (about 40× a solo bill in the House, about 18× in the Senate).
* Volume farming (co-sponsoring large numbers of bills) is handled by per-critter session caps (§9.1), not by per-bill caps.

---

## 4. Participation & Attendance ("Showing Up Matters")

### 4.1 Roll Call Participation

Roll-call participation percentage for a given position is a **direct multiplier** against any positional / structural points earned for that position.

* Higher participation directly increases realized power
* Missed votes reduce the value of held positions

Participation modifiers are position-specific and session-specific. Which votes count depends on the position:

| Position                         | Participation measured by                  |
| -------------------------------- | ------------------------------------------ |
| Committee seat or role           | That committee's recorded roll-call votes  |
| Subcommittee seat or role        | That subcommittee's recorded roll-call votes |
| Chamber leadership role          | Chamber floor roll-call votes              |
| Caucus leadership role           | Chamber floor roll-call votes              |

Floor votes also score as individual productivity events (§8.3, 7.1). For rank-and-file members this is the only way floor attendance counts; for leadership it also feeds the multiplier, which is intended because floor management is their job.

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

Permanent select and special committees (House Permanent Select Committee on Intelligence, Senate Select Committee on Intelligence, Senate Special Committee on Aging) are tiered like standing committees. The temporary-tier rules under *Select / Special Committees* apply only to committees created mid-session.

The same committee name can sit in different tiers by chamber (e.g., House vs Senate Judiciary). The chamber mappings are authoritative; the examples are illustrative.

### Tier 1 – Power Committees

*High control over money, rules, or national security; strong leadership pipeline.*

**Examples (illustrative):**

* Appropriations
* Ways & Means / Finance
* Armed Services
* Energy & Commerce
* Rules (House)

**Base Value:** 100

**Chamber Mappings:**
*   **House:** Appropriations; Ways & Means; Energy & Commerce; Rules; Armed Services.
*   **Senate:** Appropriations; Finance; Armed Services; Foreign Relations; Judiciary.

---

### Tier 2 – Major Policy Committees

*Significant jurisdiction, high visibility, but less direct control over spending or rules.*

**Examples:**

* Judiciary (House)
* Foreign Affairs (House)
* Homeland Security
* Budget
* Transportation & Infrastructure

**Base Value:** 70

**Chamber Mappings:**
*   **House:** Judiciary; Foreign Affairs; Homeland Security; Budget; Transportation & Infrastructure; Financial Services; Oversight & Accountability; Permanent Select Committee on Intelligence.
*   **Senate:** Banking, Housing & Urban Affairs; Commerce, Science & Transportation; Energy & Natural Resources; Health, Education, Labor & Pensions; Budget; Homeland Security & Governmental Affairs; Intelligence.

---

### Tier 3 – Secondary / Specialized Committees

*Focused jurisdictions; valued by specific constituencies or regions.*

**Examples:**

* Agriculture
* Veterans’ Affairs
* Science, Space & Technology
* Natural Resources
* Small Business

**Base Value:** 40

**Chamber Mappings:**
*   **House:** Agriculture; Education & the Workforce; Natural Resources; Science, Space & Technology; Small Business; Veterans' Affairs.
*   **Senate:** Agriculture, Nutrition & Forestry; Environment & Public Works; Aging; Indian Affairs; Rules & Administration; Small Business & Entrepreneurship; Veterans' Affairs.

---

### Tier 4 – Low-Prestige / Administrative Committees

*Narrow scope, limited agenda-setting power, or ceremonial functions.*

**Examples:**

* House Administration
* Ethics
* Joint Library / Printing

**Base Value:** 15

**Chamber Mappings:**
*   **House:** House Administration; Ethics.
*   **Senate:** Ethics.
*   **Joint:** Joint Library; Joint Printing; Joint Taxation; Joint Economic.

---

## Role-Based Modifiers

Applied to the committee’s base value.

| Role                | Multiplier | Notes                            |
| ------------------- | ---------- | -------------------------------- |
| Chair               | ×3.0       | Major prestige and control       |
| Ranking Member      | ×2.0       | Minority leadership              |
| Subcommittee Chair  | ×1.5       | Applies to parent committee tier |
| Subcommittee Member | ×1.1       | Rounds down                      |
| Regular Member      | ×1.0       | Base value                       |

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

Categories are ordinal; the multipliers below are the Default Ruleset values.

**Authorship Categories:**

* **Author / Primary Sponsor** – Drafting lead or official lead sponsor: **5.0x**
* **Early Co-Sponsor** – Joined before any committee action: **2.5x**
* **Mid Co-Sponsor** – Joined during committee consideration: **1.5x**
* **Late Co-Sponsor** – Joined after the bill was reported: **1.0x**
* **Procedural / Symbolic Co-Sponsor** – Joined after floor consideration began: **0.2x**

**Stage Cutoffs:**

| Category    | Joined…                                                                      |
| ----------- | ---------------------------------------------------------------------------- |
| Early       | Before the bill's first committee hearing or markup (includes original co-sponsors) |
| Mid         | After the first hearing or markup, up to the committee reporting the bill (ordered reported, reported, or discharged) |
| Late        | After the committee reports the bill, before floor consideration begins      |
| Procedural  | After floor consideration begins                                             |

* Stages are measured in the chamber where the bill was introduced.
* If a bill skips a stage (e.g., no hearing, or brought straight to the floor), that window is empty and the next cutoff applies.

**Key Rules:**

* Only actions explicitly marked *Authorship-Eligible* may reference this scale.
* A critter may only occupy **one authorship category per bill**.
* Early vs late cutoffs are defined by the bill's progression (Stage Cutoffs above), not absolute dates.
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
| Committee hearings                 | No                  | Sponsor / co-sponsor members only      |
| Committee markups                  | No                  | Jurisdiction strictly enforced         |
| Ordered reported / reported        | No                  | Requires committee vote                |
| Discharge motions                  | Yes                 | Procedural override without membership |
| Floor scheduling (rules, calendar) | No                  | Sponsor / co-sponsors only             |
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
4. **Bill committee actions** (referral, hearing, markup, ordered reported, reported, discharged) score only for committee members who are the bill's **sponsor or a co-sponsor** at the time of the action. Other committee members score nothing for that bill, including committee chairs and ranking members.

#### Standard Exceptions (Explicitly Allowed)

The following actions always score at **Full Credit**, regardless of committee membership:

* Bill introduction
* Sponsorship / co-sponsorship
* Floor votes
* Floor amendments
* Passage votes

#### Leadership & Jurisdiction Overrides

* Committee Chairs and Ranking Members score a bill's committee actions only when they sponsor or co-sponsor it (Core Rule 4). Their role is rewarded through positional points, not per-bill credit, so it isn't counted twice.
* Chamber leadership (Speaker, Majority/Minority Leaders, Whips) scores a bill's committee and floor scheduling actions only when they sponsor or co-sponsor it. Agenda control is rewarded through positional points, not per-bill credit.

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
* Committee points go to members who back the bill, not to everyone who sits on the committee.
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

* **Description:** Member introduces a bill or resolution. Every bill has exactly one sponsor, who is the member that introduces it; introduction and primary sponsorship are the same act and score once.

* **Score:** `{PTS_BILL_INTRO}`, scaled by the **Author / Primary Sponsor** category

* **Frequency:** Common (high-volume, low individual impact)

**Data Mapping**

* Bill Status: `introducedDate`, `sponsors[]` (single entry), `isByRequest`

**Design Notes**

* Only award once per bill.
* Bills introduced "by request" (`isByRequest == true`) score with the **Procedural / Symbolic** category instead of Author, since the sponsor is not necessarily endorsing the bill.
* Optional rarity modifier by bill type.

---

### 1.2 Cosponsor Added

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

All actions in this section follow Core Rule 4: they score only for committee members who sponsor or co-sponsor the bill.

### 2.1 Committee Referral

* **Type:** Attempt

* **Authorship-Eligible:** No

* **Committee-Gated:** Yes

* **Description:** Bill referred to a committee where the member serves and is the bill's sponsor or a co-sponsor.

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

All actions in this section score only for the bill's sponsor and co-sponsors at the time of the action, including when the procedural step is taken by chamber leadership.

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

* **Score:** `{PTS_FLOOR_CONSIDERATION}`, to the bill's sponsor and co-sponsors only
* **Data mapping:** `actions[].text` contains "Considered"

---

### 4.2 Amendment Offered

* **Type:** Attempt

* **Authorship-Eligible:** Yes

* **Committee-Gated:** No

* **Score:** `{PTS_AMENDMENT_OFFERED}`, to the amendment's sponsor

* **Data mapping:** `AMENDMENT_OFFERED`. A House amendment is offered on the floor; a Senate amendment counts only when it is proposed on the floor, not when it is merely submitted (filed). Most Senate amendments are filed and never brought up.

---

### 4.3 Amendment Agreed To

* **Type:** Result

* **Authorship-Eligible:** Yes

* **Committee-Gated:** No

* **Score:** `{PTS_AMENDMENT_PASSED}`, to the amendment's sponsor

* **Data mapping:** `AMENDMENT_ADOPTED`, the amendment's final outcome

---

### 4.4 Amendment Rejected

* **Score:** `{PTS_AMENDMENT_FAILED}`, to the amendment's sponsor

* **Data mapping:** `AMENDMENT_FAILED`, the amendment's final outcome

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

## 10. Default Ruleset v0.1 (Engine Interpretations)

The scoring engine (`pipeline/src/pipeline/scoring.py`) reads every constant from [`pipeline/rulesets/default.toml`](pipeline/rulesets/default.toml). Where this document left a rule open, v0.1 decides it as follows. All point values are first guesses, calibrated by a backtest on the 118th Congress (`critters score`, `critters report`).

**Who scores an event**

* Introduction: the sponsor, as Author (by-request bills as Procedural).
* Co-sponsorship: the joining co-sponsor, with the category for the bill's stage on the join date and the dilution share for their rank.
* Committee actions (referral, hearing, markup, ordered reported, reported, discharged): backers (the sponsor and co-sponsors on the event date, less withdrawn co-sponsors) who sit on the acting committee or its parent committee that day.
* Discharge petitions, floor scheduling, floor consideration, conference, presentment and veto overrides: all backers on the event date, flat points each.
* Chamber passage and enactment: all backers, with authorship category and dilution. "Heavily diluted" enactment uses `1 / rank` instead of `1 / rank^0.5`.
* Amendments: the amendment's sponsor, as Author. Committee-sponsored amendments score no one.
* A critter scores each action type once per bill per chamber (§9.2); repeated calendar placements or referrals don't add up.
* Failed passage, failed veto overrides and vetoes score nothing in v0.1.

**Votes**

* Each yea, nay or present vote scores for a member seated that day. A vote is worth a session's full-attendance value divided by the chamber's expected roll calls (620 House, 345 Senate, the 118th's averages), so perfect attendance is worth the same in both chambers, about 30 points a session, although the House holds about twice as many roll calls. Votes are about a fifth of the median member's productivity (21% House, 18% Senate in 2023). In a year with more or fewer roll calls than expected, full attendance is worth proportionally more or less.
* Delegates and the Resident Commissioner vote only in the Committee of the Whole, so their votes are valued against those roll calls (270 expected a session; 394 in 2023, 144 in 2024). Perfect attendance is worth the same to them as to any member. Otherwise they score as House members.
* Voting yea on a nomination that is confirmed adds `{PTS_CONFIRM_SUCCESS}`. `{PTS_CONFIRM_VOTE}` is 0.

**Power**

* Committee seats: tier base × role. Ex officio seats score nothing (they're courtesy seats, mostly held by leaders scored elsewhere).
* Subcommittee seats add a bonus on the parent committee's tier base: member +10%, chair +50%, ranking member +25% (the last isn't in the design).
* Select committees formed at the session start are tiered: the China select committee and the Weaponization and Coronavirus select subcommittees at Tier 2; the Helsinki Commission and the Senate narcotics caucus at Tier 4. Ad hoc task forces are a flat 30.
* Leadership posts, per session: Speaker 400; floor leaders 300; whips 200; party conference or caucus chairs, President pro tempore and assistant leaders 100; other elected posts 40.
* Participation: committee seats use floor participation until committee votes are loaded. The Speaker, who by custom rarely votes, is exempt.
* Chamber factors: senators' positional points are multiplied by 0.43 and their productivity other than votes by 0.58, so the median senator matches the median House member on both pillars. Senators hold about twice as many seats (median 4 committees and 9 subcommittees, against 2 and 4) and do more non-vote legislating per head (median 165 against 101 in 2023). Without the factors the median senator had 386 power against 165, and senators took the whole top 10. The cost is that a senator's bill events score 58% of the same event for a House member.

**Weights and caps**

* Bill-type weight on every event of a bill: bills and joint resolutions 1.0, concurrent resolutions 0.5, simple resolutions 0.2. Simple resolutions are mostly commemorations and House rules; in the 118th, 709 of the 1,709 measures that passed a chamber were simple resolutions.
* Ceremonial bills (post office and other facility namings, Congressional Gold Medals, commemorative coins) are weighted 0.2, like simple resolutions; the lower of the two weights applies, without stacking. A bill is ceremonial if CRS tags it "Congressional tributes" and it has at most 10 subjects (big bills such as the NDAA carry the tag for one naming section), or if its title matches a naming, gold medal or coin pattern. In the 118th, 93 of the 274 laws were ceremonial (68 of them post office namings), and before the weight they earned 13.5% of all productivity points.
* Per-critter session caps near the 118th's 95th percentile: 50 introductions, 400 co-sponsorships, 40 amendments offered. Items beyond a cap stay in the ledger at zero.
* One productivity scale multiplies every productivity item. It is set so the median full-session member earns about as much from productivity as from power (0.13 for the 118th).

**Balance (118th backtest).** Medians for members seated all year, power / productivity: House 165 / 166 in 2023 and 174 / 164 in 2024; Senate 166 / 158 and 171 / 169. Senators hold 1 of the top 10 and 5 of the top 100 in 2023 (2 and 12 in 2024), below their 18% share of members: the House's 435 members produce a longer tail of high scorers.

---

## 11. Open Design Questions (For Next Iteration)

* Committee vote data: House committee votes exist only as per-committee PDFs, about half of them scans (Design-Data §10.1), and Senate committees don't publish recorded votes consistently. Committee seats use floor participation until a structured source appears.
* Amendment vs standalone bill weighting
* Handling multi-year bills
* Scoring vetoes and executive interaction

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
* Reduced if your critter misses votes in the committees or roles they hold

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

* Committee actions on a bill only score if your critter sits on that committee **and** sponsors or co-sponsors the bill.
* Committee leadership raises your critter's power, not their per-bill points.
* Being powerful without jurisdiction limits what you can score.

Leadership can influence outcomes — but committees still do the work.

---

### 12.4 Showing Up Still Counts

Holding a powerful role doesn’t help if your critter doesn’t participate.

* Missing committee votes reduces the value of committee seats; missing floor votes reduces the value of leadership roles and forfeits vote points.
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

