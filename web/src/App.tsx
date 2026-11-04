import { Link, Route, Routes, useLocation, useSearchParams } from "react-router-dom";
import { useApi, useAsOf, type Status } from "./api";
import { when } from "./format";
import Critter from "./pages/Critter";
import Home from "./pages/Home";
import League from "./pages/League";
import Market from "./pages/Market";
import Roster from "./pages/Roster";
import SignIn from "./pages/SignIn";
import { useSession } from "./session";

function AsOf() {
  const [params, setParams] = useSearchParams();
  const on = params.get("on") ?? "";
  const set = (value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set("on", value);
    else next.delete("on");
    setParams(next);
  };
  return (
    <label className="as-of">
      As of
      <input type="date" value={on} onChange={(e) => set(e.target.value)} />
      {on && (
        <button type="button" className="link" onClick={() => set("")}>
          today
        </button>
      )}
    </label>
  );
}

function Account() {
  const { me, loaded, signOut } = useSession();
  const location = useLocation();
  if (!loaded) return null;
  if (!me) {
    if (["/signin", "/signup"].includes(location.pathname)) return null;
    return <Link to={`/signin?next=${encodeURIComponent(location.pathname + location.search)}`}>Sign in</Link>;
  }
  return (
    <span className="account">
      {me.username}
      <button type="button" className="link" onClick={signOut}>
        Sign out
      </button>
    </span>
  );
}

function Freshness() {
  const { data } = useApi<Status>("/api/status");
  if (!data) return null;
  const failed = data.sources.filter((s) => !s.ok);
  return (
    <footer className="footer">
      Data updated {when(data.updated_at)}
      {failed.length > 0 && <span className="warn"> · {failed.map((s) => s.source).join(", ")} behind</span>}
    </footer>
  );
}

export default function App() {
  const { query } = useAsOf();
  return (
    <>
      <header className="header">
        <Link to={`/${query()}`} className="brand">
          Fantasy Congress Critters
        </Link>
        <div className="header-right">
          <AsOf />
          <Account />
        </div>
      </header>
      <main className="main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/leagues/:leagueId" element={<League />} />
          <Route path="/leagues/:leagueId/market" element={<Market />} />
          <Route path="/leagues/:leagueId/rosters/:rosterId" element={<Roster />} />
          <Route path="/critters/:bioguide" element={<Critter />} />
          <Route path="/signin" element={<SignIn />} />
          <Route path="/signup" element={<SignIn signup />} />
          <Route path="*" element={<p>Page not found.</p>} />
        </Routes>
      </main>
      <Freshness />
    </>
  );
}
