import { useState } from "react";

/** A button that asks once more before it acts: the first click shows `confirm` and a
Confirm button; errors from `action` show beside it. */
export default function Confirm({
  label,
  confirm,
  action,
  disabled,
  title,
}: {
  label: string;
  confirm: string;
  action: () => Promise<void>;
  disabled?: boolean;
  title?: string;
}) {
  const [asking, setAsking] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  if (!asking) {
    return (
      <button type="button" className="small-button" disabled={disabled} title={title} onClick={() => setAsking(true)}>
        {label}
      </button>
    );
  }
  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      await action();
      setAsking(false);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <span className="confirm">
      <span className="small">{confirm}</span>
      <button type="button" className="small-button primary" disabled={busy} onClick={run}>
        Confirm
      </button>
      <button type="button" className="link small" disabled={busy} onClick={() => (setAsking(false), setError(null))}>
        Cancel
      </button>
      {error && <span className="error small">{error}</span>}
    </span>
  );
}
