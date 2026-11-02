# Fantasy Congress Critters

Documents: [Overview](README.md) | [Scoring](Design-Scoring.md) | [Economy](Design-Economy.md) | [Rulesets](Design-Rulesets.md) | [Data](Design-Data.md) | [Pages](Design-Pages.md)

## At a Glance

**Fantasy Congress Critters** is a fantasy sports–style game where players draft U.S. congressional actors ("Critters") and earn points based on real-world legislative activity, influence, and participation. Players manage budgets across legislative years, weigh risk vs. reward when drafting incumbents or candidates, and are rewarded for early investment in successful legislative ideas rather than passive alignment with popular outcomes.

The core fantasy tension:

* **Predicting power** vs **predicting productivity** (power is flat positional value; productivity is earned through work and results)
* **Early conviction** vs **late bandwagoning**
* **Institutional leverage** vs **showy but empty activity**

## Core Player Skills Rewarded

* Political foresight
* Understanding institutional power
* Risk management
* Opportunity cost evaluation
* Long-term planning across cycles

---

## Where to Start

- Scoring design and rules: `Design-Scoring.md`
- Economy, drafting, and budgeting: `Design-Economy.md`
- Rulesets and engine configuration: `Design-Rulesets.md`
- Data sources, ontology, and normalization: `Design-Data.md`
- Page inventory and schemas: `Design-Pages.md`

---

## First Release Scope

**In:**

- Current-session incumbents, House and Senate
- Positional and productivity scoring
- Session and Annual leagues
- Standing committees (including permanent select and special committees)
- Play-money budgets only; no real money

**Deferred:**

- Drafting candidates and future incumbents (needs an election odds source)
- Busyness modifier (no structured data for official travel)
- Mid-session select committees and ad hoc committees
- Contextual modifiers (majority/minority, bipartisanship)
- Multi-ownership discounts (flat price at launch)
- Representative, Presidential, and Senatorial leagues
- Custom rulesets

---

## Project Status (Draft)

- Scoring values and caps are placeholders; tune by replaying past Congresses through the engine.
- Budget rules and pricing formulas are incomplete.
- Ontology mappings exist, but entity domains still need formal definitions.
