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
    party        text,
    PRIMARY KEY (bioguide_id, start_date)
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

CREATE TABLE IF NOT EXISTS events (
    event_id       bigserial PRIMARY KEY,
    bill_id        text NOT NULL REFERENCES bills ON DELETE CASCADE,
    event_type     text NOT NULL,
    event_date     date NOT NULL,
    chamber        text,
    committee_code text,
    critter_id     text,
    source         text NOT NULL,
    detail         text
);
CREATE INDEX IF NOT EXISTS events_bill ON events (bill_id);
CREATE INDEX IF NOT EXISTS events_type_date ON events (event_type, event_date);
CREATE INDEX IF NOT EXISTS events_critter ON events (critter_id) WHERE critter_id IS NOT NULL;
