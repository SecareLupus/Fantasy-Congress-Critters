-- Raw-but-structured source records, then normalized events.
-- Bill child tables are replaced wholesale whenever a bill is reloaded.

CREATE TABLE IF NOT EXISTS critters (
    bioguide_id        text PRIMARY KEY,
    first_name         text,
    last_name          text,
    official_full_name text,
    birthday           date,
    govtrack_id        integer,
    thomas_id          text,
    lis_id             text,
    wikidata_id        text,
    fec_ids            text[] NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS critter_terms (
    bioguide_id  text NOT NULL REFERENCES critters ON DELETE CASCADE,
    term_type    text NOT NULL,  -- rep | sen
    start_date   date NOT NULL,
    end_date     date NOT NULL,
    state        text NOT NULL,
    district     integer,
    senate_class integer,
    party        text,  -- the party at the end of the term; see critter_parties for changes
    PRIMARY KEY (bioguide_id, start_date)
);

-- Party over time. One row per term, or one per affiliation when a member switched
-- mid-term (congress-legislators party_affiliations). end_date is inclusive, and the
-- day of a switch belongs to the new party. caucus is set when it differs from party.
CREATE TABLE IF NOT EXISTS critter_parties (
    bioguide_id text NOT NULL REFERENCES critters ON DELETE CASCADE,
    start_date  date NOT NULL,
    end_date    date NOT NULL,
    party       text,
    caucus      text,
    PRIMARY KEY (bioguide_id, start_date)
);

-- Chamber and party leadership posts (Speaker, floor leaders, whips, conference posts).
-- end_date is the day the next holder takes over; NULL while held.
CREATE TABLE IF NOT EXISTS critter_leadership (
    bioguide_id text NOT NULL REFERENCES critters ON DELETE CASCADE,
    chamber     text NOT NULL,
    title       text NOT NULL,
    start_date  date NOT NULL,
    end_date    date,
    PRIMARY KEY (bioguide_id, title, start_date)
);

CREATE TABLE IF NOT EXISTS committees (
    committee_code        text PRIMARY KEY,  -- BILLSTATUS system code, e.g. hsii00, hsii24
    parent_committee_code text,
    name                  text NOT NULL,
    chamber               text,              -- house | senate | joint
    is_current            boolean NOT NULL
);

CREATE TABLE IF NOT EXISTS bills (
    bill_id            text PRIMARY KEY,  -- congress-type-number, e.g. 118-hr-2882
    congress           integer NOT NULL,
    bill_type          text NOT NULL,
    number             integer NOT NULL,
    title              text,
    introduced_date    date,
    origin_chamber     text,
    policy_area        text,
    sponsor_id         text,
    sponsor_by_request boolean NOT NULL,
    update_date        timestamptz
);
CREATE INDEX IF NOT EXISTS bills_congress ON bills (congress);

CREATE TABLE IF NOT EXISTS bill_cosponsors (
    bill_id          text NOT NULL REFERENCES bills ON DELETE CASCADE,
    bioguide_id      text NOT NULL,
    sponsorship_date date,
    is_original      boolean NOT NULL,
    withdrawn_date   date,
    PRIMARY KEY (bill_id, bioguide_id)
);

CREATE TABLE IF NOT EXISTS bill_subjects (
    bill_id text NOT NULL REFERENCES bills ON DELETE CASCADE,
    subject text NOT NULL,  -- CRS legislative subject term
    PRIMARY KEY (bill_id, subject)
);

CREATE TABLE IF NOT EXISTS bill_committee_activities (
    bill_id               text NOT NULL REFERENCES bills ON DELETE CASCADE,
    committee_code        text NOT NULL,
    parent_committee_code text,
    committee_name        text,
    chamber               text,
    activity              text NOT NULL,
    activity_at           timestamptz
);
CREATE INDEX IF NOT EXISTS bill_committee_activities_bill ON bill_committee_activities (bill_id);

CREATE TABLE IF NOT EXISTS bill_actions (
    bill_id         text NOT NULL REFERENCES bills ON DELETE CASCADE,
    seq             integer NOT NULL,
    action_date     date NOT NULL,
    action_time     time,
    text            text NOT NULL,
    action_type     text,
    action_code     text,
    source_name     text,
    committee_codes text[] NOT NULL DEFAULT '{}',
    recorded_votes  jsonb NOT NULL DEFAULT '[]',
    PRIMARY KEY (bill_id, seq)
);

CREATE TABLE IF NOT EXISTS amendments (
    amendment_id         text PRIMARY KEY,  -- e.g. 118-hamdt-173
    bill_id              text NOT NULL REFERENCES bills ON DELETE CASCADE,
    congress             int NOT NULL,
    amendment_type       text NOT NULL,
    number               int NOT NULL,
    chamber              text NOT NULL,
    sponsor_id           text,
    sponsor_name         text,
    on_behalf_of_id      text,
    submitted_date       date,
    proposed_date        date,
    description          text,
    purpose              text,
    amended_amendment_id text
);
CREATE INDEX IF NOT EXISTS amendments_bill ON amendments (bill_id);

CREATE TABLE IF NOT EXISTS amendment_cosponsors (
    amendment_id     text NOT NULL REFERENCES amendments ON DELETE CASCADE,
    bioguide_id      text NOT NULL,
    sponsorship_date date,
    is_original      boolean NOT NULL,
    withdrawn_date   date,
    PRIMARY KEY (amendment_id, bioguide_id)
);

CREATE TABLE IF NOT EXISTS amendment_actions (
    amendment_id   text NOT NULL REFERENCES amendments ON DELETE CASCADE,
    seq            int NOT NULL,
    action_date    date NOT NULL,
    action_time    time,
    text           text NOT NULL,
    action_type    text,
    action_code    text,
    source_name    text,
    recorded_votes jsonb NOT NULL DEFAULT '[]',
    PRIMARY KEY (amendment_id, seq)
);

CREATE TABLE IF NOT EXISTS events (
    event_id       bigserial PRIMARY KEY,
    bill_id        text NOT NULL REFERENCES bills ON DELETE CASCADE,
    event_type     text NOT NULL,
    event_date     date NOT NULL,
    chamber        text,
    committee_code text,
    critter_id     text,
    source         text NOT NULL,
    detail         text,
    amendment_id   text
);
CREATE INDEX IF NOT EXISTS events_bill ON events (bill_id);
CREATE INDEX IF NOT EXISTS events_type_date ON events (event_type, event_date);
CREATE INDEX IF NOT EXISTS events_critter ON events (critter_id) WHERE critter_id IS NOT NULL;

-- Committee seats over time, built from congress-legislators roster snapshots
-- (see rosters.py). end_date is exclusive. first_seen/last_seen are the snapshot
-- dates that evidence the seat; start/end are the effective dates used for scoring.
CREATE TABLE IF NOT EXISTS committee_memberships (
    congress       int NOT NULL,
    committee_code text NOT NULL,
    bioguide_id    text NOT NULL,
    side           text,
    role           text NOT NULL,
    title          text,
    start_date     date NOT NULL,
    end_date       date NOT NULL,
    first_seen     date NOT NULL,
    last_seen      date NOT NULL,
    CHECK (start_date < end_date)
);
CREATE INDEX IF NOT EXISTS committee_memberships_critter ON committee_memberships (bioguide_id);
CREATE INDEX IF NOT EXISTS committee_memberships_committee ON committee_memberships (committee_code);

-- Scoring runs: one per (ruleset, congress) computation. Items explain every point.
CREATE TABLE IF NOT EXISTS score_runs (
    run_id          bigserial PRIMARY KEY,
    congress        int NOT NULL,
    ruleset_version text NOT NULL,
    ruleset         jsonb NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS score_items (
    run_id         bigint NOT NULL REFERENCES score_runs ON DELETE CASCADE,
    bioguide_id    text NOT NULL,
    session        int NOT NULL,
    pillar         text NOT NULL,  -- power | productivity
    category       text NOT NULL,
    item_date      date NOT NULL,
    points         double precision NOT NULL,
    bill_id        text,
    amendment_id   text,
    vote_id        text,
    committee_code text,
    detail         jsonb
);
CREATE INDEX IF NOT EXISTS score_items_run_critter ON score_items (run_id, bioguide_id);

-- A run's points by settlement week (seats split across the weeks held), for standings.
CREATE TABLE IF NOT EXISTS weekly_points (
    run_id       bigint NOT NULL REFERENCES score_runs ON DELETE CASCADE,
    bioguide_id  text NOT NULL,
    session      int NOT NULL,
    week         int NOT NULL,
    power        double precision NOT NULL,
    productivity double precision NOT NULL,
    PRIMARY KEY (run_id, session, bioguide_id, week)
);

-- Roll-call votes. The bill reference comes from the chamber's own record; it is
-- the measure the vote was on (a rule vote points at the H.Res, not the bill it governs).
CREATE TABLE IF NOT EXISTS roll_calls (
    vote_id          text PRIMARY KEY,
    chamber          text NOT NULL,
    congress         int NOT NULL,
    session          int NOT NULL,
    roll_number      int NOT NULL,
    vote_date        date NOT NULL,
    vote_time        time,
    question         text,
    vote_type        text,
    result           text,
    legis_num        text,
    bill_id          text,
    amendment_num    text,
    amendment_author text,
    description      text,
    UNIQUE (chamber, congress, session, roll_number)
);
CREATE INDEX IF NOT EXISTS roll_calls_bill ON roll_calls (bill_id);

CREATE TABLE IF NOT EXISTS member_votes (
    vote_id      text NOT NULL REFERENCES roll_calls ON DELETE CASCADE,
    bioguide_id  text NOT NULL,
    position     text NOT NULL,
    raw_position text NOT NULL,
    party        text,
    state        text,
    PRIMARY KEY (vote_id, bioguide_id)
);
CREATE INDEX IF NOT EXISTS member_votes_critter ON member_votes (bioguide_id);

-- Bill and amendment actions that cite a roll call (from BILLSTATUS recordedVotes).
DROP VIEW IF EXISTS roll_call_actions;
CREATE VIEW roll_call_actions AS
WITH cited AS (
    SELECT a.bill_id, NULL::text AS amendment_id, a.seq, a.action_date, a.action_code,
           a.source_name, a.text, a.recorded_votes
    FROM bill_actions a
    UNION ALL
    SELECT am.bill_id, a.amendment_id, a.seq, a.action_date, a.action_code,
           a.source_name, a.text, a.recorded_votes
    FROM amendment_actions a JOIN amendments am USING (amendment_id)
)
SELECT rc.vote_id, c.bill_id, c.amendment_id, c.seq, c.action_date, c.action_code,
       c.source_name, c.text
FROM cited c
CROSS JOIN LATERAL jsonb_array_elements(c.recorded_votes) v
JOIN roll_calls rc
  ON rc.chamber = v->>'chamber'
 AND rc.congress = (v->>'congress')::int
 AND rc.session = (v->>'session')::int
 AND rc.roll_number = (v->>'roll_number')::int;

-- Session Costs computed from a scoring run (Design-Economy §5.2).
CREATE TABLE IF NOT EXISTS critter_prices (
    run_id                 bigint NOT NULL REFERENCES score_runs ON DELETE CASCADE,
    session                int NOT NULL,
    fec_cycle              int NOT NULL,
    bioguide_id            text NOT NULL,
    chamber                text NOT NULL,
    projected_power        double precision NOT NULL,
    projected_productivity double precision NOT NULL,
    multiplier             double precision NOT NULL,
    session_cost           int NOT NULL,
    signing_fee            double precision NOT NULL,
    weekly_fee             double precision NOT NULL,
    PRIMARY KEY (run_id, session, bioguide_id)
);

-- League settings presets, authored by GameMakers (e.g. "standard").
CREATE TABLE IF NOT EXISTS league_presets (
    name        text PRIMARY KEY,
    description text,
    settings    jsonb NOT NULL,
    authored_by text NOT NULL,
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- Leagues (Design-Rulesets §6A). settings are resolved from a preset plus the game
-- master's overrides when the league is created, so later preset edits don't reach it.
-- The league freezes a copy of its ruleset; neither changes once the league starts.
CREATE TABLE IF NOT EXISTS leagues (
    league_id       bigserial PRIMARY KEY,
    name            text NOT NULL,
    league_type     text NOT NULL,
    visibility      text NOT NULL CHECK (visibility IN ('official', 'private')),
    start_date      date NOT NULL,
    end_date        date NOT NULL,  -- exclusive
    ruleset_version text NOT NULL,
    ruleset         jsonb NOT NULL,
    preset          text REFERENCES league_presets,
    settings        jsonb NOT NULL,
    created_by      text NOT NULL,
    creator_role    text NOT NULL CHECK (creator_role IN ('gamemaker', 'commissioner')),
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CHECK (start_date < end_date)
);

-- A player's roster in a league (Design-Pages §13.7).
CREATE TABLE IF NOT EXISTS rosters (
    roster_id bigserial PRIMARY KEY,
    league_id bigint NOT NULL REFERENCES leagues ON DELETE CASCADE,
    player    text NOT NULL,
    joined_on date NOT NULL,
    UNIQUE (league_id, player)
);

-- Purchases and drops (Design-Economy §5.2). A purchase records the price paid, which
-- doesn't change with later repricing, and the settlement weeks it reserved. A drop points
-- at its purchase and records the first week the critter is no longer held.
CREATE TABLE IF NOT EXISTS transactions (
    txn_id         bigserial PRIMARY KEY,
    roster_id      bigint NOT NULL REFERENCES rosters ON DELETE CASCADE,
    kind           text NOT NULL CHECK (kind IN ('purchase', 'drop')),
    bioguide_id    text NOT NULL,
    congress       int NOT NULL,
    session        int NOT NULL,
    made_on        date NOT NULL,
    week           int NOT NULL,  -- purchase: first week held; drop: first week no longer held
    purchase_id    bigint REFERENCES transactions,  -- drop: the purchase it ends
    price_run      bigint REFERENCES score_runs,     -- purchase: the run it was priced from
    chamber        text,
    session_cost   int,
    signing_fee    double precision,
    weekly_fee     double precision,
    last_week      int,   -- purchase: last week reserved
    extra_fee      int NOT NULL DEFAULT 0,
    points_penalty double precision NOT NULL DEFAULT 0,
    created_at     timestamptz NOT NULL DEFAULT now(),
    CHECK ((kind = 'purchase') = (purchase_id IS NULL))
);
CREATE INDEX IF NOT EXISTS transactions_roster ON transactions (roster_id);
