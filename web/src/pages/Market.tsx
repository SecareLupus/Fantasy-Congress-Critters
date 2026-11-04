import { useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { useApi, useAsOf, type Listing, type Market as MarketData } from "../api";
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
  const { query } = useAsOf();
  const [params, setParams] = useSearchParams();
  const year = params.get("year");
  const { data, error } = useApi<MarketData>(`/api/leagues/${leagueId}/market${query({ year })}`);
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
        <p className="notice">{data.closed}</p>
      ) : (
        <p className="muted">
          Bought on {day(data.as_of)}, a critter is held from week {data.next_week} ({data.weeks_left} weeks left): the
          signing fee, which is never refunded, plus the weekly fee for each week left. Prices are set before the
          session and don't change.
        </p>
      )}
      <details className="rules-box">
        <summary>League rules</summary>
        <Rules settings={lg.settings} />
      </details>
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
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
