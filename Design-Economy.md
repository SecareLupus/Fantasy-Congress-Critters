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

---

### 5.2 Pricing Full Critters (Current Session)

Each critter has a **Session Cost**.

* Session Cost defines the total price for owning the critter for the full session
* At purchase, the full Session Cost (pro-rated if bought mid-session) is **reserved** from the player's budget. Available balance = budget − reserved, so a player can never be overdrawn.
* Reserved cost is **charged periodically** (e.g., weekly or monthly). Periodic charging only matters for releasing the unspent remainder when ownership ends early.
* Players cannot purchase beyond their available balance

Rules:

* A critter cannot be purchased for less than a full session commitment
* If a critter leaves office mid-session (resignation, death, special election loss):

  * Periodic charges stop immediately
  * No further payments are required; the unspent reservation returns to the available balance
* Players may **drop** a critter at any time. The critter stops scoring for that roster, and the player pays the league's **drop cost** (§6A.7).
* Critters cannot be **sold**. Ownership is non-exclusive, so there is no buyer.

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
