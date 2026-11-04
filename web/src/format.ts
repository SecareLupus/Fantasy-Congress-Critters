const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const cents = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 });

export const dollars = (n: number) => money.format(n);
export const dollarsCents = (n: number) => cents.format(n);
export const pts = (n: number | null | undefined, digits = 1) => (n ?? 0).toFixed(digits);
export const pct = (n: number | null | undefined) => (n == null ? "–" : `${(n * 100).toFixed(1)}%`);

export function day(iso: string | null | undefined): string {
  if (!iso) return "–";
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

export function when(iso: string | null | undefined): string {
  if (!iso) return "never";
  return new Date(iso).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}

/** COSPONSOR_ADDED -> Cosponsor added */
export function label(code: string): string {
  const s = code.toLowerCase().replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export const chamberName = (c: string) => (c === "sen" ? "Senate" : "House");

export function partyLetter(party: string | null | undefined): string {
  if (!party) return "?";
  return party.startsWith("Democrat") ? "D" : party.startsWith("Republican") ? "R" : party.charAt(0);
}

export function seat(c: { chamber: string; state: string; district: number | null }): string {
  if (c.chamber === "sen") return c.state;
  return c.district ? `${c.state}-${c.district}` : `${c.state}-AL`;
}

/** "119-hr-2882" -> "H.R. 2882" */
export function billName(id: string): string {
  const [, type, number] = id.split("-");
  const names: Record<string, string> = {
    hr: "H.R.", s: "S.", hjres: "H.J.Res.", sjres: "S.J.Res.", hconres: "H.Con.Res.",
    sconres: "S.Con.Res.", hres: "H.Res.", sres: "S.Res.",
  };
  return `${names[type] ?? type.toUpperCase()} ${number}`;
}

export function congressUrl(id: string): string {
  const [congress, type, number] = id.split("-");
  const kinds: Record<string, string> = {
    hr: "house-bill", s: "senate-bill", hjres: "house-joint-resolution", sjres: "senate-joint-resolution",
    hconres: "house-concurrent-resolution", sconres: "senate-concurrent-resolution",
    hres: "house-resolution", sres: "senate-resolution",
  };
  return `https://www.congress.gov/bill/${congress}th-congress/${kinds[type]}/${number}`;
}

export const leagueType = (t: string) => label(t.replace("_private", " private"));
