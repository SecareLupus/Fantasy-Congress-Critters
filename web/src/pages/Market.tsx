import { useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { post, useApi, useAsOf, type Listing, type Market as MarketData, type TradeResult } from "../api";
import Confirm from "../Confirm";
import { chamberName, day, dollars, dollarsCents, partyLetter, pts, seat } from "../format";
import Loading from "../Loading";
import { Rules } from "./League";

type Column = { key: string; label: string; value: (c: Listing) => number | string; num?: boolean };

const COLUMNS: Column[] = [
  { key: "name", label: "Critter", value: (c) => c.name },
  { key: "seat", label: "Seat", value: (c) => `${c.chamber}${c.state}${String(c.district ?? 0).padStart(2, "0")}` },
  { key: "cost", label: "Session Cost", value: (c) => c.session_cost, num: true },
  { key: "now", label: "Cost now", value: (c) => c.cost_now, num: true },
  { key: "projected", label: "Projected", value: (c) => c.projected_power + c.projected_productivity, num: true },
  { key: "points", label: "Points so far", value: (c) => c.points, num: true },
  { key: "owners", label: "Owners", value: (c) => c.owners.length, num: true },
];

export default function Market() {
  const { leagueId } = useParams();
  const { on, query } = useAsOf();
  const [params, setParams] = useSearchParams();
  const year = params.get("year");
  const { data, error, reload } = useApi<MarketData>(`/api/leagues/${leagueId}/market${query({ year })}`);
  const [done, setDone] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [chamber, setChamber] = useState("");
  const [party, setParty] = useState("");
  const [sort, setSort] = useState<{ key: string; desc: boolean }>({ key: "cost", desc: true });

  const rows = useMemo(() => {
    if (!data) return [];
    const col = COLUMNS.find((c) => c.key === sort.key)!;
    const text = search.trim().toLowerCase();
    return data.critters
      .filter((c) => !text || c.name.toLowerCase().includes(text) || c.state.toLowerCase() === text)
      .filter((c) => !chamber || c.chamber === chamber)
      .filter((c) => !party || (party === "O" ? !["D", "R"].includes(partyLetter(c.party)) : partyLetter(c.party) === party))
      .sort((a, b) => {
        const [x, y] = [col.value(a), col.value(b)];
        const order = typeof x === "number" ? x - (y as number) : x.localeCompare(y as string);
        return sort.desc ? -order : order;
      });
  }, [data, search, chamber, party, sort]);

  if (!data) return <Loading error={error} />;
  const lg = data.league;
  const open = !data.closed;
  const mine = data.mine;
  const trading = open && !!mine && !on;
  const rules = lg.settings.roster_rules;

  /** Why the player can't buy this critter now, or null if they can. */
  const refusal = (c: Listing): string | null => {
    if (!mine) return null;
    if (mine.held.includes(c.bioguide_id)) return "on your roster";
    if (mine.held.length >= rules.roster_limit) return "roster full";
    const slots = rules.chamber_slots;
    if (slots && (c.chamber === "sen" ? mine.senate >= slots.senate : mine.house >= slots.house))
      return `${c.chamber === "sen" ? "Senate" : "House"} slots full`;
    if (c.cost_now > mine.available + 0.005) return "can't afford";
    return null;
  };
  const buy = async (c: Listing) => {
    const r = await post<TradeResult>(`/api/leagues/${lg.league_id}/buy`, { bioguide_id: c.bioguide_id, year: data.year });
    setDone(`Bought ${r.name}: on your roster from week ${r.first_week}. ${dollarsCents(r.available)} left to spend.`);
    reload();
  };
  const setYear = (y: string) => {
    const next = new URLSearchParams(params);
    next.set("year", y);
    setParams(next);
  };
  return (
    <>
      <p className="crumbs">
        <Link to={`/leagues/${lg.league_id}${query()}`}>{lg.name}</Link>
      </p>
      <h1>
        Market{" "}
        {data.years.length > 1 ? (
          <select value={data.year} onChange={(e) => setYear(e.target.value)}>
            {data.years.map((y) => (
              <option key={y}>{y}</option>
            ))}
          </select>
        ) : (
          data.year
        )}
      </h1>
      {data.closed ? (
        <p className="notice">
          {data.closed}
          {data.closed_detail && <span className="muted small"> For the game master: {data.closed_detail}</span>}
        </p>
      ) : (
        <p className="muted">
          Bought on {day(data.as_of)}, a critter is held from week {data.next_week} ({data.weeks_left} weeks left): the
          signing fee, which is never refunded, plus the weekly fee for each week left. Prices are set before the
          session and don't change.
        </p>
      )}
      {mine && (
        <p>
          <Link to={`/leagues/${lg.league_id}/rosters/${mine.roster_id}${query()}`}>Your roster</Link>: {mine.held.length} of{" "}
          {rules.roster_limit} critters
          {rules.chamber_slots && ` (${mine.house}/${rules.chamber_slots.house} House, ${mine.senate}/${rules.chamber_slots.senate} Senate)`}
          , <strong>{dollarsCents(mine.available)}</strong> available of {dollars(mine.budget)}.
        </p>
      )}
      {done && <p className="notice">{done}</p>}
      <details className="rules-box">
        <summary>League rules</summary>
        <Rules settings={lg.settings} />
      </details>
      {data.critters.length > 0 && (
        <>
          <div className="filters">
            <input type="search" placeholder="Name or state (TX)" value={search} onChange={(e) => setSearch(e.target.value)} />
            <select value={chamber} onChange={(e) => setChamber(e.target.value)}>
              <option value="">Both chambers</option>
              <option value="rep">House</option>
              <option value="sen">Senate</option>
            </select>
            <select value={party} onChange={(e) => setParty(e.target.value)}>
              <option value="">All parties</option>
              <option value="D">Democrats</option>
              <option value="R">Republicans</option>
              <option value="O">Others</option>
            </select>
            <span className="muted">{rows.length} critters</span>
          </div>
          <div className="scroll">
            <table className="market">
              <thead>
                <tr>
                  {COLUMNS.filter((c) => open || c.key !== "now").map((c) => (
                    <th
                      key={c.key}
                      className={`sortable ${c.num ? "num" : ""}`}
                      aria-sort={sort.key === c.key ? (sort.desc ? "descending" : "ascending") : "none"}
                      onClick={() => setSort({ key: c.key, desc: sort.key === c.key ? !sort.desc : !!c.num })}
                    >
                      {c.label}
                      {sort.key === c.key ? (sort.desc ? " ▼" : " ▲") : ""}
                    </th>
                  ))}
                  {trading && <th />}
                </tr>
              </thead>
              <tbody>
                {rows.map((c) => (
                  <tr key={c.bioguide_id}>
                    <td>
                      <Link to={`/critters/${c.bioguide_id}${query({ league: lg.league_id, year: data.year })}`}>{c.name}</Link>
                    </td>
                    <td>
                      {chamberName(c.chamber)} · {partyLetter(c.party)}-{seat(c)}
                    </td>
                    <td className="num">{dollars(c.session_cost)}</td>
                    {open && <td className="num">{dollarsCents(c.cost_now)}</td>}
                    <td className="num">{pts(c.projected_power + c.projected_productivity, 0)}</td>
                    <td className="num strong">{pts(c.points)}</td>
                    <td className="num" title={c.owners.join(", ")}>
                      {c.owners.length || ""}
                    </td>
                    {trading && (
                      <td className="nowrap">
                        {refusal(c) ? (
                          <span className="muted small">{refusal(c)}</span>
                        ) : (
                          <Confirm
                            label="Buy"
                            confirm={`${dollarsCents(c.signing_fee)} now (never refunded), then ${dollarsCents(c.weekly_fee)} a week for ${data.weeks_left} weeks`}
                            action={() => buy(c)}
                          />
                        )}
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </>
  );
}
