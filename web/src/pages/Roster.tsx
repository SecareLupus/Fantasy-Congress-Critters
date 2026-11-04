import { Link, useParams } from "react-router-dom";
import { useApi, useAsOf, type Roster as RosterData, type RosterCritter } from "../api";
import { chamberName, day, dollars, dollarsCents, partyLetter, pts, seat } from "../format";
import Loading from "../Loading";

function status(c: RosterCritter): string {
  if (c.status === "dropped") return `Dropped ${day(c.dropped_on)}, held weeks ${c.first_week}–${(c.drop_week ?? 1) - 1}`;
  if (c.status === "left_office") return `Left office ${day(c.left_office)}`;
  return `Held from week ${c.first_week}`;
}

export default function Roster() {
  const { leagueId, rosterId } = useParams();
  const { query } = useAsOf();
  const { data, error } = useApi<RosterData>(`/api/leagues/${leagueId}/rosters/${rosterId}${query()}`);
  if (!data) return <Loading error={error} />;
  const lg = data.league;
  return (
    <>
      <p className="crumbs">
        <Link to={`/leagues/${lg.league_id}${query()}`}>{lg.name}</Link>
      </p>
      <h1>{data.player}</h1>
      <p className="muted">
        Joined {day(data.joined_on)} · {pts(data.total)} points
      </p>
      {data.years.map((y) => (
        <section key={y.year}>
          <h2>
            {y.year} <span className="muted small">({y.ended} of {y.weeks} weeks ended)</span>
          </h2>
          <div className="stats">
            <div>
              <span className="stat">{pts(y.total)}</span>
              <span className="muted">points</span>
            </div>
            <div>
              <span className="stat">{pts(y.power, 0)}</span>
              <span className="muted">power</span>
            </div>
            <div>
              <span className="stat">{pts(y.productivity, 0)}</span>
              <span className="muted">productivity</span>
            </div>
            <div>
              <span className="stat">{dollarsCents(y.budget.available)}</span>
              <span className="muted">available of {dollars(y.budget.budget)}</span>
            </div>
            <div>
              <span className="stat">{dollarsCents(y.budget.spent)}</span>
              <span className="muted">spent</span>
            </div>
            <div>
              <span className="stat">{dollarsCents(y.budget.reserved)}</span>
              <span className="muted">reserved for weeks to come</span>
            </div>
          </div>
          {y.critters.length === 0 ? (
            <p className="muted">No critters yet.</p>
          ) : (
            <div className="scroll">
              <table>
                <thead>
                  <tr>
                    <th>Critter</th>
                    <th>Seat</th>
                    <th className="num">Session Cost</th>
                    <th>Bought</th>
                    <th className="num">Points</th>
                    <th className="num">Power</th>
                    <th className="num">Prod.</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {y.critters.map((c) => (
                    <tr key={`${c.bioguide_id}-${c.made_on}`} className={c.status === "held" ? "" : "inactive"}>
                      <td>
                        <Link to={`/critters/${c.bioguide_id}${query({ league: lg.league_id, year: y.year })}`}>
                          {c.name}
                        </Link>
                      </td>
                      <td>
                        {chamberName(c.chamber)} · {partyLetter(c.party)}-{seat(c)}
                      </td>
                      <td className="num">{dollars(c.session_cost)}</td>
                      <td>{day(c.made_on)}</td>
                      <td className="num strong">{pts(c.power + c.productivity)}</td>
                      <td className="num">{pts(c.power, 0)}</td>
                      <td className="num">{pts(c.productivity, 0)}</td>
                      <td>{status(c)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {y.penalties > 0 && <p className="muted">Drop penalties: −{y.penalties} points</p>}
        </section>
      ))}
    </>
  );
}
