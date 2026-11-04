import { Link } from "react-router-dom";
import { useApi, useAsOf, type LeagueSummary } from "../api";
import { day, leagueType } from "../format";
import Loading from "../Loading";

export default function Home() {
  const { query } = useAsOf();
  const { data, error } = useApi<LeagueSummary[]>("/api/leagues");
  if (!data) return <Loading error={error} />;
  return (
    <>
      <h1>Leagues</h1>
      {data.length === 0 ? (
        <p className="muted">No leagues yet.</p>
      ) : (
        <div className="scroll">
          <table>
            <thead>
              <tr>
                <th>League</th>
                <th>Type</th>
                <th>Dates</th>
                <th className="num">Players</th>
              </tr>
            </thead>
            <tbody>
              {data.map((l) => (
                <tr key={l.league_id}>
                  <td>
                    <Link to={`/leagues/${l.league_id}${query()}`}>{l.name}</Link>
                  </td>
                  <td>
                    {leagueType(l.league_type)} <span className="muted">({l.visibility})</span>
                  </td>
                  <td>
                    {day(l.start_date)} – {day(l.end_date)}
                  </td>
                  <td className="num">{l.players}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
