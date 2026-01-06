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

