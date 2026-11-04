import { Link } from "react-router-dom";
import { useApi, useAsOf, type LeagueSummary } from "../api";
import { day, leagueType } from "../format";
import Loading from "../Loading";
import { useSession } from "../session";

export default function Home() {
  const { query } = useAsOf();
  const { me } = useSession();
  const { data, error } = useApi<LeagueSummary[]>("/api/leagues");
  if (!data) return <Loading error={error} />;
  return (
    <>
      {me && me.rosters.length > 0 && (
        <>
          <h1>Your rosters</h1>
          <ul className="plain">
            {me.rosters.map((r) => (
              <li key={r.roster_id}>
                <Link to={`/leagues/${r.league_id}/rosters/${r.roster_id}${query()}`}>{r.league}</Link>{" "}
                <span className="muted">· joined {day(r.joined_on)}</span>
              </li>
            ))}
          </ul>
        </>
      )}
      <div className="title-row">
        <h1>Leagues</h1>
        {me && (
          <Link className="button" to="/leagues/new">
            Create a league
          </Link>
        )}
      </div>
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
