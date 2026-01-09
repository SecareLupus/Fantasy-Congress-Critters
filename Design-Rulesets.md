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

* Custom rulesets cannot violate core engine invariants (e.g., no negative scores, no retroactive scoring without consent).
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

