import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { post, type Me } from "../api";
import { useSession } from "../session";

/** Sign in, or with `signup` create an account from an invite code (?invite= fills it in). */
export default function SignIn({ signup = false }: { signup?: boolean }) {
  const { setMe } = useSession();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [invite, setInvite] = useState(params.get("invite") ?? "");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const next = params.get("next") ?? "/";

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const me = signup
        ? await post<Me>("/api/signup", { invite_code: invite, username, password })
        : await post<Me>("/api/signin", { username, password });
      setMe(me);
      navigate(next.startsWith("/") ? next : "/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="form" onSubmit={submit}>
      <h1>{signup ? "Create your account" : "Sign in"}</h1>
      {signup && (
        <label>
          Invite code
          <input value={invite} onChange={(e) => setInvite(e.target.value)} required autoComplete="off" placeholder="K7QM-3XPA-HW2N" />
        </label>
      )}
      <label>
        Username
        <input value={username} onChange={(e) => setUsername(e.target.value)} required autoComplete="username" />
        {signup && <span className="muted small">3 to 24 letters, digits, hyphens or underscores. Other players see it.</span>}
      </label>
      <label>
        Password
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={signup ? 10 : undefined}
          autoComplete={signup ? "new-password" : "current-password"}
        />
        {signup && <span className="muted small">At least 10 characters.</span>}
      </label>
      {error && <p className="error">{error}</p>}
      <button className="button" disabled={busy}>
        {signup ? "Create account" : "Sign in"}
      </button>
      <p className="muted small">
        {signup ? (
          <>
            Already have an account? <Link to={`/signin?next=${encodeURIComponent(next)}`}>Sign in</Link>
          </>
        ) : (
          <>
            Have an invite code? <Link to={`/signup?next=${encodeURIComponent(next)}`}>Create an account</Link>. Forgot your
            password? Ask whoever invited you to reset it.
          </>
        )}
      </p>
    </form>
  );
}
