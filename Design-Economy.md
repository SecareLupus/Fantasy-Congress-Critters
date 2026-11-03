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
* Rosters change at settlement week boundaries, so no one buys a week whose points are already known. A purchase made before the session is held from week 1; one made during a week is held from the next week. Each week's fee is charged when the week starts.
* If a critter leaves office mid-session (resignation, death, special election loss):

  * Weekly charges stop immediately: weeks starting after the departure aren't charged
  * The unspent reservation returns to the available balance
  * The critter leaves the roster and the slot frees, with no drop cost
* Players may **drop** a critter at any time. A drop made during a week takes effect the next week: the critter scores through the week already paid for, then stops scoring for that roster, and the unspent weekly reservation returns. The signing fee is the drop cost: it is already spent, and any replacement charges its own (§6A.7). A dropped critter can be bought again, for a new signing fee.
* A mid-session purchase pays the full signing fee on the critter's current Session Cost, plus weekly fees for the weeks left
* A league counts only the settlement weeks that start within its dates, so a league that starts mid-session (a presidential league on January 20) reserves and scores only its own weeks
* A roster scores the points its critters earn in the weeks it holds them, once each week has ended
* Critters cannot be **sold**. Ownership is non-exclusive, so there is no buyer.

#### Session Cost formula (v0.1)

> Session Cost = Projected Points × Price per Point × Market Multiplier, rounded to $10

**Projected points** use only what is known on the session's first day:

* **Power:** the value of every seat and leadership post held that day (tier × role × chamber factor, as in Scoring §8.2), times the critter's roll-call participation last session. Leadership and high-impact committee roles are priced through this term, so they need no separate premium.
* **Productivity:** the chamber median plus 0.7 × (the critter's productivity last session, per full year served − the chamber median). Last-session productivity predicts the next session less well than seats do, so it is pulled toward the median. A critter who served fewer than 60 days last session gets the chamber median.

**A new Congress, before committee rosters are posted.** A new Congress convenes on January 3 but seats its committees weeks later (the 119th's House committees appear on January 21, 2025, most subcommittees on April 4). The market stays open; until the rosters are posted, committee seats are projected and discounted, the same way freshmen and candidates are priced on expectations:

* A returning member keeps the committee seats they held when the last Congress ended. In a chamber whose majority changed, chairs become ranking members and ranking members chairs.
* A member new to their chamber (a freshman, or one who moved from the other chamber) gets the median committee seat value that chamber's freshmen held when the last Congress ended.
* Projected committee seats are priced at 90% of their value. Leadership posts are elected on the first day, so they aren't discounted.
* Once the rosters are posted, new purchases are priced from the real seats. Earlier buyers keep their price: a returning chair is a bargain, a member who loses a gavel a trap.

**Market multiplier**, clamped to 0.75–1.25:

* **Donations:** −15% to +15%, by the critter's percentile of total receipts in the last FEC cycle complete when the session opens (FEC candidate summary), ranked against members of the same chamber who are, or are not, up for election. A critter with no receipts on record (appointed, or elected after that cycle) ranks at the median.
* **Up for re-election this session:** +5%

**Price per point:** $14. This sets the median critter at $5,000 a session: two median backers' worth, since the median interest group gives a member it backs $2,500 a year (see Calibration).

Mid-session repricing for new purchases is open (see TODO). `critters price` computes Session Costs from a scoring run with the constants in the ruleset's `[pricing]` section; `--as-of` prices on a later date, such as when a new Congress's rosters are posted.

#### Calibration (118th Congress backtest)

Pricing the 2024 session from what was known on Jan 3, 2024 (2023 scores, seats held that day, the 2022 FEC cycle):

* The scale comes from FEC records of committee money to sitting members (PACs, leadership PACs and other committees, 2023–24). In each session year, the median committee gave a member it backed $2,500, in both chambers (quartiles $1,000–5,000). The median House member had about 130 such backers a year and the median senator about 70. Super PAC spending for a median member was $0–1,040 a year: outside money lands on a few competitive races, not on the typical critter. Legal contribution limits play no part in the anchor; it is what interests actually put in.
* Prices run from $1,280 to $12,180: median $4,940, 75th percentile $5,890.
* Price tracks 2024 points at r = 0.75. The projection alone tracks at 0.78, and last session's points alone at 0.81 (power alone 0.94), so the multiplier gives up some accuracy on purpose. Mispriced critters are where players find an edge.
* Donations barely track points: r = 0.20 between log 2024-cycle receipts and 2024 points in the House, 0.02 in the Senate. Senate receipts mostly show who was up for election (class 1 median $10.6M; classes 2 and 3, $2–3M).
* Being up for re-election does not change in-session scoring: the median senator's 2024/2023 points ratio was 1.06 in class 1 and 1.05–1.07 in classes 2 and 3. The +5% is a demand lever, not a forecast.
* Best value in 2024: Moylan (146 points per $1,000 charged), Cornyn (126), Lawler (124). Worst: Clyburn (25), Granger (30), McHenry (36). Critters who resigned (Gallagher, Buck, Gaetz) cost less than their price, because weekly charges stop.

Out of sample, pricing the 119th Congress's first session (2025) from 2024, with every constant fitted on the 118th:

* Across a Congress boundary, last season's points predict less: r = 0.65 between 2024 and 2025 points, against 0.81 within the 118th. Chairs change, and the Senate majority flipped.
* Priced on January 3 with projected seats, price tracks 2025 points at r = 0.58. Priced once all committee seats were posted (April 4), r = 0.76. Ignoring committee seats entirely would give 0.53.
* The January 3 prices hold real traps that a reader of the news would avoid: Michael Waltz, Marco Rubio and J.D. Vance left Congress on January 20 for the administration. Freshmen are priced at the median, so standouts such as Nick Begich (735 points for $4,560) are the best buys.

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
* Each league sets its budget (Design-Rulesets §6A.7). The Standard preset's is **$50,000** per legislative year, about 8 × the 75th-percentile Session Cost. An average 8-critter roster fits with room to spare. A roster can hold about three stars ($8,790–12,180) only if the rest comes from the cheaper tier. In the 2024 backtest, the 8 top scorers together cost $69,300, and the best roster $50,000 could have bought with hindsight scored 5,712 points, against about 2,800 for a roster of median critters.
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
