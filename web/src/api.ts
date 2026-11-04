import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

export type Settings = {
  budget_rules: { annual_budget: number };
  roster_rules: { roster_limit: number; chamber_slots: { house: number; senate: number } | null };
  win_condition: string;
  drop_cost: { extra_fee: number; points_penalty: number };
};

export type LeagueSummary = {
  league_id: number;
  name: string;
  league_type: string;
  visibility: string;
  start_date: string;
  end_date: string;
  players: number;
};

export type Year = {
  year: number;
  congress: number;
  session: number;
  first_week: number;
  last_week: number;
  weeks: number;
  ended: number;
  final: number;
  next_week: number | null;
  run_id: number | null;
  price_run: number | null;
};

export type Standing = {
  rank: number;
  roster_id: number;
  player: string;
  total: number;
  power: number;
  productivity: number;
  penalties: number;
};

export type League = LeagueSummary & {
  as_of: string;
  ruleset_version: string;
  preset: string | null;
  created_by: string;
  creator_role: string;
  frozen: boolean;
  open_to_join: boolean;
  settings: Settings;
  years: Year[];
  standings: Standing[];
};

export type Card = {
  bioguide_id: string;
  name: string;
  chamber: "rep" | "sen";
  state: string;
  district: number | null;
  party: string | null;
};

export type RosterCritter = Card & {
  status: "held" | "dropped" | "left_office";
  made_on: string;
  first_week: number;
  last_week: number;
  session_cost: number;
  signing_fee: number;
  weekly_fee: number;
  dropped_on: string | null;
  drop_week: number | null;
  left_office: string | null;
  power: number;
  productivity: number;
};

export type Roster = {
  roster_id: number;
  player: string;
  joined_on: string;
  as_of: string;
  league: LeagueSummary & { settings: Settings };
  total: number;
  years: (Year & {
    budget: { budget: number; spent: number; reserved: number; available: number };
    power: number;
    productivity: number;
    penalties: number;
    total: number;
    critters: RosterCritter[];
  })[];
};

export type Price = {
  bioguide_id: string;
  chamber: string;
  session_cost: number;
  signing_fee: number;
  weekly_fee: number;
  projected_power: number;
  projected_productivity: number;
  multiplier: number;
};

export type Listing = Card & Price & { cost_now: number; points: number; owners: string[] };

export type Market = Year & {
  league: LeagueSummary & { settings: Settings };
  as_of: string;
  years: number[];
  closed: string | null;
  weeks_left?: number;
  critters: Listing[];
};

export type Week = {
  week: number;
  start: string;
  end: string;
  power: number | null;
  productivity: number | null;
  state: "final" | "ended" | "upcoming";
};

export type Critter = Year & {
  bioguide_id: string;
  name: string;
  birthday: string | null;
  govtrack_id: number | null;
  wikidata_id: string | null;
  fec_ids: string[];
  terms: { chamber: string; start_date: string; end_date: string; state: string; district: number | null; party: string | null }[];
  leadership: { chamber: string; title: string; start_date: string; end_date: string | null }[];
  as_of: string;
  league: (LeagueSummary & { settings: Settings }) | null;
  card: Card | null;
  power: number;
  productivity: number;
  weekly: Week[];
  counted_through: string;
  breakdown: {
    categories: { category: string; items: number; points: number }[];
    bills: { bill_id: string; title: string | null; points: number; categories: string[]; sponsor: boolean }[];
    positions: { category: string; committee_code: string | null; name: string; role: string | null; start_date: string; end_date: string; value: number }[];
    participation: number | null;
  } | null;
  price: Price | null;
  owners: string[];
};

export type Status = {
  sources: { source: string; congress: number | null; attempted_at: string; ok: boolean; note: string | null; succeeded_at: string | null; latest: string | null }[];
  updated_at: string | null;
};

/** Fetch an API path; null skips the request. */
export function useApi<T>(path: string | null): { data?: T; error?: string } {
  const [state, setState] = useState<{ path?: string; data?: T; error?: string }>({});
  useEffect(() => {
    if (!path) return;
    let live = true;
    fetch(path)
      .then(async (r) => {
        const body = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(body.detail ?? `${r.status} ${r.statusText}`);
        return body as T;
      })
      .then((data) => live && setState({ path, data }))
      .catch((e: Error) => live && setState({ path, error: e.message }));
    return () => {
      live = false;
    };
  }, [path]);
  // Don't show the previous page's data while the next one loads.
  return state.path === path ? { data: state.data, error: state.error } : {};
}

/** The date the game is shown as of (?on=), which links carry from page to page. */
export function useAsOf(): { on: string | null; query: (extra?: Record<string, string | number | null | undefined>) => string } {
  const [params] = useSearchParams();
  const on = params.get("on");
  return {
    on,
    query: (extra = {}) => {
      const q = new URLSearchParams();
      if (on) q.set("on", on);
      for (const [k, v] of Object.entries(extra)) if (v !== null && v !== undefined) q.set(k, String(v));
      const s = q.toString();
      return s ? `?${s}` : "";
    },
  };
}

export type Me = {
  account_id: number;
  username: string;
  role: "player" | "commissioner" | "gamemaker";
  rosters: { roster_id: number; league_id: number; league: string; joined_on: string; start_date: string; end_date: string }[];
};

/** POST JSON (the API refuses anything else for changes); the error message is the API's. */
export async function post<T>(path: string, body: object = {}): Promise<T> {
  const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    const detail = data.detail;
    // FastAPI reports a malformed body as a list of field errors.
    throw new Error(typeof detail === "string" ? detail : `${r.status} ${r.statusText}`);
  }
  return data as T;
}
