import { useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import { post, useApi, useAsOf, type League as LeagueData, type Settings } from "../api";
import { day, dollars, leagueType, pts } from "../format";
import Loading from "../Loading";
import { useSession } from "../session";

export function Rules({ settings }: { settings: Settings }) {
  const slots = settings.roster_rules.chamber_slots;
  const drop = settings.drop_cost;
  return (
    <dl className="rules">
      <dt>Budget</dt>
      <dd>{dollars(settings.budget_rules.annual_budget)} a year</dd>
      <dt>Roster</dt>
      <dd>
        {settings.roster_rules.roster_limit} critters
        {slots && ` (at most ${slots.house} House, ${slots.senate} Senate)`}
      </dd>
      <dt>Drops</dt>
      <dd>
        Signing fee lost
        {drop.extra_fee > 0 && `, plus ${dollars(drop.extra_fee)}`}
        {drop.points_penalty > 0 && `, minus ${drop.points_penalty} points`}
      </dd>
      <dt>Winner</dt>
      <dd>{settings.win_condition === "cumulative" ? "Most points" : "Head to head"}</dd>
    </dl>
  );
}

/** Join with the signed-in account, or a prompt to sign in first. */
function Join({ league }: { league: LeagueData }) {
  const { me, refresh } = useSession();
  const navigate = useNavigate();
  const location = useLocation();
  const { query } = useAsOf();
  const [error, setError] = useState<string | null>(null);
  if (!me) {
    return (
      <p className="notice">
        <Link to={`/signin?next=${encodeURIComponent(location.pathname)}`}>Sign in</Link> to join this league.
      </p>
    );
  }
  const join = async () => {
    setError(null);
    try {
      const { roster_id } = await post<{ roster_id: number }>(`/api/leagues/${league.league_id}/join`);
      await refresh();
      navigate(`/leagues/${league.league_id}/rosters/${roster_id}${query()}`);
    } catch (err) {
      setError((err as Error).message);
    }
  };
  return (
    <div className="notice">
      <button type="button" className="button" onClick={join}>
        Join {league.name}
      </button>{" "}
      as {me.username}. You'll start with {dollars(league.settings.budget_rules.annual_budget)} to spend on critters.
      {error && <p className="error">{error}</p>}
    </div>
  );
}

export default function League() {
  const { leagueId } = useParams();
  const { on, query } = useAsOf();
  const { me } = useSession();
  const { data, error } = useApi<LeagueData>(`/api/leagues/${leagueId}${query()}`);
  if (!data) return <Loading error={error} />;
  const mine = me?.rosters.find((r) => r.league_id === data.league_id);
  return (
    <>
      <p className="crumbs">
        <Link to={`/${query()}`}>Leagues</Link>
      </p>
      <h1>{data.name}</h1>
      <p className="muted">
        {leagueType(data.league_type)} league, {day(data.start_date)} to {day(data.end_date)} · ruleset{" "}
        {data.ruleset_version} · run by {data.created_by}
      </p>
      {mine ? (
        <p>
          <Link className="button" to={`/leagues/${data.league_id}/rosters/${mine.roster_id}${query()}`}>
            Your roster
          </Link>
        </p>
      ) : (
        data.open_to_join && !on && <Join league={data} />
      )}
      <div className="split">
        <section>
          <h2>Standings</h2>
          {data.standings.length === 0 ? (
            <p className="muted">No players yet.</p>
          ) : (
            <div className="scroll">
              <table>
                <thead>
                  <tr>
                    <th className="num">#</th>
                    <th>Player</th>
                    <th className="num">Points</th>
                    <th className="num">Power</th>
                    <th className="num">Productivity</th>
                    <th className="num">Penalties</th>
                  </tr>
                </thead>
                <tbody>
                  {data.standings.map((s) => (
                    <tr key={s.roster_id} className={s.roster_id === mine?.roster_id ? "mine" : ""}>
                      <td className="num">{s.rank}</td>
                      <td>
                        <Link to={`/leagues/${data.league_id}/rosters/${s.roster_id}${query()}`}>{s.player}</Link>
                      </td>
                      <td className="num strong">{pts(s.total)}</td>
                      <td className="num">{pts(s.power, 0)}</td>
                      <td className="num">{pts(s.productivity, 0)}</td>
                      <td className="num">{s.penalties ? `−${s.penalties}` : ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <p>
            <Link className="button" to={`/leagues/${data.league_id}/market${query()}`}>
              Market
            </Link>
          </p>
        </section>
        <aside>
          <h2>Season</h2>
          {data.years.map((y) => (
            <div key={y.year} className="progress">
              <div>
                <strong>{y.year}</strong> · {y.ended} of {y.weeks} weeks ended
                {y.final > 0 && `, ${y.final} final`}
              </div>
              <div className="bar">
                <span className="final" style={{ width: `${(100 * y.final) / y.weeks}%` }} />
                <span className="ended" style={{ width: `${(100 * (y.ended - y.final)) / y.weeks}%` }} />
              </div>
            </div>
          ))}
          <p className="muted small">
            Points count once a week ends, and become final a few days later when every source has caught up.
            {!on && " Standings are as of today."}
          </p>
          <h2>Rules</h2>
          <Rules settings={data.settings} />
          {!data.frozen && <p className="muted small">Settings can still change until the league starts.</p>}
        </aside>
      </div>
    </>
  );
}
