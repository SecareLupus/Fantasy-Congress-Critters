import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { post, useApi, type League, type Settings } from "../api";
import Confirm from "../Confirm";
import { day } from "../format";
import Loading from "../Loading";
import SettingsForm from "../SettingsForm";

/** For a league's game master: its settings before it starts, the join link for a private
league, and its players. */
export default function ManageLeague() {
  const { leagueId } = useParams();
  const { data, error, reload } = useApi<League>(`/api/leagues/${leagueId}`);
  const [name, setName] = useState("");
  const [settings, setSettings] = useState<Settings | null>(null);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    if (data) {
      setName(data.name);
      setSettings(data.settings);
    }
  }, [data]);

  if (!data || !settings) return <Loading error={error} />;
  if (!data.manageable) return <p className="error">Only this league's game master can manage it.</p>;

  const link = data.join_code ? `${window.location.origin}/leagues/${data.league_id}?join=${data.join_code}` : null;
  const save = async () => {
    setMessage(null);
    try {
      await post(`/api/leagues/${data.league_id}/settings`, { name, settings });
      setMessage({ ok: true, text: "Saved." });
      reload();
    } catch (err) {
      setMessage({ ok: false, text: (err as Error).message });
    }
  };

  return (
    <>
      <p className="crumbs">
        <Link to={`/leagues/${data.league_id}`}>{data.name}</Link>
      </p>
      <h1>Manage {data.name}</h1>
      <p className="muted">
        {data.visibility === "private" ? "Private" : "Official"} league, {day(data.start_date)} to {day(data.end_date)}.
      </p>

      {link && (
        <section>
          <h2>Join link</h2>
          <p>Anyone with an account and this link can join. Make a new one to stop the old link working.</p>
          <div className="filters">
            <input className="wide-input" readOnly value={link} onFocus={(e) => e.target.select()} />
            <button type="button" className="small-button" onClick={() => navigator.clipboard?.writeText(link)}>
              Copy
            </button>
            <Confirm
              label="New link"
              confirm="The current link will stop working."
              action={async () => {
                await post(`/api/leagues/${data.league_id}/join-code`);
                reload();
              }}
            />
          </div>
        </section>
      )}

      <section>
        <h2>Settings</h2>
        {data.frozen ? (
          <p className="muted">The league has started, so its settings are frozen.</p>
        ) : (
          <div className="form wide left">
            <label>
              Name
              <input value={name} onChange={(e) => setName(e.target.value)} maxLength={80} />
            </label>
            <SettingsForm value={settings} onChange={setSettings} />
            <p className="muted small">Settings can change until the league starts on {day(data.start_date)}.</p>
            {message && <p className={message.ok ? "notice" : "error pre"}>{message.text}</p>}
            <button type="button" className="button" onClick={save}>
              Save
            </button>
          </div>
        )}
      </section>

      <section>
        <h2>Players</h2>
        {data.standings.length === 0 ? (
          <p className="muted">No one has joined yet.</p>
        ) : (
          <div className="scroll">
            <table>
              <tbody>
                {data.standings.map((s) => (
                  <tr key={s.roster_id}>
                    <td>
                      <Link to={`/leagues/${data.league_id}/rosters/${s.roster_id}`}>{s.player}</Link>
                    </td>
                    <td className="num">
                      {!data.frozen && (
                        <Confirm
                          label="Remove"
                          confirm={`Remove ${s.player} and their roster?`}
                          action={async () => {
                            await post(`/api/leagues/${data.league_id}/rosters/${s.roster_id}/remove`);
                            reload();
                          }}
                        />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {data.frozen && <p className="muted small">Players can't be removed once the league has started.</p>}
      </section>
    </>
  );
}
