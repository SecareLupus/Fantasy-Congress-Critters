# Fantasy Congress Critters – Rulesets

Documents: [Overview](README.md) | [Scoring](Design-Scoring.md) | [Economy](Design-Economy.md) | [Rulesets](Design-Rulesets.md) | [Data](Design-Data.md) | [Pages](Design-Pages.md)

---
## 6A. Rulesets & Engine Configuration (Draft)

Fantasy Congress Critters is designed around **pluggable rulesets**. Scoring, pricing, and eligibility logic are driven by a ruleset configuration rather than hardcoded behavior.

### 6A.1 Default Ruleset

* The **Default Ruleset** defines the canonical way the game is played.
* It is intended to be:

  * Stable
  * Backward-compatible
  * Changed rarely and deliberately

The default ruleset follows a **Semantic Versioning (SemVer)** model:
* **Major (X):** Breaking changes to engine logic or fundamental scoring philosophy.
* **Minor (Y):** Adjusted constants (tiers, multipliers), new action types, or non-breaking features.
* **Patch (Z):** Bug fixes in parsing, typo corrections in documentation.

**Freezing Rule:** Once a league starts, its ruleset version is **frozen** for that lifecycle, unless a "Major Reform Event" occurs or GameMakers push a critical patch.

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

* Custom rulesets cannot violate core engine invariants (e.g., no negative critter scores, no retroactive scoring without consent).
* "No negative critter scores" means a critter's action or inaction never costs a player points. Penalties for a player's own decisions (e.g., a points-based drop cost) may deduct points from that player's total.
* League metadata always records the active ruleset and version.

---

## 6A.4 Official League Types (Standard Rules)

Official leagues are managed by GameMakers and always use the current "Standard" ruleset version.

| League Type | Duration | Description |
| :--- | :--- | :--- |
| **Session League** | Variable | Starts/Ends with a specific Legislative Session of Congress. |
| **Annual League** | 1 Year | Full calendar year lifecycle. |
| **Representative League** | 2 Years | Spans a full House of Representatives term. |
| **Presidential League** | 4 Years | Spans a U.S. Presidential term. |
| **Senatorial League** | 6 Years | Concurrent 6-year cycles, with a new league starting every 2 years (Class-based). |

> [!NOTE]
> **Class-based scheduling** references official U.S. Senate designations (Classes I, II, and III) as defined in Article I, Section 3 of the Constitution. These are not game-specific constructs but align the game with real-world election cohorts. A new league starts every 2 years to track each cohort through their full 6-year term.

---

## 6A.5 Custom League Configuration

Users may create custom leagues with varying degrees of control.

| League Type | Ruleset | Governance |
| :--- | :--- | :--- |
| **Standard Private** | Current Standard | Private membership, standard timings. |
| **Flexible Private** | Current Standard | Custom Start/End dates, private membership. |
| **Custom Ruleset** | Overridden Rules | Custom scoring/rules (Deferred to post-initial release). |

---

## 6A.6 Governance & Authority

| Authority | Responsibility |
| :--- | :--- |
| **GameMakers** | Define "Standard" ruleset versions; manage official leagues. |
| **League Commissioner** | Managed custom league settings; approves custom rules (when supported). |
| **The Engine** | Ensures scoring invariants cannot be violated by custom rules. |

---

## 6A.7 League Settings

Roster and competition rules are settings on each league, not constants in the engine or the ruleset. A game master sets them when creating the league: a GameMaker for official leagues, a commissioner for private ones. They are levers for balance and for strategic variety, so official leagues may differ from one another too.

* A league starts from a **preset**, a named set of settings authored by GameMakers ("Standard" is one), and the game master overrides any setting within the limits below. The league keeps its own copy, so editing a preset later only affects new leagues.
* A league also records the ruleset (§6A.1) it scores and prices with, frozen as a copy.
* Settings and ruleset can change until the league starts, and are frozen from then on.
* The engine rejects settings outside these limits, and ones that break core invariants.

| Setting | Options |
| :--- | :--- |
| **budget_rules.annual_budget** | Play dollars per legislative year, at least 1. Standard preset: $50,000, about 8 × the 75th-percentile Session Cost (Design-Economy §6.1). |
| **roster_rules.roster_limit** | Most critters a roster can hold, 1–100. Standard preset: 8. |
| **roster_rules.chamber_slots** | Optional: most critters from each chamber, `{house, senate}`. Each is at most the roster limit, and together they must be able to fill a roster. Standard preset: none. |
| **win_condition** | `cumulative` points, or weekly `head_to_head` matchups. Standard preset: cumulative. |
| **drop_cost.extra_fee** | Play dollars charged on a drop, on top of the signing fee (Design-Economy §5.2), which is always lost while unspent weekly fees return. Standard preset: 0. |
| **drop_cost.points_penalty** | Points deducted from the player's total on a drop, not floored at zero (a player's own decision, so it doesn't break "no negative critter scores"). Standard preset: 0. |

League timing follows the league type (§6A.4): a session or a Congress runs from January 3, a presidential league from January 20 after a presidential election, a senatorial league over a six-year class term. Standard Private leagues use one of those timings; Flexible Private leagues set their own dates.

--- | :--- |
| **Roster size** | Maximum critters per roster |
| **Roster slots** | Optional per-chamber slots (e.g., N House, M Senate) |
| **Win condition** | Cumulative points; weekly head-to-head matchups |
| **Starting budget** | Amount per legislative year (Standard: $50,000) |
| **Drop cost** | What dropping a critter costs. Standard: the signing fee (§5.2), which is never refunded, while unspent weekly fees return. Private leagues may add a flat fee from the budget or a points deduction from the player's total (not floored at zero). Without a cost, the full-session commitment has no force. |

---

Budgeting rules (Section 6) live in [Design-Economy](Design-Economy.md).

