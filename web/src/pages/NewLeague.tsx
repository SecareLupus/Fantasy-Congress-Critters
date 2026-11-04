import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { post, useApi, type LeagueOptions, type Settings } from "../api";
import Loading from "../Loading";
import SettingsForm from "../SettingsForm";
import { useSession } from "../session";

const TYPE_NAMES: Record<string, string> = {
  standard_private: "Private, on an official schedule",
  flexible_private: "Private, on your own dates",
  session: "Session: one year of a Congress",
  annual: "Annual: a calendar year",
  representative: "Representative: a whole Congress (2 years)",
  presidential: "Presidential: a presidential term (4 years)",
  senatorial: "Senatorial: a Senate class term (6 years)",
};

/** Which dates each schedule needs. */
const NEEDS: Record<string, ("congress" | "session" | "year" | "start" | "end")[]> = {
  session: ["congress", "session"],
  annual: ["year"],
  representative: ["congress"],
  presidential: ["year"],
  senatorial: ["year"],
  flexible_private: ["start", "end"],
};

export default function NewLeague() {
  const { me, loaded } = useSession();
  const navigate = useNavigate();
  const { data, error } = useApi<LeagueOptions>("/api/league-options");
  const [name, setName] = useState("");
  const [type, setType] = useState("standard_private");
  const [timing, setTiming] = useState("session");
  const [dates, setDates] = useState({ congress: "", session: "", year: "", start: "", end: "" });
  const [preset, setPreset] = useState("standard");
  const [settings, setSettings] = useState<Settings | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!data) return;
    setDates((d) => ({ ...d, congress: String(data.congress), session: String(data.session), year: String(data.year) }));
    const first = data.presets[preset] ? preset : Object.keys(data.presets)[0];
    if (first) {
      setPreset(first);
      setSettings(data.presets[first].settings);
    }
    // Only when the options first arrive.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  if (loaded && !me) return <p className="notice">Sign in to create a league.</p>;
  if (!data || !settings) return <Loading error={error ?? (data && "no presets yet: save one with critters league preset save")} />;

  const schedule = type === "standard_private" ? timing : type;
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setProblem(null);
    const picked = Object.fromEntries(
      NEEDS[schedule].map((k) => [k, k === "start" || k === "end" ? dates[k] : Number(dates[k])]),
    );
    try {
      const { league_id } = await post<{ league_id: number }>("/api/leagues", {
        name,
        league_type: type,
        timing: type === "standard_private" ? timing : null,
        preset,
        settings,
        ...picked,
      });
      navigate(`/leagues/${league_id}/manage`);
    } catch (err) {
      setProblem((err as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const types = [...data.private_types, ...(data.can_create_official ? data.official_types : [])];
  const field = (k: keyof typeof dates, label: string, type = "number") => (
    <label key={k}>
      {label}
      <input type={type} value={dates[k]} required onChange={(e) => setDates({ ...dates, [k]: e.target.value })} />
    </label>
  );

  return (
    <form className="form wide" onSubmit={submit}>
      <p className="crumbs">
        <Link to="/">Leagues</Link>
      </p>
      <h1>Create a league</h1>
      <label>
        Name
        <input value={name} onChange={(e) => setName(e.target.value)} required maxLength={80} />
      </label>
      <label>
        Kind
        <select value={type} onChange={(e) => setType(e.target.value)}>
          {types.map((t) => (
            <option key={t} value={t}>
              {TYPE_NAMES[t] ?? t}
            </option>
          ))}
        </select>
        <span className="muted small">
          {data.official_types.includes(type)
            ? "Official: listed for every player to join."
            : "Private: unlisted; players join with the link you share. You're its commissioner."}
        </span>
      </label>
      {type === "standard_private" && (
        <label>
          Schedule
          <select value={timing} onChange={(e) => setTiming(e.target.value)}>
            {data.official_types.map((t) => (
              <option key={t} value={t}>
                {TYPE_NAMES[t]}
              </option>
            ))}
          </select>
        </label>
      )}
      <div className="pair">
        {NEEDS[schedule].map((k) =>
          k === "congress"
            ? field(k, "Congress (e.g. 120)")
            : k === "session"
              ? field(k, "Session (1 or 2)")
              : k === "year"
                ? field(k, schedule === "annual" ? "Year" : "First year")
                : field(k, k === "start" ? "Starts" : "Ends (not included)", "date"),
        )}
      </div>
      <label>
        Start from preset
        <select
          value={preset}
          onChange={(e) => {
            setPreset(e.target.value);
            setSettings(data.presets[e.target.value].settings);
          }}
        >
          {Object.entries(data.presets).map(([n, p]) => (
            <option key={n} value={n}>
              {p.description ?? n}
            </option>
          ))}
        </select>
      </label>
      <SettingsForm value={settings} onChange={setSettings} />
      <p className="muted small">
        Scores with ruleset {data.ruleset_version}. You can change the settings until the league starts.
      </p>
      {problem && <p className="error pre">{problem}</p>}
      <button className="button" disabled={busy}>
        Create league
      </button>
    </form>
  );
}
