import { useState, type FormEvent } from "react";
import { post, useApi, type Invite } from "../api";
import { day } from "../format";
import Loading from "../Loading";

/** Invite codes for new accounts, for GameMakers (the same as critters invite). */
export default function Invites() {
  const { data, error, reload } = useApi<Invite[]>("/api/invites");
  const [form, setForm] = useState({ role: "player", uses: "1", days: "30", count: "1", note: "" });
  const [made, setMade] = useState<string[]>([]);
  const [problem, setProblem] = useState<string | null>(null);
  if (!data) return <Loading error={error} />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setProblem(null);
    try {
      const { codes } = await post<{ codes: string[] }>("/api/invites", {
        role: form.role, uses: Number(form.uses), days: Number(form.days), count: Number(form.count), note: form.note || null,
      });
      setMade(codes);
      reload();
    } catch (err) {
      setProblem((err as Error).message);
    }
  };
  const link = (code: string) => `${window.location.origin}/signup?invite=${code}`;
  const input = (k: keyof typeof form, label: string, extra: object = {}) => (
    <label>
      {label}
      <input value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} {...extra} />
    </label>
  );

  return (
    <>
      <h1>Invites</h1>
      <form className="form wide left" onSubmit={submit}>
        <div className="pair">
          <label>
            Role
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="player">Player</option>
              <option value="commissioner">Commissioner</option>
              <option value="gamemaker">GameMaker</option>
            </select>
          </label>
          {input("uses", "Accounts per code", { type: "number", min: 1 })}
          {input("days", "Days until it expires (0: never)", { type: "number", min: 0 })}
          {input("count", "How many codes", { type: "number", min: 1, max: 100 })}
        </div>
        {input("note", "Who it's for")}
        {problem && <p className="error">{problem}</p>}
        <button className="button">Make invites</button>
      </form>
      {made.length > 0 && (
        <div className="notice">
          <p>Send each person their link:</p>
          <ul className="plain">
            {made.map((c) => (
              <li key={c}>
                <code>{link(c)}</code>
              </li>
            ))}
          </ul>
        </div>
      )}
      <h2>All invites</h2>
      <div className="scroll">
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>Role</th>
              <th className="num">Used</th>
              <th>Expires</th>
              <th>For</th>
              <th>Accounts</th>
            </tr>
          </thead>
          <tbody>
            {data.map((i) => (
              <tr key={i.code}>
                <td className="nowrap">
                  <code>{i.code}</code>
                </td>
                <td>{i.role}</td>
                <td className="num">
                  {i.uses}/{i.max_uses}
                </td>
                <td>{i.expires_at ? day(i.expires_at) : "never"}</td>
                <td>{i.note}</td>
                <td>{i.accounts.join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
