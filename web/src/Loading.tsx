/** Placeholder while a page's data loads, or its error. */
export default function Loading({ error }: { error?: string }) {
  return error ? <p className="error">{error}</p> : <p className="muted">Loading…</p>;
}
