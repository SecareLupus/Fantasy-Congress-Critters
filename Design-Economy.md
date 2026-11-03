# Fantasy Congress Critters – Economy

Documents: [Overview](README.md) | [Scoring](Design-Scoring.md) | [Economy](Design-Economy.md) | [Rulesets](Design-Rulesets.md) | [Data](Design-Data.md) | [Pages](Design-Pages.md)

---
## 5. Drafting & Pricing Model

> Despite the name, this is **not a zero-sum draft**. Critters may be purchased by multiple players.

### 5.1 Draft Currency

* Players acquire critters using **play-money budgets** denominated in in-game dollars. No real money enters or leaves the game; real-world figures (donations, election odds) are only pricing inputs.
* Critter prices float based on real-world financial and political data
* Critters may be purchased **before or during** a session

Timing modifiers apply:

* Pre-session purchases are cheapest
* Mid-session purchases are pro-rated but carry a premium due to reduced control window

Both come from the signing fee (§5.2): it is paid in full whenever a critter is bought, so the earlier the purchase, the more weeks it covers.

---

### 5.2 Pricing Full Critters (Current Session)

Each critter has a **Session Cost**.

Every seated member of the House or Senate can be purchased, including the five delegates and Puerto Rico's Resident Commissioner. They serve on committees, introduce and co-sponsor bills, and vote in the Committee of the Whole, though not on final passage; Scoring §10 values their votes accordingly.

* Session Cost defines the total price for owning the critter for the full session
* Session Cost is paid in two parts:

  * **Signing fee:** 25% of Session Cost, spent at purchase and never refunded
  * **Weekly fee:** the other 75%, spread over the session's 52 weeks. At purchase, the weekly fees for the rest of the session are **reserved** from the player's budget and charged each week.
* Available balance = budget − spent − reserved, so a player can never be overdrawn
* Players cannot purchase beyond their available balance

Rules:

* A critter cannot be purchased for less than a full session commitment: the purchase reserves every remaining week of the session
* If a critter leaves office mid-session (resignation, death, special election loss):

  * Weekly charges stop immediately
  * The unspent reservation returns to the available balance
* Players may **drop** a critter at any time. The critter stops scoring for that roster and the unspent weekly reservation returns. The signing fee is the drop cost: it is already spent, and any replacement charges its own (§6A.7).
* A mid-session purchase pays the full signing fee on the critter's current Session Cost, plus weekly fees for the weeks left
* Critters cannot be **sold**. Ownership is non-exclusive, so there is no buyer.

#### Session Cost formula (v0.1)

> Session Cost = Projected Points × Price per Point × Market Multiplier, rounded to $10

**Projected points** use only what is known on the session's first day:

* **Power:** the value of every seat and leadership post held that day (tier × role × chamber factor, as in Scoring §8.2), times the critter's roll-call participation last session. Leadership and high-impact committee roles are priced through this term, so they need no separate premium.
* **Productivity:** the chamber median plus 0.7 × (the critter's productivity last session, per full year served − the chamber median). Last-session productivity predicts the next session less well than seats do, so it is pulled toward the median. A critter who served fewer than 60 days last session gets the chamber median.

**Market multiplier**, clamped to 0.75–1.25:

* **Donations:** −15% to +15%, by the critter's percentile of total receipts for the election cycle (FEC candidate summary), ranked against members of the same chamber who are, or are not, up for election
* **Up for re-election this session:** +5%

**Price per point:** $14. This sets the median critter at $5,000 a session: two median backers' worth, since the median interest group gives a member it backs $2,500 a year (see Calibration).

Mid-session repricing for new purchases is open (see TODO).

#### Calibration (118th Congress backtest)

Pricing the 2024 session from 2023 data:

* The scale comes from FEC records of committee money to sitting members (PACs, leadership PACs and other committees, 2023–24). In each session year, the median committee gave a member it backed $2,500, in both chambers (quartiles $1,000–5,000). The median House member had about 130 such backers a year and the median senator about 70. Super PAC spending for a median member was $0–1,040 a year: outside money lands on a few competitive races, not on the typical critter. Legal contribution limits play no part in the anchor; it is what interests actually put in.
* Prices run from $1,330 to $12,290: median $5,000, 75th percentile $6,080.
* Price tracks 2024 points at r = 0.78. Last session's points alone track at r = 0.81 (power alone 0.94), so the multiplier gives up a little accuracy on purpose. Mispriced critters are where players find an edge.
* Donations barely track points: r = 0.20 between log receipts and 2024 points in the House, 0.02 in the Senate. Senate receipts mostly show who was up for election (class 1 median $10.6M; classes 2 and 3, $2–3M).
* Being up for re-election does not change in-session scoring: the median senator's 2024/2023 points ratio was 1.06 in class 1 and 1.05–1.07 in classes 2 and 3. The +5% is a demand lever, not a forecast.
* Best value in 2024: Padilla (125 points per $1,000), Moylan, Cornyn, Peters (109). Worst: Clyburn (25), Granger (30), Pelosi (36). Critters who resigned (Gallagher, Buck, Gaetz) cost less than their price, because weekly charges stop.

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

### 6.1 Annual Budgets

* Budgets are allocated **per legislative year**
* The Standard budget is **$50,000** per legislative year, about 8 × the 75th-percentile Session Cost. An average 8-critter roster fits with room to spare. A roster can hold about three stars ($8,850–12,290) only if the rest comes from the cheaper tier. In the 2024 backtest, the 8 top scorers together cost $71,460, and the best roster $50,000 could have bought with hindsight scored 5,411 points, against about 2,800 for a roster of median critters.
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

## 8. Session Flow & Multi-Ownership

### 8.1 Purchasing Flow

* Players may purchase critters at any time before or during a session
* Ownership is **non-exclusive**

If multiple players purchase the same critter:

* The first purchaser pays full price
* Subsequent purchasers receive **small successive discounts**, based on order of purchase
* Discounts are intentionally modest to preserve early-mover advantage

---


See [Design-Scoring](Design-Scoring.md) for Sections 8.2 and 8.3.
